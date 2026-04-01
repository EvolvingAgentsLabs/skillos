---
skill_id: memory/trace/memory-trace-manager
name: memory-trace-manager
type: tool
domain: memory
family: trace
extends: memory/base
version: 1.0.0
description: Captures and structures execution traces for training data generation and audit trails
capabilities: [trace-capture, structured-logging, training-data-export, audit-trail]
tools_required: [Read, Write, Grep, Bash]
subagent_type: null
token_cost: low
reliability: 92%
invoke_when: [logging agent interactions, generating training data, capturing execution traces]
full_spec: system/skills/memory/trace/memory-trace-manager.md
---
