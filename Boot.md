---
name: boot
type: skill
priority: 0
description: SkillOS boot manifest — every agent and runtime MUST read this first before any execution
runtimes:
  - claude-code
  - qwen
  - codex
  - any-llm-runtime
---

# SkillOS Boot

> **This is the first skill loaded by every SkillOS-compatible runtime.**
> Read this file before executing any goal, loading any agent, or interpreting any command.

## Banner

```
   _____ __   _ ____             ____  _____
  / ___// /__(_) / /            / __ \/ ___/
  \__ \/ //_/ / / /   ______   / / / /\__ \
 ___/ / ,< / / / /   /_____/  / /_/ /___/ /
/____/_/|_/_/_/_/              \____//____/

  Pure Markdown Operating System v1.0
  Powered by Claude Code Runtime
```

## Boot Checklist

Every runtime MUST complete these steps before processing any user command:

1. **Read this file** (`Boot.md`) — you are here
2. **Verify working directory** — confirm you are running from the SkillOS root
3. **Load SmartLibrary** — read `system/SmartLibrary.md` for component registry
4. **Check agent discovery** — scan `.claude/agents/` for available agents
5. **Initialize project structure** — ensure `projects/` directory exists
6. **System ready** — report status and await first goal

## Boot Protocol by Runtime

### Claude Code (`skillos.py` terminal)
- Read `Boot.md` and render banner to terminal
- Display system status (working dir, session PID, agent count, project count)
- Start scheduler background thread
- Invoke `boot skillos` to initialize session context

### QWEN Runtime (`qwen_runtime.py`)
- Read `Boot.md` as first context injection before any system prompt
- Parse boot checklist and execute each step as a `read_file` tool call
- Set `session_booted = true` in runtime state after checklist completes

### Claude Code Agents (`.claude/agents/`)
- On first invocation in a session, read `Boot.md` to orient system context
- Use boot checklist to verify environment before delegating to sub-agents

### Any LLM Runtime / Codex / External Agent
- Treat `Boot.md` as the system manifest
- Banner section: display to user if interactive
- Boot Checklist: execute sequentially before first goal
- All agents and tools are defined as markdown files — read, interpret, execute

## Runtime Capabilities

| Capability | Claude Code | Qwen Runtime | Required |
|------------|-------------|-------------|----------|
| File I/O (Read/Write) | Native tools | read_file/write_file | Yes |
| Shell (Bash/curl) | Native Bash | execute_bash | Yes |
| Agent delegation | Task tool | delegate_to_agent | Yes |
| evolving-memory | EvolvingMemoryTool.md (curl) | query_memory_graph, log_trace, trigger_dream | Recommended |
| RoClaw robot | RoClawTool.md (curl) | execute_bash (curl) + robot_telemetry | For robotics |
| Web search | WebSearch/WebFetch | web_fetch | Optional |

All runtimes access RoClaw hardware through the same HTTP bridge at `:8430`.
All runtimes access evolving-memory through the same REST API at `:8420`.

## System Invariants

These rules apply to ALL runtimes at ALL times:

- **Everything is markdown** — agents, tools, skills are `.md` files
- **No hardcoded logic** — behavior emerges from LLM interpreting markdown specs
- **Projects are isolated** — each goal creates/uses `projects/[ProjectName]/`
- **Memory is sacred** — always log agent interactions; never skip memory writes
- **Agents compose** — complex tasks = multiple focused agents, not one monolith

## Quick Reference

| Command | Description |
|---------|-------------|
| `boot skillos` | Initialize SkillOS session |
| `skillos execute: "<goal>"` | Execute a goal |
| `skillos simulate: "<goal>"` | Generate training data |
| `schedule every <interval> <goal>` | Recurring scheduled task |
| `jobs` | Show scheduled task queue |
| `agents` | List discovered agents |
| `help` | Full command reference |

## File Locations

| Resource | Path |
|----------|------|
| This file | `Boot.md` |
| Agent registry | `system/SmartLibrary.md` |
| Memory store | `system/SmartMemory.md` |
| System agents | `system/agents/` |
| System tools | `system/tools/` |
| Projects | `projects/` |
| Agent discovery | `.claude/agents/` |
