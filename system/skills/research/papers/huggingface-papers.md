---
name: huggingface-papers
extends: research/base
domain: research
family: papers
source: github:huggingface/skills/huggingface-papers
source_file: components/skills/huggingface-papers/SKILL.md
version: 1.0.0
tools: [WebFetch, WebSearch, Write]
---

# Hugging Face Papers

Search, browse, and retrieve ML research papers from the Hugging Face Papers portal
(`huggingface.co/papers`). Provides structured access to daily paper highlights,
trending papers, and ArXiv abstract retrieval.

## Source

Wraps `components/skills/huggingface-papers/SKILL.md` (sourced from `huggingface/skills`).

---

## Capabilities

| Operation | Description |
|-----------|-------------|
| **Search papers** | Find papers by keyword or topic |
| **Daily papers** | Get today's highlighted papers |
| **Trending** | Top papers by upvotes/discussion |
| **Paper detail** | Fetch abstract, authors, links for a specific paper |
| **ArXiv fetch** | Retrieve full abstract from arxiv.org |

---

## Protocol

### Search Papers

```
WebFetch: https://huggingface.co/papers?q={url-encoded-query}
```
Parse results: paper title, authors, abstract snippet, arxiv ID, HF upvotes.
Return ranked list (by upvotes descending).

### Daily Papers

```
WebFetch: https://huggingface.co/papers
```
Extract today's curated paper list with titles and brief descriptions.

### Paper Detail

```
WebFetch: https://huggingface.co/papers/{arxiv-id}
```
Extract: full abstract, author list, model/dataset links, community discussion summary.

### ArXiv Full Abstract

```
WebFetch: https://arxiv.org/abs/{arxiv-id}
```
Extract: title, authors, abstract, submission date, categories.

---

## Output Format

```markdown
## Paper: {Title}

- **ArXiv ID**: {id}
- **Authors**: {author1}, {author2}, ...
- **Date**: {YYYY-MM-DD}
- **HF Upvotes**: {N}
- **Abstract**: {full abstract}
- **Links**: [ArXiv](https://arxiv.org/abs/{id}) | [PDF](https://arxiv.org/pdf/{id})
- **Related models/datasets**: {HF Hub links if any}
```

---

## Examples

**"Find recent papers on chain-of-thought reasoning"**
→ Search HF Papers → return top 5 by upvotes with abstracts

**"What are today's highlighted ML papers?"**
→ Fetch huggingface.co/papers → parse daily list → summarize top 3

**"Get details on arxiv paper 2310.06825"**
→ Fetch HF Papers + ArXiv → return full structured detail
