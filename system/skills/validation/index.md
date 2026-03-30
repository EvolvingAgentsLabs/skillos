---
domain: validation
skill_count: 1
base: system/skills/validation/base.md
---

# Validation Domain Index

Skills for system health checks, spec integrity, and preflight validation.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| validation-agent | system | validation-agent | system health check, after boot, preflight, spec integrity | validation/system/validation-agent.manifest.md |

## Routing Notes
- Invoke after boot or before critical pipelines.
- Returns structured health report: HEALTHY / DEGRADED / CRITICAL.
- Read-only — never modifies system state.
