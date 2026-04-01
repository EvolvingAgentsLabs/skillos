---
skill_id: orchestration/core/system-agent
name: system-agent
type: agent
domain: orchestration
family: core
extends: orchestration/base
version: 1.0.0
description: Core orchestrator — decomposes goals, selects skills, delegates tasks, assembles results
capabilities: [goal-decomposition, skill-routing, parallel-delegation, state-management, pipeline-orchestration]
tools_required: [Read, Write, Bash, Task, Glob, Grep]
subagent_type: system-agent
token_cost: high
reliability: 95%
invoke_when: [any new goal execution, workflow orchestration, multi-step task coordination]
full_spec: system/skills/orchestration/core/system-agent.md
---
