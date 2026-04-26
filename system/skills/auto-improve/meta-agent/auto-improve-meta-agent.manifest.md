---
skill_id: auto-improve/meta-agent/auto-improve-meta-agent
name: auto-improve-meta-agent
type: agent
domain: auto-improve
family: meta-agent
extends: auto-improve/base
version: 1.0.0
description: Background meta-agent that reads failure traces and proposes targeted improvements to stale or underperforming SkillOS skill specifications
capabilities: [trace-analysis, spec-improvement, anti-overfitting-check, proposal-generation]
tools_required: [Read, Write, Grep, Glob]
subagent_type: auto-improve-meta-agent
token_cost: medium
reliability: 85%
stale_after_hours: N/A
invoke_when: [stale skill detected by usage-tracker, manual improvement request, failure spike on a skill]
full_spec: system/skills/auto-improve/meta-agent/auto-improve-meta-agent.md
---
