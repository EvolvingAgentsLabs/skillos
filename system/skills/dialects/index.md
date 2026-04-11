---
domain: dialects
skill_count: 3
base: system/skills/dialects/base.md
---

# Dialects Domain Index

Skills for domain-specific token compression, expansion, and dialect discovery.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| dialect-compiler-agent | compiler | dialect-compiler-agent | compress content for storage, reduce token cost, prepare memory entries | dialects/compiler/dialect-compiler-agent.manifest.md |
| dialect-expander-agent | expander | dialect-expander-agent | expand compressed content, restore readable prose, decode bytecode | dialects/expander/dialect-expander-agent.manifest.md |
| dialect-registry-tool | registry | _(tool, no subagent)_ | list dialects, match dialect to task, describe dialect metadata | dialects/registry/dialect-registry-tool.manifest.md |

## Routing Notes
- For **compressing content before storage** → `dialect-compiler-agent` (handles dialect selection, rule application, validation).
- For **expanding compressed content** → `dialect-expander-agent` (handles irreversible dialects gracefully, reports information loss).
- For **quick dialect lookup** without full compilation → `dialect-registry-tool` (reads `_index.md`, low cost).
