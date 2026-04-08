# SkillOS — Pure Markdown Operating System

SkillOS is a proof-of-concept OS where every component [agents, tools, memory, orchestration] is defined entirely in markdown documents. No code compilation. No complex APIs. Just markdown that any LLM interprets at runtime to become a composable problem-solving system.

> Evolved from [LLMos](https://github.com/EvolvingAgentsLabs/llmos) — testing Skills as basic programs.

![SkillOS running in Claude Code](docs/assets/skillos_claude_screen.png)

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/EvolvingAgentsLabs/skillos.git && cd skillos

# 2. Run Claude Code
claude --dangerously-skip-permissions

# 3. Boot SkillOS
boot skillos
```

### Full Setup (in case you want to explore alternative runtimes)

Initialize the agent discovery system before booting:

```bash
./setup_agents.sh    # Mac/Linux
.\setup_agents.ps1   # Windows
```

Requires: Python 3.11+, Git, Claude Code CLI.

---

## Runtimes

### Option 1: SkillOS Terminal (Recommended)
**Best for:** Interactive use, the full Unix-like experience

```bash
./skillos.sh
# Or directly:
python3 skillos.py
```

```
skillos$ Create a tutorial on chaos theory
skillos$ Monitor tech news and generate a briefing
skillos$ help
```

> Requires: Python 3.11+, `rich` (auto-installed on first run), Claude Code CLI

### Option 2: Claude Code (Direct)
**Best for:** Scripting, CI/CD, single-command execution

```bash
claude --dangerously-skip-permissions "boot skillos"
claude --dangerously-skip-permissions "skillos execute: 'Your goal here'"
```

### Option 3: Agent Runtime (Multi-Provider)
**Best for:** Lightweight use, free-tier access, local/offline use

```bash
pip install openai python-dotenv

OPENROUTER_API_KEY=... python agent_runtime.py "Your goal here"            # Qwen (default)
GEMINI_API_KEY=... python agent_runtime.py --provider gemini "Your goal"   # Gemini
python agent_runtime.py interactive                                          # Interactive mode
```

See [docs/runtimes.md](docs/runtimes.md) for full setup, environment variables, and a runtime comparison table.

---

## Core Concept

Everything is either an **Agent** (decision maker) or a **Tool** (executor), defined in markdown:

```markdown
---
name: example-agent
type: agent
description: An agent that solves problems
tools: Read, Write, WebFetch
extends: orchestration/base
---

# ExampleAgent
You are a research specialist. Given a topic, you...
```

Skills are organized in a **3-level hierarchy** (Domain → Family → Skill) with a 4-step lazy loading protocol that reduces routing-phase token consumption by ~61% versus a flat registry.

```
Domain → Family → Skill
──────────────────────────────────────────────────
orchestration/  core/           system-agent
memory/         analysis/       memory-analysis-agent
                consolidation/  memory-consolidation-agent
                query/          query-memory-tool
robot/          navigation/     roclaw-navigation-agent
                scene/          roclaw-scene-analysis-agent
                dream/          roclaw-dream-agent
validation/     system/         validation-agent
recovery/       error/          error-recovery-agent
project/        scaffold/       project-scaffold-tool
                packages/       skill-package-manager-tool
```

---

## Key Features

- **Pure Markdown** — No code compilation. The LLM is the interpreter.
- **Hierarchical Skills** — Domain → Family → Skill taxonomy with 4-step lazy loading
- **Token Efficient** — 61% reduction in routing-phase token consumption
- **Knowledge Wiki** — Compounding knowledge base inspired by Karpathy's LLM Wiki pattern
- **Memory System** — Every execution improves future runs via structured memory
- **Robot Integration** — SkillOS as Prefrontal Cortex for the RoClaw physical robot
- **Multi-Provider** — Works with Claude Code, Qwen, Gemini, or local Ollama
- **Dynamic Agents** — New agents created as markdown at runtime, no restarts needed

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/architecture.md](docs/architecture.md) | Skill tree, lazy loading, agent discovery, execution flow |
| [docs/skills.md](docs/skills.md) | Authoring agents and tools, manifests, inheritance, best practices |
| [docs/memory.md](docs/memory.md) | SmartMemory, short/long-term layers, memory-driven execution |
| [docs/runtimes.md](docs/runtimes.md) | Claude Code, Qwen/Gemini, Ollama — setup and comparison |
| [docs/scenarios.md](docs/scenarios.md) | All built-in scenarios and how to run them |
| [docs/robot.md](docs/robot.md) | RoClaw physical robot integration, Cognitive Trinity |
| [docs/security.md](docs/security.md) | Skill package security scanning and threat model |
| [docs/tutorial-echo-q.md](docs/tutorial-echo-q.md) | Step-by-step: Operation Echo-Q quantum computing scenario |

---

## Example Commands

```bash
# Research and content
skillos execute: "Research the latest AI developments and create a report"
skillos execute: "Write a technical blog post about quantum computing"

# Development
skillos execute: "Create a data pipeline for processing CSV files"
skillos execute: "Analyze this codebase and suggest improvements"

# Knowledge base (Karpathy LLM Wiki pattern)
skillos execute: "Initialize a knowledge base on transformer architectures"
skillos execute: "What are the key differences between MHA and MLA attention?"

# Physical robot
skillos execute: "Navigate to the kitchen and describe what you see"

# Built-in scenarios
skillos execute: "Run the Operation Echo-Q scenario"
skillos execute: "Run the RealWorld_Research_Task scenario in EXECUTION MODE"
```

---

## Related Projects

| Project | Role |
|---------|------|
| [LLMos](https://github.com/EvolvingAgentsLabs/llmos) | Predecessor — foundation concepts |
| [RoClaw](https://github.com/EvolvingAgentsLabs/RoClaw) | Physical robot — Cerebellum |

---

## License

Apache License 2.0 — see [LICENSE](LICENSE)

---

*Built by [Evolving Agents Labs Initiative](https://evolvingagentslabs.github.io)*
