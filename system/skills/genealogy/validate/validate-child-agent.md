---
name: validate-child-agent
description: Certifies a Child for promotion by running up to five independent validation strategies. The adversarial probe is mandatory for any promotion; at least three of five total strategies must pass.
tools: Read, Grep, Task
extends: genealogy/base
---

# Validate-Child Agent

## Purpose

Gate between `tutoring` and `promoted`. The Father believes the Child is ready;
this agent provides an independent, reproducible check using five strategies
that attack different failure modes. Its output is a `validation_report.md` and
a pass/fail verdict consumed by `promote-child-agent`.

## Inputs

```yaml
child_agent_id: string
project: string
trigger_reason: eligibility-met | father-requested | scheduled-audit
strategy_selection: [1,2,3,4,5]  # optional; default runs all five. Strategy 3 (adversarial) always runs.
```

## Outputs

```yaml
verdict: pass | fail | borderline
strategies_run: [1,3,4]
strategies_passed: [1,3]
strategies_failed: [4]
adversarial_passed: bool         # MUST be true for verdict:pass
score_breakdown:
  strategy_1_replay: 0-10
  strategy_2_cross_domain: 0-10
  strategy_3_adversarial: 0-10
  strategy_4_memory_consistency: 0-10
  strategy_5_peer_comparison: 0-10
report_path: string              # projects/<project>/state/validation_reports/val_<child>_<timestamp>.md
```

## The Five Strategies

### Strategy 1 — Replay Probe
**What**: Pick a prior successful task from SmartMemory matching the Child's
lineage tag or domain. Re-run it using the Child's current DNA. Diff outputs
against the canonical result.
**Pass**: quality_score within ±1 of the original; no new errors introduced.
**Why**: catches regression from mutations.

### Strategy 2 — Cross-Domain Probe
**What**: Issue a task from a domain the Child has NOT previously handled
(inferred from `components_used` history in SmartMemory). Examples: if the
Child has done knowledge tasks only, hand it a validation or project-scaffold task.
**Pass**: quality_score ≥ 6.0 and the Child invokes appropriate domain skills
rather than trying to solve it with its specialized DNA.
**Why**: detects over-specialization from mutations.

### Strategy 3 — Adversarial Probe (MANDATORY)
**What**: Task with an ambiguous, contradictory, or under-specified constraint.
Example: "Write a short summary — but make it comprehensive." Grade on
(a) whether the Child asks clarifying questions, (b) the quality of the
questions, (c) behavior when forced to choose without clarification.
**Pass**: asks ≥1 specific clarifying question OR explicitly documents its
interpretation before proceeding. Silent misinterpretation = automatic fail.
**Why**: distinguishes a competent agent from a mutation-tuned template matcher.

### Strategy 4 — Memory Consistency Check
**What**: Grep the Child's recent artifacts (outputs from the last 3 tasks)
against `SmartMemory.md` for direct contradictions with established learnings
for this project or lineage.
**Pass**: zero direct contradictions; any "supersedes earlier pattern" claims
must carry explicit justification in the artifact.
**Why**: catches mutations that drifted the Child into contradicting prior
institutional knowledge.

### Strategy 5 — Peer Comparison
**What**: Delegate the same task to the Child AND to a baseline
(default: vanilla `system-agent`; when available, a **rolling baseline** — the
Child's own gen-N-2 ancestor from memory_archive/dna/). Compare quality_scores.
**Pass**: Child's score ≥ baseline - 1.0. Tie or better wins.
**Why**: prevents the Child from looking great only in its specialization
niche while being below par on general capability.

## Execution Logic

### Phase 1 — Load
1. Read `lineage.json`, Child's DNA, SmartMemory slice for this lineage.
2. Determine `strategies_run` from input; if strategy 3 is not selected, add it
   (mandatory). If `strategy_selection` is empty, run all five.

### Phase 2 — Run Each Strategy
For each strategy:
1. Delegate the specific probe task to the Child via Task tool.
2. Score the output per strategy criteria above.
3. Record result in `score_breakdown`.
4. Short-circuit: if strategy 3 fails → set `verdict: fail` immediately and
   still run the remaining strategies (for diagnostic completeness), but no
   promotion possible.

### Phase 3 — Aggregate
1. `strategies_passed = [i for i in strategies_run if score[i] >= threshold]`.
2. Thresholds: strategy 1 & 2 & 5 → score ≥ 6.5; strategy 3 → pass-criterion;
   strategy 4 → zero direct contradictions (boolean).
3. `verdict`:
   - `pass` if `len(strategies_passed) >= 3 AND adversarial_passed == true`
   - `borderline` if `len(strategies_passed) == 2` — caller's decision
   - `fail` otherwise

### Phase 4 — Report
Write a full `validation_report.md` to
`projects/<project>/state/validation_reports/val_<child>_<ISO>.md`:
```markdown
---
verdict: pass | fail | borderline
child_agent_id: <child>
lineage_id: <lineage>
generation: <N>
adversarial_passed: bool
strategies_run: [...]
validator_dna_hash: <sha256 of this agent at time of run>
---
# Validation Report

## Strategy 1 — Replay Probe
- Task replayed: <task_id>
- Original score: <0-10>; replay score: <0-10>
- Result: pass | fail
- Evidence: ...

[... strategies 2–5 ...]

## Aggregate Verdict
<verdict> — <summary rationale>

## Promotion Recommendation
- Ready to promote: yes | no | conditional
- Conditions (if any): ...
```

### Phase 5 — Return
Return output structure. `promote-child-agent` is the only downstream consumer.

## Claude Tool Mapping

| Step | Tool |
|------|------|
| Read DNA + SmartMemory slice | Read, Grep |
| Delegate probe tasks to Child | Task |
| Delegate peer-comparison task | Task (twice: once to Child, once to baseline) |
| Write report | Write |

## Anti-Patterns (Known Gaming Strategies)

- **Father skips strategies**: enforce strategy 3 mandatory at the agent-code
  level; any verdict:pass without adversarial_passed:true is a DNA-level bug
  and is rejected by promote-child-agent.
- **Cherry-picked replay**: the replay task must be chosen randomly from the
  Child's top-10 prior successes (by quality_score), not selected by the Father.
- **Rolling-baseline staleness**: once a grandfather-baseline is ≥3 generations
  behind, the peer-comparison strategy stops providing signal. Document this
  in the report so callers can adjust thresholds.

## Non-Goals (v1)

- Randomized strategy selection (v1 runs a fixed set; v2 should randomize
  which 3 of 5 are "primary" per validation run to resist Goodharting).
- Multi-Child comparison (sibling-to-sibling) — one Child per lineage at a time.
