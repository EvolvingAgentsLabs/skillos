#!/usr/bin/env python3
"""
Unified Agent Runtime for SkillOS - Complete Implementation
Provider-agnostic runtime supporting Qwen (OpenRouter) and Gemini backends.
Combines all features: interactive mode, sequential execution, LLM-powered compaction.
"""

from __future__ import annotations

import os
import re
import json
import sys
import time
import random
import asyncio
import subprocess
from dataclasses import dataclass, field
from openai import OpenAI, APIStatusError, APIConnectionError, APITimeoutError
from dotenv import load_dotenv
from permission_policy import PermissionPolicy, PermissionMode, SKILLOS_DEFAULT_POLICY, get_policy
from compactor import CompactionConfig, should_compact, compact_messages, compact_messages_async
from sandbox import create_executor

# Fix Windows console encoding for emojis
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load API keys and other configs from .env file
load_dotenv()

# ── Retry configuration ──────────────────────────────────────────
_RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0    # seconds
_RETRY_MAX_DELAY = 30.0    # seconds


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a markdown string."""
    match = re.match(r"^---\n(.*?\n)---", content, re.DOTALL)
    if not match:
        return {}
    import yaml
    return yaml.safe_load(match.group(1)) or {}


@dataclass
class StepResult:
    """Result of a single cognitive pipeline step."""
    step_num: int
    agent_name: str
    output: str = ""
    files_written: list[str] = field(default_factory=list)
    char_count: int = 0
    status: str = "pending"  # pending | pass | partial | fail


@dataclass
class StepValidation:
    """Validation criteria for a pipeline step."""
    min_chars: int = 2000
    require_file_write: bool = True
    required_sections: list[str] = field(default_factory=list)


class AgentRuntime:
    PROVIDER_CONFIGS = {
        "qwen": {
            "base_url": "https://openrouter.ai/api/v1",
            "api_key_env": "OPENROUTER_API_KEY",
            "model": "qwen/qwen3.6-plus:free",
            "manifest": "QWEN.md",
            "cache_headers": {
                "HTTP-Referer": "https://skillos.dev",
                "X-Title": "SkillOS",
            },
        },
        "gemini": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "api_key_env": "GEMINI_API_KEY",
            "model": "gemini-2.5-flash",
            "manifest": "GEMINI.md",
            "cache_headers": {},
        },
        "gemma": {
            "base_url": "http://localhost:11434/v1",
            "base_url_env": "OLLAMA_BASE_URL",
            "api_key_env": "OLLAMA_API_KEY",
            "api_key_default": "ollama",
            "model": "gemma4",
            "model_env": "GEMMA_MODEL",
            "manifest": "GEMINI.md",
            "cache_headers": {"Bypass-Tunnel-Reminder": "true"},
        },
        "gemma-openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "api_key_env": "OPENROUTER_API_KEY",
            "model": "google/gemma-4-26b-a4b-it",
            "model_env": "GEMMA_OPENROUTER_MODEL",
            "manifest": "GEMINI.md",
            "cache_headers": {
                "HTTP-Referer": "https://skillos.dev",
                "X-Title": "SkillOS",
            },
        },
    }

    # ── Model Capability Registry ────────────────────────────────────
    MODEL_CAPABILITIES: dict[str, dict] = {
        "claude-opus-4-6":           {"tier": "high", "recommended_strategy": "agentic"},
        "gemini-2.5-flash":          {"tier": "high", "recommended_strategy": "agentic"},
        "gemini-2.5-pro":            {"tier": "high", "recommended_strategy": "agentic"},
        "google/gemma-4-26b-a4b-it": {"tier": "mid",  "recommended_strategy": "cognitive_pipeline"},
        "gemma4":                    {"tier": "mid",  "recommended_strategy": "cognitive_pipeline"},
        "qwen/qwen3.6-plus:free":    {"tier": "low",  "recommended_strategy": "pipeline"},
    }
    _DEFAULT_CAPABILITY = {"tier": "mid", "recommended_strategy": "cognitive_pipeline"}

    def __init__(self, manifest_path: str | None = None, permission_policy: PermissionPolicy | None = None, provider: str = "qwen", stream: bool = True, sandbox_mode: str = "local"):
        cfg = self.PROVIDER_CONFIGS[provider]
        resolved_base_url = os.getenv(cfg.get("base_url_env", ""), "") or cfg["base_url"]
        api_key_default = cfg.get("api_key_default", "")
        self.client = OpenAI(
            base_url=resolved_base_url,
            api_key=os.getenv(cfg["api_key_env"], api_key_default),
            default_headers=cfg.get("cache_headers", {}),
        )
        self.model = os.getenv(cfg.get("model_env", ""), "") or cfg["model"]
        self.provider_name = provider
        self.use_streaming = stream
        self.tools = {}
        self.system_prompt = ""
        self.policy = permission_policy or SKILLOS_DEFAULT_POLICY
        self.executor = create_executor(sandbox_mode)
        self.compaction_config = CompactionConfig()
        self.compaction_config.configure_for_model(self.model)
        self._active_project_dir = ""  # Set by execute_scenario/run_cognitive_pipeline for delegation context
        resolved_manifest = manifest_path or cfg["manifest"]
        self._load_manifest(resolved_manifest)
        print(f"✅ Agent Runtime Initialized (provider={provider}, model={self.model}, manifest={resolved_manifest}, sandbox={sandbox_mode}).")

    def _load_manifest(self, path):
        """Loads the system prompt and compiles native tools from the manifest.

        Supports two manifest formats:
          - QWEN format: ``### NATIVE TOOLS`` with ``<tool>`` XML blocks containing ``<python_code>``
          - GEMINI format: ``### Tools`` with ``#### tool_name`` sections containing shell scripts
        """
        print(f"--- Loading manifest from {path} ---")
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        if "### NATIVE TOOLS" in content:
            self._load_qwen_format(content)
        elif "### Tools" in content:
            self._load_gemini_format(content)
        else:
            raise ValueError(f"Unrecognized manifest format in {path} (expected '### NATIVE TOOLS' or '### Tools')")

        print("--- Manifest loaded successfully. ---")

    # ── QWEN format loader (XML <tool> blocks with <python_code>) ────

    def _load_qwen_format(self, content: str):
        parts = content.split("### NATIVE TOOLS")
        self.system_prompt = parts[0].strip()

        tool_blocks = re.findall(r"<tool name=\"(.*?)\">(.*?)</tool>", parts[1], re.DOTALL)
        for name, block in tool_blocks:
            description = re.search(r"<description>(.*?)</description>", block, re.DOTALL).group(1).strip()
            code = re.search(r"<python_code>(.*?)</python_code>", block, re.DOTALL).group(1).strip()

            # Special handling for call_llm tool
            if name == "call_llm":
                self.tools[name] = self._handle_call_llm
                print(f"  - Registered special tool: {name}")
                continue

            # Special handling for delegate_to_agent tool
            if name == "delegate_to_agent":
                self.tools[name] = self._handle_delegate_to_agent
                print(f"  - Registered special tool: {name}")
                continue

            try:
                restricted_globals = {k: v for k, v in globals().items()
                                      if k != "__builtins__"}
                _blocked = ("exec", "eval", "compile")
                safe_builtins = {k: v for k, v in __builtins__.items()
                                 if k not in _blocked} if isinstance(__builtins__, dict) else {
                    k: getattr(__builtins__, k) for k in dir(__builtins__)
                    if k not in _blocked and not k.startswith("_")
                }
                restricted_globals["__builtins__"] = safe_builtins
                namespace = {}
                exec(code, restricted_globals, namespace)
                for key, value in namespace.items():
                    if callable(value) and not key.startswith('_'):
                        self.tools[name] = value
                        print(f"  - Compiled tool: {name}")
                        break
            except Exception as e:
                print(f"!!! Error compiling tool '{name}': {e}")

    # ── GEMINI format loader (shell script blocks) ───────────────────

    # Instructions appended to GEMINI.md system prompts so the LLM uses
    # the same <tool_call> / <final_answer> wire format that run_goal parses.
    _GEMINI_TOOL_FORMAT_INSTRUCTIONS = """

---
### RUNTIME TOOL CALL FORMAT

When you need to use a tool, format it EXACTLY like this:
```
<tool_call name="tool_name">
{"parameter1": "value1", "parameter2": "value2"}
</tool_call>
```

When you have completed all tasks, you MUST end with:
```
<final_answer>
Your complete summary of what was accomplished
</final_answer>
```

### TOOL SIGNATURES

