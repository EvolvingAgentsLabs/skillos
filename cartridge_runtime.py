"""Cartridge Runtime — Gemma-native Claude-Code-style subagent execution.

A *Cartridge* is a self-contained domain package under ``cartridges/<name>/``:

    cartridges/<name>/
        cartridge.yaml          # manifest
        router.md               # closed-set intent classifier prompt
        agents/*.md             # narrow system prompts + few-shot examples
        flows/*.flow.md         # declarative agent sequences
        schemas/*.schema.json   # JSON Schemas for inter-agent payloads
        validators/*.py         # deterministic post-step checks
        evals/cases.yaml        # regression set (input → expected structure)

The runtime layer supplies:

    Blackboard          typed KV store shared across subagents
    CartridgeRegistry   discovery + intent matching
    CartridgeRunner     executes a flow on a pre-built AgentRuntime

The key design decision: every piece of non-determinism — routing, schema,
tool allow-list, validator — is declared in the cartridge, NOT inferred at
runtime by the LLM. Gemma 4 only needs to fill slots whose shape is already
pinned down.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

try:
    import yaml  # PyYAML
except ImportError:  # pragma: no cover
    yaml = None


# ─────────────────────────────────────────────────────────────────────
# Blackboard
# ─────────────────────────────────────────────────────────────────────

@dataclass
class BlackboardEntry:
    """A single typed value on the cartridge blackboard."""
    value: Any
    schema_ref: str = ""             # filename under cartridge/schemas/
    produced_by: str = ""            # agent name
    description: str = ""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class Blackboard:
    """Typed key-value store shared across subagents in a cartridge flow.

    Each entry carries metadata: its originating agent, an optional JSON
    Schema reference, and a human description that is surfaced to
    downstream agents so they can interpret the data.
    """

    def __init__(self, schemas_dir: str | Path = ""):
        self._entries: dict[str, BlackboardEntry] = {}
        self._schemas_dir = Path(schemas_dir) if schemas_dir else None

    # --- accessors ---------------------------------------------------

    def put(self, key: str, value: Any, *, schema_ref: str = "",
            produced_by: str = "", description: str = "",
            validate: bool = True) -> tuple[bool, str]:
        """Store a value. Returns (ok, message). On schema mismatch, still
        stores the value but returns ok=False so the caller can retry."""
        ok, message = True, "ok"
        if validate and schema_ref and self._schemas_dir:
            ok, message = self._validate_against_schema(value, schema_ref)
        self._entries[key] = BlackboardEntry(
            value=value,
            schema_ref=schema_ref,
            produced_by=produced_by,
            description=description,
        )
        return ok, message

    def get(self, key: str) -> BlackboardEntry | None:
        return self._entries.get(key)

    def value(self, key: str, default: Any = None) -> Any:
        entry = self._entries.get(key)
        return entry.value if entry is not None else default

    def has(self, key: str) -> bool:
        return key in self._entries

    def keys(self) -> list[str]:
        return list(self._entries.keys())

    def snapshot(self) -> dict[str, dict]:
        """Serializable view for persistence or display."""
        return {
            k: {
                "value": e.value,
                "schema_ref": e.schema_ref,
                "produced_by": e.produced_by,
                "description": e.description,
                "created_at": e.created_at,
            }
            for k, e in self._entries.items()
        }

    # --- projections -------------------------------------------------

    def bundle(self, keys: list[str]) -> dict[str, Any]:
        """Return the raw values for a subset of keys — what a subagent
        actually consumes as its ``input_data`` dict."""
        result = {}
        for k in keys:
            if k in self._entries:
                result[k] = self._entries[k].value
        return result

    def describe(self, keys: list[str]) -> str:
        """Render a human-readable description block of selected keys so
        the receiving agent knows what each input means."""
        lines = []
        for k in keys:
            entry = self._entries.get(k)
            if not entry:
                continue
            desc = entry.description or "(no description)"
            origin = entry.produced_by or "user"
            lines.append(f"- `{k}` (from {origin}): {desc}")
        return "\n".join(lines) if lines else "(no inputs)"

    # --- schema validation -------------------------------------------

    def _validate_against_schema(self, value: Any,
                                  schema_ref: str) -> tuple[bool, str]:
        """Attempt JSON Schema validation; falls back to structural check
        if ``jsonschema`` is not installed."""
        if not self._schemas_dir:
            return True, "no schemas_dir configured"
        schema_path = self._schemas_dir / schema_ref
        if not schema_path.exists():
            return True, f"schema file missing: {schema_ref}"
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return False, f"could not parse schema: {exc}"

        try:
            import jsonschema  # type: ignore
            try:
                jsonschema.validate(value, schema)
                return True, "schema ok"
            except jsonschema.ValidationError as exc:
                return False, f"schema violation: {exc.message}"
        except ImportError:
            return _minimal_schema_check(value, schema)


def _minimal_schema_check(value: Any, schema: dict) -> tuple[bool, str]:
    """Very small dependency-free structural check.

    Verifies top-level type and (for objects) that all ``required`` keys
    are present. Not a full JSON Schema implementation — just enough to
    catch catastrophic format errors when ``jsonschema`` is unavailable.
    """
    expected = schema.get("type")
    if expected == "object":
        if not isinstance(value, dict):
            return False, "expected object"
        for req in schema.get("required", []):
            if req not in value:
                return False, f"missing required field '{req}'"
    elif expected == "array":
        if not isinstance(value, list):
            return False, "expected array"
    elif expected == "string" and not isinstance(value, str):
        return False, "expected string"
    elif expected == "integer" and not isinstance(value, int):
        return False, "expected integer"
    elif expected == "number" and not isinstance(value, (int, float)):
        return False, "expected number"
    elif expected == "boolean" and not isinstance(value, bool):
        return False, "expected boolean"
    return True, "ok (minimal check)"


# ─────────────────────────────────────────────────────────────────────
# Cartridge manifest + agent spec
# ─────────────────────────────────────────────────────────────────────

@dataclass
class AgentSpec:
    """Parsed agent definition from cartridges/<name>/agents/<agent>.md."""
    name: str
    path: str
    body: str                        # system prompt (markdown sans frontmatter)
    needs: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    produces_schema: str = ""        # filename, e.g. weekly_menu.schema.json
    produces_description: str = ""
    tools: list[str] = field(default_factory=list)
    max_turns: int = 3
    description: str = ""


@dataclass
class SkillStep:
    """A single step in a multi-skill flow (Upgrade 4)."""
    skill: str                           # skill name to execute
    needs: list[str] = field(default_factory=list)
    produces: list[str] = field(default_factory=list)
    produces_schema: str = ""
    data_map: dict[str, str] = field(default_factory=dict)  # remap blackboard keys → skill params
    defaults: dict[str, Any] = field(default_factory=dict)  # default values injected into data


@dataclass
class FlowDef:
    """A flow definition — supports both agent lists and skill step lists."""
    steps: list[str | SkillStep] = field(default_factory=list)
    mode: str = "standard"               # "standard", "agentic"

    @property
    def is_agentic(self) -> bool:
        return self.mode == "agentic"


@dataclass
class CartridgeManifest:
    """Parsed cartridge.yaml."""
    name: str
    path: str
    description: str = ""
    entry_intents: list[str] = field(default_factory=list)
    flows: dict[str, list[str]] = field(default_factory=dict)
    flow_defs: dict[str, FlowDef] = field(default_factory=dict)
    blackboard_schema: dict[str, str] = field(default_factory=dict)
    validators: list[str] = field(default_factory=list)
    max_turns_per_agent: int = 3
    default_flow: str = ""
    variables: dict[str, Any] = field(default_factory=dict)
    type: str = "standard"           # "standard" (LLM agents) or "js-skills"
    skills_source: str = ""          # path to Gallery skills directory (for js-skills)


def _parse_flow_steps(raw: list) -> list:
    """Parse flow step definitions from YAML.

    Supports:
      - Simple strings: "agent-name"
      - Rich dicts: {skill: "name", needs: [...], produces: [...]}
    """
    steps = []
    for item in raw:
        if isinstance(item, str):
            steps.append(item)
        elif isinstance(item, dict):
            steps.append(SkillStep(
                skill=item.get("skill", item.get("name", "")),
                needs=list(item.get("needs", []) or []),
                produces=list(item.get("produces", []) or []),
                produces_schema=item.get("produces_schema", ""),
                data_map=dict(item.get("data_map", {}) or {}),
                defaults=dict(item.get("defaults", {}) or {}),
            ))
        else:
            steps.append(str(item))
    return steps


# ─────────────────────────────────────────────────────────────────────
# Registry
# ─────────────────────────────────────────────────────────────────────

class CartridgeRegistry:
    """Discovers cartridges on disk and offers intent matching."""

    def __init__(self, root: str | Path = "cartridges"):
        self.root = Path(root)
        self._manifests: dict[str, CartridgeManifest] = {}
        self._agents_cache: dict[tuple[str, str], AgentSpec] = {}
        if self.root.exists():
            self._load_all()

    # --- loading -----------------------------------------------------

    def _load_all(self) -> None:
        for entry in sorted(self.root.iterdir()):
            if not entry.is_dir():
                continue
            yaml_path = entry / "cartridge.yaml"
            if not yaml_path.exists():
                continue
            try:
                manifest = self._load_manifest(yaml_path)
                self._manifests[manifest.name] = manifest
            except Exception as exc:  # pragma: no cover
                print(f"[cartridge-registry] skipped {entry.name}: {exc}")

    def _load_manifest(self, yaml_path: Path) -> CartridgeManifest:
        if yaml is None:
            raise RuntimeError("PyYAML not installed — run `pip install pyyaml`")
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        cartridge_dir = yaml_path.parent
        flows_raw = data.get("flows", {}) or {}
        if isinstance(flows_raw, list):
            flat = {}
            for item in flows_raw:
                if isinstance(item, dict):
                    flat.update(item)
            flows_raw = flat

        # Parse flows into both legacy format (list[str]) and rich FlowDef
        flows_legacy: dict[str, list[str]] = {}
        flow_defs: dict[str, FlowDef] = {}
        for fname, fval in flows_raw.items():
            if isinstance(fval, dict):
                # Rich format: {mode: "agentic", tools: [...]} or step dicts
                mode = fval.get("mode", "standard")
                steps_raw = fval.get("steps", fval.get("tools", []))
                steps = _parse_flow_steps(steps_raw)
                flow_defs[fname] = FlowDef(steps=steps, mode=mode)
                flows_legacy[fname] = [
                    s if isinstance(s, str) else s.skill for s in steps
                ]
            elif isinstance(fval, list):
                steps = _parse_flow_steps(fval)
                flow_defs[fname] = FlowDef(steps=steps, mode="standard")
                flows_legacy[fname] = [
                    s if isinstance(s, str) else s.skill for s in steps
                ]
            else:
                flows_legacy[fname] = [str(fval)]
                flow_defs[fname] = FlowDef(steps=[str(fval)])

        # Resolve skills_source relative to cartridge directory
        skills_source = data.get("skills_source", "")
        if skills_source:
            resolved = (cartridge_dir / skills_source).resolve()
            skills_source = str(resolved)

        manifest = CartridgeManifest(
            name=data.get("name", cartridge_dir.name),
            path=str(cartridge_dir),
            description=data.get("description", ""),
            entry_intents=list(data.get("entry_intents", []) or []),
            flows=flows_legacy,
            flow_defs=flow_defs,
            blackboard_schema=dict(data.get("blackboard_schema", {}) or {}),
            validators=list(data.get("validators", []) or []),
            max_turns_per_agent=int(data.get("max_turns_per_agent", 3)),
            default_flow=data.get("default_flow", ""),
            variables=dict(data.get("variables", {}) or {}),
            type=data.get("type", "standard"),
            skills_source=skills_source,
        )
        if not manifest.default_flow and manifest.flows:
            manifest.default_flow = next(iter(manifest.flows.keys()))
        return manifest

    # --- accessors ---------------------------------------------------

    def list(self) -> list[CartridgeManifest]:
        return list(self._manifests.values())

    def names(self) -> list[str]:
        return list(self._manifests.keys())

    def get(self, name: str) -> CartridgeManifest | None:
        return self._manifests.get(name)

    def load_agent(self, cartridge: str, agent_name: str) -> AgentSpec | None:
        cache_key = (cartridge, agent_name)
        if cache_key in self._agents_cache:
            return self._agents_cache[cache_key]
        manifest = self.get(cartridge)
        if not manifest:
            return None
        agent_path = Path(manifest.path) / "agents" / f"{agent_name}.md"
        if not agent_path.exists():
            return None
        content = agent_path.read_text(encoding="utf-8")
        frontmatter, body = _split_frontmatter(content)
        spec = AgentSpec(
            name=frontmatter.get("name", agent_name),
            path=str(agent_path),
            body=body,
            needs=list(frontmatter.get("needs", []) or []),
            produces=list(frontmatter.get("produces", []) or []),
            produces_schema=frontmatter.get("produces_schema", ""),
            produces_description=frontmatter.get("produces_description", ""),
            tools=list(frontmatter.get("tools", []) or []),
            max_turns=int(frontmatter.get("max_turns",
                                          manifest.max_turns_per_agent)),
            description=frontmatter.get("description", ""),
        )
        self._agents_cache[cache_key] = spec
        return spec

    # --- intent matching ---------------------------------------------

    def match_intent(self, goal: str,
                     min_score: int = 2) -> tuple[str | None, int]:
        """Keyword-overlap router. No LLM call.

        Returns (cartridge_name, score). Score is the count of intent
        tokens (≥ 3 chars, not stopwords) that appear in the goal.
        Requires score ≥ ``min_score`` to avoid spurious matches.
        """
        best, best_score = None, 0
        goal_tokens = _tokenize(goal)
        for m in self._manifests.values():
            for intent in m.entry_intents:
                intent_tokens = _tokenize(intent)
                overlap = sum(1 for t in intent_tokens if t in goal_tokens)
                if overlap > best_score:
                    best_score, best = overlap, m.name
        if best_score < min_score:
            return None, best_score
        return best, best_score


_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with",
    "my", "your", "our", "is", "are", "be", "do", "make", "create",
})


def _tokenize(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-zA-Z]{3,}", text.lower())
            if t not in _STOPWORDS}


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter. Returns (frontmatter, body)."""
    if not text.startswith("---"):
        return {}, text
    if yaml is None:
        return {}, text
    try:
        end = text.index("\n---", 3)
    except ValueError:
        return {}, text
    block = text[3:end].strip()
    body = text[end + 4:].lstrip()
    data = yaml.safe_load(block) or {}
    return (data if isinstance(data, dict) else {}), body


