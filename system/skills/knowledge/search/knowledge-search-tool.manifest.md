---
skill_id: knowledge/search/knowledge-search-tool
name: knowledge-search-tool
type: tool
domain: knowledge
family: search
extends: knowledge/base
version: 1.0.0
description: Lightweight keyword + structural search over wiki .md files — returns ranked results with context for LLM consumption. Hybrid BM25-style term frequency + WikiLink graph traversal.
capabilities: [keyword-search, structural-search, ranked-results, context-extraction, backlink-traversal]
tools_required: [Grep, Read, Glob, Bash]
subagent_type: null
token_cost: low
reliability: 93%
invoke_when: [search wiki, find pages about topic, locate concept, which pages mention, search knowledge base]
full_spec: system/skills/knowledge/search/knowledge-search-tool.md
---
