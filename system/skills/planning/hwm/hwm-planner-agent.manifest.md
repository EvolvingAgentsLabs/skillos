---
skill_id: planning/hwm/hwm-planner-agent
name: hwm-planner-agent
type: agent
domain: planning
family: hwm
extends: planning/base
version: 1.0.0
description: >
  Hierarchical Planning with Latent World Models. Two-level planner: L2 high-level
  macro-planner generates subgoals via long-horizon world model; L1 low-level
  primitive-planner executes toward each subgoal using short-horizon world model.
capabilities:
  - hierarchical-goal-decomposition
  - subgoal-generation
  - world-model-simulation
  - mppi-style-optimization
  - bilevel-planning
  - replanning-on-divergence
tools_required: [Read, Write, Bash, Task, Glob, Grep]
subagent_type: hwm-planner-agent
token_cost: medium
reliability: 90%
invoke_when:
  - system-agent planning phase for complex goals
  - multi-step long-horizon task execution
  - subgoal decomposition improves success rate
  - task requires more than 3 sequential skill invocations
paper: "Hierarchical Planning with Latent World Models"
arxiv: "2604.03208"
authors: "Wancong Zhang, Basile Terver, Artem Zholus, et al. (Meta FAIR / NYU)"
full_spec: system/skills/planning/hwm/hwm-planner-agent.md
---
