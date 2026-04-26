# Planning: Hierarchical World Models (HWM)

SkillOS integrates the **HWM** planning algorithm as its default logic execution strategy.

> **Paper**: *Hierarchical Planning with Latent World Models* — Wancong Zhang, Basile Terver,
> Artem Zholus, et al. (Meta FAIR / NYU, 2025) — arXiv:2604.03208
>
> **Core claim**: *"A high-level planner optimizes macro-actions using a long-horizon world model
> to reach the goal; the first predicted latent state serves as a subgoal for a low-level
> planner, which optimizes primitive actions with a short-horizon world model."*

---

## Why HWM in SkillOS?

Traditional skill orchestration selects the next skill greedily (one step at a time) without
simulating future states. HWM adds a **planning horizon**: before acting, the system predicts
what the world will look like after a sequence of actions and picks the sequence with the lowest
cost — just like a chess player thinking several moves ahead.

The two-level hierarchy addresses a key trade-off:
- **Long-horizon planning is expensive** if done at the primitive-action level
- **Short-horizon planning misses long-range structure**
- **HWM**: plan at the skill level (few, abstract steps), execute at the tool level (fine-grained)

---

## Architecture

```
GOAL
  │
  ▼
┌──────────────────────────────────────────────────────────┐
│  L2: High-Level World Model  (hwm-planner-agent)         │
│                                                          │
│  Operates on:  skill invocations (macro-actions)         │
│  Horizon:      H = 8 macro-steps                         │
│  Candidates:   N = 10 action sequences                   │
│  Predicts:     skill-level state transitions             │
│                                                          │
│  Output: A* = best macro-action sequence                 │
│          sg = first_predicted_state(A*₁)  ← SUBGOAL     │
└────────────────────────┬─────────────────────────────────┘
                         │  subgoal sg
                         ▼
┌──────────────────────────────────────────────────────────┐
│  L1: Low-Level World Model  (hwm-planner-agent)          │
│                                                          │
│  Operates on:  tool calls (primitive actions)            │
│  Horizon:      K = 4 primitive steps (= step_skip)       │
│  Candidates:   N = 10 action sequences                   │
│  Target:       subgoal sg (NOT the final goal)           │
│  Predicts:     tool-level state transitions              │
│                                                          │
│  Output: P* = best primitive action sequence             │
│          execute P*[0] only → replan next step           │
└──────────────────────────────────────────────────────────┘
```

---

## SkillOS Mapping

The HWM concepts map directly onto SkillOS's markdown-driven execution model:

| HWM concept | SkillOS equivalent |
|---|---|
| Observation / state `s` | Execution state in `projects/[P]/state/world_state.md` |
| Latent encoding `z` | Structured YAML world state description |
| Goal `g` | User goal string |
| **L2 world model** | LLM reasoning over skill-level transitions |
| **L1 world model** | LLM reasoning over tool-level transitions |
| Macro-action | Skill invocation (e.g., `knowledge-ingest-agent`) |
| Primitive action | Tool call (Read, Write, Bash, Task, WebFetch…) |
| `step_skip = 4` | 4 primitive tool calls per macro-action |
| **Subgoal `sg`** | `state/subgoal.md` — first L2 predicted state |
| MPPI optimization | N=10 candidate sequences ranked by cost |
| Cost function | Semantic distance from predicted state to goal |
| Final transition steps | `flat-planner-agent` for last 3 steps near goal |
| Replanning | Triggered on divergence > 0.3 or 3-step stagnation |

---

## Algorithm

### Phase 1: Encode World State

Create or update `projects/[Project]/state/world_state.md`:

```yaml
timestamp: "2026-04-08T12:00:00Z"
level: "L2"
description: "3 raw sources exist; wiki not yet built; goal is to produce a knowledge base"
artifacts:
  - path: "projects/MyKB/raw/paper1.pdf"
    type: "input"
    summary: "Source paper on transformers"
skills_invoked: []
pending_capabilities: [knowledge-ingest-agent, knowledge-compile-agent]
goal_distance: 0.9    # far from goal
confidence: 0.8
```

### Phase 2: L2 Macro-Planning

Generate 10 candidate skill sequences, simulate each with the L2 world model, pick the best:

```
Candidate 1: [knowledge-ingest-agent, knowledge-compile-agent, knowledge-query-agent]
  Simulate: after ingest → wiki has summaries → cost 0.5
            after compile → wiki complete → cost 0.2
            after query → Q&A ready → cost 0.05
  Total cost: 1.0 * 0.05 + 0.3 * mean(0.5, 0.2) = 0.155  ← BEST

Candidate 2: [knowledge-compile-agent, knowledge-ingest-agent, ...]
  Simulate: compile before ingest → wiki empty → cost 0.9
  Total cost: 0.9 + ... = 0.72  (worse)

→ A* = [knowledge-ingest-agent, knowledge-compile-agent, knowledge-query-agent]
→ sg = "wiki has summaries for all 3 sources, _index.md updated"
```

### Phase 3: Subgoal Extraction

Save subgoal to `projects/[Project]/state/subgoal.md`:

