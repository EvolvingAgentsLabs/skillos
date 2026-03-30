---
domain: orchestration
skill_count: 1
base: system/skills/orchestration/base.md
---

# Orchestration Domain Index

Skills responsible for goal decomposition, workflow management, and task delegation.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| system-agent | core | system-agent | any new goal, workflow orchestration, multi-step coordination | orchestration/core/system-agent.manifest.md |

## Routing Notes
- `system-agent` is the entry point for ALL user goals. It reads this index only if
  a sub-task requires re-invoking orchestration (rare).
- Token cost: high — load full spec immediately for this domain.
