---
name: huggingface-papers
version: 1.0.0
source_repo: huggingface/skills
source_path: skills/huggingface-papers/
license: Apache-2.0
installed_by: SkillOS
description: Search and retrieve ML research papers from the Hugging Face Papers portal
tools: [WebFetch, WebSearch, Write]
dependencies: []
---

# Hugging Face Papers (Source)

Raw skill source from `huggingface/skills`.
SkillOS-integrated version: `system/skills/research/papers/huggingface-papers.md`

## What This Skill Does

Provides access to the Hugging Face Papers portal (`huggingface.co/papers`):
- Search papers by keyword or topic
- Browse daily highlighted papers
- Get trending papers by upvotes
- Fetch full paper details including abstract and model/dataset links
- Access ArXiv abstracts directly

## Quick Start

```
WebFetch: https://huggingface.co/papers?q=chain-of-thought
```

Returns a list of matching papers with titles, authors, abstracts, ArXiv IDs, and HF upvote counts.

## No Dependencies Required

Uses WebFetch/WebSearch — no Python packages needed.
