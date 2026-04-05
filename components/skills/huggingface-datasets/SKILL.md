---
name: huggingface-datasets
version: 1.0.0
source_repo: huggingface/skills
source_path: skills/huggingface-datasets/
license: Apache-2.0
installed_by: SkillOS
description: Load, explore, filter, and analyse datasets from the Hugging Face Hub
tools: [Bash, Write, Read]
dependencies:
  - datasets>=2.0.0
  - huggingface_hub>=0.20.0
---

# Hugging Face Datasets (Source)

Raw skill source from `huggingface/skills`.
SkillOS-integrated version: `system/skills/research/datasets/huggingface-datasets.md`

## What This Skill Does

- Load any public dataset from the HF Hub with a single call
- Inspect dataset schema (features, splits, row counts)
- Filter, shuffle, and sample rows
- Export to CSV/JSON for downstream processing
- Search the Hub for datasets matching a keyword

## Quick Start

```python
from datasets import load_dataset

# Load a dataset
ds = load_dataset("squad", split="train")
print(ds.features)       # schema
print(len(ds))           # row count
print(ds[0])             # first row

# Filter and export
positive = ds.filter(lambda x: len(x["context"]) > 200)
positive.to_csv("output.csv")
```

## Install Dependencies

```bash
pip install datasets huggingface_hub
```
