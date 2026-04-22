---
skill_id: genealogy/validate/validate-child-agent
name: validate-child-agent
type: agent
domain: genealogy
family: validate
extends: genealogy/base
version: 1.0.0
description: Runs five validation strategies (replay, cross-domain, adversarial, memory-consistency, peer-comparison) to certify a Child for promotion. Adversarial probe is mandatory.
capabilities: [replay-testing, cross-domain-probing, adversarial-probing, memory-consistency-check, peer-comparison]
tools_required: [Read, Grep, Task]
subagent_type: validate-child-agent
token_cost: high
reliability: 92%
invoke_when: [child meets eligibility thresholds, pre-promotion audit, quality escalation]
full_spec: system/skills/genealogy/validate/validate-child-agent.md
---
