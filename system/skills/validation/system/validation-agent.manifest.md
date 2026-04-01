---
skill_id: validation/system/validation-agent
name: validation-agent
type: agent
domain: validation
family: system
extends: validation/base
version: 1.0.0
description: System health checks — validates agent specs, SmartLibrary consistency, memory log integrity
capabilities: [spec-validation, library-consistency-check, memory-log-validation, health-reporting]
tools_required: [Read, Write, Grep, Glob]
subagent_type: validation-agent
token_cost: low
reliability: 92%
invoke_when: [system health check, after boot, preflight validation, spec integrity check]
full_spec: system/skills/validation/system/validation-agent.md
---
