---
skill_id: memory/analysis/memory-analysis-agent
name: memory-analysis-agent
type: agent
domain: memory
family: analysis
extends: memory/base
version: 1.0.0
description: Cross-project pattern recognition and historical learning insights from SmartMemory
capabilities: [pattern-recognition, historical-analysis, performance-prediction, experience-querying]
tools_required: [Read, Grep, Bash]
subagent_type: memory-analysis-agent
token_cost: low
reliability: 90%
invoke_when: [historical context needed, pattern analysis, learning from past executions, memory query]
full_spec: system/skills/memory/analysis/memory-analysis-agent.md
---
