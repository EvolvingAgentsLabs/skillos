---
skill_domain: forge
type: base-template
version: 1.0.0
---

# Forge Domain — Shared Behaviors

All skills in the `forge/` domain inherit these conventions.

## Purpose
Forge is the **meta-layer** of SkillOS. Forge skills do not execute user goals directly.
They produce, mutate, and retire artifacts that the execution layer (Gemma 4 + cartridges +
JS sandbox) can run: markdown skills, JS skills, cartridges, subagents, and test suites.

## Two-tier runtime invariant
- **Hot path**: Gemma 4 (via Ollama, default tag `gemma4:e2b`) + pre-compiled cartridges.
  Handles ~all user-goal execution.
- **Forge path**: Claude Code (cloud, via `Task` tool or `claude` CLI) is invoked **only**
  when a capability gap is detected or a skill must evolve. Claude never executes user work
  directly — it emits artifacts that Gemma can then run.

## When forge fires
A `GapEvent` is emitted and a forge job is queued when one of the following occurs:
1. Router cannot resolve a skill for a sub-goal after SkillIndex → domain → manifest walk.
2. A candidate skill lacks a valid `gemma_compat` attestation.
3. A skill returns `insufficient_capability` or exhausts retries on Gemma.
4. SmartMemory shows a skill's pass-rate has dropped below threshold (triggers evolve).
5. A Gemma model upgrade invalidates existing attestations (triggers mass re-validate).
6. User explicitly requests `skillos execute: "forge <description>"`.

## Artifact contract
Every artifact forge produces MUST include:
- `kind:` one of `markdown-skill | js-skill | cartridge | subagent | test-suite`.
- `target_model:` e.g. `gemma4:e2b` — the model it was validated against.
- `gemma_compat:` block written only by `forge/validate/*` after successful tests.
- Source-of-creation: `produced_by: forge/<family>/<agent>`, `forge_job_id: <uuid>`.

## Budget & guardrails (non-optional)
- Per-project **token/$ ledger** with hard stops.
- **Forge-loop detector**: same gap re-triggering forge >3× in 24 h pauses and escalates.
- **Offline mode** (`SKILLOS_FORGE_OFFLINE=1`) surfaces gaps as user-fixable errors
  instead of silent cloud calls.
- **Validation gate is mandatory**: no artifact enters the hot path without a
  `gemma_compat` attestation signed by `forge/validate/*`.
- **Rollback**: every skill/cartridge write is a versioned replace. Old versions are
  archived under `projects/[P]/forge/archive/<ts>/` and reverted with one command.

## Escalation
On any of the following, halt and require explicit user approval:
- Budget hit.
- Validation fails after `max_retries` attempts.
- Generated artifact requests a tool outside the project's allow-list.
- Forge-loop detector fires.

## Logging
Every forge job appends a structured entry to `projects/[P]/forge/journal.md`:
```yaml
- job_id: <uuid>
  trigger: gap | evolve | user_request | model_upgrade
  goal: "<human-readable>"
  artifacts_produced: [<paths>]
  claude_tokens_used: N
  wall_clock_s: N
  outcome: pass | fail | rolled_back
```
