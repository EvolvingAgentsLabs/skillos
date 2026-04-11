---
type: skill-index
version: 1.1.0
total_skills: 22
last_updated: "2026-04-08"
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
| knowledge | 5 | system/skills/knowledge/index.md | build wiki, ingest sources, Q&A, lint KB, search | system/skills/knowledge/base.md |
| robot | 5 | system/skills/robot/index.md | physical robot, navigation, camera, dreams | system/skills/robot/base.md |
| validation | 1 | system/skills/validation/index.md | health checks, spec integrity, preflight | system/skills/validation/base.md |
| recovery | 1 | system/skills/recovery/index.md | error handling, retry, circuit breaker | system/skills/recovery/base.md |
| project | 2 | system/skills/project/index.md | scaffolding, package install, new project | system/skills/project/base.md |
| **planning** | **2** | **system/skills/planning/index.md** | **goal decomposition, subgoal generation, HWM hierarchical planning** | **system/skills/planning/base.md** |

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
| roclaw-dream-consolidation-agent | robot/dream | roclaw-dream-consolidation-agent | medium |
| roclaw-tool | robot/tools | _(tool)_ | low |
| knowledge-ingest-agent | knowledge/ingest | knowledge-ingest-agent | medium |
| knowledge-compile-agent | knowledge/compile | knowledge-compile-agent | high |
| knowledge-query-agent | knowledge/query | knowledge-query-agent | medium |
| knowledge-lint-agent | knowledge/lint | knowledge-lint-agent | medium |
| knowledge-search-tool | knowledge/search | _(tool)_ | low |
| validation-agent | validation/system | validation-agent | low |
| error-recovery-agent | recovery/error | error-recovery-agent | low |
| project-scaffold-tool | project/scaffold | _(tool)_ | low |
| skill-package-manager-tool | project/packages | _(tool)_ | low |
| **hwm-planner-agent** | **planning/hwm** | **hwm-planner-agent** | **medium** |
| **flat-planner-agent** | **planning/flat** | **flat-planner-agent** | **low** |

## Token Budget Guidance

| Loading stage | Lines loaded | Cumulative |
|---------------|-------------|-----------|
| This file (SkillIndex.md) | ~50 | 50 |
| + domain index.md | +30–60 | ~100 |
| + skill manifest | +15 | ~115 |
| + full skill spec | +250–330 | ~365–445 |

**Compare to old SmartLibrary.md approach**: 295 lines loaded upfront regardless of need.
**Savings**: ~61% reduction in routing-phase token consumption.
