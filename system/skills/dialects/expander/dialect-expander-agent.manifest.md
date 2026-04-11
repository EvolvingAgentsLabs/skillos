---
skill_id: dialects/expander/dialect-expander-agent
name: dialect-expander-agent
type: agent
domain: dialects
family: expander
extends: dialects/base
version: 1.0.0
description: Expands compressed content back to readable prose — handles irreversible dialects gracefully, reports information loss
capabilities: [dialect-expansion, irreversible-handling, register-selection, information-loss-reporting]
tools_required: [Read, Grep]
subagent_type: dialect-expander-agent
token_cost: medium
reliability: 88%
invoke_when: [expand compressed content, restore readable prose, decode bytecode, interpret pointer notation]
full_spec: system/skills/dialects/expander/dialect-expander-agent.md
---
