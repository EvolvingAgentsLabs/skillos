---
skill_id: genealogy/promote/promote-child-agent
name: promote-child-agent
type: agent
domain: genealogy
family: promote
extends: genealogy/base
version: 1.0.0
description: Executes the promotion ceremony. Archives retiring Father's DNA, flips statuses in lineage.json, records a promotion_event in SmartMemory, and authorizes the new Father to spawn.
capabilities: [dna-archival, lineage-status-transition, promotion-event-logging, spawn-authorization]
tools_required: [Read, Write, Bash, Task]
subagent_type: promote-child-agent
token_cost: low
reliability: 97%
invoke_when: [validate-child-agent verdict:pass, eligibility criteria all met]
full_spec: system/skills/genealogy/promote/promote-child-agent.md
---