- `read_file`: `{"path": "file/path.md"}`
- `write_file`: `{"path": "file/path.md", "content": "..."}`
- `append_to_file`: `{"path": "file/path.md", "content": "..."}`
- `list_files`: `{"path": "directory/"}`
- `web_fetch`: `{"url": "https://..."}`
- `delegate_to_agent`: `{"agent_name": "agent-name", "task_description": "what to do", "input_data": {}}`
- `call_llm`: `{"prompt": "your question"}`
- `memory_store`: `{"type": "volatile|task|permanent", "key": "name", "value": "data"}`
- `memory_recall`: `{"type": "volatile|task|permanent", "key": "name"}`
- `memory_search`: `{"pattern": "search term"}`

Agents are discovered in `system/agents/` and `.claude/agents/`. Use agent names without path or extension (e.g. `"research-assistant-agent"`, not `"system/agents/research-assistant-agent.md"`).
"""

    def _load_gemini_format(self, content: str):
        parts = content.split("### Tools", 1)
        self.system_prompt = parts[0].strip() + self._GEMINI_TOOL_FORMAT_INSTRUCTIONS
        tools_section = parts[1]

        # Split into individual tool sections by #### headings
        tool_sections = re.split(r"^####\s+", tools_section, flags=re.MULTILINE)

        for section in tool_sections:
            if not section.strip():
                continue

            # Extract tool name from first line
            lines = section.strip().split("\n", 1)
            tool_name = lines[0].strip()
            body = lines[1] if len(lines) > 1 else ""

            # Extract shell script from ```sh ... ``` block
            sh_match = re.search(r"```sh\n(.*?)```", body, re.DOTALL)
            shell_script = sh_match.group(1).strip() if sh_match else None

            # Map Gemini CLI-specific tools to Python runtime equivalents
            if tool_name == "run_agent":
                self.tools["delegate_to_agent"] = self._handle_delegate_to_agent
                print(f"  - Mapped {tool_name} → delegate_to_agent")
                continue
            if tool_name == "run_tool":
                # run_tool delegates via shell; in Python runtime we use delegate_to_agent
                print(f"  - Skipped {tool_name} (handled via delegate_to_agent)")
                continue
            if tool_name == "google_search":
                self.tools["call_llm"] = self._handle_call_llm
                print(f"  - Mapped {tool_name} → call_llm")
                continue

            if not shell_script:
                print(f"  - Skipped {tool_name} (no shell script found)")
                continue

            # Create a Python wrapper that runs the shell script via subprocess
            self.tools[tool_name] = self._make_shell_tool(shell_script, tool_name)
            print(f"  - Wrapped shell tool: {tool_name}")

        # Ensure special tools are always available
        if "call_llm" not in self.tools:
            self.tools["call_llm"] = self._handle_call_llm
            print(f"  - Registered special tool: call_llm")
        if "delegate_to_agent" not in self.tools:
            self.tools["delegate_to_agent"] = self._handle_delegate_to_agent
            print(f"  - Registered special tool: delegate_to_agent")

    def _make_shell_tool(self, script: str, tool_name: str):
        """Create a Python callable that executes a GEMINI.md shell script."""
        executor = self.executor

        def tool_fn(**kwargs):
            env = {"GEMINI_TOOL_ARGS": json.dumps(kwargs)}
            result = executor.execute(script, env=env, timeout=30)
            if result.returncode != 0:
                return f"Error running {tool_name}: {result.stderr}" if result.stderr else result.stdout
            return result.stdout
        return tool_fn

    def _handle_call_llm(self, prompt: str):
        """Handles recursive calls to the LLM."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        return self._call_llm(messages)

    def _handle_delegate_to_agent(self, agent_name: str, task_description: str,
                                    input_data: dict = None, *,
                                    max_turns: int = 5, project_dir: str = ""):
        """Handles delegation to specialized agents with full tool access.

        Runs a mini agentic loop (like _run_step_with_tools) so that delegated
        agents can use tools (write_file, read_file, etc.), produce substantial
        output, and interact over multiple turns.

        Args:
            agent_name: Name of the agent to delegate to.
            task_description: What the agent should do.
            input_data: Optional structured data to pass to the agent.
            max_turns: Maximum LLM round-trips for the delegated agent.
            project_dir: Project directory for file operations context.
                Falls back to self._active_project_dir if not provided.
        """
        # Use instance-level project dir if not explicitly passed
        if not project_dir:
            project_dir = getattr(self, "_active_project_dir", "")
        print(f"\n🎯 Delegating to agent: {agent_name}")

        # Load the agent definition — use compiled load_agent tool if available,
        # otherwise fall back to built-in filesystem search.
        if "load_agent" in self.tools:
            agent_info = self.tools["load_agent"](agent_name)
        else:
            agent_info = self._find_agent(agent_name)

        if not agent_info.get("found"):
            # Try dynamic generation from a minimal context
            agent_info = {
                "found": True,
                "content": self._generate_agent_spec(
                    agent_name,
                    {"step": 0, "agent": agent_name, "goal": task_description, "output": ""},
                    task_description,
                    project_dir or ".",
                ),
                "description": f"Dynamically generated agent for: {task_description[:80]}",
                "tools": "write_file, read_file, list_files",
            }
            print(f"   📝 Generated agent spec for '{agent_name}'")

        agent_system = agent_info["content"]
        print(f"   📋 Agent description: {agent_info['description']}")
        print(f"   🛠️  Available tools: {list(self.tools.keys())}")

        # Inject context from project output files (if project_dir is set)
        file_injection = ""
        if project_dir:
            injected_files = []
            for scan_dir in [os.path.join(project_dir, d) for d in ["output", "state"]]:
                if not os.path.isdir(scan_dir):
                    continue
                for root, _dirs, files in os.walk(scan_dir):
                    for fname in sorted(files):
                        fpath = os.path.join(root, fname)
                        try:
                            with open(fpath, "r", encoding="utf-8") as f:
                                content = f.read()
                            if content.strip():
                                truncated = content[:3000] if len(content) > 3000 else content
                                rel_path = os.path.relpath(fpath, project_dir)
                                injected_files.append(
                                    f"### File: `{rel_path}`\n```\n{truncated}\n```"
                                )
                        except (OSError, UnicodeDecodeError):
                            continue
            if injected_files:
                file_injection = (
                    "\n\n## AVAILABLE PROJECT FILES\n\n"
                    + "\n\n".join(injected_files[:10])
                )

        # Build task prompt
        input_section = ""
        if input_data:
            input_section = f"\n\n## INPUT DATA\n\n```json\n{json.dumps(input_data, indent=2)}\n```"

        task_prompt = (
            f"## YOUR TASK\n\n{task_description}\n"
            f"{input_section}"
            f"\n\n## INSTRUCTIONS\n\n"
            f"- Execute this task according to your specialized capabilities\n"
            f"- Use write_file to save any substantial output to files\n"
            f"- Produce COMPREHENSIVE, DETAILED content\n"
            f"- End with a <final_answer> summarizing what you accomplished\n"
            f"{file_injection}"
        )

        # Temporarily swap system prompt to agent persona + tool instructions
        original_system_prompt = self.system_prompt
        self.system_prompt = agent_system + self._GEMINI_TOOL_FORMAT_INSTRUCTIONS

        files_written: list[str] = []
        all_output = ""

        try:
            # Tool-call scaffold: show the model the exact XML format as few-shot
            scaffold_example = (
                f'Here is an example of the tool call format you MUST use:\n\n'
                f'<tool_call name="write_file">\n'
                f'{{"path": "output.md", "content": "Your detailed content here..."}}\n'
                f'</tool_call>\n\n'
                f'<final_answer>\nTask complete. File saved.\n</final_answer>'
            )
            messages: list[dict] = [
                {"role": "user", "content": task_prompt},
                {"role": "assistant", "content": scaffold_example},
                {"role": "user", "content": "Good format. Now execute the task for real. Use tool calls as needed, then provide a final_answer."},
            ]

            for turn in range(max_turns):
                # Compact if needed
                if should_compact(messages, self.compaction_config):
                    try:
                        messages, _ = asyncio.run(
                            compact_messages_async(messages, self.compaction_config, self._call_llm_async)
                        )
                    except RuntimeError:
                        messages, _ = compact_messages(messages, self.compaction_config)

                try:
                    full_messages = self._build_messages(messages)
                    if self.use_streaming:
                        response = self._call_llm_stream(full_messages)
                    else:
                        response = self._call_llm(full_messages)
                except Exception as e:
                    print(f"   !!! Agent {agent_name} LLM error: {e}")
                    break

                if not response or response.strip() == "":
                    messages.append({
                        "role": "user",
                        "content": "Please provide your output with tool calls or a final_answer."
                    })
                    continue

                messages.append({"role": "assistant", "content": response})
                all_output += response + "\n"

                # Parse and execute tool calls
                tool_calls = self._parse_tool_calls(response)
                if tool_calls:
                    for tool_name, args_str in tool_calls:
                        tool_name = self._TOOL_ALIASES.get(tool_name, tool_name)
                        try:
                            clean_args = self._extract_json_object(args_str.strip())
                            try:
                                args = json.loads(clean_args)
                            except json.JSONDecodeError:
                                args = self._repair_json_args(clean_args)
                                if args is None:
                                    raise json.JSONDecodeError("Repair failed", clean_args, 0)

                            # Permission check
                            input_preview = args_str.strip()[:120]
                            authorized, reason = self.policy.authorize(tool_name, input_preview, args=args)
                            if not authorized:
                                messages.append({"role": "user", "content": f"Tool '{tool_name}' denied: {reason}"})
                                continue

                            if tool_name in self.tools:
                                tool_result = self.tools[tool_name](**args) if isinstance(args, dict) else self.tools[tool_name](args)
                            else:
                                tool_result = f"Error: Tool '{tool_name}' not found."

                            # Track file writes
                            if tool_name == "write_file" and isinstance(args, dict):
                                written_path = args.get("path", "")
                                files_written.append(written_path)
                                content_len = len(args.get("content", ""))
                                print(f"   📄 Agent wrote {written_path} ({content_len} chars)")

                            display = str(tool_result)[:300] + "..." if len(str(tool_result)) > 300 else str(tool_result)
                            messages.append({"role": "user", "content": f"Tool '{tool_name}' returned:\n{display}"})
                        except (json.JSONDecodeError, Exception) as e:
                            messages.append({"role": "user", "content": f"Error with tool '{tool_name}': {e}"})

                # Check for final answer
                final_answer = self._extract_tag_content("final_answer", response)
                if final_answer:
                    # Preserve <produces> blocks from accumulated output
                    # (cartridge agents may emit <produces> outside <final_answer>)
                    if '<produces>' in all_output and '<produces>' not in final_answer:
                        produces_match = re.search(
                            r'<produces>.*?</produces>', all_output, re.DOTALL)
                        if produces_match:
                            all_output = produces_match.group(0) + "\n\n" + final_answer
                        else:
                            all_output = final_answer
                    else:
                        all_output = final_answer
                    break

                # If no tools and no final answer, done
                if not tool_calls:
                    break

            print(f"   ✅ Agent {agent_name} completed ({len(all_output)} chars, {len(files_written)} files)")
            return all_output

        except Exception as e:
            error_msg = f"❌ Error executing agent {agent_name}: {e}"
            print(f"   {error_msg}")
            return error_msg
        finally:
            self.system_prompt = original_system_prompt

    @staticmethod
    def _find_agent(agent_name: str) -> dict:
        """Built-in agent lookup across standard directories (fallback for GEMINI manifests)."""
        for agents_dir in ["components/agents", ".claude/agents", "system/agents"]:
            if not os.path.isdir(agents_dir):
                continue
            for fname in os.listdir(agents_dir):
                if not fname.endswith(".md"):
                    continue
                fpath = os.path.join(agents_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        content = f.read()
                except OSError:
                    continue
                # Parse YAML frontmatter for name
                if content.startswith("---"):
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        for line in parts[1].strip().splitlines():
                            if line.strip().startswith("name:"):
                                name_val = line.split(":", 1)[1].strip()
                                if name_val == agent_name:
                                    desc = ""
                                    tools_val = ""
                                    for l2 in parts[1].strip().splitlines():
                                        if l2.strip().startswith("description:"):
                                            desc = l2.split(":", 1)[1].strip()
                                        elif l2.strip().startswith("tools:"):
                                            tools_val = l2.split(":", 1)[1].strip()
                                    return {
                                        "name": name_val,
                                        "description": desc,
                                        "tools": tools_val,
                                        "content": content,
                                        "found": True,
                                    }
        return {"found": False}

    @staticmethod
    def _generate_agent_spec(agent_name: str, step: dict, scenario_content: str,
                              project_dir: str) -> str:
        """Generate a markdown agent spec from scenario context when no existing agent is found.

        Extracts the relevant section from the scenario body for the agent's step,
        creates a proper agent .md file, saves it to components/agents/ and
        .claude/agents/, and returns the content.
        """
        goal = step.get("goal", "")
        output_file = step.get("output", "")
        step_num = step.get("step", 0)

        # Extract the section for this step/phase from scenario body
        section_content = ""
        body = re.sub(r"^---\n.*?\n---\n?", "", scenario_content, count=1, flags=re.DOTALL)
        # Try to find the section for this step's agent
        pattern = rf"(?:###?\s+(?:Stage|Phase)\s+{step_num}[:\s].*?)(?=\n###?\s+(?:Stage|Phase)\s+\d+|\n## Expected|\n## Execution|\n## Loop|\n## Error|\n## Success|\n## Why|\n## Usage|\Z)"
        match = re.search(pattern, body, re.DOTALL | re.MULTILINE)
        if match:
            section_content = match.group(0).strip()

        # Determine tools based on step context
        tools_list = ["Read", "Write"]
        if output_file.endswith(".py"):
            tools_list.append("Bash")
        if "wiki" in goal.lower() or "research" in goal.lower():
            tools_list.append("WebFetch")

        # Derive a human-readable role from the agent name
        role = agent_name.replace("-agent", "").replace("-", " ").title()

        spec = f"""---
name: {agent_name}
type: specialized-agent
project: {os.path.basename(project_dir)}
phase: {step_num}
capabilities:
  - {role} expertise
  - Technical content generation
  - Structured document creation
tools:
  - {chr(10) + "  - ".join(tools_list)}
---

# {role} Agent

## Purpose
{goal}

## Instructions
{section_content if section_content else f"Execute step {step_num} of the pipeline: {goal}"}

## Output
Save results to `{project_dir}/output/{output_file}` using the write_file tool.
Produce comprehensive, detailed output with at least 2000 characters.
"""

        # Save to project components/agents/
        agents_dir = os.path.join(project_dir, "components", "agents")
        os.makedirs(agents_dir, exist_ok=True)
        agent_path = os.path.join(agents_dir, f"{agent_name}.md")
        with open(agent_path, "w", encoding="utf-8") as f:
            f.write(spec)

        # Also copy to .claude/agents/ for discovery
        claude_agents_dir = ".claude/agents"
        os.makedirs(claude_agents_dir, exist_ok=True)
        prefix = os.path.basename(project_dir)
        discovery_path = os.path.join(claude_agents_dir, f"{prefix}_{agent_name}.md")
        with open(discovery_path, "w", encoding="utf-8") as f:
            f.write(spec)

        print(f"    🤖 Generated agent spec: {agent_name} → {agent_path}")
        return spec

    # ── AOT Dialect Injection + Pipeline Execution ────────────────────

    @staticmethod
    def _load_dialect_grammars(dialect_ids: list[str], dialects_dir: str = "system/dialects") -> dict[str, str]:
        """Read dialect files and extract Grammar/Syntax section + first Example.

        Returns a dict mapping dialect_id -> compact grammar string.
        """
        grammars: dict[str, str] = {}
        for did in dialect_ids:
            path = os.path.join(dialects_dir, f"{did}.dialect.md")
            if not os.path.isfile(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # Extract Grammar / Syntax section
            grammar_match = re.search(
                r"## Grammar / Syntax\n(.*?)(?=\n## |\Z)", content, re.DOTALL
            )
            grammar = grammar_match.group(1).strip() if grammar_match else ""
            # Extract first Example
            example_match = re.search(
                r"### Example 1[^\n]*\n(.*?)(?=\n### |\n## |\Z)", content, re.DOTALL
            )
            example = example_match.group(1).strip() if example_match else ""
            snippet = f"### {did} grammar\n{grammar}"
            if example:
                snippet += f"\n\n**Example**:\n{example}"
            grammars[did] = snippet
        return grammars

    def load_scenario(self, scenario_path: str) -> dict:
        """Parse a scenario file and inject dialect grammars into self.system_prompt.

        Returns the parsed frontmatter dict (includes requires_dialects, pipeline, etc.).
        """
        with open(scenario_path, "r", encoding="utf-8") as f:
            content = f.read()
        fm = _parse_frontmatter(content)
        dialect_ids = fm.get("requires_dialects", [])
        if dialect_ids:
            grammars = self._load_dialect_grammars(dialect_ids)
            if grammars:
                injection = "\n\n---\n## Dialect Grammars (AOT Injected)\n\n"
                injection += "\n\n".join(grammars.values())
                self.system_prompt += injection
                print(f"  AOT injected {len(grammars)} dialect grammars into system prompt")
        return fm

    def run_pipeline(self, scenario_path: str, problem_context: str, max_turns_per_step: int = 1) -> str:
        """Execute a scenario pipeline deterministically.

        Parses pipeline from scenario YAML, pre-loads all required dialect grammars,
        then executes each step sequentially — one LLM call per step — chaining outputs.
        """
        with open(scenario_path, "r", encoding="utf-8") as f:
            scenario_content = f.read()
        fm = _parse_frontmatter(scenario_content)

        pipeline = fm.get("pipeline", [])
        if not pipeline:
            raise ValueError(f"Scenario {scenario_path} has no pipeline field")

        dialect_ids = fm.get("requires_dialects", [])
        grammars = self._load_dialect_grammars(dialect_ids) if dialect_ids else {}

        print(f"\n{'='*60}")
        print(f"  Pipeline Execution: {len(pipeline)} steps, {len(grammars)} dialects loaded")
        print(f"{'='*60}")

        prior_outputs: list[str] = []
        results: list[str] = []

        for step in pipeline:
            step_num = step["step"]
            deliverable = step["deliverable"]
            dialect = step["dialect"]
            model_override = step.get("model")

            print(f"\n--- Pipeline Step {step_num}: {deliverable} ({dialect}) ---")

            # Build step prompt
            grammar_block = grammars.get(dialect, f"Use {dialect} dialect notation.")
            prior_context = ""
            if prior_outputs:
                prior_context = "\n\n## Prior Step Outputs\n\n" + "\n\n---\n\n".join(prior_outputs)

            step_prompt = (
                f"## Dialect Grammar\n\n{grammar_block}\n\n"
                f"## Task\n\nProduce: {deliverable}\n"
                f"Use {dialect} dialect notation ONLY. No prose.\n\n"
                f"## Problem Context\n\n{problem_context}"
                f"{prior_context}"
            )

            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": step_prompt},
            ]

            # Use model override if specified
            if model_override:
                response = self._call_with_model_override(messages, model_override)
            elif self.use_streaming:
                response = self._call_llm_stream(messages)
            else:
                response = self._call_llm(messages)

            step_output = f"### Step {step_num}: {deliverable}\n\n{response}"
            prior_outputs.append(step_output)
            results.append(step_output)
            print(f"  Step {step_num} complete ({len(response)} chars)")

        final = "\n\n---\n\n".join(results)
        print(f"\n{'='*60}")
        print(f"  Pipeline complete: {len(results)} deliverables, {len(final)} chars total")
        print(f"{'='*60}")
        return final

    def _call_with_model_override(self, messages: list[dict], model: str) -> str:
        """Call LLM with a temporary model override for per-step provider routing."""
        original_model = self.model
        self.model = model
        try:
            if self.use_streaming:
                return self._call_llm_stream(messages)
            else:
                return self._call_llm(messages)
        finally:
            self.model = original_model

    def _build_messages(self, conversation: list[dict]) -> list[dict]:
        """Prepend system prompt at call time — never stored in conversation list."""
        return [{"role": "system", "content": self.system_prompt}] + conversation

    def _call_llm(self, messages, **kwargs):
        """Call the LLM API with exponential-backoff retry on transient errors."""
        for attempt in range(_MAX_RETRIES):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    **kwargs,
                ).choices[0].message.content
            except APIStatusError as exc:
                if exc.status_code not in _RETRYABLE_STATUS_CODES:
                    raise
                delay = min(_RETRY_BASE_DELAY * (2 ** attempt), _RETRY_MAX_DELAY)
                if exc.status_code == 429:
                    delay += random.uniform(0, delay * 0.5)  # jitter
                print(f"[retry] {exc.status_code} on attempt {attempt + 1}/{_MAX_RETRIES}, "
                      f"retrying in {delay:.1f}s …")
                time.sleep(delay)
            except (APIConnectionError, APITimeoutError) as exc:
                delay = min(_RETRY_BASE_DELAY * (2 ** attempt), _RETRY_MAX_DELAY)
                print(f"[retry] {type(exc).__name__} on attempt {attempt + 1}/{_MAX_RETRIES}, "
                      f"retrying in {delay:.1f}s …")
                time.sleep(delay)
        # Final attempt — let exceptions propagate
        return self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs,
        ).choices[0].message.content

    def _call_llm_stream(self, messages, **kwargs):
        """Streaming variant — prints tokens to stdout in real time, returns full text."""
        for attempt in range(_MAX_RETRIES):
            try:
                stream = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    **kwargs,
                )
                chunks: list[str] = []
                for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        print(delta.content, end="", flush=True)
                        chunks.append(delta.content)
                print()  # newline after stream finishes
                return "".join(chunks)
            except APIStatusError as exc:
                if exc.status_code not in _RETRYABLE_STATUS_CODES:
                    raise
                delay = min(_RETRY_BASE_DELAY * (2 ** attempt), _RETRY_MAX_DELAY)
                if exc.status_code == 429:
                    delay += random.uniform(0, delay * 0.5)
                print(f"\n[retry] {exc.status_code} on attempt {attempt + 1}/{_MAX_RETRIES}, "
                      f"retrying in {delay:.1f}s …")
                time.sleep(delay)
            except (APIConnectionError, APITimeoutError) as exc:
                delay = min(_RETRY_BASE_DELAY * (2 ** attempt), _RETRY_MAX_DELAY)
                print(f"\n[retry] {type(exc).__name__} on attempt {attempt + 1}/{_MAX_RETRIES}, "
                      f"retrying in {delay:.1f}s …")
                time.sleep(delay)
        # Final attempt
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            **kwargs,
        )
        chunks: list[str] = []
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                print(delta.content, end="", flush=True)
                chunks.append(delta.content)
        print()
        return "".join(chunks)

    async def _call_llm_async(self, prompt: str, system: str = "") -> str:
        """Async LLM wrapper for compaction. Runs sync _call_llm in executor."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._call_llm, messages)

    def _extract_tag_content(self, tag, text):
        match = re.search(f"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
        return match.group(1).strip() if match else None

    # Alias map for tool names the model might use vs what the runtime registers
    _TOOL_ALIASES = {
        "run_agent": "delegate_to_agent",
    }

    @staticmethod
    def _extract_json_object(text: str) -> str:
        """Extract the first complete JSON object from text, ignoring trailing garbage.

        Models sometimes append non-JSON text (e.g. ``<channel|>...``) after the
        closing brace. This uses a simple brace/bracket counter that respects
        quoted strings to find where the JSON object ends.
        """
        start = text.find("{")
        if start == -1:
            return text
        depth = 0
        in_string = False
        escape = False
        for i in range(start, len(text)):
            c = text[i]
            if escape:
                escape = False
                continue
            if c == "\\":
                escape = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if c in "{[":
                depth += 1
            elif c in "}]":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
        return text  # fallback: return as-is

    @staticmethod
    def _repair_json_args(raw: str) -> dict | None:
        """Attempt to repair JSON with unescaped double quotes inside string values.

        LLMs (especially Gemma) often produce JSON like:
            {"path": "f.md", "content": "text with "quotes" inside"}
        which is invalid because the inner quotes aren't escaped.

        Strategy: parse key-by-key using the known structure. For each
        ``"key": "value"`` pair, the value's opening quote is right after
        ``": "`` and its closing quote is found by scanning backwards from
        the next ``", "`` or ``"}`` boundary.
        """
        raw = raw.strip()
        if not raw.startswith("{") or not raw.endswith("}"):
            return None
        inner = raw[1:-1].strip()  # strip outer braces

        result = {}
        while inner:
            # Match key
            km = re.match(r'"([^"]+)"\s*:\s*', inner)
            if not km:
                break
            key = km.group(1)
            inner = inner[km.end():]

            if not inner:
                break

            if inner[0] == '"':
                # String value — find where it truly ends.
                # Look for the pattern: ", "next_key" or end of object "
                inner = inner[1:]  # skip opening quote
                # Try to find: "next comma + space + quote + key + quote + colon"
                # Pattern: '", "' followed by a key name
                next_key = re.search(r'",\s*"[^"]+"\s*:', inner)
                if next_key:
                    value = inner[:next_key.start()]
                    inner = inner[next_key.start() + 2:]  # skip '",'
                    inner = inner.strip()
                else:
                    # Last value — everything up to final quote
                    if inner.endswith('"'):
                        value = inner[:-1]
                    else:
                        value = inner
                    inner = ""
                result[key] = value
            elif inner[0] == '{':
                # Nested object — use brace counting
                depth, i = 0, 0
                for i, c in enumerate(inner):
                    if c == '{': depth += 1
                    elif c == '}': depth -= 1
                    if depth == 0: break
                try:
                    result[key] = json.loads(inner[:i+1])
                except json.JSONDecodeError:
                    result[key] = inner[:i+1]
                inner = inner[i+1:].lstrip().lstrip(",").strip()
            elif inner[0] == '[':
                depth, i = 0, 0
                for i, c in enumerate(inner):
                    if c == '[': depth += 1
                    elif c == ']': depth -= 1
                    if depth == 0: break
                try:
                    result[key] = json.loads(inner[:i+1])
                except json.JSONDecodeError:
                    result[key] = inner[:i+1]
                inner = inner[i+1:].lstrip().lstrip(",").strip()
            else:
                # Number, bool, null — read until comma or end
                vm = re.match(r'([^,}]+)', inner)
                if vm:
                    raw_val = vm.group(1).strip()
                    try:
                        result[key] = json.loads(raw_val)
                    except json.JSONDecodeError:
                        result[key] = raw_val
                    inner = inner[vm.end():].lstrip().lstrip(",").strip()

        return result if result else None

    @staticmethod
    def _infer_tool_from_args(json_str: str) -> str | None:
        """Infer tool name from JSON argument keys when model omits the name."""
        try:
            args = json.loads(json_str)
        except json.JSONDecodeError:
            return None
        keys = set(args.keys())
        if "agent_name" in keys:
            return "delegate_to_agent"
        if "path" in keys and "content" in keys:
            return "write_file"
        if "url" in keys:
            return "web_fetch"
        if "prompt" in keys:
            return "call_llm"
        if "pattern" in keys:
            return "memory_search"
        if "type" in keys and "key" in keys and "value" in keys:
            return "memory_store"
        if "type" in keys and "key" in keys:
            return "memory_recall"
        if "path" in keys:
            return "read_file"
        if "query" in keys:
            return "call_llm"
        return None

    def _parse_json_array_tools(self, response: str) -> list[tuple[str, str]]:
        """Parse JSON array tool calls from response (Format D).

        Handles both bare JSON arrays and ```json code blocks containing arrays like:
          [{"tool_name": "write_file", "parameters": {"path": "...", "content": "..."}}]
        Also handles variants with "tool_call" or "name" instead of "tool_name".
        """
        results = []
        # Extract JSON from ```json code blocks or bare arrays
        candidates = re.findall(r"```json\s*\n(.*?)```", response, re.DOTALL)
        if not candidates:
            # Try bare JSON arrays
            candidates = re.findall(r"(\[[\s\S]*?\])", response)

        for candidate in candidates:
            try:
                parsed = json.loads(candidate.strip())
            except json.JSONDecodeError:
                continue
            if not isinstance(parsed, list):
                continue
            for item in parsed:
                if not isinstance(item, dict):
                    continue
                # Extract tool name from various key conventions
                name = item.get("tool_name") or item.get("tool_call") or item.get("name") or ""
                params = item.get("parameters") or item.get("params") or item.get("arguments") or {}
                if not name and params:
                    name = self._infer_tool_from_args(json.dumps(params))
                if name:
                    results.append((name, json.dumps(params)))
        return results

    def _parse_tool_calls(self, response: str) -> list[tuple[str, str]]:
        """Extract tool calls from LLM response. Supports formats A, A2, B, C, D.

        Returns list of (tool_name, args_json_str) tuples.
        """
        # Format A: <tool_call name="tool_name">{"arg": "val"}</tool_call>
        tool_calls = re.findall(r"<tool_call name=\"(.*?)\">(.*?)</tool_call>", response, re.DOTALL)
        # Format A2: unclosed <tool_call name="..."> — match to next tag or end
        if not tool_calls:
            for m in re.finditer(
                r'<tool_call name="(.*?)">(.*?)(?=<tool_call|<final_answer|$)',
                response, re.DOTALL,
            ):
                name, body = m.group(1).strip(), m.group(2).strip()
                body = re.sub(r"</tool_call>\s*$", "", body).strip()
                if name and body:
                    tool_calls.append((name, body))
        # Format B/C: <tool_call>\n...\n</tool_call>
        if not tool_calls:
            for m in re.finditer(r"<tool_call>(.*?)</tool_call>", response, re.DOTALL):
                body = m.group(1).strip()
                tool_name = self._infer_tool_from_args(body)
                if tool_name:
                    tool_calls.append((tool_name, body))
                else:
                    lines = body.split("\n", 1)
                    if len(lines) == 2 and not lines[0].strip().startswith("{"):
                        tool_calls.append((lines[0].strip(), lines[1].strip()))
        # Format D: JSON array of tool calls
        if not tool_calls:
            tool_calls = self._parse_json_array_tools(response)
        return tool_calls

    def run_goal(self, goal, max_turns=10):
        """Execute a goal using the general workflow system.

        The system prompt is **never** stored in the conversation list — it is
        prepended by ``_build_messages()`` at each LLM call so that compaction
        can safely truncate older conversation messages without erasing it.
        """
        print("\n" + "="*20 + " AGENT EXECUTION START " + "="*20)
        # Conversation-only list — system prompt lives in self.system_prompt
        messages: list[dict] = [
            {"role": "user", "content": f"My goal is: {goal}"}
        ]

        for i in range(max_turns):
            print(f"\n--- Turn {i+1}/{max_turns} ---")

            # Compact conversation if token estimate exceeds threshold (LLM-powered)
            if should_compact(messages, self.compaction_config):
                try:
                    messages, summary = asyncio.run(
                        compact_messages_async(messages, self.compaction_config, self._call_llm_async)
                    )
                except RuntimeError:
                    # Fallback if event loop is already running
                    messages, summary = compact_messages(messages, self.compaction_config)
                print(f"[compaction] Condensed context ({len(summary)} chars summary)")

            try:
                full_messages = self._build_messages(messages)
                if self.use_streaming:
                    response = self._call_llm_stream(full_messages)
                else:
                    response = self._call_llm(full_messages)
            except Exception as e:
                print(f"!!! Error calling LLM: {e}")
                return f"Failed to get response from LLM: {e}"

            # Handle empty responses
            if not response or response.strip() == "":
                print("!!! Empty response from agent, retrying...")
                messages.append({
                    "role": "user",
                    "content": "Please provide a response with tool calls or a final_answer."
                })
                continue

            # Only print agent output when NOT streaming (streaming already printed)
            if not self.use_streaming:
                if len(response) > 500:
                    print(f"Agent Output:\n{response[:500]}...")
                else:
                    print(f"Agent Output:\n{response}")

            messages.append({"role": "assistant", "content": response})

            # Parse tool calls (supports formats A, A2, B, C, D)
            tool_calls = self._parse_tool_calls(response)

            # Process tool calls first (if any), then check for final answer
            if tool_calls:
                for tool_name, args_str in tool_calls:
                    # Resolve tool name aliases (e.g. run_agent → delegate_to_agent)
                    tool_name = self._TOOL_ALIASES.get(tool_name, tool_name)
                    print(f"\n--- Executing Tool: {tool_name} ---")
                    try:
                        # Parse JSON arguments — strip trailing garbage after the JSON object
                        clean_args = self._extract_json_object(args_str.strip())
                        try:
                            args = json.loads(clean_args)
                        except json.JSONDecodeError:
                            # Fallback: repair JSON with unescaped quotes
                            args = self._repair_json_args(clean_args)
                            if args is None:
                                raise json.JSONDecodeError(
                                    "Repair failed", clean_args, 0
                                )
                            print(f"   (repaired malformed JSON)")

                        # Permission policy check
                        input_preview = args_str.strip()[:120]
                        authorized, reason = self.policy.authorize(tool_name, input_preview, args=args)
                        if not authorized:
                            tool_result = f"DENIED: {reason}"
                            print(f"!!! Permission denied: {reason}")
                            messages.append({
                                "role": "user",
                                "content": f"Tool '{tool_name}' was denied: {reason}"
                            })
                            continue

                        if tool_name in self.tools:
                            # Execute the tool
                            if isinstance(args, dict):
                                tool_result = self.tools[tool_name](**args)
                            else:
                                tool_result = self.tools[tool_name](args)
                        else:
                            tool_result = f"Error: Tool '{tool_name}' not found. Available tools: {', '.join(self.tools.keys())}"

                        # Truncate long outputs for display
                        display_result = str(tool_result)[:500] + "..." if len(str(tool_result)) > 500 else str(tool_result)
                        print(f"Tool Result:\n{display_result}")

                        # Special handling for agent delegation results
                        if tool_name == "delegate_to_agent" and len(str(tool_result)) > 100:
                            print(f"🎉 Agent generated {len(str(tool_result))} characters of content!")

                        # Add tool result to conversation
                        messages.append({
                            "role": "user",
                            "content": f"Tool '{tool_name}' returned:\n{tool_result}"
                        })
                    except json.JSONDecodeError as e:
                        error_message = f"Error parsing arguments for tool '{tool_name}': {e}. Args: {args_str}"
                        print(f"!!! {error_message}")
                        messages.append({
                            "role": "user",
                            "content": error_message
                        })
                    except Exception as e:
                        error_message = f"Error executing tool '{tool_name}': {e}"
                        print(f"!!! {error_message}")
                        messages.append({
                            "role": "user",
                            "content": error_message
                        })

            # After processing tool calls, check for final answer
            final_answer = self._extract_tag_content("final_answer", response)
            if final_answer:
                print("\n" + "="*20 + " GOAL ACHIEVED " + "="*20)
                return final_answer

            # If no tool calls and no final answer, prompt the agent once;
            # if it responds without tags again, treat that as the final answer.
            if not tool_calls and "final_answer" not in response.lower():
                prev_role = messages[-2]["role"] if len(messages) >= 2 else ""
                prev_content = messages[-2].get("content", "") if len(messages) >= 2 else ""
                if prev_role == "user" and "provide a final_answer" in prev_content:
                    # Model failed to use tags twice — treat response as final answer
                    print("\n" + "="*20 + " GOAL ACHIEVED " + "="*20)
                    return response
                messages.append({
                    "role": "user",
                    "content": "Please either make a tool call or provide a final_answer."
                })

        return "Agent reached maximum turns without providing a final answer."

    # ── Cognitive Pipeline Executor ──────────────────────────────────

    def _get_model_capabilities(self) -> dict:
        """Look up model capabilities; fall back to _DEFAULT_CAPABILITY for unknown models."""
        return self.MODEL_CAPABILITIES.get(self.model, self._DEFAULT_CAPABILITY)

    @staticmethod
    def _parse_cognitive_pipeline(scenario_path: str) -> list[dict]:
        """Parse a scenario file into structured pipeline steps.

        Supports two formats:
          - Format A: YAML ``pipeline`` field with step dicts
          - Format B: Markdown headings (### Stage N / ## Phase N) with
            **Agent**, **Goal**, **Output** fields
        """
        with open(scenario_path, "r", encoding="utf-8") as f:
            content = f.read()
        fm = _parse_frontmatter(content)

        # Format A: pipeline field in frontmatter
        pipeline_yaml = fm.get("pipeline")
        if pipeline_yaml:
            agents_required = fm.get("agents_required", [])
            steps = []
            for i, entry in enumerate(pipeline_yaml):
                agent_name = ""
                if i < len(agents_required):
                    raw = agents_required[i]
                    agent_name = re.sub(r"\s*\(.*?\)\s*$", "", raw).strip()
                steps.append({
                    "step": entry.get("step", i + 1),
                    "agent": agent_name,
                    "goal": entry.get("deliverable", ""),
                    "output": entry.get("deliverable", ""),
                    "dialect": entry.get("dialect", ""),
                })
            return steps

        # Format B: parse ### Stage N / ## Phase N headings from body
        # Strip frontmatter
        body = re.sub(r"^---\n.*?\n---\n?", "", content, count=1, flags=re.DOTALL)
        steps = []
        # Match both "### Stage N:" and "## Phase N:" patterns
        pattern = r"(?:^###?\s+(?:Stage|Phase)\s+(\d+)[:\s].*?)(?=\n###?\s+(?:Stage|Phase)\s+\d+|\n## Expected|\n## Execution|\n## Loop|\n## Error|\n## Success|\n## Why|\n## Usage|\n## The|\n## Deep|\Z)"
        for block_match in re.finditer(pattern, body, re.DOTALL | re.MULTILINE):
            block = block_match.group(0)
            step_num = int(block_match.group(1))

            agent_match = re.search(r"\*\*Agent\*\*:\s*`?([^`\n]+)`?", block)
            goal_match = re.search(r"\*\*Goal\*\*:\s*(.+)", block)
            output_match = re.search(r"\*\*Output\*\*:\s*`?([^`\n]+)`?", block)

            steps.append({
                "step": step_num,
                "agent": agent_match.group(1).strip() if agent_match else "",
                "goal": goal_match.group(1).strip() if goal_match else "",
                "output": output_match.group(1).strip() if output_match else "",
            })
        return steps

    def execute_scenario(self, scenario_path: str, problem_context: str, *,
                         max_turns: int = 10, max_turns_per_step: int = 5,
                         strategy_override: str | None = None,
                         project_dir: str | None = None) -> str:
        """Strategy router: pick the right execution mode for the model.

        Strategy selection:
          - strategy_override takes precedence if provided
          - Otherwise uses MODEL_CAPABILITIES[self.model]["recommended_strategy"]
          - high tier → run_goal (agentic)
          - mid tier  → run_cognitive_pipeline
          - low tier  → run_pipeline (deterministic)
        """
        if strategy_override:
            strategy = strategy_override
        else:
            caps = self._get_model_capabilities()
            strategy = caps["recommended_strategy"]

        print(f"\n📋 Strategy selected: {strategy} (model={self.model})")

        if strategy == "agentic":
            # High-tier: let the model orchestrate freely
            self.load_scenario(scenario_path)
            with open(scenario_path, "r", encoding="utf-8") as f:
                scenario_content = f.read()
            if project_dir:
                self._active_project_dir = project_dir
            goal = f"Execute the following scenario:\n\n{scenario_content}\n\nProblem context: {problem_context}"
            return self.run_goal(goal, max_turns=max_turns)

        elif strategy == "cognitive_pipeline":
            return self.run_cognitive_pipeline(
                scenario_path, problem_context,
                max_turns_per_step=max_turns_per_step,
                project_dir=project_dir,
            )

        elif strategy == "pipeline":
            return self.run_pipeline(scenario_path, problem_context,
                                     max_turns_per_step=1)

        else:
            print(f"⚠️  Unknown strategy '{strategy}', falling back to cognitive_pipeline")
            return self.run_cognitive_pipeline(
                scenario_path, problem_context,
                max_turns_per_step=max_turns_per_step,
                project_dir=project_dir,
            )

    def run_cognitive_pipeline(self, scenario_path: str, problem_context: str, *,
                               max_turns_per_step: int = 5,
                               max_retries_per_step: int = 2,
                               project_dir: str | None = None) -> str:
        """Execute a scenario as a forced step-by-step cognitive pipeline.

        Each step runs as a mini agentic loop with tool access, bounded turns,
        and output validation. Steps chain via prior_outputs.
        """
        steps = self._parse_cognitive_pipeline(scenario_path)
        if not steps:
            print("⚠️  No pipeline steps parsed — falling back to run_goal")
            self.load_scenario(scenario_path)
            with open(scenario_path, "r", encoding="utf-8") as f:
                scenario_content = f.read()
            return self.run_goal(
                f"Execute:\n{scenario_content}\n\nContext: {problem_context}",
                max_turns=10,
            )

        with open(scenario_path, "r", encoding="utf-8") as f:
            scenario_content = f.read()

        # Load dialect grammars if present
        self.load_scenario(scenario_path)

        # Determine project directory
        if not project_dir:
            fm = _parse_frontmatter(scenario_content)
            name = fm.get("name", "unnamed").replace("-", "_")
            project_dir = f"projects/Project_{name}"

        # Create project directory structure
        for subdir in ["output", "state", "memory/short_term", "memory/long_term",
                        "components/agents", "components/tools", "wiki/concepts"]:
            os.makedirs(os.path.join(project_dir, subdir), exist_ok=True)

        # Set active project dir so delegation picks it up
        self._active_project_dir = project_dir

        print(f"\n{'='*60}")
        print(f"  Cognitive Pipeline: {len(steps)} steps")
        print(f"  Project: {project_dir}")
        print(f"  Model: {self.model}")
        print(f"{'='*60}")

        prior_outputs: list[str] = []
        results: list[StepResult] = []

        for step in steps:
            step_num = step["step"]
            agent_name = step["agent"]
            output_file = step.get("output", "")

            # Determine validation thresholds
            min_chars = 3000 if output_file.endswith(".py") else 2000
            validation = StepValidation(min_chars=min_chars)

            print(f"\n{'─'*60}")
            print(f"  Step {step_num}: {step['goal'][:80]}")
            print(f"  Agent: {agent_name}")
            print(f"  Output: {output_file}")
            print(f"{'─'*60}")

            result = None
            for attempt in range(1 + max_retries_per_step):
                retry_feedback = ""
                if attempt > 0 and result:
                    passed, feedback = self._validate_step_output(result, validation)
                    retry_feedback = f"\n\n## RETRY FEEDBACK (attempt {attempt + 1})\n\n{feedback}\n\nPlease produce a MORE COMPREHENSIVE output addressing the above."

                result = self._run_step_with_tools(
                    step, prior_outputs, problem_context,
                    scenario_content,
                    max_turns=max_turns_per_step,
                    project_dir=project_dir,
                    retry_feedback=retry_feedback,
                )

                passed, feedback = self._validate_step_output(result, validation)
                if passed:
                    result.status = "pass"
                    print(f"  ✅ Step {step_num} PASSED ({result.char_count} chars, {len(result.files_written)} files)")
                    break
                else:
                    print(f"  ⚠️  Step {step_num} attempt {attempt + 1} failed validation: {feedback}")

            if result.status != "pass":
                result.status = "partial"
                print(f"  ⚡ Step {step_num} PARTIAL after {max_retries_per_step + 1} attempts")

            results.append(result)
            # Chain output to next step (truncated for context)
            output_summary = result.output[:4000] if len(result.output) > 4000 else result.output
            prior_outputs.append(f"### Step {step_num} ({agent_name}) Output:\n\n{output_summary}")

        # Build summary
        summary_lines = [f"\n{'='*60}", "  COGNITIVE PIPELINE COMPLETE", f"{'='*60}"]
        total_chars = 0
        for r in results:
            status_icon = "✅" if r.status == "pass" else "⚡"
            summary_lines.append(f"  {status_icon} Step {r.step_num} ({r.agent_name}): {r.status} — {r.char_count} chars, {len(r.files_written)} files")
            total_chars += r.char_count
        summary_lines.append(f"  Total output: {total_chars} chars")
        summary = "\n".join(summary_lines)
        print(summary)
        return summary

    def _run_step_with_tools(self, step: dict, prior_outputs: list[str],
                              problem_context: str, scenario_content: str, *,
                              max_turns: int = 5, project_dir: str = "",
                              retry_feedback: str = "") -> StepResult:
        """Run a single pipeline step as a mini agentic loop with tool access.

        Temporarily replaces self.system_prompt with the agent's markdown definition,
        then runs the same tool-call loop as run_goal().
        """
        step_num = step["step"]
        agent_name = step["agent"]
        goal = step["goal"]
        output_file = step.get("output", "")

        result = StepResult(step_num=step_num, agent_name=agent_name)

        # Load agent markdown — try discovery first, then generate dynamically
        agent_info = self._find_agent(agent_name) if agent_name else {"found": False}

        if agent_info.get("found"):
            agent_system = agent_info["content"]
        else:
            # Dynamic subagent creation: generate from scenario context
            agent_system = self._generate_agent_spec(
                agent_name or f"step-{step_num}-agent",
                step, scenario_content, project_dir,
            )

        # Build prior-output file injection: pre-read files from prior steps
        # so the model has actual file content without calling read_file.
        file_injection = ""
        prior_files_read: list[str] = []
        for prev_result in prior_outputs:
            # Extract file paths mentioned in prior step summaries
            pass  # We'll use the results list passed separately

        # Collect files from the results list (passed via prior_outputs metadata)
        # Instead, scan the project output directory for existing files
        output_dir = os.path.join(project_dir, "output")
        state_dir = os.path.join(project_dir, "state")
        wiki_dir = os.path.join(project_dir, "output", "wiki")
        injected_files = []
        for scan_dir in [output_dir, state_dir, wiki_dir]:
            if not os.path.isdir(scan_dir):
                continue
            for root, _dirs, files in os.walk(scan_dir):
                for fname in sorted(files):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            content = f.read()
                        if content.strip():
                            # Truncate large files to keep context manageable
                            truncated = content[:3000] if len(content) > 3000 else content
                            rel_path = os.path.relpath(fpath, project_dir)
                            injected_files.append(f"### File: `{rel_path}`\n```\n{truncated}\n```")
                    except (OSError, UnicodeDecodeError):
                        continue

        if injected_files:
            file_injection = "\n\n## FILES FROM PRIOR STEPS (pre-loaded for you)\n\n" + "\n\n".join(injected_files[:10])
            prior_files_read = [f for f in injected_files[:10]]

        # Build step prompt
        prior_context = ""
        if prior_outputs:
            prior_context = "\n\n## Prior Step Summaries\n\n" + "\n\n---\n\n".join(
                o[:2000] for o in prior_outputs
            )

        step_prompt = (
            f"## YOUR TASK\n\n{goal}\n\n"
            f"## OUTPUT FILE\n\nSave your output to: `{project_dir}/output/{output_file}`\n\n"
            f"## PROBLEM CONTEXT\n\n{problem_context}\n\n"
            f"## IMPORTANT INSTRUCTIONS\n\n"
            f"- Produce COMPREHENSIVE, DETAILED content (at least 2000 characters)\n"
            f"- Use write_file tool to save your output\n"
            f"- Focus ONLY on this specific task\n"
            f"- Be thorough and include mathematical detail where appropriate\n"
            f"{file_injection}"
            f"{prior_context}"
            f"{retry_feedback}"
        )

        # Temporarily swap system prompt
        original_system_prompt = self.system_prompt
        self.system_prompt = agent_system + self._GEMINI_TOOL_FORMAT_INSTRUCTIONS
        try:
            # Tool-call scaffolding: inject a concrete example so mid-tier
            # models see the exact XML format before generating their response.
            output_path = f"{project_dir}/output/{output_file}" if output_file else f"{project_dir}/output/step_{step_num}.md"
            scaffold_example = (
                f'Here is an example of the tool call format you MUST use:\n\n'
                f'<tool_call name="write_file">\n'
                f'{{"path": "{output_path}", "content": "Your detailed content here..."}}\n'
                f'</tool_call>\n\n'
                f'<final_answer>\nStep {step_num} complete. File saved to {output_path}\n</final_answer>'
            )
            messages: list[dict] = [
                {"role": "user", "content": step_prompt},
                {"role": "assistant", "content": scaffold_example},
                {"role": "user", "content": f"Good format. Now execute the task for real. Write the FULL content to `{output_path}` using write_file, then provide a final_answer."},
            ]

            for turn in range(max_turns):
                # Compact if needed
                if should_compact(messages, self.compaction_config):
                    try:
                        messages, summary = asyncio.run(
                            compact_messages_async(messages, self.compaction_config, self._call_llm_async)
                        )
                    except RuntimeError:
                        messages, summary = compact_messages(messages, self.compaction_config)

                try:
                    full_messages = self._build_messages(messages)
                    if self.use_streaming:
                        response = self._call_llm_stream(full_messages)
                    else:
                        response = self._call_llm(full_messages)
                except Exception as e:
                    print(f"    !!! Step {step_num} LLM error: {e}")
                    break

                if not response or response.strip() == "":
                    messages.append({
                        "role": "user",
                        "content": "Please provide your output with tool calls or a final_answer."
                    })
                    continue

                messages.append({"role": "assistant", "content": response})
                result.output += response + "\n"
                result.char_count = len(result.output)

                # Parse and execute tool calls
                tool_calls = self._parse_tool_calls(response)
                if tool_calls:
                    for tool_name, args_str in tool_calls:
                        tool_name = self._TOOL_ALIASES.get(tool_name, tool_name)
                        try:
                            clean_args = self._extract_json_object(args_str.strip())
                            try:
                                args = json.loads(clean_args)
                            except json.JSONDecodeError:
                                args = self._repair_json_args(clean_args)
                                if args is None:
                                    raise json.JSONDecodeError("Repair failed", clean_args, 0)

                            # Permission check
                            input_preview = args_str.strip()[:120]
                            authorized, reason = self.policy.authorize(tool_name, input_preview, args=args)
                            if not authorized:
                                messages.append({"role": "user", "content": f"Tool '{tool_name}' denied: {reason}"})
                                continue

                            if tool_name in self.tools:
                                tool_result = self.tools[tool_name](**args) if isinstance(args, dict) else self.tools[tool_name](args)
                            else:
                                tool_result = f"Error: Tool '{tool_name}' not found."

                            # Track file writes
                            if tool_name == "write_file" and isinstance(args, dict):
                                written_path = args.get("path", "")
                                result.files_written.append(written_path)
                                content_len = len(args.get("content", ""))
                                result.char_count = max(result.char_count, content_len)
                                print(f"    📄 Wrote {written_path} ({content_len} chars)")

                            display = str(tool_result)[:300] + "..." if len(str(tool_result)) > 300 else str(tool_result)
                            messages.append({"role": "user", "content": f"Tool '{tool_name}' returned:\n{display}"})
                        except (json.JSONDecodeError, Exception) as e:
                            messages.append({"role": "user", "content": f"Error with tool '{tool_name}': {e}"})

                # Check for final answer
                final_answer = self._extract_tag_content("final_answer", response)
                if final_answer:
                    result.output = final_answer
                    result.char_count = max(result.char_count, len(final_answer))
                    break

                # If no tools and no final answer, done with this step
                if not tool_calls:
                    # Auto-wrap: if the model produced substantial prose but
                    # didn't call write_file, save it automatically.
                    if not result.files_written and len(response.strip()) >= 500 and output_file:
                        auto_path = f"{project_dir}/output/{output_file}"
                        try:
                            if "write_file" in self.tools:
                                self.tools["write_file"](path=auto_path, content=response)
                                result.files_written.append(auto_path)
                                result.char_count = max(result.char_count, len(response))
                                print(f"    📝 Auto-saved prose output → {auto_path} ({len(response)} chars)")
                        except Exception as e:
                            print(f"    ⚠️  Auto-save failed: {e}")
                    break

        finally:
            self.system_prompt = original_system_prompt

        return result

    def _validate_step_output(self, result: StepResult,
                               validation: StepValidation) -> tuple[bool, str]:
        """Rule-based validation of a pipeline step's output.

        Returns (passed, feedback_message).
        """
        issues = []

        if result.char_count < validation.min_chars:
            issues.append(
                f"Output too short: {result.char_count} chars (minimum {validation.min_chars}). "
                f"Please produce more comprehensive, detailed content."
            )

        if validation.require_file_write and not result.files_written:
            issues.append(
                "No file was written. You MUST use write_file to save your output."
            )

        for section in validation.required_sections:
            if section.lower() not in result.output.lower():
                issues.append(f"Missing required section: '{section}'")

        if issues:
            return False, " | ".join(issues)
        return True, "OK"

    def interactive_mode(self, provider_label: str | None = None):
        """Interactive REPL mode for the runtime."""
        label = provider_label or self.provider_name
        print("\n" + "="*60)
        print(f"           SkillOS Agent Runtime ({label}) - Interactive Mode")
        print("="*60)
        print("Type 'help' for commands, 'exit' to quit")
        print("Or simply type your goal to execute it.")

        while True:
            try:
                user_input = input("\n🎯 skillos> ").strip()

                if user_input.lower() in ['exit', 'quit']:
                    print("Goodbye!")
                    break

                if user_input.lower() == 'help':
                    print("""
Available Commands:
- help     : Show this help message
- status   : Show current workspace status
- clear    : Clear workspace (with confirmation)
- demo     : Run architecture demo without API calls
- exit/quit: Exit interactive session

Simply type any goal to execute it, for example:
  Create a Python calculator
  Analyze the files in my workspace
  Build a REST API with FastAPI
  Execute Project Aorta using quantum cepstral analysis
  Research quantum computing trends and create a report
""")
                    continue

                if user_input.lower() == 'status':
                    workspace_files = self.tools['list_files']('workspace')
                    print(f"Workspace contains: {workspace_files}")
                    continue

                if user_input.lower() == 'clear':
                    confirm = input("Clear workspace? This will delete all files in workspace/ (y/n): ")
                    if confirm.lower() == 'y':
                        self.tools['execute_bash']('rm -rf workspace/*')
                        print("Workspace cleared.")
                    continue


                if user_input.lower() == 'demo':
                    print("Running architecture demo...")
                    agents = self.tools["list_agents"]()
                    print(f"✅ Found {len(agents)} agents")
                    print(f"✅ Tools loaded: {len(self.tools)}")
                    print("🎉 Architecture is ready for full execution!")
                    continue

                # Execute the goal
                if user_input:
                    result = self.run_goal(user_input)
                    print("\n" + "="*60)
                    print("                  FINAL RESULT")
                    print("="*60)
                    print(result)

            except KeyboardInterrupt:
                print("\n\nInterrupted. Type 'exit' to quit.")
            except Exception as e:
                print(f"Error: {e}")

