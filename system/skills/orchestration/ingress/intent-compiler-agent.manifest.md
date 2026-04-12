---
skill_id: orchestration/ingress/intent-compiler-agent
name: intent-compiler-agent
type: agent
domain: orchestration
family: ingress
extends: orchestration/base
version: 1.0.0
description: Compiles human natural language input into the most appropriate internal dialect before passing to downstream agents
capabilities: [intent-classification, dialect-selection, input-compilation, domain-routing]
tools_required: [Read, Task]
subagent_type: intent-compiler-agent
token_cost: medium
reliability: 90%
invoke_when: [incoming user goal, natural language input, parse intent]
full_spec: system/skills/orchestration/ingress/intent-compiler-agent.md
---
