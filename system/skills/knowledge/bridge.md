---
skill_domain: knowledge
type: bridge-spec
version: 1.0.0
description: Formal protocol connecting the knowledge wiki graph to SkillOS skills, memory, and agents
---

# Knowledge Bridge — Skills ↔ Wiki Integration Protocol

This document defines how SkillOS's two orthogonal systems **connect without conflating**:

```
SKILLS LAYER (vertical — the "how")     KNOWLEDGE LAYER (horizontal — the "what")
────────────────────────────────────    ────────────────────────────────────────
Domain → Family → Skill                 raw/ → wiki/ → queries/

  Skills compute, route, execute           Wiki stores, links, accumulates
  SmartMemory tracks HOW                   wiki/ records WHAT
  Ephemeral per execution                  Persistent, compounding
```

---

## The Two Systems

### System 1: Skill Tree (`system/skills/`)
- **Purpose**: Orchestration, computation, tool execution
- **Storage**: Markdown skill specs + manifests
- **Memory**: `system/SmartMemory.md` (execution outcomes, procedural memory)
- **Operated by**: SystemAgent + specialized agents
- **Grows via**: Dynamic agent creation during execution

### System 2: Knowledge Wiki (`projects/[KB]/wiki/`)
- **Purpose**: Declarative domain knowledge, compiled from sources
- **Storage**: Markdown concept/entity/summary pages + `_index.md` + `_log.md`
- **Memory**: `wiki/_log.md` (what was ingested/queried, declarative memory)
- **Operated by**: `knowledge/` domain skills exclusively
- **Grows via**: Ingest + query compounding loop

---

## Cross-Linking Protocol

### Wiki → Skills (concept pages reference agents)

Every wiki concept page MAY include a `skills:` field in its YAML frontmatter:

```yaml
---
concept: transformer-architecture
type: concept
skills: [knowledge-query-agent, knowledge-ingest-agent]
related_scenarios: [scenarios/KnowledgeBase_Research_Task.md]
skill_expertise: >
  knowledge-query-agent can synthesize multi-hop questions about this concept.
  knowledge-ingest-agent should be used when adding new transformer papers.
---
```

This tells readers (human or LLM) which SkillOS agents are best for operating on
this concept.

### Skills → Wiki (skill manifests reference knowledge domains)

Skill manifests MAY include a `knowledge_domains:` field:

```yaml
knowledge_domains: [ml-theory, attention-mechanisms]
# Indicates this skill has been exercised on these knowledge domains
# and the wiki pages it produced are listed in SmartMemory
```

### Execution → Wiki (compounding loop)

After any execution that produces knowledge outputs, SystemAgent SHOULD:
1. File outputs to `wiki/queries/[output-slug].md` via `knowledge-query-agent`.
2. Add a SmartMemory entry referencing the wiki page produced:

```yaml
wiki_pages_produced:
  - wiki/queries/transformer-study-2026-04-05.md
  - wiki/concepts/attention-mechanism.md  # if updated
```

### Wiki → SmartMemory (declarative → procedural link)

When `knowledge-query-agent` files a query output, it also appends to SmartMemory:

```yaml
---
experience_id: exp_KB_001
timestamp: ISO-8601
project: MyKnowledgeBase
goal: "What are the key differences between MHA and MLA attention?"
outcome: success
components_used: [knowledge-query-agent, knowledge-search-tool]
wiki_page: wiki/queries/mha-vs-mla-attention.md
quality_score: 9
---
```

---

## Key Distinction: SmartMemory vs. wiki/_log.md

| | `system/SmartMemory.md` | `wiki/_log.md` |
|---|---|---|
| **Stores** | Execution outcomes (procedural) | Wiki operations (declarative) |
| **Format** | YAML + outcome narrative | Timestamp table |
| **Queried by** | memory-analysis-agent | knowledge-query-agent |
| **Updated by** | memory-consolidation-agent | ingest/compile/query/lint agents |
| **Answers** | "What worked in past executions?" | "What was added to the wiki and when?" |

---

## Access Control

Only skills in the `knowledge/` domain may write to `wiki/`.
All other domains (orchestration, memory, robot, validation, recovery, project) read wiki pages
but do not modify them — they invoke knowledge domain skills to do so.

```
orchestration/system-agent  →  reads wiki/_index.md for context
                             →  invokes knowledge-query-agent to get answers
                             →  NEVER writes to wiki/ directly

memory/memory-analysis-agent → reads wiki/queries/ for past Q&A context
                              → NEVER writes to wiki/

robot/roclaw-navigation-agent → may read wiki/concepts/ for domain context
                               → NEVER writes to wiki/
```

---

## Initializing a Knowledge-Enabled Project

When SystemAgent detects a goal that involves knowledge accumulation:

1. Check if `projects/[KB]/wiki/` exists.
2. If not, invoke `knowledge-compile-agent` with `wiki/_schema.md` template from:
   `templates/wiki/_schema.template.md`
3. Scaffold the full project structure (via `project-scaffold-tool`) with `raw/` + `wiki/`.
4. All subsequent execution outputs that are knowledge (not code/reports) go to `wiki/queries/`.

---

## Obsidian Compatibility

The wiki is designed to be viewable in Obsidian:
- WikiLinks use `[[Page Name]]` format (Obsidian-native).
- `_index.md` renders as a navigable table of contents.
- Images in `raw/images/` are referenced with relative paths.
- Marp-format slides in `output/` can be rendered via the Marp for Obsidian plugin.
- The `wiki/` directory can be opened directly as an Obsidian vault.
