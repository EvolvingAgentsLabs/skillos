---
dialect_id: data-flow
name: Data Flow DAG Notation
version: 1.0.0
domain_scope: [orchestration, knowledge]
compression_type: structural
compression_ratio: "~65-80%"
reversible: true
input_format: natural-language-pipeline
output_format: dag-notation
---

# Data Flow Dialect

## Purpose

Compresses natural language pipeline descriptions, data processing workflows, and multi-step transformations into directed acyclic graph (DAG) notation. Forces the LLM to identify data sources, operations, sinks, parallelizable branches, and join points. Makes data dependencies explicit — the model must decide which operations can run concurrently and which are sequential. Prevents pipeline design errors by requiring explicit edge declarations.

## Domain Scope

- **orchestration** — Compress execution pipelines, agent delegation graphs, and data processing workflows. The DAG notation makes parallelization opportunities visible at a glance.
- **knowledge** — Describe information processing flows in wiki articles: ETL pipelines, research workflows, content production chains.

## Compression Rules

1. **Identify sources**: Data entry points tagged as `[SRC] name`. Can include glob patterns for file sources.
2. **Identify operations**: Processing steps tagged as `[OP] name`. Include function-like arguments when relevant: `[OP] cluster(similarity)`.
3. **Identify sinks**: Output destinations tagged as `[SINK] name`. Include file paths or target systems.
4. **Mark parallel branches**: Independent operations that can run concurrently tagged with `[PAR]` before the branch point.
5. **Mark join points**: Where parallel branches converge tagged with `[JOIN]`.
6. **Use edge arrows**: `→` for data flow direction between nodes.
7. **Use pipe for parallel sources**: `[SRC] a | b | c` for multiple parallel input sources.
8. **Annotate with metadata**: `{type:X, cost:N}` for operation annotations when relevant.
9. **Drop procedural prose**: Remove "first", "then", "after that", "next step is to". The graph structure encodes ordering.
10. **Preserve paths and identifiers**: File paths, API endpoints, and system names preserved exactly.

## Preservation Rules

1. **Data dependencies**: All sequential dependencies preserved as edges.
2. **Parallelism opportunities**: Independent operations correctly identified.
3. **Source and sink identifiers**: File paths, URLs, system names preserved.
4. **Operation semantics**: Transformation names descriptive enough to reconstruct behavior.
5. **Metadata annotations**: Cost, type, and constraint annotations preserved.

## Grammar / Syntax

```
DAG         := NODE (SP "→" SP NODE)*
NODE        := SOURCE | OPERATION | SINK | PARALLEL | JOIN

SOURCE      := "[SRC]" SP name (SP "|" SP name)*
OPERATION   := "[OP]" SP name ("(" args ")")? (SP annotation)?
SINK        := "[SINK]" SP name
PARALLEL    := "[PAR]" SP branch (SP "|" SP branch)*
JOIN        := "[JOIN]"

branch      := NODE (SP "→" SP NODE)*
annotation  := "{" key ":" value ("," SP key ":" value)* "}"
name        := identifier | path | glob_pattern
```

## Examples

### Example 1 — News aggregation pipeline

**Input** (42 words):
```
Fetch news from 3 sources in parallel — TechCrunch, Ars Technica, and Hacker News. Deduplicate the combined results, then summarize each unique article. Finally, merge all summaries into a single daily briefing document.
```

**Output** (14 words):
```
[SRC] techcrunch | ars | hn [PAR] → [OP] dedup → [OP] summarize [JOIN] → [SINK] briefing.md
```

**Ratio**: 42 words → 14 words, ~67% reduction

### Example 2 — Trace-to-strategy pipeline

**Input** (38 words):
```
Read all trace files from the traces directory, extract the goals from each trace, cluster them by semantic similarity, generate or update strategies based on discovered patterns, and store the results in the wiki strategies folder.
```

**Output** (13 words):
```
[SRC] traces/*.md → [OP] extract_goals → [OP] cluster(similarity) → [OP] gen_strategies → [SINK] wiki/strategies/
```

**Ratio**: 38 words → 13 words, ~66% reduction

### Example 3 — Language facade pipeline

**Input** (48 words):
```
Take the user's natural language input and compile it into the appropriate internal dialect. Route the compiled form to the correct domain agent for execution. Collect the result, then in parallel: expand the result to prose for the user, and compress a log entry for memory storage.
```

**Output** (18 words):
```
[SRC] user_input → [OP] intent_compile → [OP] route(domain) → [OP] execute → [PAR] [OP] expand_prose → [SINK] user | [OP] compress_log → [SINK] memory
```

**Ratio**: 48 words → 18 words, ~63% reduction

## Expansion Protocol

Data-flow is **reversible**. The expander reconstructs pipeline descriptions:

1. **`[SRC]` → source description**: "The pipeline begins by reading data from [source]."
2. **`[OP]` → processing step**: "The data is then processed by [operation], which [describes transformation]."
3. **`[SINK]` → output description**: "The final output is written to [destination]."
4. **`[PAR]` → parallel description**: "The following operations run in parallel:"
5. **`[JOIN]` → merge description**: "The parallel results are then combined."
6. **`→` → sequence connector**: "After [previous step], the output is passed to [next step]."
7. **`|` → enumeration**: List multiple items with "and" or commas.

### Target Registers

- **formal**: Technical specification with numbered processing stages and explicit data contracts.
- **conversational**: "First, we grab the data from X, then clean it up, and finally save it to Y."
- **technical**: YAML/JSON DAG definition with nodes, edges, and annotations.

### Reversibility Confidence

- Linear pipelines (no branching): 90-95%
- Pipelines with parallel branches: 80-90%
- Complex DAGs with annotations: 70-80%

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~65-80% |
| Token reduction | ~60-75% |
| Reversibility | High — structure fully preserved, prose context lost |
| Latency | Low (structural extraction) |
| Error rate | <3% — parallelism identification occasionally imprecise |
| Quality improvement | Makes dependencies explicit; reveals parallelization opportunities |
