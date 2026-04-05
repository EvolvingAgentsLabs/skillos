---
skill_id: research/datasets/huggingface-datasets
name: huggingface-datasets
type: tool
domain: research
family: datasets
extends: research/base
version: 1.0.0
source: github:huggingface/skills/huggingface-datasets
description: Load, explore, filter, and analyse datasets from the Hugging Face Hub
capabilities: [dataset-load, dataset-explore, dataset-filter, dataset-stats, HF-hub-access]
tools_required: [Bash, Write, Read]
token_cost: low
reliability: 87%
invoke_when: [load dataset, HuggingFace dataset, training data, benchmark dataset, explore dataset]
full_spec: system/skills/research/datasets/huggingface-datasets.md
---
