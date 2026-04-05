---
name: xlsx
extends: content/base
domain: content
family: spreadsheets
source: github:anthropics/skills/xlsx
source_file: components/skills/xlsx/SKILL.md
version: 1.0.0
tools: [Read, Write, Bash]
---

# XLSX Skill

Create, read, and edit Excel spreadsheets with formulas, charts, and multi-sheet support.

## Source

Wraps `components/skills/xlsx/SKILL.md` (sourced from `anthropics/skills`).

---

## Capabilities

| Operation | Description |
|-----------|-------------|
| **Create workbook** | New .xlsx with multiple sheets |
| **Read data** | Load sheet data into memory |
| **Write data** | Populate cells, rows, columns |
| **Formulas** | Insert Excel formula strings |
| **Charts** | Generate bar, line, pie charts |
| **Formatting** | Cell styles, number formats, colors |
| **Pivot tables** | Summarize data with pivot views |

---

## Protocol

### Creating an XLSX

```python
python3 - <<'EOF'
import openpyxl
from openpyxl.chart import BarChart, Reference

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Sales Data"

# Headers
ws.append(["Month", "Revenue", "Expenses", "Profit"])
# Data
data = [
    ["Jan", 50000, 35000, 15000],
    ["Feb", 62000, 38000, 24000],
    ["Mar", 71000, 41000, 30000],
]
for row in data:
    ws.append(row)

# Add a bar chart
chart = BarChart()
chart.title = "Monthly Performance"
chart.y_axis.title = "Amount ($)"
chart.x_axis.title = "Month"
data_ref = Reference(ws, min_col=2, min_row=1, max_col=4, max_row=4)
cats = Reference(ws, min_col=1, min_row=2, max_row=4)
chart.add_data(data_ref, titles_from_data=True)
chart.set_categories(cats)
ws.add_chart(chart, "F2")

wb.save("output/sales_data.xlsx")
print("Spreadsheet created: output/sales_data.xlsx")
EOF
```

### Reading an XLSX

```python
python3 - <<'EOF'
import openpyxl
wb = openpyxl.load_workbook("input/data.xlsx", read_only=True)
for sheet_name in wb.sheetnames:
    ws = wb[sheet_name]
    print(f"\n=== Sheet: {sheet_name} ===")
    for row in ws.iter_rows(values_only=True):
        print(" | ".join(str(c or "") for c in row))
EOF
```

---

## Dependency

| Library | Install |
|---------|---------|
| `openpyxl` | `pip install openpyxl` |
| `xlsxwriter` | `pip install xlsxwriter` (charts alternative) |

**Fallback**: CSV output if openpyxl unavailable.

---

## Output Convention

All generated XLSX files → `projects/[Project]/output/`.
