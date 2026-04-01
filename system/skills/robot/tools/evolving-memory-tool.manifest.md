---
skill_id: robot/tools/evolving-memory-tool
name: evolving-memory-tool
type: tool
domain: robot
family: tools
extends: robot/base
version: 1.0.0
description: REST bridge to evolving-memory API — ingest traces, query strategies, trigger dream consolidation
capabilities: [trace-ingestion, strategy-query, dream-trigger, memory-search, experience-store]
tools_required: [Bash, WebFetch, Read, Write]
subagent_type: null
token_cost: low
reliability: 87%
invoke_when: [store robot trace, query navigation strategy, trigger dream cycle, hippocampus access]
full_spec: system/skills/robot/tools/evolving-memory-tool.md
---
