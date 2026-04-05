---
skill_id: knowledge/query/knowledge-query-agent
name: knowledge-query-agent
type: agent
domain: knowledge
family: query
extends: knowledge/base
version: 1.0.0
description: Q&A against the wiki — reads _index.md, navigates to relevant pages, synthesizes cited answers, and files high-value outputs back into wiki/queries/ to compound the knowledge base.
capabilities: [wiki-navigation, cited-qa, answer-synthesis, query-filing, index-driven-lookup]
tools_required: [Read, Grep, Write, Glob]
subagent_type: knowledge-query-agent
token_cost: medium
reliability: 92%
invoke_when: [question about knowledge base, research query, what does the wiki say about, summarize topic, find connections between]
full_spec: system/skills/knowledge/query/knowledge-query-agent.md
---
