# SkillOS Runtimes

SkillOS supports three runtimes. All runtimes share the same skill tree, project structure, and memory system — they differ in the LLM provider and tool execution layer.

---

## Runtime 1: Claude Code (Primary)

**Best for:** Full tool access, CI/CD, scripting, production use.

Claude Code is the primary runtime. It has direct access to all Claude Code native tools (Read, Write, Bash, WebFetch, Task, Agent) and the full agent discovery system via `.claude/agents/`.

### Setup

```bash
# One-time agent initialization
./setup_agents.sh    # Mac/Linux
.\setup_agents.ps1   # Windows

# Single command execution
claude --dangerously-skip-permissions "boot skillos"
claude --dangerously-skip-permissions "skillos execute: 'your goal here'"
```

### Interactive Terminal

The `skillos.sh` wrapper launches a rich terminal REPL with markdown rendering:

```bash
./skillos.sh
# Or directly:
python3 skillos.py
```

**Terminal commands:**

| Command | Description |
|---------|-------------|
| `help` | Show available commands and examples |
| `status` | Current workspace and execution state |
| `projects` | List all projects |
| `agents` | List discovered agents |
| `history` | Execution history |
| `refine` | Re-run last goal with improvements |
| `clear` | Reset workspace (with confirmation) |
| `exit` / `quit` | Exit terminal |

**Goal refinement:**
```
skillos$ Create a web scraper for news articles
[executes...]

skillos$ refine
Previous goal: Create a web scraper for news articles
Refinement: Add retry logic and save output as JSON
[re-executes with improvement...]
```

### Permission Model

The `--dangerously-skip-permissions` flag is required for automated execution since SkillOS needs to create files, run bash commands, and fetch URLs. For interactive use with approval prompts, omit the flag.

For tighter control, use `permission_policy.py` to define ALLOW/DENY/PROMPT rules per tool.

---

## Runtime 2: Qwen / Gemini (Multi-Provider)

**Best for:** Lightweight use, learning, resource-constrained environments, free-tier access.

`agent_runtime.py` is a provider-agnostic agent runtime that supports Qwen (via OpenRouter) and Gemini (Google AI). It interprets `QWEN.md` as the system manifest and implements the same agent delegation model as Claude Code.

### Setup

```bash
pip install openai python-dotenv requests
```

Create `.env`:
```env
# For Qwen (OpenRouter — free tier available)
OPENROUTER_API_KEY=your_key_here

# For Gemini (Google AI)
GEMINI_API_KEY=your_key_here
```

### Usage

```bash
# Run with Qwen (default)
python agent_runtime.py "Your goal here"

# Run with Gemini
python agent_runtime.py --provider gemini "Your goal here"

# Use a custom manifest
python agent_runtime.py --provider gemini --manifest CUSTOM.md "Your goal"

# Interactive mode
python agent_runtime.py interactive

# Test connectivity
python agent_runtime.py --provider gemini test
```

### Local Deployment with Ollama

Run SkillOS fully offline using a local Qwen model:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull qwen:4b

# Update base_url in agent_runtime.py to:
# base_url = "http://localhost:11434/v1"
```

### Native Tools Available

The Qwen runtime implements these tools natively in Python:

| Tool | Description |
|------|-------------|
| `read_file` | Read any file |
| `write_file` | Write/create files |
| `list_files` | List directory contents |
| `execute_bash` | Run shell commands |
| `web_fetch` | Fetch URL content |
| `grep_files` | Search file content recursively |
| `call_llm` | Recursive LLM call for sub-tasks |
| `create_agent` | Dynamically create agent markdown |
| `load_agent` | Load agent spec for delegation |
| `delegate_to_agent` | Delegate to a named agent |
| `update_memory` | Write to memory log |
| `query_memory` | Query past experiences |
| `query_memory_graph` | Query evolving-memory graph (:8420) |
| `log_trace` | Log trace to evolving-memory |
| `trigger_dream` | Start dream consolidation cycle |
| `get_memory_stats` | Get evolving-memory statistics |
| `robot_telemetry` | Get live robot telemetry (:8430) |

### Context Compaction

For long-running sessions, `compactor.py` provides LLM-powered context compaction:

```python
from compactor import compact_context

# Synchronous
summary = compact_context(messages, provider="gemini")

# Async
summary = await compact_context_async(messages, provider="qwen")
```

This summarizes older messages to stay within context limits while preserving key decisions and results.

---

## Runtime 3: Direct API

Any HTTP client can interact with SkillOS components directly.

**Boot and execute via curl:**
```bash
claude --dangerously-skip-permissions "boot skillos"
```

**Access robot tools directly (requires bridge):**
```bash
curl -s -X POST http://localhost:8430/tool/robot.go_to \
  -H "Content-Type: application/json" \
  -d '{"location": "kitchen"}'
```

---

## Runtime Comparison

| Feature | Claude Code | Qwen/Gemini | Local Ollama |
|---------|-------------|-------------|--------------|
| Full tool access | Yes | Yes (Python) | Yes (Python) |
| Agent sub-spawning | Yes (native) | Yes (delegate_to_agent) | Yes |
| Robot integration | Yes | Yes | Yes |
| Dream consolidation | Yes | Yes (native tools) | Yes |
| Cost | Claude pricing | OpenRouter / Google AI | Free |
| Offline use | No | No | Yes |
| Context window | Large | Provider-dependent | Model-dependent |
| LLM-powered compaction | N/A | Yes (compactor.py) | Yes |

---

## Environment Variables

```env
# Claude Code
# (uses Claude Code's own auth — no additional vars needed)

# Qwen via OpenRouter
OPENROUTER_API_KEY=sk-or-...

# Gemini
GEMINI_API_KEY=AI...

# Local Ollama
OLLAMA_HOST=http://localhost:11434
```
