---
skill_domain: project
type: base-template
version: 1.0.0
---

# Project Domain — Shared Behaviors

All skills in the `project/` domain inherit these conventions.

## Project Naming Convention
Goal content determines project name automatically:
- Format: `projects/Project_[descriptive_name]/`
- "chaos theory tutorial" → `projects/Project_chaos_theory_tutorial/`
- "news intelligence" → `projects/Project_news_intelligence/`

## Standard Project Structure
Every project created must follow this layout:
```
projects/[ProjectName]/
├── components/
│   ├── agents/      # Project-specific agent markdown specs
│   └── tools/       # Project-specific tool markdown specs
├── input/           # Input documents and instructions
├── output/          # Generated outputs and deliverables
├── memory/
│   ├── short_term/  # Agent interactions, session logs
│   └── long_term/   # Consolidated insights
└── state/           # plan.md, context.md, variables.json, history.md, constraints.md
```

## Scaffold Protocol
Use `project/scaffold/project-scaffold-tool` to create the above structure atomically.
Always verify structure exists before execution begins.

## Package Management
Use `project/packages/skill-package-manager-tool` for skill installation.
All installed skills are tracked in `system/packages.lock`.
Sources are configured in `system/sources.list`.