```yaml
created_at: "2026-04-08T12:00:01Z"
source_macro_action: "knowledge-ingest-agent"
description: "wiki/ has summaries for all 3 raw sources; _index.md is updated"
target_artifacts:
  - "projects/MyKB/wiki/summaries/paper1.md"
  - "projects/MyKB/wiki/_index.md"
estimated_macro_steps_remaining: 2
```

### Phase 4: L1 Primitive Planning

Plan tool calls to reach the subgoal (not the final goal):

```
Target: subgoal = "wiki has summaries for 3 sources"

Candidate 1: [Read(paper1.pdf), Write(wiki/summaries/paper1.md), ...]
  Simulate: after Read → content available → cost 0.7
            after Write → summary exists → cost 0.4
  Total cost: 0.155  ← BEST

→ P* = [Read(paper1.pdf), Write(wiki/summaries/paper1.md), ...]
→ Execute P*[0] = Read("projects/MyKB/raw/paper1.pdf")
```

### Phase 5: Execute and Replan

```
Execute: Read("projects/MyKB/raw/paper1.pdf")
Observe new state → update world_state.md
  goal_distance: 0.85  (small improvement — one source read)

Divergence check: predicted "content available" → actual "content available" → 0.0 ✓
Stagnation check: goal_distance improved (0.9 → 0.85) ✓
Steps remaining: 9 > final_trans_steps(3) → continue with HWM

→ L1 plan again toward same subgoal
→ Execute next primitive action: Write("wiki/summaries/paper1.md", ...)
→ ... repeat until subgoal reached
→ Subgoal reached → run L2 again → new subgoal from A*₂
→ ... repeat until goal reached or steps ≤ 3 → switch to flat-planner
```

---

## State Files

| File | Written by | Purpose |
|------|-----------|---------|
| `state/world_state.md` | HWM planner (every step) | Current latent state encoding |
| `state/subgoal.md` | HWM planner (every L2 cycle) | Active L1 target |
| `state/planning_trace.md` | HWM planner (every step) | Prediction vs. actual log |
| `state/plan.md` | System-agent | Full macro-action plan |

---

## Selector Heuristic

The system-agent picks the planner automatically:

| Condition | Planner |
|-----------|---------|
| Goal has ≥ 3 inferred steps | `hwm-planner-agent` |
| Goal is simple / 1–2 steps | `flat-planner-agent` |
| Currently in final transition (≤ 3 steps from goal) | `flat-planner-agent` |
| HWM stagnation after 3 cycles | Escalate to system-agent for diagnosis |

---

## Configuration

Override defaults in the Task tool prompt or via `state/constraints.md`:

```yaml
hwm_config:
  step_skip: 4           # primitive actions per macro-action
  horizon_L2: 8          # max macro-steps in L2 plan
  horizon_L1: 4          # max primitive steps in L1 plan
  n_candidates: 10       # candidate sequences per MPPI iteration
  replan_every: 1        # replan after N executed actions
  final_trans_steps: 3   # switch to flat planner this many steps from goal
  goal_distance_threshold: 0.1
  divergence_threshold: 0.3
  stagnation_window: 3   # steps without improvement before escalation
```

---

## Planning Trace

Every planning step is logged in `state/planning_trace.md` for debugging and memory consolidation:

```markdown
## Step 1 — 2026-04-08T12:00:01Z

**Phase**: L2 Macro-Planning
**Current state**: 3 raw sources unprocessed; wiki empty
**Goal distance**: 0.90
**Active subgoal**: n/a (first L2 cycle)

### L2 Candidates (top 3)
| Rank | Macro-action | Predicted state | Cost |
|------|-------------|-----------------|------|
| 1 | knowledge-ingest-agent | wiki has 3 summaries | 0.155 |
| 2 | knowledge-compile-agent | wiki empty (premature) | 0.720 |
| 3 | memory-analysis-agent | no progress on wiki | 0.900 |

**Selected**: knowledge-ingest-agent
**Subgoal**: wiki has summaries for all 3 raw sources

### L1 Candidates (top 3)
| Rank | Tool call | Predicted state | Cost |
|------|-----------|-----------------|------|
| 1 | Read(raw/paper1.pdf) | paper1 content available | 0.155 |

**Selected action**: Read("projects/MyKB/raw/paper1.pdf")

### Execution Result
**Predicted**: paper1 content available in memory
**Actual**: paper1 content available in memory
**Divergence**: 0.00
**Replanning triggered**: no
```

---

## Skills Reference

| Skill | Location | When used |
|-------|----------|-----------|
| `hwm-planner-agent` | `system/skills/planning/hwm/` | Complex goals (≥ 3 steps) |
| `flat-planner-agent` | `system/skills/planning/flat/` | Simple goals, final transition |

Both skills extend `planning/base`, which defines the shared MPPI protocol, world state schema,
cost function, and replanning trigger definitions.

---

## Further Reading

- HWM paper: arXiv:2604.03208
- HWM reference implementation: https://github.com/kevinghst/HWM_PLDM
- Planning domain base: `system/skills/planning/base.md`
- Full HWM spec: `system/skills/planning/hwm/hwm-planner-agent.md`
