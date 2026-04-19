# Cartridges: Gemma-Native Subagents for SkillOS

**Status**: v1 — reference implementation
**Module**: `cartridge_runtime.py`
**Cartridge root**: `cartridges/`
**Integration**: `skillos.py` (REPL), `agent_runtime.py` (delegation)

---

## What problem this solves

Claude Code's subagent system is spectacular because it rides on a
high-tier model. When you swap in Gemma 4 (26B, open-weights) via
`agent_runtime.py`, three things break:

1. **Routing**: Gemma can't reliably pick subagents from an open set.
2. **Tool-call XML**: Over many turns, format drifts and retries explode.
3. **Plan stability**: Free-form multi-step plans diverge.

Cartridges fix all three by **pre-sealing the plan space per domain**.
A cartridge is a self-contained bundle that declares exactly which
subagents exist, in what order they run, what they consume and produce,
what validators apply, and which JSON Schemas guard the blackboard.
Gemma only has to fill structured slots — a task it performs reliably.

The result: a full Claude-Code-style subagent experience
(delegation, tool access, isolated context, result passing), scoped
domain-by-domain. Scaling the system means **authoring cartridges**, not
upgrading the model.

---

## Mental model

```
     ┌────────────────────────────────────────────────────────────┐
     │  skillos.py  (REPL)                                        │
     │    ├─ "design electrical installation for a 3-BR house"    │
     │    └─ intent router → cartridge "residential-electrical"   │
     └────────────────────────────────────────────────────────────┘
                              │
                              ▼
     ┌────────────────────────────────────────────────────────────┐
     │  CartridgeRegistry                                         │
     │    loads cartridges/*/cartridge.yaml                       │
     │    exposes match_intent(), get(), load_agent()             │
     └────────────────────────────────────────────────────────────┘
                              │
                              ▼
     ┌────────────────────────────────────────────────────────────┐
     │  CartridgeRunner(runtime, registry)                        │
     │    ├─ Router picks flow (router.md, closed-set)            │
     │    ├─ For each agent in flow:                              │
     │    │     · bundle blackboard inputs (spec.needs)           │
     │    │     · rt.delegate_to_agent(agent, task, input_data)   │
     │    │     · parse <produces>{…}</produces>                  │
     │    │     · JSON-Schema validate → blackboard.put(...)      │
     │    │     · retry once on validation failure                │
     │    └─ run manifest.validators (pure Python)                │
     └────────────────────────────────────────────────────────────┘
                              │
                              ▼
     ┌────────────────────────────────────────────────────────────┐
     │  Blackboard                                                │
     │    typed KV store (value + schema_ref + produced_by + desc)│
     │    snapshot → returned to user as final result             │
     └────────────────────────────────────────────────────────────┘
```

---

## Directory layout

```
cartridges/
└── <name>/
    ├── cartridge.yaml           manifest (required)
    ├── router.md                closed-set intent classifier (optional)
    ├── agents/
    │   └── <agent>.md           one per subagent — frontmatter + body
    ├── flows/
    │   └── <flow>.flow.md       human-readable flow doc (optional)
    ├── schemas/
    │   └── <key>.schema.json    JSON Schema for blackboard values
    ├── validators/
    │   └── *.py                 post-flow deterministic checks
    └── evals/
        └── cases.yaml           regression set for install gating
```

### `cartridge.yaml` (manifest)

```yaml
name: cooking                    # must match folder name
description: >
  Meal planning, recipe authoring, and shopping-list generation.

# Keyword overlap with these patterns routes an incoming REPL goal
# to this cartridge (no LLM call).
entry_intents:
  - plan weekly menu
  - plan meals for the week
  - shopping list for the week

# Ordered agent sequences. The LLM router picks exactly one.
flows:
  plan-weekly-menu:
    - menu-planner
    - shopping-list-builder
    - recipe-writer
  quick-shopping-list:
    - menu-planner
    - shopping-list-builder

default_flow: plan-weekly-menu

# Typed blackboard — maps key → JSON Schema filename.
blackboard_schema:
  weekly_menu:   weekly_menu.schema.json
  shopping_list: shopping_list.schema.json
  recipes:       recipes.schema.json

# Deterministic post-flow checks (pure Python, zero LLM calls).
validators:
  - menu_complete.py
  - shopping_list_sane.py

max_turns_per_agent: 3

variables:
  locale: en_US
  default_household_size: 2
```

