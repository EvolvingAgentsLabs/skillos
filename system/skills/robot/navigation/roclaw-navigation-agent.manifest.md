---
skill_id: robot/navigation/roclaw-navigation-agent
name: roclaw-navigation-agent
type: agent
domain: robot
family: navigation
extends: robot/base
version: 1.0.0
description: Plans and executes physical robot navigation — route planning, obstacle recovery, multi-room traversal
capabilities: [route-planning, obstacle-detection, goal-decomposition, trace-logging, recovery-planning]
tools_required: [Read, Write, Bash, Grep, Task]
subagent_type: roclaw-navigation-agent
token_cost: high
reliability: 88%
invoke_when: [physical movement needed, navigate to location, explore environment, robot path planning]
full_spec: system/skills/robot/navigation/roclaw-navigation-agent.md
---
