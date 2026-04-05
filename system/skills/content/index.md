---
domain: content
type: domain-index
version: 1.0.0
total_skills: 7
base: system/skills/content/base.md
---

# Content Domain Index

Use for: document creation, spreadsheet editing, presentation building, skill meta-tools.

## Skills

| Skill | Family | subagent_type | Manifest | Token Cost |
|-------|--------|---------------|---------|-----------|
| pdf | documents | _(tool)_ | system/skills/content/documents/pdf.manifest.md | low |
| docx | documents | _(tool)_ | system/skills/content/documents/docx.manifest.md | low |
| xlsx | spreadsheets | _(tool)_ | system/skills/content/spreadsheets/xlsx.manifest.md | low |
| pptx | presentations | _(tool)_ | system/skills/content/presentations/pptx.manifest.md | low |
| skill-creator | meta | _(tool)_ | system/skills/content/meta/skill-creator.manifest.md | low |
| mcp-builder | meta | _(tool)_ | system/skills/content/meta/mcp-builder.manifest.md | medium |
| claude-api | meta | _(tool)_ | system/skills/content/meta/claude-api.manifest.md | low |

## Invoke When

- User asks to create, edit, or read a PDF, Word doc, Excel sheet, or PowerPoint
- Agent needs to produce a formatted document output
- Building a new skill or MCP server from a spec
- Making sub-LLM API calls for parallelism or cost optimization

## Base Behaviors

Inherited from `system/skills/content/base.md`:
- Output path convention: `projects/[Project]/output/`
- Python library fallback chain (pypdf → reportlab → pandoc)
- Provenance header on all generated documents