### JS Skill Cartridges (`type: js-skills`)

A variant cartridge type that runs JavaScript skills (Gallery format) via Node.js
instead of LLM agents. See [docs/js-skills.md](js-skills.md) for the full guide.

```yaml
name: demo
type: js-skills              # ← enables JS executor path
skills_source: skills         # directory containing Gallery skill folders

flows:
  run-skill:                  # LLM extracts params → Node.js executes
    - param-extractor
    - js-executor
  agentic:                    # LLM decides autonomously
    mode: agentic
  pipeline:                   # Multi-skill chaining
    - skill: query-wikipedia
      needs: [user_goal]
      produces: [wiki_data]
```

Key differences from standard cartridges:
- `skills/` directory replaces (or supplements) `agents/` for JS skill steps
- `js-executor` step runs deterministically via Node.js (0 LLM calls)
- `SkillStep` flow entries have `skill`/`needs`/`produces` fields
- `mode: agentic` gives the LLM `load_skill` + `run_js` tools
- Skills can call the orchestrating LLM via `__skillos.llm.chat()`

### Agent file (`agents/<agent>.md`)

```markdown
---
name: menu-planner
description: Produces a structured 7-day menu.
needs: [user_goal]
produces: [weekly_menu]
produces_schema: weekly_menu.schema.json
produces_description: 7-day menu with 3 meals per day.
max_turns: 2
---

# Menu Planner

[system prompt — chain of thought instructions, constraints, few-shot examples]

## Output shape

<produces>
{
  "weekly_menu": { ... }
}
</produces>
```

Frontmatter fields:

| Field                  | Meaning                                                  |
|------------------------|----------------------------------------------------------|
| `name`                 | Agent identifier (should match filename).                |
| `needs`                | Blackboard keys the agent reads as `input_data`.         |
| `produces`             | Blackboard keys the agent writes.                        |
| `produces_schema`      | JSON Schema filename (under cartridge `schemas/`).       |
| `produces_description` | Human sentence surfaced to downstream agents.            |
| `tools`                | Optional whitelist of tool names (subset of runtime).    |
| `max_turns`            | Override cartridge `max_turns_per_agent`.                |

### Validators (`validators/*.py`)

```python
def validate(blackboard: dict) -> tuple[bool, str]:
    ...
    return True, "ok"
```

The `blackboard` arg is the snapshot dict from `Blackboard.snapshot()`.
Validators run **after** all agents in the flow complete. Fatal failures
return `False`; warnings can return `True` with a note. See
`cartridges/residential-electrical/validators/compliance_checker.py`
for a meaningful example (IEC 60364 subset).

### JSON Schemas (`schemas/*.schema.json`)

Standard JSON Schema Draft 7. The runtime uses the `jsonschema` package
when available and falls back to a minimal structural check otherwise.
`additionalProperties: false` is recommended on object schemas to keep
Gemma honest.

### Evals (`evals/cases.yaml`)

```yaml
cases:
  - id: plan-2people-vegetarian
    goal: "Plan my meals for next week, 2 adults, vegetarian"
    flow: plan-weekly-menu
    assertions:
      - key: weekly_menu.household_size
        equals: 2
      - key: weekly_menu.days
        length: 7
      - key: recipes
        length: 7
```

A cartridge is considered production-ready when ≥ 85% of cases pass on
the target model tier. (The eval runner is a small script consumers can
assemble from `CartridgeRunner`; an example lives in
`tests/test_cartridge_runtime.py`.)

---

## Runtime API

### Blackboard

