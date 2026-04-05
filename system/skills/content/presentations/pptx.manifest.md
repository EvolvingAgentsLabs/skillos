---
skill_id: content/presentations/pptx
name: pptx
type: tool
domain: content
family: presentations
extends: content/base
version: 1.0.0
source: github:anthropics/skills/pptx
description: Create and edit PowerPoint presentations with slides, themes, and speaker notes
capabilities: [pptx-create, pptx-edit, slide-layout, themes, speaker-notes, charts-in-slides]
tools_required: [Read, Write, Bash]
token_cost: low
reliability: 90%
invoke_when: [create presentation, PowerPoint, PPTX output, slide deck, keynote-style output]
full_spec: system/skills/content/presentations/pptx.md
---
