---
skill_id: orchestration/egress/human-renderer-agent
name: human-renderer-agent
type: agent
domain: orchestration
family: egress
extends: orchestration/base
version: 1.0.0
description: Expands internal dialect output into human-readable prose at the egress boundary of the Language Facade
capabilities: [dialect-expansion, register-selection, prose-rendering, output-formatting]
tools_required: [Read, Task]
subagent_type: human-renderer-agent
token_cost: medium
reliability: 90%
invoke_when: [render output for user, expand dialect to prose, final response formatting]
full_spec: system/skills/orchestration/egress/human-renderer-agent.md
---
