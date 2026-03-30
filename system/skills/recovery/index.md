---
domain: recovery
skill_count: 1
base: system/skills/recovery/base.md
---

# Recovery Domain Index

Skills for error classification, retry management, and circuit breaking.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| error-recovery-agent | error | error-recovery-agent | any tool failure, step error, retry needed, circuit check | recovery/error/error-recovery-agent.manifest.md |

## Routing Notes
- Automatically invoked by SystemAgent on any step failure.
- Returns: `resolved` | `degraded_success` | `escalate` | `circuit_open`.
- Circuit breaker opens after 3 weighted failures in 15 min window.
