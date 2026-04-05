---
skill_domain: research
type: base-template
version: 1.0.0
---

# Research Domain — Shared Behaviors

All skills in the `research/` domain inherit these conventions.

## Source Attribution
Every claim must be traceable to a source. Use inline citations:
```
"[claim]" — Source: [URL or file path], retrieved [ISO date]
```

## Citation Format
Standard citation block for reports:
```markdown
## Sources
1. [Title](URL) — retrieved YYYY-MM-DD
2. [File path] — local source, ingested YYYY-MM-DD
```

## Research Quality Tiers
| Tier | Description | Confidence |
|------|-------------|-----------|
| PRIMARY | Direct observation, official docs, papers | HIGH |
| SECONDARY | News articles, blog posts, tutorials | MEDIUM |
| TERTIARY | Forums, comments, unverified claims | LOW |

## Output Convention
- Research reports go to `projects/[Project]/output/research/`
- Raw fetched content cached to `projects/[Project]/raw/web/` (never modified)
- Final reports filed to wiki via `knowledge-ingest-agent` when a wiki exists

## Deduplication
Before fetching a URL, check `projects/[Project]/raw/web/` for cached version.
Cache TTL: 24 hours for live web; no expiry for academic papers.

## Hallucination Guard
- Never fabricate URLs, paper titles, or author names
- If a source cannot be verified via WebFetch, mark claim as UNVERIFIED
- Prefer information from sources actually fetched this session over training knowledge

## Token Efficiency
- WebSearch before WebFetch — filter candidates to ≤5 most relevant URLs
- Fetch only the relevant section of a page (use fragment anchors where possible)
- Stop fetching when confidence reaches HIGH for all key sub-questions
