---
name: pptx
extends: content/base
domain: content
family: presentations
source: github:anthropics/skills/pptx
source_file: components/skills/pptx/SKILL.md
version: 1.0.0
tools: [Read, Write, Bash]
---

# PPTX Skill

Create and edit PowerPoint presentations with slides, themes, and speaker notes.

## Source

Wraps `components/skills/pptx/SKILL.md` (sourced from `anthropics/skills`).

> **Marp alternative**: For simpler slide decks, prefer `knowledge-query-agent` with Marp
> markdown output (no dependencies, renders in Obsidian). Use this skill when native .pptx
> format is required.

---

## Capabilities

| Operation | Description |
|-----------|-------------|
| **Create presentation** | New .pptx with title slide |
| **Add slides** | Append slides with layouts |
| **Speaker notes** | Add presenter notes |
| **Themes** | Apply built-in or custom themes |
| **Charts** | Embed bar, line, pie charts |
| **Images** | Insert images from file |
| **Read presentation** | Extract slide text content |

---

## Protocol

### Creating a PPTX

```python
python3 - <<'EOF'
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN

prs = Presentation()

# Title slide
title_slide_layout = prs.slide_layouts[0]
slide = prs.slides.add_slide(title_slide_layout)
slide.shapes.title.text = "Presentation Title"
slide.placeholders[1].text = "Subtitle or Author"

# Bullet slide
bullet_layout = prs.slide_layouts[1]
slide = prs.slides.add_slide(bullet_layout)
slide.shapes.title.text = "Key Points"
tf = slide.placeholders[1].text_frame
tf.text = "First key point"
for point in ["Second key point", "Third key point"]:
    p = tf.add_paragraph()
    p.text = point
    p.level = 1

# Speaker notes
notes_slide = slide.notes_slide
notes_slide.notes_text_frame.text = "Expand on key points here."

prs.save("output/presentation.pptx")
print("Presentation created: output/presentation.pptx")
EOF
```

### Reading a PPTX

```python
python3 - <<'EOF'
from pptx import Presentation
prs = Presentation("input/slides.pptx")
for i, slide in enumerate(prs.slides, 1):
    print(f"\n=== Slide {i} ===")
    for shape in slide.shapes:
        if shape.has_text_frame:
            print(shape.text_frame.text)
EOF
```

---

## Dependency

| Library | Install |
|---------|---------|
| `python-pptx` | `pip install python-pptx` |

**Fallback**: Marp markdown slides if python-pptx unavailable.
Template: `---marp: true\n---\n# Slide Title\n\n- Bullet\n---\n`

---

## Output Convention

All generated PPTX files → `projects/[Project]/output/`.
Marp fallback slides → `projects/[Project]/output/slides.md`.
