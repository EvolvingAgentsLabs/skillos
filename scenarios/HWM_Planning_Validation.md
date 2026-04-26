---
name: hwm-planning-validation-scenario
description: >
  End-to-end test of HWM Hierarchical Planning integration (PR #15).
  Tests the full planning domain: SkillIndex routing, planner selector heuristic,
  HWM two-level planning (L2 macro → subgoal → L1 primitive), flat planner fallback,
  replanning triggers, state file management, and system-agent Step 2b integration.
version: "1.0"
difficulty: intermediate
estimated_duration_minutes: 12
mode: EXECUTION
prerequisites:
  - PR #15 HWM planning domain merged or branch checked out
  - system/skills/planning/ directory exists with base.md, index.md, hwm/, flat/
  - system/skills/SkillIndex.md contains planning domain (total_skills ≥ 27)
paper: "arXiv 2604.03208 — Hierarchical Planning with Latent World Models (HWM)"
---

# HWM Planning Validation Scenario

## Overview

This scenario validates the full HWM hierarchical planning integration from PR #15:

1. **SkillIndex Routing** — planning domain discovered via 4-step lazy loading
2. **Planner Selector** — complex goals → HWM, simple goals → flat
3. **HWM Two-Level Planning** — L2 macro-planner, subgoal extraction, L1 primitive planner
4. **Flat Planner** — single-level fallback for simple goals
5. **State File Management** — world_state.md, subgoal.md, planning_trace.md
6. **System-Agent Step 2b** — HWM integrated before skill routing
7. **Health Checks** — hwm_planning_trace_complete, hwm_goal_distance_converged

---

## Phase 1: SkillIndex Routing + Planner Selection

### Step 1.1: Verify planning domain exists in SkillIndex

```
Action: Read system/skills/SkillIndex.md
Verify:
  - Domain Table contains row: planning | 2 | system/skills/planning/index.md
  - Quick Skill Lookup contains: hwm-planner-agent, flat-planner-agent
  - total_skills includes the 2 planning skills
```

**Pass criteria**: Both planning skills appear in SkillIndex.

### Step 1.2: Verify 4-step lazy loading chain

```
Action: Read system/skills/planning/index.md
Verify: Lists hwm-planner-agent and flat-planner-agent with manifest paths

Action: Read system/skills/planning/hwm/hwm-planner-agent.manifest.md
Verify: type=agent, full_spec path points to hwm-planner-agent.md

Action: Read system/skills/planning/flat/flat-planner-agent.manifest.md
Verify: type=agent, full_spec path points to flat-planner-agent.md
```

**Pass criteria**: Full 4-step chain resolves for both planners.

### Step 1.3: Test selector heuristic

Apply the routing logic from planning/index.md:

```
Test cases:
  A) Goal: "Build a knowledge wiki about quantum computing, ingest 5 sources, compile, and lint"
     Expected: hwm-planner-agent (> 3 steps, multi-skill orchestration)

  B) Goal: "Read the file README.md and summarize it"
     Expected: flat-planner-agent (≤ 3 steps, simple goal)

  C) Goal: "Write a one-line fix to Boot.md"
     Expected: flat-planner-agent (single step, direct)

  D) Goal: "Research topic, analyze findings, create report, validate, publish"
     Expected: hwm-planner-agent (5+ steps, unclear horizon)
```

**Pass criteria**: All 4 test cases route to the correct planner.

---

## Phase 2: HWM Two-Level Planning (Complex Goal)

Use a test project to exercise the full HWM pipeline.

### Step 2.0: Create test project

```
Action: Create projects/Project_hwm_test/state/ directory
Action: Write projects/Project_hwm_test/state/world_state.md with initial state:

timestamp: [now]
level: "L2"
description: "Fresh project, no artifacts yet"
artifacts: []
skills_invoked: []
pending_capabilities: ["research", "analysis", "compilation", "validation"]
goal_distance: 1.0
confidence: 0.3
```

### Step 2.1: L2 Macro-Planning — generate candidate sequences

Simulate the L2 planner's candidate generation for the goal:
**"Research a topic, analyze findings, compile a report, and validate it"**

```
Generate N=3 candidate macro-action sequences (reduced from 10 for test speed):

Candidate 1: [knowledge-query-agent, memory-analysis-agent, knowledge-compile-agent, validation-agent]
Candidate 2: [knowledge-ingest-agent, knowledge-query-agent, knowledge-compile-agent, validation-agent]
Candidate 3: [knowledge-compile-agent, knowledge-query-agent, validation-agent, knowledge-lint-agent]

For each candidate, predict L2 state transitions:
  - After skill 1: what artifacts exist, goal_distance?
  - After skill 2: what new state?
  - ...

Compute costs:
  total_cost = 1.0 * distance(final_predicted_state, goal)
             + 0.3 * mean(distance(z_t, goal) for all t)

Select A* = argmin(cost)
```

**Pass criteria**:
- At least 3 candidates generated
- Each candidate has a predicted trajectory with costs
- A* selected has lowest total cost
- Output includes macro_plan with skill names and predicted states

### Step 2.2: Subgoal Extraction

```
subgoal = first_predicted_state(A*[0])

Action: Write projects/Project_hwm_test/state/subgoal.md
Verify schema:
  created_at: [timestamp]
  source_planner: "L2"
  description: [natural language — intermediate target after first macro-action]
  target_artifacts: [expected files after first skill completes]
  target_skills_invoked: [first skill name]
  estimated_steps_to_goal: [remaining count]
```

**Pass criteria**: subgoal.md written with valid schema, description is meaningful.

### Step 2.3: L1 Primitive Planning toward subgoal

```
Generate N=3 candidate primitive-action sequences toward the subgoal (not the final goal):

For each candidate:
  Generate sequence of tool calls: [Read, Grep, Write, ...]
  Predict state after each tool call
  Compute cost toward SUBGOAL (not goal)

Select P* = argmin(cost toward subgoal)
Return P*[0] — the next action to execute
```

**Pass criteria**:
- L1 targets the subgoal, NOT the final goal
- Primitive actions are valid tool names (Read, Write, Bash, Glob, Grep, Task)
- P*[0] is a single concrete tool call

### Step 2.4: Planning trace recording

```
Action: Write projects/Project_hwm_test/state/planning_trace.md
Record:
  step: 1
  level: "L1"
  action: [P*[0] tool call]
  predicted_state: [what L1 predicted]
  actual_state: [what actually happened — simulate success]
  divergence: 0.05
  goal_distance: 0.85
```

**Pass criteria**: planning_trace.md contains at least one step record with all fields.

### Step 2.5: World state update

```
Action: Update projects/Project_hwm_test/state/world_state.md
  goal_distance decreased from 1.0
  skills_invoked list updated
  artifacts list updated
```

**Pass criteria**: world_state.md reflects execution progress.

---

## Phase 3: Flat Planner (Simple Goal)

### Step 3.1: Flat planner for simple goal

Apply flat planner to: **"Read README.md and count its lines"**

```
Generate N=3 candidate primitive sequences:
  Candidate 1: [Read README.md, count lines in output]
  Candidate 2: [Bash wc -l README.md]
  Candidate 3: [Glob README.md, Read, count]

Select P* = argmin(cost)
Return P*[0]
```

**Pass criteria**:
- Output has `planner: "flat"` (not "hwm")
- No subgoal.md written (flat planner doesn't generate subgoals)
- Primitive actions are reasonable for the goal

### Step 3.2: Verify no subgoal overhead

```
Verify: projects/Project_hwm_test/state/subgoal.md was NOT updated for this goal
  (flat planner does not write subgoals)
```

**Pass criteria**: subgoal.md unchanged from Phase 2 (or absent if using fresh state).

---

## Phase 4: Replanning Triggers + Final Transition

### Step 4.1: Divergence-triggered replan

Simulate a scenario where actual state diverges from predicted:

```
Step record:
  predicted_state: "knowledge-query-agent returned 5 relevant articles"
  actual_state: "knowledge-query-agent returned 0 articles (KB empty)"
  divergence: 0.8 (> threshold 0.3)

Expected behavior: re-run L2 planning with updated state
```

**Pass criteria**: When divergence > 0.3, system triggers L2 replanning.

### Step 4.2: Stagnation detection

```
Simulate 3 consecutive steps where goal_distance doesn't decrease:
  Step N:   goal_distance = 0.45
  Step N+1: goal_distance = 0.45
  Step N+2: goal_distance = 0.46

Expected behavior: escalate — try alternative macro-actions
```

**Pass criteria**: After 3 stagnant steps, system escalates.

### Step 4.3: Final transition to flat planner

```
Simulate world state near goal:
  remaining_steps ≤ 3 (final_trans_steps default)

Expected behavior: switch from hwm-planner-agent to flat-planner-agent
```

**Pass criteria**: Planner switches from HWM to flat for final steps.

---

## Phase 5: System-Agent Integration + Health Checks

### Step 5.1: Verify Step 2b exists in system-agent

```
Action: Read system/skills/orchestration/core/system-agent.md
Verify:
  - Step 2b "HWM Hierarchical Planning" section exists
  - References planning/index.md for planner selection
  - Describes the 5-step protocol (encode state, L2 plan, extract subgoal, L1 plan, replan check)
  - Note about Step 3 being "informed by HWM macro-action sequence"
```

**Pass criteria**: Step 2b fully present in system-agent spec.

### Step 5.2: Verify health checks

```
Action: Read post_execution_checks in system-agent.md
Verify:
  - "hwm_planning_trace_complete" check exists (reads state/planning_trace.md)
  - "hwm_goal_distance_converged" check exists (reads state/world_state.md, goal_distance ≤ 0.1)
```

**Pass criteria**: Both HWM health checks present.

### Step 5.3: Verify .claude/agents/ discovery

```
Action: Verify .claude/agents/hwm-planner-agent.md exists
Action: Verify .claude/agents/flat-planner-agent.md exists
Action: Verify .claude/agents/system-agent.md contains Step 2b
```

**Pass criteria**: All agent discovery copies are in sync.

---

## Phase 6: Cleanup

```
Action: Remove projects/Project_hwm_test/ (test project)
```

---

## Success Criteria (15 checks)

| # | Check | Phase |
|---|-------|-------|
| 1 | Planning domain in SkillIndex Domain Table | 1.1 |
| 2 | Both planners in Quick Skill Lookup | 1.1 |
| 3 | 4-step lazy loading chain resolves for both planners | 1.2 |
| 4 | Selector routes complex goals to HWM, simple to flat | 1.3 |
| 5 | L2 macro-planner generates candidates with costs | 2.1 |
| 6 | A* selected is lowest-cost candidate | 2.1 |
| 7 | subgoal.md written with valid schema | 2.2 |
| 8 | L1 targets subgoal (not final goal) | 2.3 |
| 9 | planning_trace.md records step with all fields | 2.4 |
| 10 | world_state.md updated after execution | 2.5 |
| 11 | Flat planner returns planner="flat", no subgoal written | 3.1-3.2 |
| 12 | Divergence > 0.3 triggers L2 replan | 4.1 |
| 13 | 3 stagnant steps triggers escalation | 4.2 |
| 14 | Final transition switches to flat planner | 4.3 |
| 15 | System-agent Step 2b + health checks + .claude/agents/ in sync | 5.1-5.3 |
