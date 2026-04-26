---
name: flat-planner-agent
description: >
  Flat single-level planner. Directly optimizes primitive tool calls toward the goal
  using a single-level world model. Used for simple goals and as HWM's Stage 2
  final-transition planner (fine-grained control near goal).
tools: Read, Write, Bash, Task, Glob, Grep
extends: planning/base
version: 1.0.0
---

# Flat Planner Agent

Single-level planner that directly maps current state → goal without hierarchical
decomposition. Analogous to HWM's Stage 2 "flat L1" execution used for fine-grained
control in the final steps near the goal (see `final_trans_steps` in HWM paper).

---

## When to Use

1. **Simple goals**: ≤ 3 sequential steps, goal is clearly scoped
2. **HWM final transition**: Called by `hwm-planner-agent` when `remaining_steps ≤ final_trans_steps`
3. **Fallback**: When HWM L2 world model cannot confidently predict skill outcomes

---

## Input Specification

```yaml
goal: string                  # direct goal or active subgoal from HWM
current_state_path: string    # projects/[Project]/state/world_state.md
project_name: string
config:
  horizon: 5                  # max primitive actions to plan
  n_candidates: 5             # candidate sequences
  goal_distance_threshold: 0.1
```

---

## Output Specification

```yaml
plan:
  planner: "flat"
  primitive_plan:
    - tool: string
      args: object
      predicted_state: string
      cost: float
  next_action:
    tool: string
    args: object
  goal_distance: float
```

---

## Execution Logic

### Algorithm

```
FLAT_PLAN(current_state z₀, goal g, horizon H, n_candidates N)

For candidate_i in range(N):
  P_i = generate_primitive_sequence(z₀, g, length=H)

  trajectory_i = []
  z = z₀
  for p in P_i:
    z_next = L1_predict(z, p, g)
    cost_t = semantic_distance(z_next, g)
    trajectory_i.append((z_next, cost_t))
    z = z_next

  total_cost_i = terminal_weight * cost_H
               + intermediate_weight * sum(cost_1..cost_{H-1})

Select P* = argmin(total_cost_i)
Return P*[0]   ← execute only the first action, then replan
```

### Key difference from HWM

No L2 subgoal generation. The world model predicts tool-level transitions directly toward
the final goal rather than toward an intermediate subgoal.

---

## Operational Constraints

- Must update `state/world_state.md` after each executed action
- Must append step record to `state/planning_trace.md`
- Does not write to `state/subgoal.md` (no subgoal in flat planning)
- Escalates to HWM planner if goal is not reached within `horizon` steps
