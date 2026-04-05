---
name: pptx
version: 1.0.0
source_repo: anthropics/skills
source_path: skills/pptx/
license: MIT
installed_by: SkillOS
description: Create and edit PowerPoint presentations with slides, themes, speaker notes
tools: [Bash]
dependencies:
  - python-pptx>=0.6.23
---

# PPTX Skill (Source)

Raw skill source from `anthropics/skills`.
SkillOS-integrated version: `system/skills/content/presentations/pptx.md`

## What This Skill Does

- **Create**: New .pptx presentations with title and bullet slides
- **Edit**: Modify text, add slides to existing presentations
- **Themes**: Apply slide layouts and master templates
- **Speaker notes**: Add presenter notes per slide
- **Charts**: Embed data charts in slides
- **Images**: Insert image files into slides

## Quick Start

```python
from pptx import Presentation
from pptx.util import Inches

prs = Presentation()

# Title slide
slide = prs.slides.add_slide(prs.slide_layouts[0])
slide.shapes.title.text = "My Presentation"
slide.placeholders[1].text = "Subtitle"

# Bullet slide
slide = prs.slides.add_slide(prs.slide_layouts[1])
slide.shapes.title.text = "Key Points"
tf = slide.placeholders[1].text_frame
tf.text = "First point"
p = tf.add_paragraph()
p.text = "Second point"

# Speaker notes
slide.notes_slide.notes_text_frame.text = "Talk about these points..."

prs.save("presentation.pptx")
```

## Install Dependencies

```bash
pip install python-pptx
```
