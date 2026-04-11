---
skill_domain: planning
type: base-template
version: 1.0.0
paper: "Hierarchical Planning with Latent World Models (HWM)"
arxiv: "2604.03208"
---

# Planning Domain — Shared Behaviors

All skills in the `planning/` domain inherit these conventions.
Grounded in the **HWM paper** (Wancong Zhang et al., 2025):
*"A high-level planner optimizes macro-actions using a long-horizon world model to reach the goal;
the first predicted latent state serves as a subgoal for a low-level planner, which optimizes
primitive actions with a short-horizon world model."*

---

## Role

Planning skills are responsible for:
1. Encoding the current world state into a structured latent representation
2. Predicting future states using a world model (LLM reasoning over skills/tools)
3. Optimizing action sequences to minimize distance from predicted state to goal
4. Generating subgoals (intermediate target states) for lower-level execution

---

## World State Representation

Before planning, encode the current execution state as a structured YAML latent vector.
Save to `projects/[Project]/state/world_state.md`.

```yaml
# world_state.md schema
timestamp: ISO string
level: "L2"  # or "L1"
description: string          # one-sentence natural language summary
artifacts:                   # files/outputs that currently exist
  - path: string
    type: "output" | "state" | "memory" | "log"
    summary: string
skills_invoked: []           # list of skill names called so far
pending_capabilities: []     # capabilities still needed to reach goal
goal_distance: float         # 0.0 = goal reached, 1.0 = not started
confidence: float            # planner's confidence in current plan
```

---

## Action Representation

### Macro-Action (L2 — high-level)
A skill invocation. Operates at coarse time scale (`step_skip` macro-steps per L1 cycle).

```yaml
macro_action:
  skill: string              # skill name from SkillIndex
  input_state: string        # encoded L2 state going in
  predicted_next_state: string  # L2's prediction of resulting state
  cost: float                # predicted distance(predicted_state, goal)
```

### Primitive Action (L1 — low-level)
A tool call. Multiple primitive actions compose one macro-action.

```yaml
primitive_action:
  tool: string               # Read | Write | Bash | Task | Glob | Grep | WebFetch
  args: object               # tool arguments
  predicted_next_state: string  # L1's prediction of resulting state
  cost: float
```

---

## Subgoal Protocol

The key HWM innovation: **the first L2 predicted state becomes the L1 target**.

```
subgoal = first_predicted_L2_state(macro_action_1)
```

Save the active subgoal to `projects/[Project]/state/subgoal.md`:

```yaml
# subgoal.md schema
created_at: ISO string
source_planner: "L2"
description: string          # natural language description of intermediate target
target_artifacts: []         # files/outputs that should exist when subgoal is reached
target_skills_invoked: []    # skills that should have run
estimated_steps_to_goal: int # remaining after this subgoal
```

---

## MPPI-Style Optimization

Both L2 and L1 planners use iterative candidate generation and selection,
analogous to Model Predictive Path Integral (MPPI) from the HWM paper.

### Algorithm

```
For n_candidates in range(N):
  Generate candidate action sequence A_n (length = horizon)
  Simulate: predict state trajectory using world model
  Compute cost: sum of distances to subgoal/goal at each step
Select A* = argmin(cost)
Return A*[0]  (execute first action only, then replan)
```

### Parameters (defaults)

```yaml
mppi_config:
  n_candidates: 10           # candidate action sequences per iteration
  horizon_L2: 8              # L2 planning horizon (macro-steps)
  horizon_L1: 4              # L1 planning horizon (step_skip primitive steps)
  replan_every: 1            # replan after every executed action
  final_trans_steps: 3       # switch to flat L1 when this close to goal
  cost_weights:
    terminal: 1.0            # weight on final state distance
    intermediate: 0.3        # weight on intermediate state distances
```

---

## Cost Function

```
cost(trajectory, goal) = terminal_weight * distance(z_T, g)
                       + intermediate_weight * sum(distance(z_t, g) for t in 1..T-1)
```

Where `distance(z, g)` is the semantic similarity between state description `z` and goal `g`,
computed as embedding cosine distance (or LLM-assessed relevance if embeddings unavailable).

---

## Replanning Trigger

Replan when:
- Actual state diverges from predicted state (divergence > threshold)
- A skill invocation fails (error recovery → replan)
- Remaining steps drop below `final_trans_steps` (switch to flat L1)
- `goal_distance` has not decreased for 3 consecutive steps (stagnation)

---

## State Files

| File | Owner | Purpose |
|------|-------|---------|
| `state/world_state.md` | Planning skills | Current latent state encoding |
| `state/subgoal.md` | HWM planner | Active L1 target |
| `state/plan.md` | System-agent | Full execution plan |
| `state/planning_trace.md` | Planning skills | Per-step prediction vs. actual log |
