---
skill_id: dialects/compiler/dialect-compiler-agent
name: dialect-compiler-agent
type: agent
domain: dialects
family: compiler
extends: dialects/base
version: 1.0.0
description: Compresses content using a domain-specific dialect — resolves dialect, applies compression rules, validates preservation constraints
capabilities: [dialect-compression, auto-dialect-selection, preservation-validation, multi-dialect-support]
tools_required: [Read, Grep]
subagent_type: dialect-compiler-agent
token_cost: medium
reliability: 90%
invoke_when: [compress content for storage, reduce token cost, prepare memory entries, compress strategy, compress trace]
full_spec: system/skills/dialects/compiler/dialect-compiler-agent.md
---
