---
skill_id: analytics/tabular/data-analysis-agent
name: data-analysis-agent
type: agent
domain: analytics
family: tabular
extends: analytics/base
version: 1.0.0
source: original
description: Analyse CSV/JSON/tabular data using Python (pandas/numpy) and produce charts + markdown reports
capabilities: [data-load, schema-inference, statistical-analysis, charting, report-generation, python-analysis]
tools_required: [Read, Write, Bash, Glob, Grep]
subagent_type: data-analysis-agent
token_cost: medium
reliability: 88%
invoke_when: [analyse data, CSV analysis, data statistics, chart generation, data exploration, tabular data]
full_spec: system/skills/analytics/tabular/data-analysis-agent.md
---
