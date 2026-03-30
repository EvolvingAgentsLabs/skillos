---
domain: project
skill_count: 2
base: system/skills/project/base.md
---

# Project Domain Index

Skills for project initialization, directory scaffolding, and skill package management.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| project-scaffold-tool | scaffold | _(tool, no subagent)_ | new project creation, project structure missing | project/scaffold/project-scaffold-tool.manifest.md |
| skill-package-manager-tool | packages | _(tool, no subagent)_ | install skill, search capability, capability gap detected | project/packages/skill-package-manager-tool.manifest.md |

## Routing Notes
- Every new goal execution → `project-scaffold-tool` to ensure project structure exists.
- Missing capability detected → `skill-package-manager-tool` for on-demand skill acquisition.
- Reads `system/sources.list`, writes to `system/packages.lock`.
