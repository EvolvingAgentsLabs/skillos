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

## Runtime 2: Qwen / Gemini / Gemma (Multi-Provider)

**Best for:** Lightweight use, learning, resource-constrained environments, free-tier access.

`agent_runtime.py` is a provider-agnostic agent runtime that supports Qwen (via OpenRouter), Gemini (Google AI), Gemma 4 (via Ollama or OpenRouter), and any OpenAI-compatible endpoint. It interprets the provider's manifest and implements the same agent delegation model as Claude Code.

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

# For Gemma 4 via OpenRouter (uses same key as Qwen)
# OPENROUTER_API_KEY=your_key_here
```

### Usage

```bash
# Run with Qwen (default)
python agent_runtime.py "Your goal here"

# Run with Gemini
python agent_runtime.py --provider gemini "Your goal here"

# Run with Gemma 4 via OpenRouter (26B model)
python agent_runtime.py --provider gemma-openrouter "Your goal here"

# Use a custom manifest
python agent_runtime.py --provider gemini --manifest CUSTOM.md "Your goal"

# Interactive mode
python agent_runtime.py interactive

# Test connectivity
python agent_runtime.py --provider gemini test
```

### Scenario Runner

`run_scenario.py` is a generic scenario runner that replaces per-scenario scripts. It uses the strategy router to automatically pick the right execution mode:

```bash
# Run Echo-Q with Gemma 4 (auto-selects cognitive_pipeline for mid-tier models)
python run_scenario.py scenarios/Operation_Echo_Q.md "quantum cepstral analysis" \
    --provider gemma-openrouter --no-stream

# Run Aorta with explicit strategy override
python run_scenario.py scenarios/ProjectAortaScenario.md "quantum arterial navigation" \
    --provider gemma-openrouter --strategy cognitive_pipeline --no-stream

# Run with a specific project directory
python run_scenario.py scenarios/Operation_Echo_Q.md "quantum cepstral analysis" \
    --provider gemma-openrouter --project-dir projects/Project_echo_q_custom
```

See [docs/cognitive-pipeline.md](cognitive-pipeline.md) for how the strategy router and cognitive pipeline work.

### Gemma 4 via Ollama

Run SkillOS locally (or via a free Colab GPU tunnel) using Google's Gemma 4:

```bash
# Install Ollama (macOS/Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull default model (~9.6 GB)
ollama pull gemma4

# Run with Gemma
python agent_runtime.py --provider gemma "Your goal here"

# Interactive mode
python agent_runtime.py --provider gemma interactive

# Test connectivity
python agent_runtime.py --provider gemma test
```

**Model variants** (set via `GEMMA_MODEL` env var):

| Tag | Params | VRAM | Context |
|-----|--------|------|---------|
| `gemma4` | 12B (Q4) | ~9.6 GB | 128K |
| `gemma4:e2b` | 12B (Q2) | ~7.2 GB | 128K |
| `gemma4:26b` | 27B (Q4) | ~18 GB | 256K |
| `gemma4:31b` | 27B (Q8) | ~20 GB | 256K |

**Remote tunnel (Colab + Cloudflare):**

```bash
# On your local machine, point to the Cloudflare tunnel URL:
OLLAMA_BASE_URL=https://xxx.trycloudflare.com/v1 python agent_runtime.py --provider gemma "Say hello"

# Override model variant:
GEMMA_MODEL=gemma4:e2b python agent_runtime.py --provider gemma interactive
```

See `notebooks/skillos_gemma4_colab.ipynb` for a self-contained Colab notebook that sets up Ollama + Gemma 4 + Cloudflare tunnel on a free T4 GPU, and [docs/tutorial-gemma4-colab.md](tutorial-gemma4-colab.md) for the full walkthrough.

### Gemma 4 via OpenRouter

Run Gemma 4 (26B) through OpenRouter's API — no local GPU required:

```bash
# Uses your existing OpenRouter API key
python agent_runtime.py --provider gemma-openrouter "Your goal here"

# Run multi-agent scenarios (auto-selects cognitive pipeline)
python run_scenario.py scenarios/Operation_Echo_Q.md "quantum cepstral analysis" \
    --provider gemma-openrouter --no-stream
```

The `gemma-openrouter` provider uses `google/gemma-4-26b-a4b-it` via OpenRouter. It shares the same `OPENROUTER_API_KEY` as the Qwen provider but uses the GEMINI manifest format.

**Cognitive Pipeline:** Mid-tier models like Gemma 4 automatically use the cognitive pipeline strategy, which forces step-by-step agent execution instead of letting the model self-orchestrate. This improves output from ~5K chars (collapsed single-turn) to ~28K chars (structured multi-step). See [docs/cognitive-pipeline.md](cognitive-pipeline.md) for details.

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

| Feature | Claude Code | Qwen/Gemini | Gemma (Ollama) | Gemma (OpenRouter) |
|---------|-------------|-------------|----------------|-------------------|
| Full tool access | Yes | Yes (Python) | Yes (Python) | Yes (Python) |
| Agent delegation | Yes (native) | Yes (with tool loop) | Yes (with tool loop) | Yes (with tool loop) |
| Cognitive pipeline | N/A (not needed) | Available | Available | Auto-selected |
| Multi-agent scenarios | Agentic (self-orchestrate) | Agentic | Cognitive pipeline | Cognitive pipeline |
| Robot integration | Yes | Yes | Yes | Yes |
| Dream consolidation | Yes | Yes (native tools) | Yes | Yes |
| Cost | Claude pricing | OpenRouter / Google AI | Free (local or Colab) | ~$0.05/scenario |
| Offline use | No | No | Yes (local Ollama) | No |
| Context window | Large | Provider-dependent | 128K–256K | 128K |
| LLM-powered compaction | N/A | Yes (compactor.py) | Yes (compactor.py) | Yes (compactor.py) |

---

## Environment Variables

```env
# Claude Code
# (uses Claude Code's own auth — no additional vars needed)

# Qwen via OpenRouter
OPENROUTER_API_KEY=sk-or-...

# Gemini
GEMINI_API_KEY=AI...

# Gemma 4 via Ollama
OLLAMA_BASE_URL=https://xxx.trycloudflare.com/v1 # omit for local Ollama (defaults to localhost:11434)
OLLAMA_API_KEY=ollama                            # Ollama ignores auth; placeholder for OpenAI client
GEMMA_MODEL=gemma4                               # override: gemma4:e2b, gemma4:26b, gemma4:31b

# Gemma 4 via OpenRouter (uses same key as Qwen)
OPENROUTER_API_KEY=sk-or-...                     # same key works for both Qwen and Gemma-OpenRouter
```
