---
skill_domain: validation
type: base-template
version: 1.0.0
---

# Validation Domain — Shared Behaviors

All skills in the `validation/` domain inherit these conventions.

## Validation Scope
Validation skills perform read-only health checks. They never modify system state.
They report findings as structured health reports and exit with a status code.

## Report Format
Every validation report includes:
```markdown
# System Health Report
- **Status**: HEALTHY | DEGRADED | CRITICAL
- **Timestamp**: ISO-8601
- **Checks Performed**: N
- **Passed**: N | **Failed**: N | **Warnings**: N

## Check Results
| Check | Status | Detail |
|-------|--------|--------|
| ...   | PASS   | ...    |

## Recommended Actions
```

## Invocation Pattern
Validation skills are invoked:
1. After `boot skillos` to confirm system integrity.
2. Before major execution pipelines as a preflight check.
3. On-demand via `skillos execute: "validate system"`.

## Escalation
Report CRITICAL status to SystemAgent immediately. SystemAgent decides whether to
block execution or proceed with degraded mode.
