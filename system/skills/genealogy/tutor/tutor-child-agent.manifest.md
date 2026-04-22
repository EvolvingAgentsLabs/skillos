---
skill_id: genealogy/tutor/tutor-child-agent
name: tutor-child-agent
type: agent
domain: genealogy
family: tutor
extends: genealogy/base
version: 1.0.0
description: Reviews a Child's DNA mutation proposal and either merges it into the Child's spec or rejects with feedback. Runs per child task or on proposal file.
capabilities: [dna-review, mutation-merging, feedback-generation, tutoring-session-logging]
tools_required: [Read, Write, Edit, Grep, Task]
subagent_type: tutor-child-agent
token_cost: medium
reliability: 88%
invoke_when: [mutation-proposal file present, child completed a task, tutor cycle requested]
full_spec: system/skills/genealogy/tutor/tutor-child-agent.md
---
