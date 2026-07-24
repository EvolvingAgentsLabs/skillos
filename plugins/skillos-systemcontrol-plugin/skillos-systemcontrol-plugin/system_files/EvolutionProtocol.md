# Evolution Protocol

## Overview
The Evolution Protocol defines how agents are improved over time through controlled, evidence-based changes. It embeds the anti-overfitting gate, minimal-surface edit preference, and staged change management to ensure the system evolves without regressing.

## Core Principle: Controlled Evolution

Evolution is not "make agents better." Evolution is:
1. **Measure** — score agents on actual traces (never hypotheticals)
2. **Diagnose** — classify failures using the 7-type taxonomy
3. **Propose** — draft minimal changes targeting the root cause
4. **Validate** — pass every proposal through the anti-overfitting gate
5. **Stage** — queue approved proposals for human review
6. **Apply** — only after explicit approval
7. **Verify** — confirm the change improved scores in subsequent executions

## Anti-Overfitting Gate

### Definition
A change is "overfitting" if it optimizes for the specific failures observed but doesn't improve the agent's general capability.

### The Test
```
For every proposed change, ask:

  "If the specific tasks that caused these failures
   were removed from the workload entirely,
   would this change still make the agent better?"

  YES → The change is generically beneficial → APPROVE
  NO  → The change is a rubric hack → REJECT
```

### Examples

| Proposed Change | Test Result | Verdict |
|----------------|-------------|---------|
| "Add timeout recovery for Bash commands" | YES — timeouts happen in any task | APPROVE |
| "Add knowledge about PostgreSQL schema syntax" | NO — only helps if DB tasks recur | REJECT |
| "Specify output must be valid JSON" | YES — format contracts help all uses | APPROVE |
| "Handle the case where file X doesn't exist" | DEPENDS — if X is project-specific: REJECT; if it's a common pattern: APPROVE |

### Boundary Cases
- If uncertain, lean toward REJECT — false negatives (missing an improvement) are safer than false positives (introducing overfitting)
- If the same change would be proposed independently of the failure traces, it's likely generic → APPROVE
- Domain-specific knowledge additions almost always fail the gate unless the agent is explicitly domain-scoped

## Minimal-Surface Edit Preference

### Ranking (Least Invasive First)

| Rank | Edit Type | Description | Risk |
|------|-----------|-------------|------|
| 1 | **Instruction Clarification** | Add 1 sentence to disambiguate a decision point | Lowest |
| 2 | **Tool Addition** | Add a tool to the YAML `tools:` list | Low |
| 3 | **Recovery Rule** | Add a fallback clause for a specific error type | Low-Med |
| 4 | **Output Contract** | Tighten the output format specification | Medium |
| 5 | **Path/Assumption Update** | Fix stale path, API endpoint, or fact | Medium |
| 6 | **Checkpoint Guidance** | Add progress tracking for long workflows | Higher |

### Rules
- **Never rewrite entire agent specs** (NC-1) — prefer 5-line patches
- **One change per proposal** — enables clear attribution if something breaks
- **If 3+ changes needed**, the agent may be fundamentally broken → consider pruning and replacement instead of evolution
- **Always show the diff** — exact `old_string` → `new_string` for every proposed change

## Staged Change Management

### The Pipeline
```
PROPOSED → VALIDATED → STAGED → APPROVED → APPLIED → VERIFIED
```

### Stage Definitions

1. **PROPOSED**: EvolutionControlAgent identifies a change
2. **VALIDATED**: Change passes anti-overfitting gate
3. **STAGED**: Change is written to `evolution_proposals.md` for review
4. **APPROVED**: Human explicitly approves the change
5. **APPLIED**: Change is made to the agent's markdown file
6. **VERIFIED**: Subsequent executions confirm improved scores

### Rollback
If a change is APPLIED but scores degrade:
- Revert the change (restore original text)
- Log the failure as a negative constraint
- Mark the proposal as FAILED in the evolution log
- The same change cannot be re-proposed without new evidence (NC-7)

## Evidence Requirements

### Minimum Evidence for a Proposal
- At least 3 traces showing the same failure pattern
- Failure must be classified by the 7-type taxonomy
- Root cause must be traceable to a specific section of the agent's prompt or config
- Impact estimate: how many traces would this change have fixed?

### Insufficient Evidence
If fewer than 3 traces show a pattern:
- Log the observation for future reference
- Do not generate a proposal
- The pattern may emerge with more data

## Evolution Constraints

### From Negative Constraints (NC-1 through NC-7)
- **NC-1**: Never rewrite entire specs during self-improvement
- **NC-2**: Never apply improvements without anti-overfitting gate
- **NC-3**: Never let monitoring tools block primary execution
- **NC-4**: No duplicate improvement spawns per skill per session
- **NC-5**: Never apply improvements directly to production
- **NC-6**: Never fabricate failure evidence
- **NC-7**: Never re-propose rejected improvements without new evidence

### Additional Evolution Rules
- Maximum 3 proposals per agent per evolution cycle
- Changes to security-relevant sections require SecurityAuditAgent re-scan
- Evolution cannot add new capabilities — only improve existing ones
- If an agent's score is below 0.3 for 3 consecutive evaluations, recommend pruning instead

## Integration with Dream Engine

Evolution proposals that are APPLIED should generate traces for dream consolidation:
- Log the before/after state
- Track whether the change improved scores
- Dream Engine can extract "what kinds of changes actually work" as meta-strategies
- Over time, the system learns which edit types are most effective for which failure types
