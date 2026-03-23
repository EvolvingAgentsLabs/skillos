---
name: knowledge-synthesis-task
version: v1
description: >
  Multi-source knowledge aggregation pipeline: parallel content fetching from
  N sources, followed by entity extraction, deduplication, cross-source
  synthesis, and structured knowledge base generation.
delegation_pattern: parallel_fanout_then_synthesis
error_recovery: graceful_degradation
---

# Knowledge Synthesis Task: Multi-Source Knowledge Base Builder

## Scenario Overview

Builds a structured knowledge base from multiple sources (web pages, local
files, or both). Fetches sources in parallel, extracts entities and concepts,
deduplicates and reconciles across sources, then synthesizes into a navigable
knowledge base with cross-references.

## Agent Network

| Agent | Role | Pattern |
|---|---|---|
| FetchAgent (×N) | Retrieve and pre-process each source | Parallel fan-out |
| EntityExtractorAgent | Extract entities, concepts, relationships | Sequential (after fetch) |
| DeduplicationAgent | Identify duplicates, resolve conflicts | Sequential (after extraction) |
| SynthesisAgent | Build cross-referenced knowledge base | Sequential (after dedup) |
| IndexAgent | Generate index, TOC, and search hints | Sequential (final) |

## Input

Specify sources in the goal as:
- Web URLs to fetch
- Local file paths in `input/`
- Topic + count (auto-discover via web search)

## Execution Pipeline

### Phase 1: Parallel Content Fetch (Fan-Out)

**Pattern**: One FetchAgent per source, all concurrent
**Agent**: FetchAgent (instantiated per source)
**Tools**: WebFetch or Read (depending on source type)

For each source:
1. Fetch content (`WebFetch` for URLs, `Read` for local files)
2. Strip boilerplate (navigation, ads, footers) — keep main content
3. Identify content type: article, documentation, research paper, reference
4. Extract metadata: title, author, date, URL/path
5. Write `state/source_{index}_content.md`

**Error Recovery**:
- HTTP error → retry once, then skip and log
- Empty content → skip source, continue with remaining
- Minimum viable: proceed with >= 50% of sources

### Phase 2: Entity and Concept Extraction (Sequential)

**Agent**: EntityExtractorAgent
**Tools**: Read, Write

1. Read all `source_*_content.md` files
2. Extract per source:
   - Named entities: people, organizations, technologies, places
   - Key concepts and definitions
   - Claims and assertions (with source attribution)
   - Relationships between entities
3. Assign confidence score to each extraction
4. Write `state/entity_map.md`

**Entity map format:**
```yaml
entities:
  - name: [entity]
    type: [person|org|tech|concept]
    sources: [list of source indices]
    definitions: [per-source definitions]
    confidence: [0.0–1.0]

relationships:
  - from: [entity]
    to: [entity]
    type: [uses|created_by|related_to|contrasts_with]
    sources: [list]
```

### Phase 3: Deduplication and Conflict Resolution (Sequential)

**Agent**: DeduplicationAgent
**Tools**: Read, Write
**Depends On**: Phase 2

1. Read `entity_map.md`
2. Group entities with same/similar names (e.g., "ML" = "Machine Learning")
3. Merge duplicate entries, preserving all source references
4. Resolve conflicting definitions:
   - If definitions agree: merge into canonical definition
   - If definitions conflict: preserve both with source attribution
5. Prune low-confidence extractions (< 0.4 confidence)
6. Write `state/canonical_entities.md`

### Phase 4: Knowledge Base Synthesis (Sequential)

**Agent**: SynthesisAgent
**Tools**: Read, Write
**Depends On**: Phase 3

1. Read `canonical_entities.md` and all source content
2. For each major concept/entity, write a knowledge article:
   - Definition and context
   - Key properties and relationships
   - Source citations with quotes
   - "See also" cross-references to related entities
3. Group articles into thematic sections
4. Write individual article files to `output/kb/[concept].md`
5. Write `state/synthesis_map.md` (structure of the KB)

### Phase 5: Indexing (Sequential)

**Agent**: IndexAgent
**Tools**: Read, Write, Glob
**Depends On**: Phase 4

1. Read `synthesis_map.md` and all output KB files
2. Generate:
   - Table of contents with section hierarchy
   - Full entity index (alphabetical with links)
   - Cross-reference matrix (which articles reference which)
   - Source attribution summary
3. Write `projects/[ProjectName]/output/knowledge_base/INDEX.md`
4. Write `projects/[ProjectName]/output/knowledge_base/SOURCES.md`

## Expected Output

```
projects/[ProjectName]/output/knowledge_base/
├── INDEX.md                    # Table of contents + entity index
├── SOURCES.md                  # Source attribution and reliability
├── [section]/
│   ├── [concept_1].md          # Individual knowledge articles
│   ├── [concept_2].md
│   └── ...
└── cross_references.md         # Entity relationship map
```

## Success Criteria

- At least 50% of sources successfully fetched
- Minimum 10 distinct entities extracted
- Deduplication reduces entity count by at least 10%
- Each knowledge article has >= 2 source citations
- INDEX.md provides complete navigation
- Cross-references link related concepts

## Usage

```bash
skillos execute: "Build a knowledge base from these 5 documentation pages about Kubernetes networking: [url1] [url2] [url3] [url4] [url5]"

skillos execute: "Synthesize a knowledge base on retrieval-augmented generation (RAG) from the papers in projects/RAGResearch/input/"

skillos execute: "Create a structured knowledge base on the React ecosystem by researching React, Redux, Next.js, and Zustand documentation"

skillos execute: "Build a competitor analysis knowledge base by fetching and synthesizing the product pages and blogs of Stripe, Paddle, and Braintree"
```
