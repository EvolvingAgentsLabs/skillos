---
skill_domain: analytics
type: base-template
version: 1.0.0
---

# Analytics Domain — Shared Behaviors

All skills in the `analytics/` domain inherit these conventions.

## Data Path Convention
- Input data lives in `projects/[Project]/input/` or `projects/[Project]/raw/`
- All output artifacts (reports, charts, exports) go to `projects/[Project]/output/`
- Intermediate processing files (cleaned data, temp CSVs) go to `projects/[Project]/output/tmp/`
- Never modify source data files

## Python Environment Convention
Run all Python analysis via `Bash` tool:
```bash
python3 -c "
import pandas as pd
import numpy as np
# ... analysis code
"
```
Or write a temp script to `projects/[Project]/output/tmp/analysis.py` and execute it.

## Standard Output Formats
| Output type | Format | Path |
|------------|--------|------|
| Summary stats | Markdown table | `output/summary.md` |
| Charts | PNG via matplotlib | `output/charts/*.png` |
| Processed data | CSV | `output/processed/*.csv` |
| Full report | Markdown | `output/analysis_report.md` |

## Dependency Check
Before running analysis, check library availability:
```bash
python3 -c "import pandas, numpy, matplotlib" 2>&1
```
Fall back to shell tools (awk, sort, uniq) if Python libs unavailable.

## Schema Inference
Always infer and document the data schema before analysis:
- Column names, types, nullable
- Row count, date range (if time series)
- Missing value counts

## Token Efficiency
- Read only the first 20 rows of a data file for schema inference before full load
- Use Grep to search within data files when looking for specific values
- For large files (>10MB), process in chunks via pandas chunking
