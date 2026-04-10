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
from openai import OpenAI, APIStatusError, APIConnectionError, APITimeoutError
from dotenv import load_dotenv
from permission_policy import PermissionPolicy, PermissionMode, SKILLOS_DEFAULT_POLICY, get_policy
from compactor import CompactionConfig, should_compact, compact_messages, compact_messages_async

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
    }

    def __init__(self, manifest_path: str | None = None, permission_policy: PermissionPolicy | None = None, provider: str = "qwen", stream: bool = True):
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
        self.compaction_config = CompactionConfig()
        self.compaction_config.configure_for_model(self.model)
        resolved_manifest = manifest_path or cfg["manifest"]
        self._load_manifest(resolved_manifest)
        print(f"✅ Agent Runtime Initialized (provider={provider}, model={self.model}, manifest={resolved_manifest}).")

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
                namespace = {}
                exec(code, globals(), namespace)
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

    @staticmethod
    def _make_shell_tool(script: str, tool_name: str):
        """Create a Python callable that executes a GEMINI.md shell script."""
        def tool_fn(**kwargs):
            env = os.environ.copy()
            env["GEMINI_TOOL_ARGS"] = json.dumps(kwargs)
            result = subprocess.run(
                ["bash", "-c", script],
                capture_output=True, text=True, env=env, timeout=30,
            )
            output = result.stdout.strip()
            if result.returncode != 0:
                err = result.stderr.strip()
                return f"Error running {tool_name}: {err}" if err else output
            return output
        return tool_fn

    def _handle_call_llm(self, prompt: str):
        """Handles recursive calls to the LLM."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        return self._call_llm(messages)

    def _handle_delegate_to_agent(self, agent_name: str, task_description: str, input_data: dict = None):
        """Handles delegation to specialized agents."""
        print(f"\n🎯 Delegating to agent: {agent_name}")

        # Load the agent definition — use compiled load_agent tool if available,
        # otherwise fall back to built-in filesystem search.
        if "load_agent" in self.tools:
            agent_info = self.tools["load_agent"](agent_name)
        else:
            agent_info = self._find_agent(agent_name)
        if not agent_info.get("found"):
            return f"❌ Agent '{agent_name}' not found."

        # Create agent-specific prompt using the agent's context
        agent_prompt = f"""
{agent_info['content']}

## CURRENT TASK

{task_description}

## INPUT DATA

{json.dumps(input_data or {}, indent=2)}

## INSTRUCTIONS

Execute this task according to your specialized capabilities and return the results.
Focus on generating high-quality, detailed content appropriate to your role.
Do not use tool calls - just provide your expert response directly.
"""

        print(f"   📋 Agent description: {agent_info['description']}")
        print(f"   🛠️  Available tools: {agent_info.get('tools', 'N/A')}")

        # Make LLM call with agent context
        messages = [
            {"role": "system", "content": agent_prompt},
            {"role": "user", "content": f"Execute the task: {task_description}"}
        ]

        try:
            response = self._call_llm(messages)
            print(f"   ✅ Agent {agent_name} completed task")
            print(f"   📄 Generated {len(response)} characters")
            return response
        except Exception as e:
            error_msg = f"❌ Error executing agent {agent_name}: {e}"
            print(f"   {error_msg}")
            return error_msg

    @staticmethod
    def _find_agent(agent_name: str) -> dict:
        """Built-in agent lookup across standard directories (fallback for GEMINI manifests)."""
        for agents_dir in [".claude/agents", "system/agents"]:
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

            # Check for tool calls in the response
            tool_calls = re.findall(r"<tool_call name=\"(.*?)\">(.*?)</tool_call>", response, re.DOTALL)

            # Process tool calls first (if any), then check for final answer
            if tool_calls:
                for tool_name, args_str in tool_calls:
                    print(f"\n--- Executing Tool: {tool_name} ---")
                    try:
                        # Parse JSON arguments
                        args = json.loads(args_str.strip())

                        # Permission policy check
                        input_preview = args_str.strip()[:120]
                        authorized, reason = self.policy.authorize(tool_name, input_preview)
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

            # If no tool calls and no final answer, prompt the agent
            if not tool_calls and "final_answer" not in response.lower():
                messages.append({
                    "role": "user",
                    "content": "Please either make a tool call or provide a final_answer."
                })

        return "Agent reached maximum turns without providing a final answer."



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

    # Parse CLI flags: --permission-policy, --provider, --manifest, --max-turns, --no-stream
    policy_arg = None
    provider_arg = "qwen"
    manifest_arg = None  # None = auto-select from provider config
    max_turns_arg = 10
    stream_arg = True
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
        else:
            filtered_args.append(sys.argv[i])
            i += 1

    policy = get_policy(policy_arg) if policy_arg else SKILLOS_DEFAULT_POLICY
    runtime = AgentRuntime(manifest_path=manifest_arg, permission_policy=policy, provider=provider_arg, stream=stream_arg)

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