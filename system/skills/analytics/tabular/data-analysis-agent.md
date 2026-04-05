---
name: data-analysis-agent
extends: analytics/base
domain: analytics
family: tabular
source: original
version: 1.0.0
tools: [Read, Write, Bash, Glob, Grep]
---

# Data Analysis Agent

Analyse CSV, JSON, and tabular data files using Python (pandas/numpy).
Produces summary statistics, charts (matplotlib), and a structured markdown report.

---

## Protocol

### Phase 1 — Data Discovery

Locate input data files:
```bash
find projects/[Project]/input -name "*.csv" -o -name "*.json" -o -name "*.tsv" | sort
```
If no input/ files found, check `projects/[Project]/raw/` and `projects/[Project]/output/datasets/`.

### Phase 2 — Schema Inference

Read first 20 rows to infer schema before loading full dataset:

```python
python3 - <<'EOF'
import pandas as pd

df = pd.read_csv("input/data.csv", nrows=20)
print("Shape (sample):", df.shape)
print("\nColumns and types:")
print(df.dtypes)
print("\nMissing values (sample):")
print(df.isnull().sum())
print("\nFirst 3 rows:")
print(df.head(3).to_markdown())
EOF
```

Document the schema in the report before proceeding.

### Phase 3 — Full Analysis

```python
python3 - <<'EOF'
import pandas as pd
import numpy as np
import json

df = pd.read_csv("input/data.csv")

report = {}

# Basic stats
report["shape"] = {"rows": len(df), "columns": len(df.columns)}
report["missing"] = df.isnull().sum().to_dict()
report["dtypes"] = df.dtypes.astype(str).to_dict()

# Numeric summary
numeric = df.select_dtypes(include=[np.number])
if not numeric.empty:
    report["numeric_summary"] = numeric.describe().to_dict()

# Categorical summary
categorical = df.select_dtypes(include=["object", "category"])
for col in categorical.columns[:5]:   # cap at 5 to avoid huge output
    report[f"value_counts_{col}"] = df[col].value_counts().head(10).to_dict()

with open("output/analysis_stats.json", "w") as f:
    json.dump(report, f, indent=2, default=str)

print("Stats saved to output/analysis_stats.json")
EOF
```

### Phase 4 — Chart Generation

```python
python3 - <<'EOF'
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import os

os.makedirs("output/charts", exist_ok=True)
df = pd.read_csv("input/data.csv")

numeric = df.select_dtypes(include="number")

# Distribution histograms
for col in numeric.columns[:4]:   # cap at 4 columns
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(df[col].dropna(), bins=30, edgecolor="black", alpha=0.7)
    ax.set_title(f"Distribution: {col}")
    ax.set_xlabel(col)
    ax.set_ylabel("Frequency")
    fig.tight_layout()
    fig.savefig(f"output/charts/{col}_hist.png", dpi=100)
    plt.close(fig)
    print(f"Chart saved: output/charts/{col}_hist.png")

# Correlation heatmap (if ≥2 numeric columns)
if len(numeric.columns) >= 2:
    fig, ax = plt.subplots(figsize=(8, 6))
    corr = numeric.corr()
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.columns)
    plt.colorbar(im, ax=ax)
    ax.set_title("Correlation Matrix")
    fig.tight_layout()
    fig.savefig("output/charts/correlation_heatmap.png", dpi=100)
    plt.close(fig)
    print("Chart saved: output/charts/correlation_heatmap.png")
EOF
```

### Phase 5 — Report Generation

Write `projects/[Project]/output/analysis_report.md`:

```markdown
---
dataset: [filename]
rows: [N]
columns: [N]
generated: [ISO timestamp]
---

# Data Analysis Report: [Dataset Name]

## Dataset Overview
| Property | Value |
|----------|-------|
| Rows | N |
| Columns | N |
| Missing values | N total |

## Schema
[Column types table]

## Key Statistics
[Numeric summary table]

## Distribution Analysis
[Histogram charts embedded as markdown image links]

## Correlation Analysis
[Heatmap + notable correlations]

## Notable Findings
[Bullet list of significant observations]

## Recommendations
[Next steps for data use or further analysis]
```

---

## Fallback (no Python libraries)

If pandas/matplotlib unavailable, use shell tools:
```bash
# Row count
wc -l input/data.csv

# Column names
head -1 input/data.csv

# Unique values in column 1
cut -d',' -f1 input/data.csv | sort | uniq -c | sort -rn | head -20
```

---

## Examples

**"Analyse the sales data in input/sales_2025.csv"**
→ Schema inference → full stats → 4 histograms + heatmap → analysis_report.md

**"What's the distribution of response times in input/logs.json?"**
→ Load JSON → extract field → histogram → summary stats

**"Find correlations between features in the dataset"**
→ Correlation matrix → heatmap → top 5 correlated pairs listed
