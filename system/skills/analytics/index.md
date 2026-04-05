---
domain: analytics
type: domain-index
version: 1.0.0
total_skills: 2
base: system/skills/analytics/base.md
---

# Analytics Domain Index

Use for: tabular data analysis, git workflow automation, code review.

## Skills

| Skill | Family | subagent_type | Manifest | Token Cost |
|-------|--------|---------------|---------|-----------|
| data-analysis-agent | tabular | data-analysis-agent | system/skills/analytics/tabular/data-analysis-agent.manifest.md | medium |
| git-workflow-agent | tabular | git-workflow-agent | system/skills/analytics/tabular/git-workflow-agent.manifest.md | low |

## Invoke When

- Analysing CSV, JSON, or tabular data files
- Generating charts or statistical summaries
- Automating git operations: branch, commit, PR, changelog
- Reviewing code changes and summarising diffs

## Base Behaviors

Inherited from `system/skills/analytics/base.md`:
- Data path conventions: input/ → output/
- Python via Bash (pandas/numpy/matplotlib)
- Schema inference before analysis
- Source data immutability
