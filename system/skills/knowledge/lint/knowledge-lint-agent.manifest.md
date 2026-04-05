---
skill_id: knowledge/lint/knowledge-lint-agent
name: knowledge-lint-agent
type: agent
domain: knowledge
family: lint
extends: knowledge/base
version: 1.0.0
description: Health check over the wiki — detects contradictions, stale claims, orphan pages, missing cross-references, data gaps, and suggests new article candidates. Incrementally cleans and enhances wiki integrity.
capabilities: [contradiction-detection, orphan-detection, stale-claim-detection, gap-analysis, cross-ref-repair, article-suggestion]
tools_required: [Read, Write, Grep, Glob]
subagent_type: knowledge-lint-agent
token_cost: medium
reliability: 88%
invoke_when: [wiki health check, find contradictions, find orphan pages, wiki quality check, lint knowledge base]
full_spec: system/skills/knowledge/lint/knowledge-lint-agent.md
---
