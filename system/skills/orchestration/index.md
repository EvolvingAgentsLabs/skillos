---
domain: orchestration
skill_count: 3
base: system/skills/orchestration/base.md
---

# Orchestration Domain Index

Skills responsible for goal decomposition, workflow management, and task delegation.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| system-agent | core | system-agent | any new goal, workflow orchestration, multi-step coordination | orchestration/core/system-agent.manifest.md |
| intent-compiler-agent | ingress | intent-compiler-agent | incoming user goal, natural language input, parse intent | orchestration/ingress/intent-compiler-agent.manifest.md |
| human-renderer-agent | egress | human-renderer-agent | render output for user, expand dialect to prose, final response formatting | orchestration/egress/human-renderer-agent.manifest.md |

## Routing Notes
- `system-agent` is the entry point for ALL user goals. It reads this index only if
  a sub-task requires re-invoking orchestration (rare).
- Token cost: high — load full spec immediately for this domain.
- **Two-tier runtime**: before delegating, `system-agent` consults
  `orchestration/provider-router.md` to decide between Hot (Gemma + cartridges),
  Warm (Gemma E4B), or Forge (Claude Code for meta-work only). Forge never runs
  user goals directly.

## Policies (shared, non-skill)
| File | Purpose |
|------|---------|
| `orchestration/provider-router.md` | Tier selection (Hot/Warm/Forge), budget, offline gate |
| `orchestration/base.md` | Delegation protocol, state management, logging |
