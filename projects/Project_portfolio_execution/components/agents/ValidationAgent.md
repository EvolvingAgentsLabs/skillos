---
name: ValidationAgent
type: dynamic
project: Project_portfolio_execution
capabilities:
  - Verification
  - Test execution
  - Reference integrity
tools:
  - Bash
  - Grep
  - Glob
---

# Validation Agent

Specialized agent for verifying that CUT operations didn't break references and DEVELOP operations compile correctly.

## Context
- Parent trace: tr_portfolio_execution_20260426
- Goal: Verify integrity after pruning and development
- Constraints: C25 (don't diverge test from prod)

## Task
1. Verify no remaining imports/references to deleted files
2. Run llm_os Rust compilation check
3. Run llm_os grammar fixtures
4. Verify promote_traces.py syntax
