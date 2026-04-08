---
skill_id: planning/flat/flat-planner-agent
name: flat-planner-agent
type: agent
domain: planning
family: flat
extends: planning/base
version: 1.0.0
description: >
  Flat single-level planner. Directly optimizes primitive actions toward the goal
  without hierarchical decomposition. Used for simple/short-horizon goals and as
  the final-transition planner in HWM's Stage 2.
capabilities:
  - single-level-planning
  - primitive-action-optimization
  - goal-direct-execution
tools_required: [Read, Write, Bash, Task, Glob, Grep]
subagent_type: flat-planner-agent
token_cost: low
reliability: 85%
invoke_when:
  - simple goals with 1-3 steps
  - final-transition phase of HWM (last few steps near goal)
  - HWM overhead not justified
full_spec: system/skills/planning/flat/flat-planner-agent.md
---
