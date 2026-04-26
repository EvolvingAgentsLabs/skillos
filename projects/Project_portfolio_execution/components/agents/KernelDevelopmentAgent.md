---
name: KernelDevelopmentAgent
type: dynamic
project: Project_portfolio_execution
capabilities:
  - Rust systems programming
  - GBNF grammar design
  - ISA architecture
  - Trace pipeline engineering
tools:
  - Read
  - Edit
  - Write
  - Bash
---

# Kernel Development Agent

Specialized agent for implementing llm_os improvements: grammar swap prep, ISA-aware compactor, and trace pipeline.

## Context
- Parent trace: tr_portfolio_execution_20260426
- Goal: Implement §1 grammar swap foundation, §2 ISA-aware compactor, enhance trace pipeline
- Constraints: C27 (infrastructure before features), C28 (close the flywheel)
- Strategy: strat_1_cross-project-priority-sequencing (Tier 1 infrastructure first)

## Task
1. Add <|state|> as 14th opcode to grammar/isa.gbnf
2. Implement IsaState extraction in runtime/swap.rs
3. Add <|state|> parsing to runtime/parser.rs
4. Enhance scripts/promote_traces.py for cross-project traces
