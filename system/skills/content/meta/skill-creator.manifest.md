---
skill_id: content/meta/skill-creator
name: skill-creator
type: tool
domain: content
family: meta
extends: content/base
version: 1.0.0
source: github:anthropics/skills/skill-creator
description: Bootstrap new SkillOS skills from a template — generates manifest, spec, and base files
capabilities: [skill-scaffolding, manifest-generation, spec-writing, skill-registration]
tools_required: [Read, Write, Bash, Glob]
token_cost: low
reliability: 95%
invoke_when: [create new skill, scaffold skill, add capability, generate agent spec, new tool spec]
full_spec: system/skills/content/meta/skill-creator.md
---
