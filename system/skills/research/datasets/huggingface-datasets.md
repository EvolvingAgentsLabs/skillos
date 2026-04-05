---
name: huggingface-datasets
extends: research/base
domain: research
family: datasets
source: github:huggingface/skills/huggingface-datasets
source_file: components/skills/huggingface-datasets/SKILL.md
version: 1.0.0
tools: [Bash, Write, Read]
---

# Hugging Face Datasets

Load, explore, filter, and analyse datasets from the Hugging Face Hub.
Provides programmatic access to thousands of public datasets for training, evaluation, and analysis.

## Source

Wraps `components/skills/huggingface-datasets/SKILL.md` (sourced from `huggingface/skills`).

---

## Capabilities

| Operation | Description |
|-----------|-------------|
| **Load dataset** | Download and load a HF dataset by name |
| **Explore schema** | Inspect features, splits, row count |
| **Filter** | Apply conditions to produce a subset |
| **Sample** | Draw random or stratified samples |
| **Export** | Save to CSV/JSON for downstream use |
| **Search Hub** | Find datasets matching a keyword |

---

## Protocol

### Load and Inspect

```python
python3 - <<'EOF'
from datasets import load_dataset

# Load a dataset (cached locally after first download)
dataset = load_dataset("squad", split="train")

print("Features:", dataset.features)
print("Row count:", len(dataset))
print("First row:", dataset[0])
EOF
```

### Search Hugging Face Hub

```python
python3 - <<'EOF'
from huggingface_hub import HfApi
api = HfApi()
datasets = api.list_datasets(search="sentiment analysis", limit=10)
for d in datasets:
    print(d.id, "-", getattr(d, "description", "")[:80])
EOF
```

### Filter and Export

```python
python3 - <<'EOF'
from datasets import load_dataset
import json

dataset = load_dataset("imdb", split="train")

# Filter to positive reviews
positive = dataset.filter(lambda x: x["label"] == 1)
print(f"Positive reviews: {len(positive)}")

# Export to JSON
positive.to_json("output/imdb_positive.json")
print("Exported to output/imdb_positive.json")
EOF
```

### Sample

```python
python3 - <<'EOF'
from datasets import load_dataset

dataset = load_dataset("glue", "mrpc", split="train")
sample = dataset.shuffle(seed=42).select(range(100))
sample.to_csv("output/mrpc_sample.csv")
print(f"Sampled {len(sample)} rows → output/mrpc_sample.csv")
EOF
```

---

## Dependency

```bash
pip install datasets huggingface_hub
```

---

## Output Convention

Downloaded datasets cached to `~/.cache/huggingface/datasets/` (HF default).
Exported files → `projects/[Project]/output/datasets/`.

---

## Examples

**"Load the OpenHermes instruction dataset and show its schema"**
→ `load_dataset("teknium/OpenHermes-2.5")` → print features + 3 sample rows

**"Find datasets for named entity recognition"**
→ Hub search → return top 5 with row counts and licenses

**"Export 1000 random samples from the Alpaca dataset to CSV"**
→ Load → shuffle → select(1000) → to_csv → save to output/
