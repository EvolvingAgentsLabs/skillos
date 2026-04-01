---
skill_id: robot/dream/roclaw-dream-agent
name: roclaw-dream-agent
type: agent
domain: robot
family: dream
extends: robot/base
version: 1.0.0
description: Bio-inspired dream consolidation — triggers SWS/REM/Consolidation phases, evolves navigation strategies
capabilities: [dream-consolidation, negative-constraint-creation, strategy-evolution, sws-rem-cycles]
tools_required: [Read, Write, Bash, Grep, Task]
subagent_type: roclaw-dream-agent
token_cost: medium
reliability: 85%
invoke_when: [nightly learning, post-session consolidation, strategy refinement, dream cycle trigger]
full_spec: system/skills/robot/dream/roclaw-dream-agent.md
---
