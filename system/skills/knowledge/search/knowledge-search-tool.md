---
name: knowledge-search-tool
description: Lightweight hybrid search over wiki .md files. Keyword + WikiLink graph traversal. Returns ranked results with context for LLM consumption.
tools: Grep, Read, Glob, Bash
extends: knowledge/base
domain: knowledge
family: search
version: 1.0.0
---

# KnowledgeSearchTool

**Pattern**: Karpathy LLM Wiki — Search (qmd-style CLI tool)
**Status**: [REAL] - Production Ready
**Reliability**: 93%

> "I vibe coded a small and naive search engine over the wiki, which I both use directly
> (in a web ui), but more often I want to hand it off to an LLM via CLI as a tool for
> larger queries." — Karpathy

This tool provides the CLI-first search interface Karpathy describes. It is designed
to be composed — the knowledge-query-agent calls it as part of larger query workflows.

---

## Search Protocol

### Input
```
query: string           # search terms
wiki_path: string       # path to wiki/ directory
mode: keyword|graph|hybrid  # default: hybrid
max_results: int        # default: 10
context_lines: int      # lines of context around match, default: 3
```

### Step 1: Index Check
```
Action: Read
Path: [wiki_path]/_index.md
```
Use the index to identify candidate sections before doing full grep. This cuts search
scope by matching against category headers first.

### Step 2: Term Frequency Search (BM25-style)

```
Action: Grep
Pattern: [query terms as regex, OR-joined]
Path: [wiki_path]/
Output: files_with_matches + content
```

Score each result file by:
- Term frequency: how many times do query terms appear?
- Title match: does the filename contain query terms? (×3 boost)
- Frontmatter match: do `concept:`, `entity:`, or `key_claims:` fields match? (×2 boost)
- Section header match: do `##` headings contain query terms? (×1.5 boost)

### Step 3: WikiLink Graph Traversal (for `graph` and `hybrid` modes)

Starting from top-3 term-frequency matches:
1. Extract all `[[WikiLinks]]` from those pages.
2. For each linked page, check if it also contains query terms.
3. Linked pages that match get a `+graph_boost` score.

This surfaces related pages that use different terminology but are conceptually linked.

### Step 4: Rank and Return

Return results as structured markdown (LLM-consumable):

```markdown
## Search Results for: "[query]"
**Wiki**: [wiki_path]
**Results**: N found, top M shown

---

### 1. [Page Title] — Score: 0.92
**Path**: wiki/concepts/transformer-architecture.md
**Type**: concept
**Snippet**:
> ...the attention mechanism **[query term]** allows the model to weight
> different positions when computing representations...

**Related pages** (via WikiLinks): [[attention-mechanism]], [[encoder-decoder]]

---

### 2. [Page Title] — Score: 0.78
...
```

### Step 5: Graph Expansion (optional)

If `mode: graph`, also return:
```markdown
## WikiLink Graph (2 hops from top result)
[page-a] → [[page-b]] → [[page-c]]
[page-a] → [[page-d]]
```

---

## CLI Interface

The tool can be invoked directly via Bash for LLM-as-CLI pattern:

```bash
# Direct search via grep pipeline
grep -rn "[query]" [wiki_path]/ --include="*.md" -l | head -10

# With context
grep -rn "[query]" [wiki_path]/ --include="*.md" -C 3
```

For the knowledge-query-agent, this tool is typically invoked as:
```
Action: Grep
Pattern: [query]
Path: [wiki_path]/concepts/
```
followed by targeted Read of the highest-signal files.

---

## Integration with knowledge-query-agent

The query agent calls this tool in Step 3 of its protocol:
```
1. knowledge-query-agent receives question
2. → calls knowledge-search-tool to find relevant wiki pages
3. → reads the top 3-5 results
4. → synthesizes answer with citations
```

This keeps the query agent token-efficient: it doesn't need to load the full wiki,
just the search-surfaced relevant pages.

---

## Operational Constraints

- Search scope: `wiki/` directory only (never `raw/` — use ingest agent for that).
- Max results returned: 20 (to avoid overwhelming the calling agent's context).
- Minimum query length: 2 characters.
- For queries against very large wikis (>500 pages), scope to a specific subdirectory:
  `wiki/concepts/` or `wiki/entities/` rather than full `wiki/`.
