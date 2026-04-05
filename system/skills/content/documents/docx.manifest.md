---
skill_id: content/documents/docx
name: docx
type: tool
domain: content
family: documents
extends: content/base
version: 1.0.0
source: github:anthropics/skills/docx
description: Create, read, and edit Microsoft Word documents with full formatting support
capabilities: [docx-create, docx-read, docx-edit, heading-styles, tables, images]
tools_required: [Read, Write, Bash]
token_cost: low
reliability: 92%
invoke_when: [create Word document, edit docx, write report in Word, DOCX output]
full_spec: system/skills/content/documents/docx.md
---
