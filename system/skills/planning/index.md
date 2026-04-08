---
type: domain-index
domain: planning
version: 1.0.0
skills: 2
base: system/skills/planning/base.md
---

# Planning Domain Index

Hierarchical planning skills grounded in the **HWM paper** (arXiv 2604.03208).
Two-level architecture: L2 macro-planner generates subgoals, L1 primitive-planner executes them.

---

## Available Skills

| Skill | Type | Manifest | Token Cost | Use when |
|-------|------|----------|------------|----------|
| `hwm-planner-agent` | agent | `planning/hwm/hwm-planner-agent.manifest.md` | medium | complex / long-horizon goals, subgoal decomposition needed |
| `flat-planner-agent` | agent | `planning/flat/flat-planner-agent.manifest.md` | low | short-horizon goals, final steps near goal, simple tasks |

---

## Domain Routing

**Route to `hwm-planner-agent` when** (keywords / signals):
- Goal has more than ~3 sequential steps
- Goal requires multi-skill orchestration
- Task horizon is unclear or long
- Subgoal decomposition would help
- Keywords: `plan`, `decompose`, `strategy`, `hierarchical`, `long-horizon`, `multi-step`

**Route to `flat-planner-agent` when**:
- Goal is simple and well-scoped (≤ 3 steps)
- System-agent is in final-transition phase (near goal)
- HWM subgoal generation overhead is not justified
- Keywords: `quick`, `direct`, `single-step`, `finish`, `final`

---

## Loading Order

```
1. Load this index  (~30 lines)
2. Load chosen manifest  (~15 lines)
3. Load full spec only when ready to invoke  (~200–300 lines)
```
