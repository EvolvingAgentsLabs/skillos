---
name: autoresearch-task
version: v1
description: >
  Autonomous ML experimentation loop inspired by Karpathy's autoresearch:
  a HypothesisAgent proposes changes, ImplementationAgent edits code,
  ExperimentAgent runs timed training, EvaluationAgent measures improvement,
  and the loop iterates within a fixed compute budget — git-committing every win.
delegation_pattern: autonomous_feedback_loop
error_recovery: revert_and_continue
agents_required:
  - hypothesis-agent
  - implementation-agent
  - experiment-agent
  - evaluation-agent
  - journal-agent
---

# AutoResearch Task: Autonomous ML Experimentation Loop

## Scenario Overview

Implements Andrej Karpathy's autoresearch pattern inside SkillOS: an autonomous
agent loop that proposes hypotheses, modifies a single training script, runs
timed experiments, evaluates results against a scalar metric, and commits
improvements — iterating until a compute budget is exhausted.

**~12 experiments/hour on one GPU. ~100 experiments overnight.**

## Core Design Principles (Karpathy's Three Primitives)

| Primitive | Value | Rationale |
|---|---|---|
| **One Editable Asset** | `train.py` (or any single script) | Keeps search space interpretable; every hypothesis is a diff |
| **One Scalar Metric** | `val_bpb` or user-defined metric | Enables fair comparison across all experiments |
| **Time-Boxed Cycles** | Fixed duration per experiment (e.g., 5 min) | Ensures comparability across hardware |

## The Autonomous Research Loop

```
┌─────────────────────────────────────────────────────┐
│              AUTORESEARCH LOOP (×N cycles)           │
│                                                      │
│  ┌─────────────┐                                     │
│  │  Hypothesis  │ ← reads state/experiment_log.md   │
│  │    Agent    │   + program.md (research direction) │
│  └──────┬──────┘                                     │
│         ↓ proposed diff                              │
│  ┌─────────────┐                                     │
│  │   Impl.     │ edits train.py                      │
│  │    Agent    │                                     │
│  └──────┬──────┘                                     │
│         ↓ modified train.py                          │
│  ┌─────────────┐                                     │
│  │  Experiment │ runs: `python train.py`             │
│  │    Agent    │ time-boxed to N minutes             │
│  └──────┬──────┘                                     │
│         ↓ metrics output                             │
│  ┌─────────────┐                                     │
│  │  Evaluation │ compare metric vs. baseline         │
│  │    Agent    │ KEEP if improved, REVERT if not     │
│  └──────┬──────┘                                     │
│         ↓ if improved                                │
│  ┌─────────────┐                                     │
│  │   Journal   │ git commit + update experiment_log  │
│  │    Agent    │                                     │
│  └─────────────┘                                     │
│         ↓                                            │
│    [loop until budget exhausted]                     │
└─────────────────────────────────────────────────────┘
```

## Project Structure

```
projects/Project_autoresearch/
├── input/
│   ├── train.py              # The single editable training script
│   ├── program.md            # Research direction and constraints (human-edited)
│   └── data/                 # Training data
├── components/agents/
│   ├── hypothesis-agent.md
│   ├── implementation-agent.md
│   ├── experiment-agent.md
│   ├── evaluation-agent.md
│   └── journal-agent.md
├── state/
│   ├── experiment_log.md     # All experiments: hypothesis, result, decision
│   ├── baseline_metric.json  # Best metric value so far
│   ├── current_cycle.json    # Loop counter and budget remaining
│   └── hypothesis_history.md # What's been tried (prevents repeats)
├── output/
│   ├── best_train.py         # Current best-performing version
│   ├── research_report.md    # Final summary of all discoveries
│   └── experiment_journal/   # Per-experiment records
└── memory/
    ├── short_term/
    └── long_term/
```

## program.md (Research Direction File)

Humans write this. Agents read it. Example:

