---
skill_id: memory/consolidation/memory-consolidation-agent
name: memory-consolidation-agent
type: agent
domain: memory
family: consolidation
extends: memory/base
version: 1.0.0
description: Consolidates short-term agent interactions into long-term insights and SmartMemory entries
capabilities: [log-consolidation, insight-extraction, pattern-cataloging, smartmemory-update]
tools_required: [Read, Write, Grep, Glob]
subagent_type: memory-consolidation-agent
token_cost: medium
reliability: 85%
invoke_when: [end of project execution, session close, learning capture, memory maintenance]
full_spec: system/skills/memory/consolidation/memory-consolidation-agent.md
---
