---
skill_id: research/web/web-research-agent
name: web-research-agent
type: agent
domain: research
family: web
extends: research/base
version: 1.0.0
source: original
description: Multi-step intelligent web research pipeline — decomposes questions, fetches sources, synthesizes cited reports
capabilities: [web-search, source-scoring, claim-extraction, research-synthesis, report-generation]
tools_required: [WebSearch, WebFetch, Write, Read, Glob]
subagent_type: web-research-agent
token_cost: medium
reliability: 85%
invoke_when: [research topic, web research, find information, investigate, look up, current events, fact check]
full_spec: system/skills/research/web/web-research-agent.md
---
