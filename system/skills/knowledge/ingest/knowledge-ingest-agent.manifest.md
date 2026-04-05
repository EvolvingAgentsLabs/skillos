---
skill_id: knowledge/ingest/knowledge-ingest-agent
name: knowledge-ingest-agent
type: agent
domain: knowledge
family: ingest
extends: knowledge/base
version: 1.0.0
description: Reads new raw/ sources and incrementally updates up to 15 wiki pages — summaries, concepts, entities, cross-references, _index.md, and _log.md
capabilities: [source-reading, wiki-page-creation, incremental-update, cross-referencing, backlink-maintenance, log-appending]
tools_required: [Read, Write, Glob, Grep]
subagent_type: knowledge-ingest-agent
token_cost: medium
reliability: 90%
invoke_when: [new source added to raw/, ingest document, update wiki from source, add article to knowledge base]
full_spec: system/skills/knowledge/ingest/knowledge-ingest-agent.md
---
