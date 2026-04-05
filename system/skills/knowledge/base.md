---
skill_domain: knowledge
type: base-template
version: 1.0.0
inspiration: Andrej Karpathy — LLM Wiki / Knowledge Base pattern
---

# Knowledge Domain — Shared Behaviors

All skills in the `knowledge/` domain implement Karpathy's **LLM-compiled wiki** pattern:
raw source documents are ingested once and compiled by the LLM into a persistent, compounding
markdown wiki — not re-derived on every query (unlike RAG), but continuously accumulated.

---

## Three-Layer Architecture

```
Layer 1: raw/        — Immutable curated sources (articles, papers, repos, images)
Layer 2: wiki/       — LLM-maintained compiled knowledge (.md files, cross-referenced)
Layer 3: _schema.md  — Wiki structure definition (tells LLM what to maintain)
```

The wiki is a **compounding artifact**: every ingest, query, and lint operation makes it richer.
The human curates sources and asks questions. The LLM handles all maintenance.

---

## Standard Project Structure

Every knowledge base project follows this layout:

```
projects/[KBName]/
├── raw/                        # Immutable source documents (never modified by LLM)
│   ├── articles/               # Web articles (ideally as .md via Obsidian Web Clipper)
│   ├── papers/                 # Research papers
│   ├── repos/                  # Code repository summaries
│   ├── images/                 # Referenced images
│   └── _sources.md            # Ingest log: what was added, when, by whom
├── wiki/                       # LLM-compiled knowledge (fully managed by LLM)
│   ├── _schema.md             # Wiki structure definition (LLM's constitution)
│   ├── _index.md              # Content catalog organized by category (auto-maintained)
│   ├── _log.md                # Append-only chronological log of all operations
│   ├── concepts/              # Core concept articles (one per major topic)
│   ├── entities/              # Named entities: people, papers, orgs, datasets
│   ├── summaries/             # Per-source document summaries with backlinks
│   └── queries/               # Filed high-value Q&A outputs (become wiki pages)
└── output/                    # Generated outputs (slides, reports, images)
```

---

## Wiki Schema Convention (`wiki/_schema.md`)

Each knowledge base defines its own schema — the LLM's constitution for that wiki.
It specifies:

```markdown
# Wiki Schema for [KBName]

## Categories
- concepts/: One article per major concept. Format: title, summary, related concepts, sources.
- entities/: One page per named entity. Format: name, type, description, appearances.
- summaries/: One page per raw source. Format: source path, key claims, relation to concepts.

## Cross-Reference Rules
- Every concept page links to related concepts via [[WikiLink]] format.
- Every summary page backlinks to the concepts it supports or contradicts.
- Every entity page lists all summaries that mention it.

## _index.md Structure
Table of contents organized by category with one-line descriptions.

## _log.md Format
| Timestamp | Operation | Target | Summary |
|-----------|-----------|--------|---------|
```

---

## Core Operations

### Ingest
When new sources are added to `raw/`:
1. LLM reads each new source.
2. Updates or creates up to 15 wiki pages simultaneously (summaries, concepts, entities).
3. Maintains cross-references and backlinks.
4. Appends an entry to `wiki/_log.md`.
5. Updates `wiki/_index.md`.

### Compile (Full Rebuild)
Rebuilds the entire wiki from `raw/` from scratch. Used when schema changes.

### Query
LLM synthesizes answers from wiki pages with citations.
High-value query outputs are filed back into `wiki/queries/` to compound the wiki.

### Lint
Health check over the wiki:
- Contradictions between concept pages.
- Stale claims (source no longer supports them).
- Orphan pages (no backlinks).
- Missing cross-references between related concepts.
- Data gaps (concepts referenced but not yet written).

### Search
Lightweight keyword + structural search over wiki `.md` files.
Returns ranked results with surrounding context for LLM consumption.

---

## Token Efficiency Guidelines

- Always read `wiki/_index.md` first (the catalog) rather than crawling wiki/ directly.
- Use Grep before Read for targeted concept lookup.
- For Q&A, load `_index.md` + targeted concept pages, not the full wiki.
- Cache `_index.md` reads within a session (changes only on ingest/lint).

---

## Output Formats

| Format | Tool | Use case |
|--------|------|----------|
| Markdown report | Write | Default — filed back into wiki/queries/ |
| Marp slides | Write (.md with Marp frontmatter) | Presentations |
| Obsidian-compatible | Write (WikiLink format `[[...]]`) | Local IDE viewing |
| matplotlib summary | Bash (python -c ...) | Visual data analysis |
