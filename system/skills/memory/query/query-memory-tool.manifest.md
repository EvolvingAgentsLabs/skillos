---
skill_id: memory/query/query-memory-tool
name: query-memory-tool
type: tool
domain: memory
family: query
extends: memory/base
version: 1.0.0
description: Standardized bridge for memory-driven decision making — routes queries to memory-analysis-agent
capabilities: [memory-lookup, decision-support, experience-retrieval, cached-consultation]
tools_required: [Read, Grep, Bash, Task]
subagent_type: null
token_cost: low
reliability: 90%
invoke_when: [decision support needed, quick memory lookup, before planning, context enrichment]
full_spec: system/skills/memory/query/query-memory-tool.md
---
