---
name: data-analysis-task
version: v1
description: >
  Four-agent data analysis pipeline: parallel Ingestion and Profiling agents,
  followed by sequential Analysis and Visualization agents, producing a
  structured data intelligence report.
delegation_pattern: parallel_fanout_then_sequential
error_recovery: per_stage
---

# Data Analysis Task: Structured Data Intelligence Pipeline

## Scenario Overview

Analyzes structured data (CSV, JSON, or tabular text files) using a 4-agent
pipeline. Two agents run in parallel (ingestion and profiling), followed by
sequential analysis and report generation with ASCII chart visualizations.

## Agent Network

| Agent | Role | Pattern |
|---|---|---|
| IngestionAgent | Load, validate, and normalize data | Parallel (with ProfilingAgent) |
| ProfilingAgent | Statistical summary and anomaly detection | Parallel (with IngestionAgent) |
| AnalysisAgent | Trend identification and correlation analysis | Sequential (after parallel phase) |
| ReportAgent | Generate data intelligence report with charts | Sequential (after analysis) |

## Input

Provide one or more of:
- Path to CSV or JSON file(s) in the project `input/` directory
- Inline data description in the goal
- URL to a public dataset

## Execution Pipeline

### Phase 1: Parallel Ingestion and Profiling

**Pattern**: Parallel Fan-Out

#### IngestionAgent
**Tools**: Read, Bash, Write

1. `Read` input file(s)
2. Detect format (CSV, JSON, TSV) and delimiter
3. Parse structure: columns/fields, data types, row count
4. Identify and flag: missing values, duplicates, type mismatches
5. Normalize to canonical format
6. Write `state/ingested_data.md` with schema and row count summary

#### ProfilingAgent
**Tools**: Read, Bash, Write

1. `Read` input file(s) in parallel with IngestionAgent
2. Compute statistical summary for each numeric column:
   - min, max, mean, median, standard deviation
3. Compute value frequency for categorical columns (top 10)
4. Detect outliers (values beyond 3 standard deviations)
5. Flag anomalies and unusual distributions
6. Write `state/data_profile.md`

### Phase 2: Analysis (Sequential)

**Agent**: AnalysisAgent
**Tools**: Read, Write
**Depends On**: Phase 1 (both agents)

1. Read `ingested_data.md` and `data_profile.md`
2. Identify top trends per column over time (if temporal data present)
3. Detect correlations between numeric columns
4. Identify top-performing and bottom-performing segments
5. Highlight key anomalies from profile
6. Write `state/analysis_findings.md`

**Analysis output structure:**
```
## Key Trends
- [trend]: [evidence]

## Correlations
- [col_a] ↔ [col_b]: [strength and direction]

## Top Segments
| Segment | Metric | Value |

## Anomalies
- [row/field]: [description]
```

### Phase 3: Report Generation (Sequential)

**Agent**: ReportAgent
**Tools**: Read, Write
**Depends On**: Phase 2

1. Read all phase outputs
2. Generate full data intelligence report:
   - Dataset overview (source, dimensions, quality score)
   - Statistical summary table
   - Top 5 findings with business interpretation
   - ASCII bar/line charts for key metrics
   - Recommendations based on findings
3. Write `projects/[ProjectName]/output/data_report.md`

**ASCII chart example:**
```
Monthly Revenue ($K)
Jan ████████████  120
Feb ██████████    100
Mar ███████████████ 150
```

## Error Recovery

| Agent | Error | Action |
|---|---|---|
| IngestionAgent | File not found | Check `input/` directory, list available files |
| IngestionAgent | Encoding error | Try UTF-8, then Latin-1 |
| ProfilingAgent | Numeric parse failure | Skip column, log warning |
| AnalysisAgent | Insufficient data (< 10 rows) | Reduce analysis scope, note limitation |
| ReportAgent | No trends found | Report data as baseline with no trend |

## Expected Output

```
projects/[ProjectName]/output/
├── data_report.md          # Full intelligence report with charts
├── ingested_data.md        # Schema and quality summary
├── data_profile.md         # Statistical profile
└── analysis_findings.md    # Trends, correlations, anomalies
```

## Success Criteria

- Data file(s) successfully parsed
- Statistical profile covers all columns
- At least 3 findings identified
- Report includes ASCII visualizations
- Data quality score calculated and reported

## Usage

```bash
skillos execute: "Analyze the sales data in projects/MySalesProject/input/sales_2024.csv and generate a monthly performance report"

skillos execute: "Profile and analyze the JSON dataset at projects/UserData/input/users.json, identify trends and anomalies"

skillos execute: "Compare Q1 and Q2 data in input/q1.csv and input/q2.csv, highlight key changes"
```
