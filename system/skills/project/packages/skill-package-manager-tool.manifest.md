---
skill_id: project/packages/skill-package-manager-tool
name: skill-package-manager-tool
type: tool
domain: project
family: packages
extends: project/base
version: 1.0.0
description: apt-like skill package manager — install, search, update, list, and remove skills from sources
capabilities: [skill-install, skill-search, skill-update, skill-list, skill-remove, on-demand-acquisition]
tools_required: [Bash, Read, Write, Grep, Glob, WebFetch]
subagent_type: null
token_cost: low
reliability: 88%
invoke_when: [install skill, search for capability, update skills, list installed skills, capability gap detected]
full_spec: system/skills/project/packages/skill-package-manager-tool.md
---
