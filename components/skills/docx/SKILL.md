---
name: docx
version: 1.0.0
source_repo: anthropics/skills
source_path: skills/docx/
license: MIT
installed_by: SkillOS
description: Create, read, and edit Microsoft Word documents with full formatting support
tools: [Bash]
dependencies:
  - python-docx>=1.0.0
---

# DOCX Skill (Source)

Raw skill source from `anthropics/skills`.
SkillOS-integrated version: `system/skills/content/documents/docx.md`

## What This Skill Does

- **Create**: Build new .docx documents with headings, paragraphs, tables, images
- **Read**: Extract text and structure from existing Word documents
- **Edit**: Modify content in-place (find/replace, append sections)
- **Style**: Apply heading styles H1-H6, bold, italic, underline

## Quick Start

```python
from docx import Document

# Create
doc = Document()
doc.add_heading("Title", 0)
doc.add_paragraph("Content paragraph.")
doc.add_heading("Section 1", level=1)
table = doc.add_table(rows=2, cols=2)
table.rows[0].cells[0].text = "Header 1"
doc.save("document.docx")

# Read
doc = Document("existing.docx")
for para in doc.paragraphs:
    print(para.style.name, para.text)
```

## Install Dependencies

```bash
pip install python-docx
```