```markdown
# Research Direction

## Goal
Improve validation bits-per-byte (val_bpb) on the character language model
in train.py, running on a single GPU with 5-minute training windows.

## What You Can Modify
- Learning rate schedule and warmup
- Batch size and gradient accumulation
- Model architecture (layers, heads, hidden dim)
- Optimizer parameters (beta1, beta2, weight decay)
- Tokenization approach
- Regularization (dropout, label smoothing)

## What You Cannot Modify
- Training data source
- Maximum sequence length (keep at 256)
- Total training time per run (5 minutes)

## Metric
Lower val_bpb is better. Baseline: 1.247

## Strategy Notes
- Try learning rate changes first (cheapest wins historically)
- Architecture changes are riskier — require stronger improvement to keep
- Document why you think each hypothesis will work
```

## Agent Specifications

### HypothesisAgent
**Tools**: Read, Write

1. Read `state/experiment_log.md` (past experiments and outcomes)
2. Read `state/hypothesis_history.md` (what's been tried)
3. Read `input/program.md` (research direction and constraints)
4. Read current `input/train.py` (understand current state)
5. Propose ONE specific hypothesis:
   - What to change and why
   - Expected improvement and reasoning
   - Risk level (LOW/MEDIUM/HIGH)
6. Write `state/current_hypothesis.md`

**Hypothesis format:**
```markdown
## Hypothesis #[N]
**Change**: Reduce learning rate from 3e-4 to 1e-4 with cosine decay
**Reasoning**: Current LR may be too high for final convergence phase
**Expected delta**: -0.02 to -0.05 val_bpb (1-4% improvement)
**Risk**: LOW (easily reversible)
**Code location**: line 47, `lr = 3e-4`
```

### ImplementationAgent
**Tools**: Read, Edit, Write

1. Read `state/current_hypothesis.md`
2. Read current `input/train.py`
3. Apply the proposed change as a minimal, clean edit
4. Verify the edit is syntactically valid (no broken indentation, etc.)
5. Write change summary to `state/current_diff.md`

**Constraints:**
- Make the smallest possible change that tests the hypothesis
- Never modify more than one variable per experiment
- Preserve all comments and formatting

### ExperimentAgent
**Tools**: Bash, Write

1. Read `state/current_cycle.json` for time budget
2. Run the experiment with timeout:
   ```bash
   timeout [N_minutes]m python input/train.py 2>&1 | tee state/run_output.log
   ```
3. Extract final metric from output log
4. Write `state/experiment_result.json`:
   ```json
   {
     "cycle": 12,
     "metric": 1.231,
     "runtime_seconds": 298,
     "status": "completed",
     "final_log_line": "step 1200 | loss 1.231 | ..."
   }
   ```

**Error recovery:**
- Training crash → write status: "failed", revert code, continue loop
- Timeout exceeded → record partial metric if available, revert, continue
- OOM error → flag as HIGH_RISK, skip similar hypotheses

### EvaluationAgent
**Tools**: Read, Write

1. Read `state/experiment_result.json`
2. Read `state/baseline_metric.json`
3. Compare: `improvement = baseline - result_metric`
4. Decision logic:
   - `improvement > 0.005` (>0.4%) → **KEEP**: update baseline, proceed to JournalAgent
   - `improvement > 0` but small → **KEEP if LOW risk**, **REVERT if MEDIUM/HIGH risk**
   - `improvement <= 0` → **REVERT**: restore previous train.py via git
5. Write `state/evaluation_decision.md`

**REVERT procedure:**
```bash
git checkout HEAD -- input/train.py
```

### JournalAgent
**Tools**: Bash, Read, Write

1. Read evaluation decision (KEEP path only)
2. Copy current `input/train.py` to `output/best_train.py`
3. Update `state/baseline_metric.json` with new best
4. Append to `state/experiment_log.md`
5. Write per-experiment record to `output/experiment_journal/cycle_[N].md`
6. Git commit with structured message:
   ```bash
   git add input/train.py state/experiment_log.md
   git commit -m "exp[N]: [hypothesis summary] | val_bpb: [old] → [new] (-[delta])"
   ```
7. Update loop counter in `state/current_cycle.json`

## Loop Orchestration

**SystemAgent** controls the outer loop:

```
initialize:
  - record baseline metric (run train.py once)
  - set current_cycle = 0, budget = N_experiments

while current_cycle < budget:
  1. invoke HypothesisAgent
  2. invoke ImplementationAgent
  3. invoke ExperimentAgent
  4. invoke EvaluationAgent
  5. if KEEP: invoke JournalAgent
  6. increment current_cycle
  7. log memory entry

finalize:
  - invoke ReportAgent (summarize all experiments)
  - consolidate learnings to long_term memory
```

## Final Report

After all cycles, **ReportAgent** generates:

```markdown
# AutoResearch Report — [Project Name]

## Summary
- Cycles run: 47 / 50
- Experiments succeeded: 44 (3 crashed)
- Improvements found: 8
- Total metric improvement: 1.247 → 1.181 (5.3% gain)

## Git Experiment Journal
| Cycle | Hypothesis | Before | After | Delta |
|---|---|---|---|---|
| 3 | LR 3e-4 → 1e-4 | 1.247 | 1.231 | -0.016 |
| 7 | Add warmup 100 steps | 1.231 | 1.218 | -0.013 |
| 15 | Increase layers 4→6 | 1.218 | 1.201 | -0.017 |
...

## Best Configuration (vs Baseline)
[diff of final train.py vs original]

## Top Discoveries
1. Learning rate 1e-4 with cosine decay: biggest single win (-0.016)
2. Warmup steps consistently help: +0.013 improvement
3. Layer depth increase effective when LR already tuned

## Failed Hypotheses (with reasoning)
- Dropout 0.1→0.2: increased val_bpb (+0.008) — likely underfitting
- Batch size 32→64: OOM on target GPU — skip for this hardware

## Recommendations for Next Run
- Start with LR range [8e-5, 2e-4] — promising zone identified
- Try attention head count variations (not yet explored)
- Consider gradient clipping (not tested)
```

## Error Recovery

| Error | Action |
|---|---|
| Training crash | Revert train.py, log failure, continue loop |
| OOM | Revert, flag hypothesis as hardware-incompatible |
| Metric regression | Revert, log as negative result (still valuable) |
| Git conflict | Reset to last known good state |
| Budget exhausted mid-run | Finalize with experiments completed so far |

## Success Criteria

- Loop runs for at least 80% of budgeted cycles
- At least 1 improvement found per 10 cycles on average
- Final metric beats baseline by > 1%
- Git log has clean, structured commit history
- Final report clearly documents all discoveries

## Adapting to Other Domains

This pattern applies to any domain with a runnable script + scalar metric:

| Domain | Editable File | Metric |
|---|---|---|
| ML training | `train.py` | val_bpb / val_loss |
| Compiler optimization | `compile_flags.sh` | binary size / run time |
| Web performance | `nginx.conf` | p99 latency |
| Prompt engineering | `system_prompt.md` | task accuracy score |
| Algorithm tuning | `solver.py` | solution quality / time |
| Database queries | `queries.sql` | execution time |

## Usage

```bash
# Run autoresearch on a training script
skillos execute: "Run autoresearch on input/train.py for 50 cycles, optimizing val_bpb — follow the program.md research direction"

# With custom compute budget
skillos execute: "Run autoresearch overnight: 100 experiment cycles on train.py, 5-minute budget per experiment, commit all improvements to git"

# On prompt engineering
skillos execute: "Run autoresearch on system_prompt.md to maximize task accuracy score — 20 cycles, modify only the prompt wording"

# Resume from checkpoint
skillos execute: "Resume autoresearch from cycle 23 in projects/Project_autoresearch/ — continue until cycle 50"
```
