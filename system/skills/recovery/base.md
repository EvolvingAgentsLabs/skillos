---
skill_domain: recovery
type: base-template
version: 1.0.0
---

# Recovery Domain — Shared Behaviors

All skills in the `recovery/` domain inherit these conventions.

## Error Classification
| Class | Examples | Default Action |
|-------|----------|----------------|
| Transient | Timeout, 429, 503 | Retry with exponential backoff |
| Permanent | 404, invalid param | Alternative approach or escalate |
| Resource | Quota, budget, context | Reduce scope or escalate |
| Logic | Missing field, schema mismatch | Retry with clarified prompt |
| Permission | 403, auth required | Escalate immediately |
| Unknown | Unclassified | Single retry then escalate |

## Retry Protocol
- Attempt 1: Immediate retry
- Attempt 2: Wait 2s
- Attempt 3: Wait 4s
- Attempt 4: Wait 8s
- Max wait: 30s
- After 3 weighted failures in 15 min: circuit breaker opens

## Circuit Breaker
When circuit is open, return `circuit_open` status immediately without retrying.
Log the opening event to `projects/[Project]/memory/short_term/`.

## Resolution Outcomes
Every recovery attempt returns one of:
- `resolved` — error fixed, execution can continue
- `degraded_success` — partial success, execution continues with reduced scope
- `escalate` — human intervention required
- `circuit_open` — too many failures, halt execution

## Recovery Logging
Log every recovery attempt to `projects/[Project]/memory/short_term/[error_id]_recovery.md`.
Include: error class, strategy used, outcome, and learnings for future prevention.