```python
from cartridge_runtime import Blackboard

bb = Blackboard(schemas_dir="cartridges/cooking/schemas")
bb.put("user_goal", "Plan 2-person vegetarian week",
       description="original user request")
ok, msg = bb.put("weekly_menu", data,
                 schema_ref="weekly_menu.schema.json",
                 produced_by="menu-planner",
                 description="7-day menu with 3 meals per day")
bb.value("weekly_menu")          # unwraps .value
bb.bundle(["weekly_menu"])       # {"weekly_menu": {…}}  — for input_data
bb.describe(["weekly_menu"])     # Markdown bullet with origin + desc
bb.snapshot()                    # serializable dict
```

### CartridgeRegistry

```python
from cartridge_runtime import CartridgeRegistry

reg = CartridgeRegistry("cartridges")
reg.names()                      # ["cooking", "residential-electrical"]
reg.get("cooking")               # CartridgeManifest
reg.match_intent("shopping list for the week")
#   → ("cooking", 3)

reg.load_agent("cooking", "menu-planner")   # AgentSpec
```

### CartridgeRunner

```python
from agent_runtime import AgentRuntime
from cartridge_runtime import CartridgeRegistry, CartridgeRunner

rt  = AgentRuntime(provider="gemma-openrouter", stream=False)
reg = CartridgeRegistry()
run = CartridgeRunner(rt, reg)

result = run.run("cooking",
                 "Plan meals next week, 2 adults, vegetarian")

result.ok                    # bool
result.flow                  # chosen flow
result.steps                 # [StepResult(...), ...]
result.blackboard            # full snapshot
result.final_summary         # printable summary
```

---

## `skillos.py` integration

The REPL gains two commands:

```
skillos$ cartridges                       # list installed cartridges
skillos$ cartridge <name> "<goal>"        # run a cartridge directly
skillos$ cartridge <name> --flow <flow> "<goal>"
skillos$ cartridge auto "<goal>"          # intent-match and dispatch
```

Automatic dispatch: if the REPL is in `provider gemma` mode and a bare
goal matches a cartridge's `entry_intents` with score ≥ 2, the goal
routes to that cartridge automatically. Explicit Claude execution is
still available via `claude <goal>` or by toggling `provider claude`.

---

## Standalone CLI

```bash
python -m cartridge_runtime --list
python -m cartridge_runtime cooking "Plan meals next week, 2 adults, veg"
python -m cartridge_runtime residential-electrical \
    "Design electrical for a 3-BR apartment: kitchen, 2 bathrooms, living room"
```

---

## Parity with Claude Code — what you get and what you don't

| Claude Code capability                | Cartridge equivalent                  |
|---------------------------------------|---------------------------------------|
| `Task` tool spawns subagent           | `delegate_to_agent` in agent_runtime  |
| Isolated subagent context             | System-prompt swap + `input_data`     |
| Agent discovery (`.claude/agents/`)   | `CartridgeRegistry.load_agent`        |
| Autonomous routing                    | **Closed-set router per cartridge**   |
| Tool access per agent                 | `tools:` frontmatter allow-list       |
| Result synthesis                      | `Blackboard` + per-flow final output  |
| Persistent memory                     | `system/SmartMemory.md` (unchanged)   |
| Cross-session state                   | `projects/<name>/state/` (unchanged)  |

**What you give up**: general-purpose routing across unseen domains. A
cartridge only succeeds inside its declared `entry_intents`. That's the
price of making Gemma reliable — and it's the design choice that makes
new domains cheap: each new cartridge is one day of authoring, not a
model upgrade.

**What you gain**: every cartridge is reviewable like code. The rules
(compliance, diet, safety) live in Python validators, not inside a
prompt. A new code-of-practice revision is a Python diff — not a prompt
rewrite of unknown quality.

---

## Guardrails layered on top

1. **Keyword router** — no LLM call for cartridge selection.
2. **Closed-set flow classifier** — LLM call is a single token from 2–6
   options, near-zero failure rate.
3. **`<produces>{…}</produces>` contract** — robust extractor with
   balanced-brace fallback; one retry with structured feedback.
