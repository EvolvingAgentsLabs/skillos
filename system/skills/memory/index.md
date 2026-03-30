---
domain: memory
skill_count: 4
base: system/skills/memory/base.md
---

# Memory Domain Index

Skills for learning, history consultation, execution tracing, and memory consolidation.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| memory-analysis-agent | analysis | memory-analysis-agent | historical context, pattern queries, past execution insights | memory/analysis/memory-analysis-agent.manifest.md |
| memory-consolidation-agent | consolidation | memory-consolidation-agent | end of session, learning capture, memory maintenance | memory/consolidation/memory-consolidation-agent.manifest.md |
| query-memory-tool | query | _(tool, no subagent)_ | quick memory lookup, decision support, before planning | memory/query/query-memory-tool.manifest.md |
| memory-trace-manager | trace | _(tool, no subagent)_ | logging execution traces, generating training data | memory/trace/memory-trace-manager.manifest.md |

## Routing Notes
- For **quick lookups** during planning → `query-memory-tool` (low cost, cached).
- For **deep pattern analysis** across projects → `memory-analysis-agent`.
- For **end-of-session learning** → `memory-consolidation-agent`.
- For **trace capture** during execution → `memory-trace-manager`.
