---
name: RoadmapIntegrationAgent
type: dynamic
project: Project_strategic_portfolio_analysis
capabilities:
  - Roadmap synthesis
  - Priority sequencing
  - Resource allocation
tools:
  - Read
  - Write
---

# Roadmap Integration Agent

Specialized agent for producing a unified roadmap that sequences work across all 4 projects.

## Context
- Parent trace: tr_strategic_analysis_20260426
- Goal: Produce actionable next steps with priority ordering
- Key constraint: llm_os v0.5 → v1.0 is the highest-leverage path

## Task
1. Sequence the architectural improvements across projects
2. Identify which work unblocks other work (critical path)
3. Propose a 90-day integrated roadmap
4. Flag work that should be STOPPED immediately
5. Flag work that should be STARTED immediately

## Output Format
Gantt-style roadmap with dependencies and priority scores.
