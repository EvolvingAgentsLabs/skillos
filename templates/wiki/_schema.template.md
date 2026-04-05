---
wiki_schema_version: 1.0.0
kb_name: "[REPLACE WITH YOUR KB NAME]"
created: "[ISO timestamp]"
domain: "[e.g., machine-learning, competitive-analysis, book-notes]"
---

# Wiki Schema — [KB Name]

> This is the **constitution** for your wiki. The LLM reads this file before every
> ingest, compile, query, or lint operation. Define your structure here and the LLM
> will maintain it consistently. You rarely need to edit wiki pages directly — the LLM does.

---

## Category Structure

Define the categories your wiki should maintain. Each becomes a subdirectory.

| Category | Directory | Purpose | Page Format |
|----------|-----------|---------|-------------|
| Concepts | `wiki/concepts/` | Core ideas, theories, methods | See Concept Template below |
| Entities | `wiki/entities/` | Named things: people, papers, orgs, datasets | See Entity Template below |
| Summaries | `wiki/summaries/` | Per-source document summaries | See Summary Template below |
| Queries | `wiki/queries/` | Filed Q&A outputs | See Query Template below |

**Add or remove categories below to match your domain:**

```
# Example for ML research:
wiki/concepts/   → transformer-architecture.md, attention-mechanism.md, scaling-laws.md
wiki/entities/   → Vaswani-et-al-2017.md, GPT-4.md, Anthropic.md
wiki/summaries/  → attention-is-all-you-need.md, gpt4-technical-report.md
wiki/queries/    → what-is-mla-attention.md, compare-moe-architectures.md
```

---

## Page Format Templates

### Concept Page (`wiki/concepts/[concept-slug].md`)

```markdown
---
concept: [concept name]
type: concept
domain: [your domain]
related: [[ConceptB]], [[ConceptC]]
sources: [[summaries/source-slug]]
skills: [knowledge-query-agent]
last_updated: [ISO timestamp]
---
# [Concept Name]

## Definition
[1-3 sentence precise definition]

## Key Properties
- [Property 1]
- [Property 2]

## How It Works
[Explanation with cross-references to related concepts]

## Related Concepts
- [[ConceptB]] — [one-line relationship]
- [[ConceptC]] — [one-line relationship]

## Sources
- [[summaries/source-slug]] — [key claim from this source]

## Open Questions
- [Question that the wiki doesn't yet answer]

## Contradictions
[Leave empty; lint agent fills this if contradictions are found]
```

### Entity Page (`wiki/entities/[entity-slug].md`)

```markdown
---
entity: [entity name]
type: [person | paper | organization | dataset | model]
domain: [your domain]
appears_in: [[summaries/source-slug]]
last_updated: [ISO timestamp]
---
# [Entity Name]

## Description
[2-4 sentence description]

## Key Contributions / Properties
- [Contribution 1]

## Appears In
- [[summaries/source-slug]] — [context of appearance]

## Related Entities
- [[EntityB]] — [relationship]
```

### Summary Page (`wiki/summaries/[source-slug].md`)

```markdown
---
source: raw/[path/to/source]
source_type: [article | paper | repo | dataset | book]
ingested: [ISO timestamp]
key_claims:
  - "[claim 1]"
  - "[claim 2]"
concepts: [[ConceptA]], [[ConceptB]]
entities: [[EntityX]]
---
# Summary: [Source Title]

## Overview
[2-3 sentence summary of the source]

## Key Claims
1. [Claim 1]
2. [Claim 2]

## Related Concepts
- [[ConceptA]] — [how source relates to this concept]

## Entities Mentioned
- [[EntityX]] — [context]

## Quotes Worth Preserving
> "[Direct quote if particularly important]"

## Limitations / Caveats
[What the source doesn't cover or gets wrong]
```

### Query Page (`wiki/queries/[query-slug].md`)

```markdown
---
query: "[exact question asked]"
timestamp: [ISO timestamp]
confidence: [HIGH | MEDIUM | LOW]
sources_used: [[concepts/...]], [[summaries/...]]
---
# [Query Title]

## Answer
[Synthesized answer]

## Key Points
- [Point] — Source: [[concepts/concept-a]]

## Connections Found
[Non-obvious connections the query surfaced]

## Gaps Identified
[Topics the query touched that the wiki doesn't cover yet]
```

---

## Cross-Reference Rules

1. Use `[[WikiLink]]` format for all internal links (Obsidian-compatible).
2. Every concept page MUST link to at least 2 related concepts.
3. Every summary page MUST backlink to the concepts it supports.
4. Every entity page MUST list all summaries that mention it.
5. When a new concept is created, grep other pages for mentions and add backlinks retroactively.

---

## `_index.md` Structure

The index is organized by category with one-line descriptions:

```markdown
# Wiki Index — [KB Name]
Last updated: [ISO timestamp] | Pages: N

## Concepts (N)
- [[concepts/concept-a]] — [one-line description]
- [[concepts/concept-b]] — [one-line description]

## Entities (N)
- [[entities/entity-x]] — [type: person/paper/org]

## Summaries (N)
- [[summaries/source-slug]] — [source title, ingested date]

## Queries (N)
- [[queries/query-slug]] — [question, date answered]
```

---

## `_log.md` Format

Append-only. Do not edit manually.

```markdown
# Wiki Operation Log — [KB Name]

| Timestamp | Operation | Target | Summary |
|-----------|-----------|--------|---------|
| [ISO] | COMPILE | ALL | Initial compile from N sources — M pages created |
| [ISO] | INGEST | summaries/source-slug | Added 3 pages, updated 2 pages |
| [ISO] | QUERY | queries/question-slug | Answered: [question summary] |
| [ISO] | LINT | ALL | N issues found, M auto-repaired |
| [ISO] | CONFLICT | concepts/concept-a | Conflict with summaries/source-b |
| [ISO] | STUB | concepts/missing-concept | Created stub, needs ingest |
```

---

## Domain-Specific Notes

> **[Fill in below for your specific knowledge domain]**

```
# Example for ML research:
# - Prefer exact paper titles as entity slugs (e.g., attention-is-all-you-need)
# - Concept pages should include mathematical notation where relevant
# - Always link model names to their originating paper entities
# - "scaling laws" and "emergent capabilities" are high-value concept pages

# Example for competitive analysis:
# - Entity types: company, product, person, market
# - Concept pages: positioning, pricing-strategy, go-to-market
# - Summarize quarterly earnings reports in summaries/
```
