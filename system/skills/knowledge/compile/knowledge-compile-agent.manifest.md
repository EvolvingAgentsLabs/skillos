---
skill_id: knowledge/compile/knowledge-compile-agent
name: knowledge-compile-agent
type: agent
domain: knowledge
family: compile
extends: knowledge/base
version: 1.0.0
description: Full wiki rebuild from raw/ — used when schema changes or wiki needs reconstruction. Processes all raw sources sequentially to produce a coherent, fully cross-referenced wiki.
capabilities: [full-rebuild, schema-driven-compilation, batch-processing, wiki-initialization]
tools_required: [Read, Write, Glob, Grep, Task]
subagent_type: knowledge-compile-agent
token_cost: high
reliability: 88%
invoke_when: [initialize new knowledge base, schema changed, wiki corrupted, full rebuild needed]
full_spec: system/skills/knowledge/compile/knowledge-compile-agent.md
---
