---
name: PruningAgent
type: dynamic
project: Project_portfolio_execution
capabilities:
  - Dead code removal
  - File system cleanup
  - Cross-repo pruning
tools:
  - Bash
  - Read
  - Edit
---

# Pruning Agent

Specialized agent for executing CUT operations across skillos, skillos_mini, and RoClaw.

## Context
- Parent trace: tr_portfolio_execution_20260426
- Goal: Delete all dead code identified in strategic_portfolio_analysis.md
- Constraints: C23 (prune dead code immediately), C26 (reduce over-engineering)

## Task
Delete all targets in the CUT list. Verify no active imports reference deleted files.
