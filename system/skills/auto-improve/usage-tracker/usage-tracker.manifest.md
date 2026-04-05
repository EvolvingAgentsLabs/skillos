---
skill_id: auto-improve/usage-tracker/usage-tracker
name: usage-tracker
type: tool
domain: auto-improve
family: usage-tracker
extends: auto-improve/base
version: 1.0.0
description: Records skill invocation timestamps and detects stale skills that are candidates for background improvement
capabilities: [record-usage, detect-staleness, list-stale-skills]
tools_required: [Read, Write]
subagent_type: "(tool — invoke inline, not via Task)"
token_cost: negligible
reliability: 99%
invoke_when: [after every skill delegation in system-agent, before auto-improve trigger check]
stale_after_hours: N/A
full_spec: system/skills/auto-improve/usage-tracker/usage-tracker.md
---