4. **JSON Schema validation** — per-key, on write to blackboard.
5. **Tool allow-list** — per-agent whitelist via `tools:` frontmatter.
6. **Deterministic validators** — pure Python, zero LLM calls, run
   after the flow. Carry the domain's hard rules.
7. **Eval gate** — a cartridge cannot be installed if its regression
   cases pass rate < 0.85 on the target model tier.

Each layer is deterministic and cheap; Gemma's remaining job is
slot-filling, which it handles reliably.

---

## Authoring a new cartridge — 7-step recipe

1. **Pick the domain** narrow enough that a plan template fits. Good
   candidates: cooking, tax filing, cleanup scripts, Terraform
   scaffolding, CI debug runbooks, home-server setup, landscape
   irrigation, invoice processing.
2. **Sketch the blackboard keys** — the KV data that flows between
   steps. Name them explicitly; each becomes a schema file.
3. **Write JSON Schemas** for every key. `additionalProperties: false`
   wherever possible.
4. **Design the agent sequence** (one flow first). Each agent reads a
   subset of the blackboard and writes exactly one key.
5. **Author each agent `.md`** with frontmatter (`needs` / `produces` /
   `produces_schema`), a chain-of-thought section, and at least one
   fully worked example output inside `<produces>` tags.
6. **Write at least one validator** as pure Python — this is where the
   domain's hard rules live. Keep it short, unit-testable, reviewable.
7. **Populate `evals/cases.yaml`** with 10–20 representative goals.
   Run them against your target model. Iterate until pass rate > 85%.

Then register: drop the folder under `cartridges/`. The runtime
discovers it automatically on next REPL start.

---

## Limits we own up to

- **No long-horizon autonomous planning.** Flows are typically 3–6
  steps. Beyond that, Gemma drifts. For longer work, compose
  cartridges manually.
- **No cross-cartridge orchestration (yet).** A single user goal runs
  inside one cartridge. Stacking cartridges across one session is on
  the roadmap but today requires a glue script.
- **Tool creation remains Claude Code territory.** Cartridges use
  existing runtime tools — they do not spawn new ones at runtime.
- **Novel-domain improvisation.** Cartridges succeed in domains with a
  stable problem shape. If a user asks a truly out-of-domain question,
  the router returns no match and the REPL falls back to Claude Code
  (or declines, depending on configuration).

These limits are features: they are what make Gemma-only operation
reliable and safe.

---

## Reference cartridges shipped in this repo

### `cartridges/cooking/`
- 3 agents (menu-planner, shopping-list-builder, recipe-writer)
- 3 schemas (weekly_menu, shopping_list, recipes)
- 2 validators (`menu_complete.py`, `shopping_list_sane.py`)
- 3 eval cases
- Illustrates: forgiving domain, pure structural validators.

### `cartridges/residential-electrical/`
- 2 agents (load-calculator, circuit-designer)
- 2 schemas (load_profile, circuits)
- 1 validator (`compliance_checker.py` — IEC 60364 subset, 80 LOC)
- Illustrates: **safety-critical deterministic validator** — the rules
  live in Python, not in a prompt. A new code edition is a Python diff.

Copy either as a starting point for your own cartridge.

---

## FAQ

**Q: Is this a replacement for the SkillOS skill tree?**
No. The skill tree (`system/skills/`) hosts cross-cutting Claude-Code
subagents used by the SystemAgent. Cartridges are a parallel mechanism
aimed at Gemma-only operation in sealed domains. A project can use
both.

**Q: Can I use a cartridge with Claude?**
Yes — `CartridgeRunner` accepts any runtime that implements
`_handle_delegate_to_agent()` and `_call_llm()`. Claude will happily
run a cartridge flow, usually passing on the first try.

**Q: Do I need `jsonschema` installed?**
Optional. The runtime prefers it when present; otherwise it falls back
to a small structural check (type + required fields).

**Q: How do I debug a failing flow?**
`RunResult.steps[i].raw_output` contains the full agent response; the
message field tells you what went wrong (missing `<produces>`, schema
violation, missing input). Turn `CartridgeRunner(..., verbose=True)`
on for turn-by-turn logs.
