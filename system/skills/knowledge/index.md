---
domain: knowledge
skill_count: 5
base: system/skills/knowledge/base.md
bridge: system/skills/knowledge/bridge.md
inspiration: Andrej Karpathy — LLM Wiki / Knowledge Base pattern
---

# Knowledge Domain Index

Skills implementing Karpathy's **LLM-compiled wiki** pattern: raw sources → compiled wiki → queries.
The wiki is a **compounding artifact** — every operation makes it richer.

See `system/skills/knowledge/bridge.md` for the formal protocol connecting skills to the wiki
knowledge graph and to other SkillOS domains.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| knowledge-ingest-agent | ingest | knowledge-ingest-agent | new source in raw/, add article, update wiki from source | knowledge/ingest/knowledge-ingest-agent.manifest.md |
| knowledge-compile-agent | compile | knowledge-compile-agent | initialize KB, schema changed, full rebuild | knowledge/compile/knowledge-compile-agent.manifest.md |
| knowledge-query-agent | query | knowledge-query-agent | question about KB, research query, find connections | knowledge/query/knowledge-query-agent.manifest.md |
| knowledge-lint-agent | lint | knowledge-lint-agent | wiki health check, find contradictions, orphan pages | knowledge/lint/knowledge-lint-agent.manifest.md |
| knowledge-search-tool | search | _(tool, no subagent)_ | search wiki, find pages about topic, locate concept | knowledge/search/knowledge-search-tool.manifest.md |

## Operation Flow

```
Initialize  → knowledge-compile-agent   (empty wiki → full wiki from raw/)
Add source  → knowledge-ingest-agent    (incremental wiki update)
Ask question→ knowledge-query-agent     (wiki Q&A + file answer back)
Maintain    → knowledge-lint-agent      (health check, repair gaps)
Find pages  → knowledge-search-tool     (keyword + graph search, called by query agent)
```

## Routing Notes

- **Starting a new KB**: use `knowledge-compile-agent` with the schema template at
  `templates/wiki/_schema.template.md`.
- **Most common operation** (adding sources): `knowledge-ingest-agent`.
- **Most common operation** (asking questions): `knowledge-query-agent`.
- The `knowledge-search-tool` is not invoked directly — the query agent uses it internally.
- Run `knowledge-lint-agent` periodically (e.g., after every 10 ingest operations).
