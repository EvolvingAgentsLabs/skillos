---
domain: validation
skill_count: 2
base: system/skills/validation/base.md
---

# Validation Domain Index

Skills for system health checks, spec integrity, security scanning, and preflight validation.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| validation-agent | system | validation-agent | system health check, after boot, preflight, spec integrity | validation/system/validation-agent.manifest.md |
| skill-security-scan-agent | security | skill-security-scan-agent | skill install, skill update, security scan, security audit | validation/security/skill-security-scan-agent.manifest.md |

## Routing Notes
- Invoke `validation-agent` after boot or before critical pipelines.
- Invoke `skill-security-scan-agent` before writing any external skill to disk.
- validation-agent returns structured health report: HEALTHY / DEGRADED / CRITICAL.
- skill-security-scan-agent returns verdicts: SAFE / WARNING / BLOCKED.
- Both are read-only — they never modify system state (scanner writes reports only).
