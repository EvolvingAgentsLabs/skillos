---
skill_id: content/spreadsheets/xlsx
name: xlsx
type: tool
domain: content
family: spreadsheets
extends: content/base
version: 1.0.0
source: github:anthropics/skills/xlsx
description: Create, read, and edit Excel spreadsheets with formulas, charts, and formatting
capabilities: [xlsx-create, xlsx-read, xlsx-edit, formulas, charts, pivot-tables, multi-sheet]
tools_required: [Read, Write, Bash]
token_cost: low
reliability: 91%
invoke_when: [create spreadsheet, edit Excel, XLSX output, tabular data to Excel, financial model]
full_spec: system/skills/content/spreadsheets/xlsx.md
---
