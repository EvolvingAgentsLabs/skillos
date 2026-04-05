---
skill_id: analytics/tabular/git-workflow-agent
name: git-workflow-agent
type: agent
domain: analytics
family: tabular
extends: analytics/base
version: 1.0.0
source: original
description: Automate git workflows — branch creation, commits, PR drafting, changelog generation, conflict detection
capabilities: [git-branch, git-commit, pr-creation, changelog, conflict-detection, code-review-summary]
tools_required: [Bash, Read, Write, Grep, Glob]
subagent_type: git-workflow-agent
token_cost: low
reliability: 92%
invoke_when: [git workflow, create branch, commit changes, make PR, changelog, code review, git automation]
full_spec: system/skills/analytics/tabular/git-workflow-agent.md
---