# Backward compatibility alias
QwenRuntime = AgentRuntime


# ===================================================
# Main Execution Block
# ===================================================
if __name__ == "__main__":
    import sys

    # Parse CLI flags: --permission-policy, --provider, --manifest, --max-turns, --no-stream, --sandbox, --scenario, --strategy, --project-dir
    policy_arg = None
    provider_arg = "qwen"
    manifest_arg = None  # None = auto-select from provider config
    max_turns_arg = 10
    stream_arg = True
    sandbox_arg = "local"
    scenario_arg = None
    strategy_arg = None
    project_dir_arg = None
    filtered_args = []
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--permission-policy" and i + 1 < len(sys.argv):
            policy_arg = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--provider" and i + 1 < len(sys.argv):
            provider_arg = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--manifest" and i + 1 < len(sys.argv):
            manifest_arg = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--max-turns" and i + 1 < len(sys.argv):
            max_turns_arg = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--no-stream":
            stream_arg = False
            i += 1
        elif sys.argv[i] == "--sandbox" and i + 1 < len(sys.argv):
            sandbox_arg = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--scenario" and i + 1 < len(sys.argv):
            scenario_arg = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--strategy" and i + 1 < len(sys.argv):
            strategy_arg = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == "--project-dir" and i + 1 < len(sys.argv):
            project_dir_arg = sys.argv[i + 1]
            i += 2
        else:
            filtered_args.append(sys.argv[i])
            i += 1

    # Graceful fallback: if e2b requested but unavailable, fall back to local
    if sandbox_arg == "e2b":
        try:
            _test_executor = create_executor("e2b")
        except (ImportError, RuntimeError) as exc:
            print(f"⚠️  E2B sandbox unavailable ({exc}), falling back to local executor.")
            sandbox_arg = "local"

    policy = get_policy(policy_arg) if policy_arg else SKILLOS_DEFAULT_POLICY
    runtime = AgentRuntime(manifest_path=manifest_arg, permission_policy=policy, provider=provider_arg, stream=stream_arg, sandbox_mode=sandbox_arg)

    # Pipeline mode: --scenario takes precedence
    if scenario_arg:
        problem_context = " ".join(filtered_args) if filtered_args else ""
        if not problem_context:
            print("Usage: python agent_runtime.py --scenario <path> [--strategy agentic|cognitive_pipeline|pipeline] [--project-dir path] \"problem context\"")
            sys.exit(1)
        result = runtime.execute_scenario(
            scenario_arg, problem_context,
            max_turns=max_turns_arg,
            strategy_override=strategy_arg,
            project_dir=project_dir_arg,
        )
        print(f"\nResult: {result}")
        sys.exit(0)

    # Parse command line arguments
    if len(filtered_args) > 0:
        command = filtered_args[0].lower()

        if command == "interactive":
            runtime.interactive_mode()
        elif command == "demo":
            print("Running architecture demo...")
            agents = runtime.tools["list_agents"]()
            print(f"✅ Found {len(agents)} agents")
            print(f"✅ Tools loaded: {len(runtime.tools)}")
            print("🎉 Architecture is ready for full execution!")
        elif command == "test":
            # Quick test mode
            print("Running quick test...")
            test_goal = "Create a simple Python script that prints 'Hello SkillOS!'"
            result = runtime.run_goal(test_goal, max_turns=3)
            print(f"\nTest result: {result}")
        else:
            # Treat unknown command as a goal to execute
            goal = " ".join(filtered_args)
            print(f"Executing goal: {goal}")
            result = runtime.run_goal(goal, max_turns=max_turns_arg)
            print(f"\nResult: {result}")
    else:
        # Default: Run Project Aorta using generic runtime
        project_aorta_goal = """Execute Project Aorta using quantum-enhanced cepstral analysis:

STEP 1: Use visionary-agent to create comprehensive project vision
- Focus on arterial navigation using CEPSTRAL ANALYSIS (not encryption)
- Emphasize homomorphic transforms and quantum Fourier Transform
- Save to workspace/project_vision.md

STEP 2: Use mathematician-agent to develop mathematical framework
- Create rigorous framework for cepstral analysis using QFT
- Include echo separation and filtering equations
- Save to workspace/mathematical_framework.md

STEP 3: Use quantum-engineer-agent to create Qiskit implementation
- Build complete quantum circuit for cepstral analysis
- Include echo detection and classical validation
- Save to workspace/quantum_poc.py

Process agents sequentially and save outputs immediately."""

        result = runtime.run_goal(project_aorta_goal)
        print(f"\n🎉 Project Aorta execution result: {result}")