---
type: domain-base
domain: auto-improve
version: 1.0.0
description: Shared behaviors for the AutoImprove self-optimization domain
---

# AutoImprove Domain — Base Behaviors

All skills in the `auto-improve` domain inherit these behaviors.

## Domain Purpose

AutoImprove implements a **background self-optimization loop** for SkillOS agents and tools.
Inspired by the AutoAgent / AutoResearch pattern:

> *A meta-agent that cannot directly execute tasks is better at improving task agents than humans are,
> because it shares the model weights and already understands the failure modes from the inside.*

## Core Principles

### 1. Meta / Task Split
The **meta-agent** (auto-improve-meta-agent) improves skill *specifications*.
The **task agents** (all other skills) execute against those specifications.
Never collapse these roles — being good at a domain ≠ being good at improving it.

### 2. Traces Are Everything
Improvement proposals MUST be grounded in real failure traces from `system/SmartMemory.md`.
A spec change without an evidenced failure trace is speculation and MUST be flagged as such.

### 3. Staleness-Triggered Improvement
A skill is "stale" when its `last_used` timestamp in the usage registry exceeds the
`staleness_threshold_hours` for that skill (default: 72 h).
Staleness is a signal that the skill may be under-exercised and possibly degrading.
The usage-tracker fires the meta-agent as a **background parallel Task** when staleness is detected.

### 4. Anti-Overfitting Gate
Before any improvement is applied, the meta-agent MUST pass a self-reflection check:
> "If the specific tasks that surfaced this failure ceased to exist, would this change
> still make the skill generically better?"
If the answer is NO, the change is a rubric hack and MUST be discarded.

### 5. Minimal Surface Edits
Prefer targeted, minimal changes over rewrites. A 5-line targeted patch to instructions
or a single new tool addition is preferred over replacing the entire spec.

### 6. Non-Blocking Background Execution
All auto-improve work MUST run as background parallel Task tool calls.
It MUST NOT delay, block, or slow down the primary user-facing execution.

### 7. Pending Review Queue
Improvements are never applied directly to production skill specs.
They are written to `system/auto_improve/pending_improvements/` for review.
The human operator applies improvements with explicit approval.

## Shared Data Paths

| Purpose | Path |
|---------|------|
| Usage registry (timestamps) | `system/auto_improve/usage_registry.json` |
| Pending improvement proposals | `system/auto_improve/pending_improvements/` |
| Archived applied improvements | `system/auto_improve/improvement_archive/` |
| Improvement activity log | `system/auto_improve/improvement_log.md` |

## Staleness Thresholds (defaults)

```yaml
staleness_defaults:
  global_threshold_hours: 72       # 3 days
  high_frequency_skills:           # skills used many times/day
    threshold_hours: 24
    examples: [system-agent, memory-analysis-agent]
  low_frequency_skills:            # skills used rarely by design
    threshold_hours: 168           # 7 days
    examples: [knowledge-compile-agent, roclaw-dream-agent]
  per_skill_override:              # set in skill manifest via stale_after_hours
    example: "stale_after_hours: 48"
```

## Improvement Proposal Format

Every pending improvement file MUST follow this schema:

```markdown
---
proposal_id: imp_YYYYMMDD_HHMMSS_<skill_id_slug>
skill_id: <domain/family/skill-name>
skill_path: system/skills/<domain>/<family>/<skill>.md
triggered_by: staleness | failure_spike | manual
trigger_timestamp: ISO-8601
failure_trace_refs: [exp_NNN, exp_NNN]   # entries in SmartMemory
meta_agent_version: 1.0.0
status: pending | approved | rejected | applied
anti_overfitting_passed: true | false
---

# Improvement Proposal: <skill display name>

## Trigger Evidence
<what failure traces or staleness data triggered this>

## Root Cause Analysis
<why the current spec is suboptimal>

## Proposed Change
### Before
```
<original excerpt>
```
### After
```
<proposed replacement>
```

## Expected Impact
<what metric or behavior this improves>

## Anti-Overfitting Check
> "If the specific tasks that surfaced this failure ceased to exist, would this change
> still make the skill generically better?"
Answer: YES / NO
Reasoning: <...>

## Risks
<any potential regressions or side-effects>
```
