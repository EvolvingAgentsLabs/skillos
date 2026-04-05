---
skill_id: content/documents/pdf
name: pdf
type: tool
domain: content
family: documents
extends: content/base
version: 1.0.0
source: github:anthropics/skills/pdf
description: Extract text/tables from PDFs, fill forms, and generate new PDF documents
capabilities: [pdf-read, pdf-write, pdf-extract, form-fill, text-extraction, table-extraction]
tools_required: [Read, Write, Bash]
token_cost: low
reliability: 90%
invoke_when: [read PDF, extract PDF, fill form, generate PDF, parse PDF, PDF tables]
full_spec: system/skills/content/documents/pdf.md
---
