---
name: data-pipeline
complexity: intermediate
pattern: parallel-ingest-then-sequential-analysis
estimated_cost: <$0.10
---

# Data Pipeline: CSV/JSON Analysis with Visualizations

Demonstrates structured data ingestion, profiling, and ASCII visualization.

## Goal

```bash
skillos execute: "Analyze the sales data at projects/MySalesProject/input/sales_2024.csv — profile each column, identify monthly trends, and generate a report with ASCII charts"
```

## Sample Input

Create `projects/MySalesProject/input/sales_2024.csv`:

```csv
date,product,region,revenue,units,rep
2024-01-05,Widget A,North,12500,50,Alice
2024-01-12,Widget B,South,8300,33,Bob
2024-01-19,Widget A,East,15200,61,Carol
2024-02-03,Widget B,North,9100,36,Alice
2024-02-14,Widget A,West,11800,47,Dave
...
```

## What Happens

1. **IngestionAgent** + **ProfilingAgent** run in parallel:
   - Ingestion: parse CSV, detect types, flag nulls
   - Profiling: compute stats, find outliers
2. **AnalysisAgent**: identifies trends, correlations, top performers
3. **ReportAgent**: generates full report with ASCII charts

## Expected Output

```markdown
# Sales Data Report — 2024

## Dataset Overview
- Rows: 247 | Columns: 6 | Missing values: 3 (1.2%)
- Date range: 2024-01-05 → 2024-12-28

## Statistical Profile
| Column | Min | Max | Mean | Std Dev |
|---|---|---|---|---|
| revenue | 4,200 | 28,900 | 12,340 | 4,890 |
| units | 16 | 116 | 49 | 19 |

## Monthly Revenue Trend
Jan  ████████████  $148K
Feb  ██████████    $122K
Mar  ██████████████ $168K
...

## Top Performers
1. Alice — $342K (23% of total)
2. Carol — $298K (20% of total)

## Key Findings
1. Q3 revenue 34% higher than Q1 — driven by Widget A in North region
2. Widget B underperforms in West region (only 8% of regional revenue)
3. Outlier detected: 2024-07-22, revenue $28,900 (2.3× mean)
```

## Variations

```bash
# JSON dataset
skillos execute: "Profile and analyze the user behavior data at input/events.json, identify usage patterns and drop-off points"

# Comparison analysis
skillos execute: "Compare Q1 and Q2 sales data from input/q1.csv and input/q2.csv, highlight what changed and why"

# Time series analysis
skillos execute: "Analyze the server metrics CSV at input/metrics.csv, identify anomaly timestamps and correlate with deployment events"

# Multi-file merge
skillos execute: "Merge and analyze all CSV files in input/monthly_reports/, produce a full-year summary report"
```

## Learning Objectives

- See parallel data processing agents in action
- Understand how agents coordinate through state files
- Learn ASCII chart generation within markdown reports
- Observe error recovery for malformed data
