---
name: docx
extends: content/base
domain: content
family: documents
source: github:anthropics/skills/docx
source_file: components/skills/docx/SKILL.md
version: 1.0.0
tools: [Read, Write, Bash]
---

# DOCX Skill

Create, read, and edit Microsoft Word documents with full formatting support.

## Source

Wraps `components/skills/docx/SKILL.md` (sourced from `anthropics/skills`).

---

## Capabilities

| Operation | Description |
|-----------|-------------|
| **Create document** | Build a new .docx from content |
| **Read document** | Extract text and structure |
| **Edit document** | Modify existing .docx |
| **Heading styles** | Apply H1-H6 heading styles |
| **Tables** | Create and populate tables |
| **Images** | Insert images from file |
| **Lists** | Bullet and numbered lists |

---

## Protocol

### Creating a DOCX

```python
python3 - <<'EOF'
from docx import Document
from docx.shared import Inches

doc = Document()
doc.add_heading("Report Title", 0)
doc.add_paragraph("Executive summary paragraph.")
doc.add_heading("Section 1", level=1)
doc.add_paragraph("Section content here.")

# Add a table
table = doc.add_table(rows=2, cols=3)
table.style = "Table Grid"
hdr = table.rows[0].cells
hdr[0].text, hdr[1].text, hdr[2].text = "Column A", "Column B", "Column C"
row = table.rows[1].cells
row[0].text, row[1].text, row[2].text = "Data 1", "Data 2", "Data 3"

doc.save("output/report.docx")
print("Document created: output/report.docx")
EOF
```

### Reading a DOCX

```python
python3 - <<'EOF'
from docx import Document
doc = Document("input/document.docx")
for para in doc.paragraphs:
    if para.style.name.startswith("Heading"):
        print(f"\n## {para.text}")
    else:
        print(para.text)
EOF
```

### Editing a DOCX

```python
python3 - <<'EOF'
from docx import Document
doc = Document("input/document.docx")
# Replace text in paragraphs
for para in doc.paragraphs:
    if "OLD_TEXT" in para.text:
        for run in para.runs:
            run.text = run.text.replace("OLD_TEXT", "NEW_TEXT")
doc.save("output/document_edited.docx")
EOF
```

---

## Dependency

| Library | Install |
|---------|---------|
| `python-docx` | `pip install python-docx` |

**Fallback**: If `python-docx` unavailable, generate markdown equivalent and note conversion:
`pandoc output/document.md -o output/document.docx`

---

## Output Convention

All generated DOCX files → `projects/[Project]/output/`.
Extracted text content → `projects/[Project]/output/extracted/`.
