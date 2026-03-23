---
name: autoresearch
complexity: expert
pattern: autonomous-feedback-loop
estimated_cost: compute-bound (not LLM-bound)
inspired_by: Andrej Karpathy's autoresearch (github.com/karpathy/autoresearch)
---

# AutoResearch: Autonomous ML Experimentation Loop

> "You go to sleep, it runs ~100 experiments, and you wake up to a git log
> of everything that worked." — Andrej Karpathy, March 2026

Karpathy's autoresearch is an autonomous agent loop that treats ML training
like a search problem: propose a hypothesis, run the experiment, keep it if
it improves the metric, discard it if not, repeat.

SkillOS maps directly onto this pattern — agents are markdown specs, the loop
is orchestrated by SystemAgent, and the git log becomes the experiment journal.

---

## The Concept

**Three primitives, one elegant loop:**

```
One Editable Asset   →  train.py  (every hypothesis is a diff)
One Scalar Metric    →  val_bpb   (vocabulary-size independent)
Time-Boxed Cycles    →  5 min/run (comparable across hardware)
```

**The loop:**

```
hypothesis → edit code → run experiment → measure metric
     ↑                                          ↓
     └── KEEP (commit) ←── better? ────── REVERT (try again)
```

**Results from Karpathy's own run:**
- 50 overnight experiments → 11% training speedup
- Shopify CEO: 37 experiments → 19% validation improvement
- 700-experiment run: dropped Time-to-GPT-2 from 2.02h → 1.80h

---

## Running in SkillOS

### Step 1 — Prepare your project

```
projects/Project_autoresearch/
└── input/
    ├── train.py       ← your training script
    └── program.md     ← your research direction
```

**Minimal `program.md`:**
```markdown
# Research Direction
## Goal
Improve val_bpb on train.py using a single GPU, 5-minute windows.
## What to modify
Learning rate, batch size, optimizer params, architecture depth.
## What NOT to modify
Data source, sequence length (keep 256), run time per experiment.
## Metric
Lower val_bpb is better. Baseline: [measure this first].
```

### Step 2 — Boot and execute

```bash
boot skillos

skillos execute: "Run autoresearch on input/train.py for 50 cycles using the program.md research direction. Use 5-minute training windows, commit every improvement to git."
```

### Step 3 — Watch it work

SkillOS will:

1. Run a baseline measurement of `train.py`
2. Start the autonomous loop:
   - **HypothesisAgent** proposes one change (reads past experiments to avoid repeats)
   - **ImplementationAgent** edits `train.py` with the minimal diff
   - **ExperimentAgent** runs `python train.py` with a timeout
   - **EvaluationAgent** compares metric vs. baseline
   - **JournalAgent** commits wins, reverts losses
3. After N cycles, **ReportAgent** summarizes everything

### Step 4 — Wake up to your git log

```
$ git log --oneline
a3f9c12 exp[23]: cosine LR decay | val_bpb: 1.218 → 1.201 (-0.017)
7b2e441 exp[15]: layers 4→6 | val_bpb: 1.231 → 1.218 (-0.013)
c91d83f exp[03]: LR 3e-4 → 1e-4 | val_bpb: 1.247 → 1.231 (-0.016)
```

---

## What SkillOS Adds

| Karpathy's autoresearch | SkillOS autoresearch |
|---|---|
| Fixed agent behavior in code | Agents defined as editable markdown specs |
| Single-purpose (LLM training) | Any domain with a script + scalar metric |
| Python codebase to modify | Modify agent markdown specs to change behavior |
| One loop controller | SystemAgent orchestrates with full state management |
| Results in git log | Results in git log + structured memory + long-term learnings |
| Rerun from scratch | Resume from checkpoint via state files |

---

## Variations

### Prompt Engineering AutoResearch

```bash
# Optimize a system prompt autonomously
skillos execute: "Run autoresearch on system_prompt.md for 20 cycles — each cycle edits the prompt and measures task accuracy on evaluation_set.json. Commit every improvement."
```

**program.md:**
```markdown
## Goal: Maximize accuracy on evaluation_set.json
## Editable file: system_prompt.md
## Metric: correct_answers / total_questions (higher is better, baseline: 0.71)
## What to modify: wording, structure, examples in the prompt
## What NOT to modify: format constraints or tool instructions
```

### Algorithm Tuning AutoResearch

```bash
# Optimize a sorting/search algorithm
skillos execute: "Run autoresearch on solver.py for 30 cycles to minimize solution time on benchmark_inputs/. Each experiment runs: python benchmark.py. Commit improvements."
```

### Web Config AutoResearch

```bash
# Optimize nginx configuration
skillos execute: "Run autoresearch on nginx.conf for 15 cycles, measuring p99 latency via: python benchmark_latency.py. program.md has constraints on what to modify."
```

### Multi-Metric AutoResearch

```bash
# Optimize for a combined metric
skillos execute: "Run autoresearch on train.py for 40 cycles optimizing a weighted metric: 0.7 * accuracy + 0.3 * (1 / inference_time_ms). Record all tradeoffs."
```

---

## How the Loop Runs in SkillOS

The autonomous loop uses 5 specialized agents and a coordinator:

```
SystemAgent (loop controller)
    ├── HypothesisAgent     reads logs, proposes next experiment
    ├── ImplementationAgent edits the target file
    ├── ExperimentAgent     runs the script (Bash with timeout)
    ├── EvaluationAgent     compares metric, decides keep/revert
    └── JournalAgent        commits wins, logs everything
```

State persists in `projects/[ProjectName]/state/`:
- `experiment_log.md` — full history of all hypotheses and outcomes
- `baseline_metric.json` — current best score
- `current_cycle.json` — loop counter and remaining budget
- `hypothesis_history.md` — prevents re-testing the same idea

This means the loop is **resumable** — if you stop mid-run, SkillOS can
pick up exactly where it left off:

```bash
skillos execute: "Resume autoresearch from where it stopped in projects/Project_autoresearch/"
```

---

## Expected Outputs

```
projects/Project_autoresearch/output/
├── research_report.md          # Full summary: all experiments, wins, insights
├── best_train.py               # The current best-performing version
└── experiment_journal/
    ├── cycle_03.md             # Per-cycle records
    ├── cycle_07.md
    └── ...
```

**Git log** (the living experiment journal):
```
exp[N]: [hypothesis] | metric: [before] → [after] ([delta])
```

---

## Learning Objectives

- Understand how SkillOS implements Karpathy's three-primitive design
- See how a feedback loop maps to sequential agent invocations
- Learn how state files enable loop resumption and hypothesis deduplication
- Observe git as a structured experiment journal
- Understand how to adapt the pattern to non-ML domains

---

## Full Scenario Reference

See `scenarios/AutoResearch_Task.md` for the complete agent specifications,
state file formats, loop orchestration logic, and error recovery procedures.
