---
skill_id: genealogy/spawn/spawn-child-agent
name: spawn-child-agent
type: agent
domain: genealogy
family: spawn
extends: genealogy/base
version: 1.0.0
description: Copies parent DNA into a new Child agent, registers lineage, and hands control to tutor
capabilities: [agent-cloning, lineage-registration, dna-hashing, manifest-generation]
tools_required: [Read, Write, Bash, Task]
subagent_type: spawn-child-agent
token_cost: low
reliability: 95%
invoke_when: [boot with kernel_mode:genealogy, after promote-child-agent, new generation required]
full_spec: system/skills/genealogy/spawn/spawn-child-agent.md
---
