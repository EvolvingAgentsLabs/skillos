---
name: skill-creator
version: 1.0.0
source_repo: anthropics/skills
source_path: skills/skill-creator/
license: MIT
installed_by: SkillOS
description: Bootstrap new skills from a template — generates manifest, spec, and registers in index
tools: [Read, Write, Bash, Glob]
dependencies: []
---

# Skill Creator (Source)

Raw skill source from `anthropics/skills`.
SkillOS-integrated version: `system/skills/content/meta/skill-creator.md`

## What This Skill Does

Accelerates skill creation by:
- Generating properly formatted manifest + spec files from a description
- Following the project's skill hierarchy conventions
- Registering the new skill in the appropriate domain index
- Optionally copying agent-type skills to `.claude/agents/` for discovery

## Quick Start

Provide:
1. Skill name (kebab-case)
2. Type: agent or tool
3. Domain and family
4. One-line description
5. Key capabilities (comma-separated)

The skill creator generates all required files following the SkillOS 3-level hierarchy:
`system/skills/{domain}/{family}/{name}.manifest.md` + `{name}.md`
