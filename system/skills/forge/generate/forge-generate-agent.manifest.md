---
skill_id: forge/generate/forge-generate-agent
name: forge-generate-agent
type: agent
domain: forge
family: generate
extends: forge/base
version: 1.0.0
description: Generates new markdown skills, JS skills, subagents, and cartridges to close a capability gap. Runs on Claude Code; outputs artifacts validated against Gemma 4.
capabilities: [skill-generation, subagent-scaffolding, cartridge-drafting, test-case-authoring, js-skill-authoring]
tools_required: [Read, Write, Grep, Glob, Task]
subagent_type: forge-generate-agent
backend: claude-code
target_model: gemma4:e2b
token_cost: high
reliability: n/a
invoke_when: [capability gap detected, no skill matches goal, user requested new skill, new domain needed]
full_spec: system/skills/forge/generate/forge-generate-agent.md
---
