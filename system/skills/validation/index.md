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
| skill-security-scan-agent | security | validation-agent | skill install (pre-install gate), skill update, on-demand security audit | validation/security/skill-security-scan-agent.manifest.md |

## Routing Notes
- Invoke `validation-agent` after boot or before critical pipelines.
- Invoke `skill-security-scan-agent` automatically on every `skill install` / `skill update` — it is a blocking gate.
- Both are read-only — never modify system state.
- Returns structured health report: HEALTHY / DEGRADED / CRITICAL (validation-agent) or SAFE / WARNING / BLOCKED (skill-security-scan-agent).
