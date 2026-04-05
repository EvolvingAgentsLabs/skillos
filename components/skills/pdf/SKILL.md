---
name: pdf
version: 1.0.0
source_repo: anthropics/skills
source_path: skills/pdf/
license: MIT
installed_by: SkillOS
description: Extract text/tables from PDFs, fill forms, generate new PDF documents
tools: [Bash]
dependencies:
  - pypdf>=4.0.0
  - pdfplumber>=0.10.0
  - reportlab>=4.0.0
---

# PDF Skill (Source)

This is the raw skill source file from `anthropics/skills`.
For SkillOS-integrated version with hierarchy and base inheritance,
see: `system/skills/content/documents/pdf.md`

## What This Skill Does

Provides PDF manipulation capabilities:
- **Read**: Extract text and table content from existing PDFs
- **Write**: Generate new PDF documents from content
- **Fill**: Populate form fields in PDF forms
- **Split/Merge**: Combine or split PDF files by page range

## Quick Start

```python
# Extract text
import pypdf
reader = pypdf.PdfReader("document.pdf")
text = "\n".join(page.extract_text() for page in reader.pages)

# Generate PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
doc = SimpleDocTemplate("output.pdf")
doc.build([Paragraph("Hello World", getSampleStyleSheet()["Normal"])])

# Fill form
writer = pypdf.PdfWriter()
writer.append(pypdf.PdfReader("form.pdf"))
writer.update_page_form_field_values(writer.pages[0], {"field": "value"})
with open("filled.pdf", "wb") as f:
    writer.write(f)
```

## Install Dependencies

```bash
pip install pypdf pdfplumber reportlab
```
