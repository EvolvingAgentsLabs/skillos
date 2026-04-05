---
skill_id: research/papers/huggingface-papers
name: huggingface-papers
type: tool
domain: research
family: papers
extends: research/base
version: 1.0.0
source: github:huggingface/skills/huggingface-papers
description: Search, browse, and retrieve ML research papers from the Hugging Face Papers portal
capabilities: [paper-search, paper-retrieval, arxiv-access, HF-papers-browse, abstract-extraction]
tools_required: [WebFetch, WebSearch, Write]
token_cost: low
reliability: 88%
invoke_when: [find ML paper, Hugging Face papers, research paper, arxiv, LLM paper, AI research]
full_spec: system/skills/research/papers/huggingface-papers.md
---
