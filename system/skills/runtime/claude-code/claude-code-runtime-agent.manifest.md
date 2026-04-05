---
skill_id: runtime/claude-code/claude-code-runtime-agent
name: claude-code-runtime-agent
type: agent
domain: runtime
family: claude-code
extends: runtime/base
version: 1.0.0
description: Default SkillOS runtime — Claude Code CLI executes all tool calls natively; no additional setup required
capabilities: [native-tool-execution, file-operations, bash, web-fetch, sub-agent-delegation, context-compaction]
tools_required: [Read, Write, Bash, Glob, Grep, Task, WebFetch]
subagent_type: claude-code-runtime-agent
token_cost: low
reliability: 99%
invoke_when: [default runtime, Claude Code CLI, Anthropic native, no runtime configured, check active runtime]
default: true
full_spec: system/skills/runtime/claude-code/claude-code-runtime-agent.md
---
