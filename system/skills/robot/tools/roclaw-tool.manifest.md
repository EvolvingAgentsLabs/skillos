---
skill_id: robot/tools/roclaw-tool
name: roclaw-tool
type: tool
domain: robot
family: tools
extends: robot/base
version: 1.0.0
description: HTTP bridge to RoClaw's 9 robot tools — go_to, explore, stop, get_status, and more
capabilities: [go_to, explore, stop, get_status, get_camera, rotate, move_arm, open_claw, close_claw]
tools_required: [Bash, Read, Write]
subagent_type: null
token_cost: low
reliability: 88%
invoke_when: [send command to robot, move robot, query robot state, camera feed needed]
full_spec: system/skills/robot/tools/roclaw-tool.md
---
