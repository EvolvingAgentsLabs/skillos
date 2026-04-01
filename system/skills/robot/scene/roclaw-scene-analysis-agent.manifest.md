---
skill_id: robot/scene/roclaw-scene-analysis-agent
name: roclaw-scene-analysis-agent
type: agent
domain: robot
family: scene
extends: robot/base
version: 1.0.0
description: VLM-based scene interpretation — semantic mapping, object identification, obstacle classification
capabilities: [scene-analysis, semantic-mapping, object-detection, environment-classification, obstacle-identification]
tools_required: [Read, Write, Bash, Grep]
subagent_type: roclaw-scene-analysis-agent
token_cost: medium
reliability: 90%
invoke_when: [camera feed analysis, obstacle encountered, build semantic map, understand environment]
full_spec: system/skills/robot/scene/roclaw-scene-analysis-agent.md
---
