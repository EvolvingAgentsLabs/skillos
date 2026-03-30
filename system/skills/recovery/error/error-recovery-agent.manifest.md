---
skill_id: recovery/error/error-recovery-agent
name: error-recovery-agent
type: agent
domain: recovery
family: error
extends: recovery/base
version: 1.0.0
description: Classifies errors, applies retry strategies with exponential backoff, implements circuit breaker
capabilities: [error-classification, exponential-backoff, circuit-breaker, alternative-approach, scope-reduction]
tools_required: [Read, Write, Grep, Bash]
subagent_type: error-recovery-agent
token_cost: low
reliability: 90%
invoke_when: [any tool failure, step error, retry needed, circuit breaker check]
full_spec: system/skills/recovery/error/error-recovery-agent.md
---
