---
skill_id: forge/evolve/forge-evolve-agent
name: forge-evolve-agent
type: agent
domain: forge
family: evolve
extends: forge/base
version: 1.0.0
description: Proposes improvements to an existing skill or cartridge based on SmartMemory degradation signals, user feedback, or a new Gemma model tag. Produces a candidate diff validated A/B against the current version.
capabilities: [skill-diffing, cartridge-improvement, regression-analysis, ab-candidate-generation]
tools_required: [Read, Write, Grep, Glob, Task]
subagent_type: forge-evolve-agent
backend: claude-code
target_model: gemma4:e2b
token_cost: high
reliability: n/a
invoke_when: [pass-rate degraded, user feedback negative, model upgrade, optimization request]
full_spec: system/skills/forge/evolve/forge-evolve-agent.md
---