# ─────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────

@dataclass
class StepResult:
    agent: str
    produced_keys: list[str] = field(default_factory=list)
    raw_output: str = ""
    validated: bool = False
    message: str = "pending"
    attempts: int = 0


@dataclass
class RunResult:
    cartridge: str
    flow: str
    goal: str
    steps: list[StepResult] = field(default_factory=list)
    blackboard: dict[str, dict] = field(default_factory=dict)
    ok: bool = False
    final_summary: str = ""


class CartridgeRunner:
    """Executes a cartridge flow on top of an AgentRuntime.

    The runner never spawns the LLM provider itself — the caller builds
    an ``AgentRuntime`` (Gemma, Qwen, Gemini, …) and passes it in. This
    keeps the cartridge layer provider-agnostic and cheaply testable.

    Required runtime duck-type (matches agent_runtime.AgentRuntime):

        _handle_delegate_to_agent(agent_name, task_description,
                                  input_data, max_turns) -> str
        _call_llm(messages) -> str

    For ``type: js-skills`` cartridges, the runner also handles deterministic
    JS skill execution via Node.js (no LLM call for the execution step).
    """

    PRODUCES_RE = re.compile(r"<produces>(.*?)</produces>", re.DOTALL)

    def __init__(self, runtime: Any, registry: CartridgeRegistry,
                 *, verbose: bool = True,
                 max_retries_per_step: int = 1):
        self.rt = runtime
        self.registry = registry
        self.verbose = verbose
        self.max_retries = max_retries_per_step
        self._skill_registries: dict[str, Any] = {}  # lazy-loaded per cartridge

    # --- public API --------------------------------------------------

    def run(self, cartridge_name: str, goal: str,
            *, flow: str | None = None,
            initial_inputs: dict[str, Any] | None = None) -> RunResult:
        manifest = self.registry.get(cartridge_name)
        if not manifest:
            raise KeyError(f"unknown cartridge: {cartridge_name}")

        flow_name = flow or self._select_flow(manifest, goal)
        agent_sequence = manifest.flows.get(flow_name)
        if not agent_sequence:
            raise KeyError(f"unknown flow '{flow_name}' in {cartridge_name}")

        flow_def = manifest.flow_defs.get(flow_name, FlowDef(steps=agent_sequence))

        schemas_dir = Path(manifest.path) / "schemas"
        bb = Blackboard(schemas_dir=schemas_dir)
        bb.put("user_goal", goal, produced_by="user",
               description="The original user request")
        for k, v in (initial_inputs or {}).items():
            bb.put(k, v, produced_by="user",
                   description=f"User-supplied input: {k}")

        # For js-skills cartridges: pre-select skill and inject instructions
        if manifest.type == "js-skills" and not flow_def.is_agentic:
            self._prepare_js_skills_context(manifest, goal, bb)

        result = RunResult(cartridge=cartridge_name, flow=flow_name, goal=goal)
        self._log(f"\n=== Cartridge '{cartridge_name}' flow '{flow_name}' ===")

        # Upgrade 2: Agentic mode — LLM has full control with skill tools
        if flow_def.is_agentic:
            step = self._run_agentic_flow(manifest, goal, bb)
            result.steps.append(step)
        else:
            # Standard sequential flow (supports both agent names and SkillSteps)
            for step_def in flow_def.steps:
                step = self._execute_flow_step(manifest, step_def, bb)
                result.steps.append(step)
                if not step.validated and self.max_retries > 0:
                    step.attempts += 1
                    step_name = step_def if isinstance(step_def, str) else step_def.skill
                    self._log(f"  [retry] {step_name}: {step.message}")
                    retry = self._execute_flow_step(
                        manifest, step_def, bb,
                        retry_feedback=step.message)
                    retry.attempts = step.attempts + retry.attempts
                    result.steps[-1] = retry

        # Deterministic validators (pure Python, declared on manifest)
        validator_messages = self._run_validators(manifest, bb)
        result.ok = all(s.validated for s in result.steps) and \
                    all(m.startswith("ok") for m in validator_messages)
        result.blackboard = bb.snapshot()
        result.final_summary = self._render_summary(manifest, flow_name,
                                                    result.steps,
                                                    validator_messages, bb)
        self._log(result.final_summary)
        return result

    def _execute_flow_step(self, manifest: CartridgeManifest,
                           step_def: str | SkillStep,
                           bb: Blackboard,
                           *, retry_feedback: str = "") -> "StepResult":
        """Execute a single flow step — dispatches to the right executor.

        Handles:
        - String agent names (legacy: "param-extractor", "js-executor")
        - SkillStep objects (Upgrade 4: multi-skill chaining with needs/produces)
        """
        # Legacy string step
        if isinstance(step_def, str):
            if manifest.type == "js-skills" and step_def == "js-executor":
                return self._run_js_skill(manifest, bb)
            return self._run_agent(manifest, step_def, bb,
                                   retry_feedback=retry_feedback)

        # Upgrade 4: SkillStep — direct JS skill execution with Blackboard I/O
        return self._run_skill_step(manifest, step_def, bb)

    # --- js-skills support ---------------------------------------------

    def _get_skill_registry(self, manifest: CartridgeManifest):
        """Lazy-load the SkillRegistry for a js-skills cartridge."""
        if manifest.name in self._skill_registries:
            return self._skill_registries[manifest.name]

        import sys as _sys
        _exp_dir = str(Path(__file__).resolve().parent / "experiments" / "gemma4-skills")
        if _exp_dir not in _sys.path:
            _sys.path.insert(0, _exp_dir)
        from skill_loader import SkillRegistry

        skills_dirs = []
        # Primary: skills_source from cartridge.yaml
        if manifest.skills_source:
            src = Path(manifest.skills_source)
            if src.is_dir():
                # Check if it has subdirs (built-in/, featured/) or is flat
                subdirs = [d for d in src.iterdir() if d.is_dir()]
                has_skill_md = any((d / "SKILL.md").exists() for d in subdirs)
                if has_skill_md:
                    skills_dirs.append(str(src))
                else:
                    # Nested: skills_source/built-in/, skills_source/featured/
                    for d in subdirs:
                        if d.is_dir():
                            skills_dirs.append(str(d))
        # Fallback: skills/ directory inside the cartridge
        cartridge_skills = Path(manifest.path) / "skills"
        if cartridge_skills.is_dir():
            skills_dirs.append(str(cartridge_skills))

        registry = SkillRegistry(*skills_dirs)
        self._skill_registries[manifest.name] = registry
        self._log(f"  📦 Loaded {len(registry)} Gallery JS skills for '{manifest.name}'")
        return registry

    def _prepare_js_skills_context(self, manifest: CartridgeManifest,
                                    goal: str, bb: Blackboard) -> None:
        """Pre-select the best-matching skill and inject its instructions
        onto the blackboard so the param-extractor agent has full context."""
        skill_reg = self._get_skill_registry(manifest)

        # Use the router (LLM or keyword) to pick a skill
        selected_skill = self._route_to_skill(manifest, goal, skill_reg)
        skill_def = skill_reg.get(selected_skill)

        if skill_def:
            bb.put("selected_skill", selected_skill,
                   produced_by="router",
                   description=f"Selected Gallery JS skill: {selected_skill}")
            bb.put("skill_instructions", skill_def.instructions,
                   produced_by="router",
                   description=f"SKILL.md instructions for {selected_skill}")
            bb.put("skill_descriptions", skill_reg.descriptions(),
                   produced_by="registry",
                   description="All available skills with descriptions")
            self._log(f"  🎯 Routed to skill: {selected_skill}")
        else:
            # Fallback: let param-extractor choose from all skills
            bb.put("selected_skill", "",
                   produced_by="router",
                   description="No specific skill selected — param-extractor must choose")
            bb.put("skill_instructions", "",
                   produced_by="router",
                   description="No skill instructions — see skill_descriptions")
            bb.put("skill_descriptions", skill_reg.descriptions(),
                   produced_by="registry",
                   description="All available skills with descriptions")
            self._log(f"  ⚠️ No skill matched — param-extractor will choose")

    def _route_to_skill(self, manifest: CartridgeManifest,
                        goal: str, skill_reg) -> str:
        """Route user goal to a specific Gallery skill.

        Uses the router.md LLM classifier if available, with keyword
        fallback against skill names and descriptions.
        """
        router_md = Path(manifest.path) / "router.md"
        skill_names = skill_reg.names()

        # Try LLM router
        if router_md.exists() and hasattr(self.rt, "_call_llm"):
            prompt = router_md.read_text(encoding="utf-8")
            system = ("You classify a user goal into exactly one skill name "
                      "from a closed set. Reply with ONE WORD: the skill name.")
            user = (f"{prompt}\n\n"
                    f"USER GOAL: {goal}\n\n"
                    f"AVAILABLE SKILLS: {', '.join(skill_names)}\n\n"
                    f"ANSWER:")
            try:
                resp = self.rt._call_llm([
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ])
                if resp:
                    resp_clean = resp.strip().splitlines()[0].strip(" .\"'`*")
                    for sname in skill_names:
                        if sname.lower() == resp_clean.lower():
                            return sname
                    for sname in skill_names:
                        if sname.lower() in resp_clean.lower():
                            return sname
            except Exception as exc:
                self._log(f"  [router] LLM failed, falling back: {exc}")

        # Keyword fallback: match against skill names and descriptions
        goal_tokens = set(_tokenize(goal))
        best, best_score = skill_names[0] if skill_names else "", 0
        for sname in skill_names:
            name_tokens = set(_tokenize(sname.replace("-", " ")))
            skill_def = skill_reg.get(sname)
            desc_tokens = set(_tokenize(skill_def.description)) if skill_def else set()
            all_tokens = name_tokens | desc_tokens
            score = len(goal_tokens & all_tokens)
            if score > best_score:
                best, best_score = sname, score
        return best

    def _run_js_skill(self, manifest: CartridgeManifest,
                      bb: Blackboard) -> "StepResult":
        """Execute a Gallery JS skill deterministically via Node.js.

        Reads skill_params from the blackboard (produced by param-extractor),
        runs the JS skill, and stores skill_result on the blackboard.
        """
        import sys as _sys
        _exp_dir = str(Path(__file__).resolve().parent / "experiments" / "gemma4-skills")
        if _exp_dir not in _sys.path:
            _sys.path.insert(0, _exp_dir)
        from js_executor import run_skill as exec_js

        self._log(f"\n--- Step: js-executor (deterministic) ---")

        params = bb.value("skill_params")
        if not params:
            return StepResult(agent="js-executor", validated=False,
                              message="skill_params not found on blackboard")

        if isinstance(params, str):
            try:
                params = json.loads(params)
            except json.JSONDecodeError:
                return StepResult(agent="js-executor", validated=False,
                                  message=f"skill_params is not valid JSON: {params[:200]}")

        skill_name = params.get("skill_name", "")
        data = params.get("data", "{}")
        secret = params.get("secret", "")

        # Ensure data is a string
        if isinstance(data, dict):
            data = json.dumps(data)

        skill_reg = self._get_skill_registry(manifest)
        skill_def = skill_reg.get(skill_name)
        if not skill_def:
            available = ", ".join(skill_reg.names())
            return StepResult(
                agent="js-executor", validated=False,
                message=f"skill '{skill_name}' not found. Available: {available}")

        self._log(f"  🔧 Executing: {skill_name}")
        self._log(f"  📥 Data: {data[:200]}")

        timeout = int(manifest.variables.get("node_timeout", 30))
        cfg = self._build_runtime_config(manifest)
        result = exec_js(skill_def, data, secret, timeout=timeout, config=cfg)

        self._log(f"  📤 Result: {result.to_llm_string()[:200]}")

        # Store result on blackboard
        result_dict = result.raw or {}
        schema_ref = manifest.blackboard_schema.get("skill_result", "")
        ok, msg = bb.put("skill_result", result_dict,
                         schema_ref=schema_ref,
                         produced_by="js-executor",
                         description=f"JS execution result from {skill_name}")

        validated = result.ok and ok
        message = "ok" if validated else (result.error or msg or "execution failed")

        return StepResult(
            agent="js-executor",
            produced_keys=["skill_result"] if validated else [],
            raw_output=result.to_llm_string(),
            validated=validated,
            message=message,
        )

    # --- Upgrade 4: Multi-skill chaining ──────────────────────────────

    def _run_skill_step(self, manifest: CartridgeManifest,
                        step: SkillStep, bb: Blackboard) -> "StepResult":
        """Execute a SkillStep — a JS skill with explicit needs/produces.

        Unlike _run_js_skill (which reads skill_params from blackboard),
        this method bundles the skill's declared `needs` from the blackboard,
        passes them as the `data` JSON, and stores the result under `produces`.
        """
        import sys as _sys
        _exp_dir = str(Path(__file__).resolve().parent / "experiments" / "gemma4-skills")
        if _exp_dir not in _sys.path:
            _sys.path.insert(0, _exp_dir)
        from js_executor import run_skill as exec_js, RuntimeConfig

        skill_reg = self._get_skill_registry(manifest)
        skill_def = skill_reg.get(step.skill)

        if not skill_def:
            return StepResult(agent=step.skill, validated=False,
                              message=f"skill '{step.skill}' not found")

        # Check blackboard has all needed inputs
        missing = [k for k in step.needs if not bb.has(k)]
        if missing:
            return StepResult(agent=step.skill, validated=False,
                              message=f"blackboard missing: {missing}")

        # Bundle needs into data JSON
        data_dict = {}

        # Apply data_map if specified (explicit key remapping)
        if step.data_map:
            for target_key, source_key in step.data_map.items():
                data_dict[target_key] = bb.value(source_key)
        else:
            for key in step.needs:
                data_dict[key] = bb.value(key)

        # Apply defaults
        for k, v in step.defaults.items():
            if k not in data_dict:
                data_dict[k] = v

        # Smart mapping: if no data_map and single need with a simple value,
        # try to auto-map by inspecting SKILL.md instructions
        if not step.data_map and skill_def.instructions and len(step.needs) == 1:
            key = step.needs[0]
            val = data_dict[key]
            if isinstance(val, str):
                import re as _re
                field_matches = _re.findall(
                    r'[-*]\s+\*?\*?(\w+)\*?\*?:\s', skill_def.instructions)
                if field_matches:
                    mapped = {field_matches[0]: val}
                    if "lang" in [f.lower() for f in field_matches]:
                        mapped["lang"] = "en"
                    # Preserve defaults
                    for k, v in step.defaults.items():
                        mapped[k] = v
                    data_dict = mapped
                elif key == "user_goal":
                    data_dict = {"text": val}
                    for k, v in step.defaults.items():
                        data_dict[k] = v

        data_json = json.dumps(data_dict)

        self._log(f"\n--- SkillStep: {step.skill} "
                  f"(needs={step.needs}, produces={step.produces}) ---")

        # Build runtime config
        cfg = self._build_runtime_config(manifest)
        timeout = int(manifest.variables.get("node_timeout", 30))
        result = exec_js(skill_def, data_json, "", timeout=timeout, config=cfg)

        self._log(f"  📤 Result: {result.to_llm_string()[:200]}")

        if not result.ok:
            return StepResult(agent=step.skill, validated=False,
                              message=result.error or "skill execution failed")

        # Store produces on blackboard
        result_data = result.raw or {}
        # If skill returns {result: "..."}, and produces has one key,
        # store the result string directly
        if step.produces:
            if len(step.produces) == 1 and "result" in result_data:
                val = result_data["result"]
                schema_ref = (manifest.blackboard_schema.get(step.produces[0])
                              or step.produces_schema)
                bb.put(step.produces[0], val,
                       schema_ref=schema_ref,
                       produced_by=step.skill,
                       description=f"Output from {step.skill}")
            else:
                # Store entire result dict, or map keys
                for key in step.produces:
                    val = result_data.get(key, result_data.get("result", ""))
                    schema_ref = (manifest.blackboard_schema.get(key)
                                  or step.produces_schema)
                    bb.put(key, val,
                           schema_ref=schema_ref,
                           produced_by=step.skill,
                           description=f"Output from {step.skill}")

        return StepResult(
            agent=step.skill,
            produced_keys=list(step.produces),
            raw_output=result.to_llm_string(),
            validated=True,
            message="ok",
        )

    def _build_runtime_config(self, manifest: CartridgeManifest):
        """Build RuntimeConfig from manifest and runtime state."""
        import sys as _sys
        _exp_dir = str(Path(__file__).resolve().parent / "experiments" / "gemma4-skills")
        if _exp_dir not in _sys.path:
            _sys.path.insert(0, _exp_dir)
        from js_executor import RuntimeConfig

        state_dir = str((Path(manifest.path) / "state").resolve())

        # Extract LLM config from the AgentRuntime if available
        llm_url = ""
        llm_model = manifest.variables.get("gemma_model", "gemma4:e2b")
        llm_key = "ollama"
        if hasattr(self.rt, "client"):
            llm_url = str(getattr(self.rt.client, "base_url", ""))
            llm_model = getattr(self.rt, "model", llm_model)
            llm_key = getattr(self.rt, "api_key", llm_key) or llm_key

        return RuntimeConfig(
            state_dir=state_dir,
            llm_api_url=llm_url,
            llm_model=llm_model,
            llm_api_key=llm_key,
            shared_state_name=manifest.name,  # all skills in cartridge share state
        )

    # --- Upgrade 2: Agentic flow mode ─────────────────────────────────

    def _run_agentic_flow(self, manifest: CartridgeManifest,
                          goal: str, bb: Blackboard) -> "StepResult":
        """Run a flow in agentic mode — the LLM has load_skill + run_js tools
        and decides autonomously which skills to use.

        This mirrors Gallery's Android approach: the LLM gets a list of skills
        and their descriptions, then decides whether and how to use them.
        """
        skill_reg = self._get_skill_registry(manifest)

        self._log(f"\n--- Agentic mode: LLM has full skill control ---")

        # Build system prompt with skill list (like Gallery's AgentChatTaskModule)
        skill_list = skill_reg.descriptions()
        system_prompt = (
            "You are an AI assistant that helps users by answering questions "
            "and completing tasks using skills.\n\n"
            "For EVERY new task or request, follow these steps:\n"
            "1. Find the most relevant skill from:\n"
            f"{skill_list}\n\n"
            "2. If a relevant skill exists, use the `load_skill` tool to read its instructions.\n"
            "3. Follow the skill's instructions exactly to call `run_js`.\n"
            "4. Present the result to the user.\n"
            "5. If no skill is relevant, answer directly from your knowledge.\n\n"
            "Output ONLY the final result."
        )

        # Register skill tools for the agentic loop
        import sys as _sys
        _exp_dir = str(Path(__file__).resolve().parent / "experiments" / "gemma4-skills")
        if _exp_dir not in _sys.path:
            _sys.path.insert(0, _exp_dir)
        from js_executor import run_skill as exec_js

        cfg = self._build_runtime_config(manifest)

        def load_skill_tool(skill_name: str) -> str:
            """Load a skill's instructions."""
            skill = skill_reg.get(skill_name.strip())
            if not skill:
                return f"Skill '{skill_name}' not found. Available: {', '.join(skill_reg.names())}"
            return f"# Skill: {skill.name}\n\n{skill.instructions}"

        def run_js_tool(skill_name: str, script_name: str = "index.html",
                        data: str = "{}") -> str:
            """Execute a JS skill."""
            skill = skill_reg.get(skill_name.strip())
            if not skill:
                return f"Error: skill '{skill_name}' not found"
            result = exec_js(skill, data, "", timeout=30, config=cfg)
            return result.to_llm_string()

        # Save and inject tools into the runtime
        original_tools = dict(self.rt.tools) if hasattr(self.rt, "tools") else {}
        try:
            if hasattr(self.rt, "tools"):
                self.rt.tools["load_skill"] = load_skill_tool
                self.rt.tools["run_js"] = run_js_tool

            # Build the tool format instructions for the LLM
            tool_instructions = (
                "\n\n## AVAILABLE TOOLS\n\n"
                "You have these tools:\n\n"
                '### load_skill\nLoad a skill\'s instructions. Call with:\n'
                '<tool_call name="load_skill">\n'
                '{"skill_name": "the-skill-name"}\n'
                '</tool_call>\n\n'
                '### run_js\nExecute a JS skill. Call with:\n'
                '<tool_call name="run_js">\n'
                '{"skill_name": "the-skill-name", "script_name": "index.html", '
                '"data": "{\\"param\\": \\"value\\"}"}\n'
                '</tool_call>\n\n'
                "After getting the result, respond with:\n"
                "<final_answer>\nYour response to the user\n</final_answer>"
            )

            task_prompt = f"USER GOAL: {goal}"

            # Use the runtime's delegation mechanism
            raw_output = self.rt._handle_delegate_to_agent(
                agent_name="agentic-skill-agent",
                task_description=task_prompt,
                input_data={"goal": goal, "available_skills": skill_reg.names()},
                max_turns=manifest.max_turns_per_agent + 2,  # extra turns for load+run
            )
        finally:
            # Restore original tools
            if hasattr(self.rt, "tools"):
                self.rt.tools.clear()
                self.rt.tools.update(original_tools)

        # Extract any skill_result from the output for blackboard
        if raw_output:
            bb.put("agentic_output", raw_output,
                   produced_by="agentic-flow",
                   description="Full output from agentic skill execution")

        return StepResult(
            agent="agentic-flow",
            produced_keys=["agentic_output"],
            raw_output=raw_output or "",
            validated=bool(raw_output),
            message="ok" if raw_output else "no output from agentic flow",
        )

    # --- internals ---------------------------------------------------

    def _select_flow(self, manifest: CartridgeManifest, goal: str) -> str:
        """Router: prefers LLM classifier from router.md if it exists and
        returns a known flow; otherwise falls back to keyword matching
        against each flow name, then to ``default_flow``."""
        router_md = Path(manifest.path) / "router.md"
        flow_names = list(manifest.flows.keys())

        if router_md.exists() and hasattr(self.rt, "_call_llm"):
            prompt = router_md.read_text(encoding="utf-8")
            system = ("You classify a user goal into exactly one flow name "
                      "from a closed set. Reply with ONE WORD: the flow name.")
            user = (f"{prompt}\n\n"
                    f"USER GOAL: {goal}\n\n"
                    f"AVAILABLE FLOWS: {', '.join(flow_names)}\n\n"
                    f"ANSWER:")
            try:
                resp = self.rt._call_llm([
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ])
                if resp:
                    resp_clean = resp.strip().splitlines()[0].strip(" .\"'`*")
                    for fname in flow_names:
                        if fname.lower() == resp_clean.lower():
                            return fname
                    for fname in flow_names:
                        if fname.lower() in resp_clean.lower():
                            return fname
            except Exception as exc:  # pragma: no cover
                self._log(f"[router] LLM failed, falling back: {exc}")

        # Fallback: keyword overlap against flow names
        goal_tokens = _tokenize(goal)
        best, best_score = manifest.default_flow or flow_names[0], 0
        for fname in flow_names:
            fname_tokens = _tokenize(fname.replace("-", " "))
            score = sum(1 for t in fname_tokens if t in goal_tokens)
            if score > best_score:
                best, best_score = fname, score
        return best

    def _run_agent(self, manifest: CartridgeManifest, agent_name: str,
                   bb: Blackboard,
                   *, retry_feedback: str = "") -> StepResult:
        spec = self.registry.load_agent(manifest.name, agent_name)
        if spec is None:
            return StepResult(agent=agent_name, validated=False,
                              message=f"agent spec not found: {agent_name}")

        missing = [k for k in spec.needs if not bb.has(k)]
        if missing:
            return StepResult(agent=agent_name, validated=False,
                              message=f"blackboard missing inputs: {missing}")

        input_data = bb.bundle(spec.needs)
        input_descriptions = bb.describe(spec.needs)

        task_description = self._compose_task(spec, input_descriptions,
                                              retry_feedback)
        self._log(f"\n--- Agent: {agent_name} "
                  f"(needs={spec.needs}, produces={spec.produces}) ---")

        raw_output = ""
        try:
            raw_output = self.rt._handle_delegate_to_agent(
                agent_name=agent_name,
                task_description=task_description,
                input_data=input_data,
                max_turns=spec.max_turns,
            )
        except Exception as exc:  # pragma: no cover
            return StepResult(agent=agent_name, raw_output=str(exc),
                              validated=False, message=f"delegation error: {exc}")

        produced = self._extract_produced(raw_output)
        validated_keys: list[str] = []
        status_messages: list[str] = []

        if not spec.produces:
            # Declarative-output-free agents (pure side-effect): accept raw.
            step = StepResult(agent=agent_name, raw_output=raw_output,
                              validated=True, message="ok (no produces)")
            return step

        if produced is None:
            return StepResult(
                agent=agent_name,
                raw_output=raw_output,
                validated=False,
                message=("no <produces>{...}</produces> JSON block found — "
                         "wrap your output in <produces>...</produces>"),
            )

        for key in spec.produces:
            if key not in produced:
                status_messages.append(f"missing key '{key}' in produces JSON")
                continue
            schema_ref = (manifest.blackboard_schema.get(key)
                          or spec.produces_schema)
            ok, msg = bb.put(
                key, produced[key],
                schema_ref=schema_ref,
                produced_by=agent_name,
                description=spec.produces_description or
                            f"Produced by {agent_name}",
            )
            if ok:
                validated_keys.append(key)
            else:
                status_messages.append(f"{key}: {msg}")

        all_present = len(validated_keys) == len(spec.produces)
        step = StepResult(
            agent=agent_name,
            produced_keys=validated_keys,
            raw_output=raw_output,
            validated=all_present and not status_messages,
            message="ok" if (all_present and not status_messages)
                    else "; ".join(status_messages) or "partial",
        )
        return step

    def _compose_task(self, spec: AgentSpec,
                      input_descriptions: str,
                      retry_feedback: str) -> str:
        produces_clause = ""
        if spec.produces:
            produces_clause = (
                "\n\n## REQUIRED OUTPUT\n\n"
                "CRITICAL: You MUST include a `<produces>` JSON block in your response.\n"
                "Do NOT use write_file for this output. Do NOT save it to a file.\n"
                "Put the `<produces>` block INSIDE your `<final_answer>` tags.\n\n"
                f"Produce exactly these keys: {spec.produces}\n"
                f"{('Conform to schema: ' + spec.produces_schema) if spec.produces_schema else ''}\n\n"
                "Wrap the JSON object in `<produces>` tags, like this:\n\n"
                "<final_answer>\n"
                "<produces>\n"
                "{\n"
                + ",\n".join(f'  \"{k}\": ...' for k in spec.produces) +
                "\n}\n"
                "</produces>\n"
                "</final_answer>\n\n"
                "Do NOT put anything between the opening `<produces>` and the `{`. "
                "Do NOT include commentary inside the JSON. "
                "Do NOT use write_file — return the JSON inline in `<produces>` tags."
            )
        retry_clause = ""
        if retry_feedback:
            retry_clause = (
                "\n\n## RETRY FEEDBACK\n\n"
                f"Previous attempt failed validation: {retry_feedback}\n"
                "Fix the issue and produce a compliant `<produces>` block."
            )
        return (
            f"# Agent Role\n\n{spec.body}\n\n"
            f"## INPUTS\n\nYou will receive these blackboard entries:\n"
            f"{input_descriptions}\n"
            f"{produces_clause}"
            f"{retry_clause}"
        )

    def _extract_produced(self, response: str) -> dict | None:
        """Parse the `<produces>{...}</produces>` JSON block.

        Falls back to the first balanced `{...}` JSON object if no tag
        is present (common Gemma glitch). Returns ``None`` if neither
        pattern yields valid JSON.
        """
        match = self.PRODUCES_RE.search(response)
        candidates: list[str] = []
        if match:
            candidates.append(match.group(1).strip())
        # Fallback: any fenced json block
        for fenced in re.findall(r"```json\s*(.*?)```", response, re.DOTALL):
            candidates.append(fenced.strip())
        # Last resort: first balanced {...}
        bal = _extract_first_json_object(response)
        if bal:
            candidates.append(bal)

        for cand in candidates:
            try:
                parsed = json.loads(cand)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
        return None

    def _run_validators(self, manifest: CartridgeManifest,
                        bb: Blackboard) -> list[str]:
        """Load each validator .py file and run its ``validate`` fn.

        Validators receive ``(blackboard_snapshot: dict)`` and return
        ``(ok: bool, message: str)``.
        """
        messages: list[str] = []
        for rel in manifest.validators:
            path = Path(manifest.path) / "validators" / rel
            if not path.exists():
                messages.append(f"validator missing: {rel}")
                continue
            try:
                module = _load_python_module(path)
                fn = getattr(module, "validate", None)
                if not callable(fn):
                    messages.append(f"{rel}: no validate() function")
                    continue
                ok, msg = fn(bb.snapshot())
                prefix = "ok" if ok else "FAIL"
                messages.append(f"{prefix} [{rel}]: {msg}")
            except Exception as exc:  # pragma: no cover
                messages.append(f"validator error [{rel}]: {exc}")
        return messages

    def _render_summary(self, manifest: CartridgeManifest, flow_name: str,
                        steps: list[StepResult],
                        validator_messages: list[str],
                        bb: Blackboard) -> str:
        lines = [
            "",
            "=" * 60,
            f"  Cartridge: {manifest.name}   Flow: {flow_name}",
            "=" * 60,
        ]
        for s in steps:
            icon = "✅" if s.validated else "⚠️"
            lines.append(f"  {icon} {s.agent}: {s.message} "
                         f"(produced={s.produced_keys}, attempts={s.attempts + 1})")
        if validator_messages:
            lines.append("")
            lines.append("  Validators:")
            for m in validator_messages:
                lines.append(f"    - {m}")
        lines.append("")
        lines.append(f"  Blackboard keys: {bb.keys()}")
        return "\n".join(lines)

    def _log(self, message: str) -> None:
        if self.verbose:
            try:
                print(message, flush=True)
            except UnicodeEncodeError:
                print(message.encode("ascii", "replace").decode(), flush=True)


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def _extract_first_json_object(text: str) -> str | None:
    """Return the first balanced {...} JSON object found, respecting
    string escapes. None if no balanced object exists."""
    start = text.find("{")
    if start < 0:
        return None
    depth, i = 0, start
    in_str, escape = False, False
    while i < len(text):
        c = text[i]
        if escape:
            escape = False
        elif c == "\\":
            escape = True
        elif c == '"':
            in_str = not in_str
        elif not in_str:
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        i += 1
    return None


