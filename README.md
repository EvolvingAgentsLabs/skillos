# SkillOS — Pure Markdown Operating System [POC]

> Transform any LLM + Agents into an intelligent operating system using pure markdown.

SkillOS is a proof-of-concept OS where every component — agents, tools, memory, orchestration — is defined entirely in markdown documents. No code compilation. No complex APIs. Just markdown that any LLM interprets at runtime to become a powerful, composable problem-solving system.

> Evolved from [LLMos](https://github.com/EvolvingAgentsLabs/llmos) — Skills as the basic unit of programing.

---

## Core Concept

Everything is either an **Agent** (decision maker) or a **Tool** (executor), defined in markdown:

```markdown
---
name: research-agent
type: agent
description: Researches topics and synthesizes findings
tools: [Read, WebFetch, Write]
---

# ResearchAgent
You are a research specialist. Given a topic, you...
```

The LLM reads this markdown at runtime and *becomes* that agent — no compilation, no deployment, no code changes. Add new capabilities by writing new markdown files.

---

## Quick Start

**Prerequisites:** Python 3.11+, Git, [Claude Code CLI](https://claude.ai/code)

```bash
# 1. Clone
git clone https://github.com/EvolvingAgentsLabs/skillos.git
cd skillos

# 2. Initialize agent discovery
./setup_agents.sh        # Mac/Linux
.\setup_agents.ps1       # Windows

# 3. Boot and run
claude --dangerously-skip-permissions "boot skillos"
claude --dangerously-skip-permissions "skillos execute: 'Research the latest AI safety papers and write a summary'"
```

Or use the interactive terminal:

```bash
./skillos.sh
```

```
skillos$ Create a tutorial on chaos theory with Python examples
skillos$ Monitor 5 tech news sources and generate a weekly briefing
skillos$ help
```

---

## Choose Your Runtime

| Runtime | Best For | Command |
|---------|----------|---------|
| **SkillOS Terminal** | Interactive use, full experience | `./skillos.sh` |
| **Claude Code** | Scripting, CI/CD, full tool access | `claude --dangerously-skip-permissions "..."` |
| **Qwen / Gemini** | Lightweight, multi-provider, free tier | `python qwen_runtime.py "..."` |

See [docs/runtimes.md](docs/runtimes.md) for full runtime documentation.

---

## What Can You Build?

```bash
# Research & Analysis
skillos execute: "Research quantum computing applications in medicine and write a report"
skillos execute: "Analyze this codebase and identify architectural improvements"

# Development
skillos execute: "Create a REST API with FastAPI and write the tests"
skillos execute: "Build a data pipeline for processing CSV files"

# Content
skillos execute: "Write a technical tutorial on Rust ownership with examples"
skillos execute: "Generate API documentation from the source code"

# Complex Projects
skillos execute: "Design and build a complete invoice processing system"
skillos execute: "Run autoresearch on input/train.py for 50 cycles — commit every improvement"
```

---

## Architecture Overview

```
skillos/
├── system/
│   └── skills/                  # Hierarchical Skill Tree (3-level taxonomy)
│       ├── SkillIndex.md        # Top-level routing (~50 lines)
│       ├── orchestration/       # SystemAgent, tool maps
│       ├── memory/              # Learning, consolidation, traces
│       ├── validation/          # Health checks, security scanning
│       ├── recovery/            # Error handling, circuit breaker
│       ├── project/             # Scaffolding, package manager
│       └── robot/               # Physical Agents (robots/environmentalbots) control (RoClaw)
├── projects/                    # Your projects (auto-created per goal)
│   └── [ProjectName]/
│       ├── components/          # Project-specific agents & tools
│       ├── output/              # Generated deliverables
│       └── memory/              # Project learning logs
├── scenarios/                   # Pre-built task scenarios
├── qwen_runtime.py              # Multi-provider agent runtime
├── roclaw_bridge.py             # Physical Agents (robots/environmentalbots) HTTP bridge
└── CLAUDE.md                    # OS configuration
```

Skills are organized as `Domain → Family → Skill` with lazy loading (~61% token reduction). See [docs/architecture.md](docs/architecture.md).

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/architecture.md](docs/architecture.md) | Skill tree, domains, lazy loading, agent discovery |
| [docs/runtimes.md](docs/runtimes.md) | Claude Code, Qwen, Gemini runtime details |
| [docs/skills.md](docs/skills.md) | How to create agents and tools |
| [docs/memory.md](docs/memory.md) | Memory system, learning, consolidation |
| [docs/security.md](docs/security.md) | Skill security scanning, antivirus gate |
| [docs/robot.md](docs/robot.md) |  Physical Agents (robots/environmentalbots) integration (RoClaw / Cognitive Trinity) |
| [docs/scenarios.md](docs/scenarios.md) | Pre-built scenarios and examples |

---

## Key Features

- **Pure Markdown**: System behavior emerges from LLM interpreting markdown — no code compilation
- **Hierarchical Skill Tree**: Domain → Family → Skill taxonomy with lazy loading for efficiency
- **Skill Package Manager**: apt-like install/update/search for skills from GitHub or local sources
- **Security Scanning**: Antivirus gate scans every skill before install (prompt injection, spoofing, exfiltration)
- **Memory-Driven Learning**: Executions are logged; past experiences inform future decisions
- **Dynamic Agent Creation**: New agents are generated as markdown at runtime when capability gaps are detected
- **Multi-Provider**: Runs on Claude Code, Qwen (OpenRouter), or Gemini
- **Physical Robot Support**: Full cognitive architecture for autonomous robotics via RoClaw

---

## Related Projects

| Project | Role |
|---------|------|
| [LLMos](https://github.com/EvolvingAgentsLabs/llmos) | Predecessor — foundation concepts |
| [RoClaw](https://github.com/EvolvingAgentsLabs/RoClaw) | Physical robot — Cerebellum |
| [evolving-memory](https://github.com/EvolvingAgentsLabs/evolving-memory) | Dream consolidation — Hippocampus |

---

## License

Apache License 2.0 — see [LICENSE](LICENSE)

---

*Built by [Evolving Agents Labs](https://evolvingagentslabs.github.io)*
