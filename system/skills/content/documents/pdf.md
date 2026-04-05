---
name: pdf
extends: content/base
domain: content
family: documents
source: github:anthropics/skills/pdf
source_file: components/skills/pdf/SKILL.md
version: 1.0.0
tools: [Read, Write, Bash]
---

# PDF Skill

Extract, parse, fill, and generate PDF documents.

## Source

Wraps `components/skills/pdf/SKILL.md` (sourced from `anthropics/skills`).
This SkillOS spec adds the `extends: content/base` inheritance layer and maps
to the SkillOS project/output path conventions.

---

## Capabilities

| Operation | Description |
|-----------|-------------|
| **Extract text** | Read all text content from a PDF |
| **Extract tables** | Parse tabular data into CSV/markdown |
| **Extract pages** | Get specific page ranges |
| **Fill forms** | Populate PDF form fields |
| **Generate PDF** | Create a new PDF from markdown or HTML |
| **Merge/split** | Combine or split PDF files |

---

## Protocol

### Reading a PDF

```python
# Via Bash tool
python3 - <<'EOF'
import sys
try:
    import pypdf
    reader = pypdf.PdfReader("input.pdf")
    for i, page in enumerate(reader.pages):
        print(f"=== Page {i+1} ===")
        print(page.extract_text())
except ImportError:
    # Fallback: pdftotext
    import subprocess
    result = subprocess.run(["pdftotext", "input.pdf", "-"], capture_output=True, text=True)
    print(result.stdout)
EOF
```

### Extracting Tables

```python
python3 - <<'EOF'
try:
    import pdfplumber
    with pdfplumber.open("input.pdf") as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    print(" | ".join(str(cell or "") for cell in row))
except ImportError:
    print("pdfplumber not available — install with: pip install pdfplumber")
EOF
```

### Generating a PDF

```python
python3 - <<'EOF'
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate("output/document.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    story = [Paragraph("Hello from SkillOS PDF skill", styles["Normal"])]
    doc.build(story)
    print("PDF generated: output/document.pdf")
except ImportError:
    # Fallback: generate HTML and note pandoc requirement
    print("reportlab not available — falling back to HTML")
    with open("output/document.html", "w") as f:
        f.write("<html><body><p>Hello from SkillOS PDF skill</p></body></html>")
    print("HTML generated: output/document.html — convert with: pandoc output/document.html -o output/document.pdf")
EOF
```

### Filling PDF Forms

```python
python3 - <<'EOF'
try:
    import pypdf
    reader = pypdf.PdfReader("form.pdf")
    writer = pypdf.PdfWriter()
    writer.append(reader)
    fields = {
        "field_name": "field_value",
        # Add more fields as needed
    }
    writer.update_page_form_field_values(writer.pages[0], fields)
    with open("output/filled_form.pdf", "wb") as f:
        writer.write(f)
    print("Form filled: output/filled_form.pdf")
except ImportError:
    print("pypdf not available — install with: pip install pypdf")
EOF
```

---

## Output Convention

All generated PDFs go to `projects/[Project]/output/`.
Extracted text content goes to `projects/[Project]/output/extracted/`.

---

## Dependency Matrix

| Library | Purpose | Install |
|---------|---------|---------|
| `pypdf` | Read/write/fill PDFs | `pip install pypdf` |
| `pdfplumber` | Table extraction | `pip install pdfplumber` |
| `reportlab` | Generate PDFs | `pip install reportlab` |
| `pdftotext` | CLI fallback | `apt install poppler-utils` |
| `pandoc` | Markdown → PDF | `apt install pandoc` |

---

## Error Handling

- If `pypdf` is unavailable, fall back to `pdftotext` CLI
- If `reportlab` is unavailable, fall back to HTML output + pandoc instructions
- Always log fallback used in output header comment
- For encrypted PDFs: attempt password-free open; if blocked, report to user

---

## Examples

**"Extract all text from report.pdf"**
→ Read `input/report.pdf` → run extraction → write to `output/extracted/report.txt`

**"Fill out the intake form"**
→ Read `input/intake_form.pdf` → identify fields → fill with provided data → write to `output/intake_form_filled.pdf`

**"Generate a PDF report of the analysis"**
→ Take markdown content → use reportlab → write to `output/analysis_report.pdf`
