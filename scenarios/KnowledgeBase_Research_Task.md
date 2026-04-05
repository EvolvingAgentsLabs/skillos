---
scenario: KnowledgeBase_Research_Task
version: 1.0
mode: EXECUTION
inspiration: Andrej Karpathy — LLM Wiki / Knowledge Base pattern
---

# Scenario: LLM Knowledge Base Research Task

## Overview

Demonstrates SkillOS's knowledge representation system: a compounding wiki that
accumulates domain knowledge across ingest, query, and lint cycles.

The wiki is a **persistent artifact** — it grows with every operation, unlike RAG
which re-derives knowledge on every query.

---

## Demo Goal

```
skillos execute: "Build a knowledge base on transformer architectures:
  1. Ingest the provided articles from raw/
  2. Answer: What are the key differences between MHA and MLA attention?
  3. Run a health check on the wiki
  4. Generate a Marp slide deck summarizing the findings"
```

---

## Expected Execution Flow

### Phase 1: Project Initialization

SystemAgent detects a knowledge accumulation goal and:
1. Creates `projects/Project_transformer_kb/` with full structure:
   ```
   raw/articles/     ← user drops source files here
   wiki/             ← LLM-compiled knowledge (starts empty)
   wiki/_schema.md   ← copied from templates/wiki/_schema.template.md
   wiki/_index.md    ← initialized empty
   wiki/_log.md      ← initialized empty
   output/           ← generated outputs
   ```
2. Reads `system/skills/SkillIndex.md` → identifies `knowledge` domain
3. Reads `system/skills/knowledge/index.md` → selects workflow

### Phase 2: Wiki Initialization

SystemAgent invokes `knowledge-compile-agent`:

```
Action: Task
subagent_type: knowledge-compile-agent
prompt: >
  Initialize wiki for transformer architecture knowledge base.
  Raw sources are in projects/Project_transformer_kb/raw/articles/.
  Schema template: templates/wiki/_schema.template.md
  Customize schema for ML research domain.
```

Compile agent:
- Reads schema template, customizes for ML domain
- Writes `wiki/_schema.md` (the wiki's constitution)
- Processes all raw sources in one coherent pass
- Creates concept pages: `transformer-architecture.md`, `attention-mechanism.md`,
  `multi-head-attention.md`, `multi-latent-attention.md`, `scaling-laws.md`
- Creates entity pages: `Vaswani-et-al-2017.md`, `DeepSeek-V2.md`
- Creates summary pages for each raw source
- Builds `wiki/_index.md` and initializes `wiki/_log.md`

### Phase 3: Query

SystemAgent invokes `knowledge-query-agent`:

```
Action: Task
subagent_type: knowledge-query-agent
prompt: >
  Question: What are the key differences between Multi-Head Attention (MHA)
  and Multi-Latent Attention (MLA)?
  Wiki: projects/Project_transformer_kb/wiki/
  Output format: markdown report, filed back to wiki/queries/
```

Query agent:
1. Reads `wiki/_index.md` → identifies relevant sections
2. Calls `knowledge-search-tool` → finds `multi-head-attention.md`, `multi-latent-attention.md`
3. Follows WikiLinks to `attention-mechanism.md`, `scaling-laws.md`
4. Synthesizes cited answer with confidence score
5. Files answer to `wiki/queries/mha-vs-mla-comparison.md`
6. Updates `_log.md` and `_index.md`
7. Reports gaps: "KV-cache optimization details need new sources"

### Phase 4: Wiki Health Check

SystemAgent invokes `knowledge-lint-agent`:

```
Action: Task
subagent_type: knowledge-lint-agent
prompt: >
  Run health check on projects/Project_transformer_kb/wiki/
  Report contradictions, orphan pages, missing cross-refs, and article candidates.
```

Lint agent runs all 8 checks, produces:
```
output/lint_report_2026-04-05.md
wiki/queries/lint_2026-04-05.md
```

### Phase 5: Output Generation

SystemAgent invokes `knowledge-query-agent` for slide generation:

```
Action: Task
subagent_type: knowledge-query-agent
prompt: >
  Generate a Marp slide deck summarizing transformer attention mechanisms.
  Source from wiki/. Output to projects/Project_transformer_kb/output/slides.md
  Format: Marp markdown (---marp: true---)
```

Output:
```
output/transformer_attention_slides.md
```
(Viewable in Obsidian with Marp plugin or at marp.app)

---

## State After Execution

```
projects/Project_transformer_kb/
├── raw/articles/
│   ├── attention-is-all-you-need.md
│   └── deepseek-v2-technical-report.md
├── wiki/
│   ├── _schema.md          ← ML-domain constitution
│   ├── _index.md           ← catalog: 5 concepts, 2 entities, 2 summaries, 2 queries
│   ├── _log.md             ← 4 operations: COMPILE, QUERY, LINT, QUERY
│   ├── concepts/
│   │   ├── transformer-architecture.md
│   │   ├── attention-mechanism.md
│   │   ├── multi-head-attention.md
│   │   ├── multi-latent-attention.md
│   │   └── scaling-laws.md
│   ├── entities/
│   │   ├── Vaswani-et-al-2017.md
│   │   └── DeepSeek-V2.md
│   ├── summaries/
│   │   ├── attention-is-all-you-need.md
│   │   └── deepseek-v2-technical-report.md
│   └── queries/
│       ├── mha-vs-mla-comparison.md   ← filed Q&A (compounding loop)
│       └── lint_2026-04-05.md         ← filed lint report
└── output/
    ├── lint_report_2026-04-05.md
    └── transformer_attention_slides.md  ← Marp slides
```

The wiki is now enriched and ready for the next query cycle. Every future question
benefits from the accumulated context.

---

## Compounding Loop Demonstration

Run again to demonstrate compounding:

```
skillos execute: "Add the new Llama-4 technical report to the transformer KB
  and answer: How does Llama-4's attention compare to DeepSeek-V2?"
```

The query agent will now have access to:
- The MHA vs. MLA comparison already filed in `wiki/queries/`
- The new summary for Llama-4
- Updated concept pages cross-referencing all three papers

Each cycle compounds. The wiki grows smarter with every operation.
