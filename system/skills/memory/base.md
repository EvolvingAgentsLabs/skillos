---
skill_domain: memory
type: base-template
version: 1.0.0
---

# Memory Domain — Shared Behaviors

All skills in the `memory/` domain inherit these conventions.

## Storage Conventions
- **Short-term**: `projects/[Project]/memory/short_term/YYYY-MM-DD_HH-MM-SS_*.md`
- **Long-term**: `projects/[Project]/memory/long_term/`
- **System-wide**: `system/SmartMemory.md` (single source of truth, queryable)
- **Archive**: `system/memory_archive/` (rotated monthly)

## Standard Log Format
Every memory entry uses YAML frontmatter + markdown body:
```yaml
---
timestamp: ISO-8601
agent: <agent-name>
action: <action-taken>
context: <project-or-task>
outcome: success | partial | failure
---
# Agent Interaction Log
## Request
## Agent Response
## Outcome
## Learnings
```

## Memory Query Protocol
Before executing memory-intensive tasks, check `system/SmartMemory.md` via Grep for
relevant past experience entries. Use `experience_id`, `goal`, and `outcome` fields for matching.

## Consolidation Trigger
At end of each project execution, invoke `memory/consolidation/memory-consolidation-agent`
to extract long-term insights from short-term logs.

## Token Efficiency
Prefer Grep-based lookup over full file reads. Cache consultation results for 1 hour
to avoid redundant reads within a session.