def _load_python_module(path: Path):
    """Load a .py file as an anonymous module (for validators)."""
    spec = importlib.util.spec_from_file_location(
        f"_cartridge_validator_{path.stem}", path
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ─────────────────────────────────────────────────────────────────────
# CLI entry point for testing a cartridge standalone
# ─────────────────────────────────────────────────────────────────────

def _cli() -> int:  # pragma: no cover
    import argparse
    parser = argparse.ArgumentParser(description="Run a SkillOS cartridge")
    parser.add_argument("cartridge", help="cartridge name (folder under cartridges/)")
    parser.add_argument("goal", help="user goal")
    parser.add_argument("--flow", help="force a specific flow name")
    parser.add_argument("--provider", default="gemma-openrouter",
                        help="AgentRuntime provider (default: gemma-openrouter)")
    parser.add_argument("--root", default="cartridges",
                        help="cartridge root directory")
    parser.add_argument("--list", action="store_true",
                        help="list cartridges and exit")
    args = parser.parse_args()

    registry = CartridgeRegistry(args.root)
    if args.list:
        for m in registry.list():
            print(f"{m.name:30s}  flows={list(m.flows.keys())}")
            print(f"    {m.description}")
        return 0

    from agent_runtime import AgentRuntime
    from permission_policy import SKILLOS_AUTONOMOUS_POLICY
    rt = AgentRuntime(provider=args.provider, stream=False,
                      permission_policy=SKILLOS_AUTONOMOUS_POLICY)

    runner = CartridgeRunner(rt, registry)
    result = runner.run(args.cartridge, args.goal, flow=args.flow)
    print("\n" + ("OK" if result.ok else "PARTIAL"))
    return 0 if result.ok else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(_cli())
