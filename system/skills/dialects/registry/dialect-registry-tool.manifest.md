---
skill_id: dialects/registry/dialect-registry-tool
name: dialect-registry-tool
type: tool
domain: dialects
family: registry
extends: dialects/base
version: 1.0.0
description: Lists, matches, and describes dialects from the registry — lightweight lookup without full compilation
capabilities: [dialect-listing, domain-matching, dialect-metadata, ranked-recommendations]
tools_required: [Read, Grep]
subagent_type: null
token_cost: low
reliability: 92%
invoke_when: [list dialects, match dialect to task, describe dialect, check available compression options]
full_spec: system/skills/dialects/registry/dialect-registry-tool.md
---
