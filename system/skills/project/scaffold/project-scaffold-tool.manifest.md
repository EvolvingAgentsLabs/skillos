---
skill_id: project/scaffold/project-scaffold-tool
name: project-scaffold-tool
type: tool
domain: project
family: scaffold
extends: project/base
version: 1.0.0
description: Bootstraps the standard project directory structure atomically for any new project
capabilities: [directory-creation, structure-validation, project-initialization]
tools_required: [Bash, Write, Read]
subagent_type: null
token_cost: low
reliability: 95%
invoke_when: [new project creation, project structure missing, project initialization]
full_spec: system/skills/project/scaffold/project-scaffold-tool.md
---
