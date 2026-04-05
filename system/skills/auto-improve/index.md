---
type: domain-index
domain: auto-improve
version: 1.0.0
skill_count: 2
base: system/skills/auto-improve/base.md
---

# Auto-Improve Domain Index

**Use this domain when**: tracking skill usage, detecting stale skills, running background
self-optimization, proposing spec improvements, applying the AutoAgent / AutoResearch loop
to SkillOS itself.

## Skills

| Skill | Type | Manifest | Full Spec | invoke_when |
|-------|------|----------|-----------|-------------|
| usage-tracker | tool | `auto-improve/usage-tracker/usage-tracker.manifest.md` | `auto-improve/usage-tracker/usage-tracker.md` | record a skill invocation OR check for stale skills |
| auto-improve-meta-agent | agent | `auto-improve/meta-agent/auto-improve-meta-agent.manifest.md` | `auto-improve/meta-agent/auto-improve-meta-agent.md` | a stale skill is detected OR failure spike observed |

## Trigger Flow

```
system-agent invokes skill X
    │
    ▼
usage-tracker.record(skill_id=X)          ← always, synchronous, ~1ms
    │
    ├── is X stale? ──NO──► done
    │
    └──YES──► spawn auto-improve-meta-agent(skill_id=X) as background Task
                    │
                    ▼
            reads SmartMemory failure traces
            reads current skill spec
            proposes targeted improvement
            passes anti-overfitting gate
            writes to pending_improvements/
            logs to improvement_log.md
```

## Integration Points

- **system-agent.md**: calls `usage-tracker` after every skill delegation (Step 5.5 in execution loop)
- **SmartMemory.md**: meta-agent queries for failure traces involving the stale skill
- **SkillIndex.md**: this domain is registered as `auto-improve`

## Token Cost

| Skill | Cost | Notes |
|-------|------|-------|
| usage-tracker | negligible | JSON read/write only |
| auto-improve-meta-agent | medium–high | runs in background, no user latency impact |
