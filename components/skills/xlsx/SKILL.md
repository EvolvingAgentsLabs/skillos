---
name: xlsx
version: 1.0.0
source_repo: anthropics/skills
source_path: skills/xlsx/
license: MIT
installed_by: SkillOS
description: Create, read, and edit Excel spreadsheets with formulas, charts, multi-sheet support
tools: [Bash]
dependencies:
  - openpyxl>=3.1.0
---

# XLSX Skill (Source)

Raw skill source from `anthropics/skills`.
SkillOS-integrated version: `system/skills/content/spreadsheets/xlsx.md`

## What This Skill Does

- **Create**: New workbooks with multiple named sheets
- **Read**: Load cell values, formulas, formatting metadata
- **Write**: Populate cells, rows, ranges with data
- **Formulas**: Insert native Excel formula strings (e.g. `=SUM(A1:A10)`)
- **Charts**: Generate bar, line, pie charts embedded in sheets
- **Formatting**: Cell colors, number formats, column widths

## Quick Start

```python
import openpyxl
from openpyxl.chart import BarChart, Reference

# Create workbook
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Data"
ws.append(["Name", "Score"])
ws.append(["Alice", 95])
ws.append(["Bob", 87])

# Add chart
chart = BarChart()
data = Reference(ws, min_col=2, min_row=1, max_row=3)
chart.add_data(data, titles_from_data=True)
ws.add_chart(chart, "D1")

wb.save("output.xlsx")

# Read
wb = openpyxl.load_workbook("input.xlsx", read_only=True)
for row in wb.active.iter_rows(values_only=True):
    print(row)
```

## Install Dependencies

```bash
pip install openpyxl
```
