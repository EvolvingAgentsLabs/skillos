---
type: skill-index
version: 1.0.0
total_skills: 28
last_updated: "2026-04-05"
---

# SkillOS Skill Index

Top-level routing table for the hierarchical skill system.
**Load this file first** to identify the domain, then load only the relevant domain index.

## Routing Protocol (4-Step Lazy Loading)

```
1. IDENTIFY domain from goal keywords (no file reads — infer from table below)
2. LOAD domain/index.md (30–60 lines) → select skill + manifest path
3. LOAD skill.manifest.md (15 lines) → confirm fit, get full_spec path
4. LOAD full_spec ONLY when ready to invoke (250–330 lines)
```

## Domain Table

| Domain | Skills | index path | Use when | Base behaviors |
|--------|--------|------------|----------|----------------|
| orchestration | 1 | system/skills/orchestration/index.md | goal execution, workflow, task coordination | system/skills/orchestration/base.md |
| memory | 4 | system/skills/memory/index.md | history, learning, patterns, logs, traces | system/skills/memory/base.md |
| robot | 5 | system/skills/robot/index.md | physical robot, navigation, camera, dreams | system/skills/robot/base.md |
| validation | 1 | system/skills/validation/index.md | health checks, spec integrity, preflight | system/skills/validation/base.md |
| recovery | 1 | system/skills/recovery/index.md | error handling, retry, circuit breaker | system/skills/recovery/base.md |
| project | 2 | system/skills/project/index.md | scaffolding, package install, new project | system/skills/project/base.md |
| content | 7 | system/skills/content/index.md | PDF, DOCX, XLSX, PPTX, skill creation, MCP, Claude API | system/skills/content/base.md |
| research | 4 | system/skills/research/index.md | web research, HF papers, datasets, LLM fine-tuning | system/skills/research/base.md |
| analytics | 2 | system/skills/analytics/index.md | data analysis, CSV/JSON, git workflow automation | system/skills/analytics/base.md |

## Quick Skill Lookup

| Skill | Domain/Family | subagent_type | Token Cost |
|-------|---------------|---------------|-----------|
| system-agent | orchestration/core | system-agent | high |
| memory-analysis-agent | memory/analysis | memory-analysis-agent | low |
| memory-consolidation-agent | memory/consolidation | memory-consolidation-agent | medium |
| query-memory-tool | memory/query | _(tool)_ | low |
| memory-trace-manager | memory/trace | _(tool)_ | low |
| roclaw-navigation-agent | robot/navigation | roclaw-navigation-agent | high |
| roclaw-scene-analysis-agent | robot/scene | roclaw-scene-analysis-agent | medium |
| roclaw-dream-agent | robot/dream | roclaw-dream-agent | medium |
| roclaw-tool | robot/tools | _(tool)_ | low |
| evolving-memory-tool | robot/tools | _(tool)_ | low |
| validation-agent | validation/system | validation-agent | low |
| error-recovery-agent | recovery/error | error-recovery-agent | low |
| project-scaffold-tool | project/scaffold | _(tool)_ | low |
| skill-package-manager-tool | project/packages | _(tool)_ | low |
| pdf | content/documents | _(tool)_ | low |
| docx | content/documents | _(tool)_ | low |
| xlsx | content/spreadsheets | _(tool)_ | low |
| pptx | content/presentations | _(tool)_ | low |
| skill-creator | content/meta | _(tool)_ | low |
| mcp-builder | content/meta | _(tool)_ | medium |
| claude-api | content/meta | _(tool)_ | low |
| web-research-agent | research/web | web-research-agent | medium |
| huggingface-papers | research/papers | _(tool)_ | low |
| huggingface-datasets | research/datasets | _(tool)_ | low |
| huggingface-llm-trainer | research/datasets | _(tool)_ | high |
| data-analysis-agent | analytics/tabular | data-analysis-agent | medium |
| git-workflow-agent | analytics/tabular | git-workflow-agent | low |

## Token Budget Guidance

| Loading stage | Lines loaded | Cumulative |
|---------------|-------------|-----------|
| This file (SkillIndex.md) | ~50 | 50 |
| + domain index.md | +30–60 | ~100 |
| + skill manifest | +15 | ~115 |
| + full skill spec | +250–330 | ~365–445 |

**Compare to old SmartLibrary.md approach**: 295 lines loaded upfront regardless of need.
**Savings**: ~61% reduction in routing-phase token consumption.
