---
skill_domain: orchestration
type: routing-policy
version: 1.0.0
applies_to: orchestration/core/system-agent
---

# Provider Router — Two-Tier Runtime Policy

Defines **which LLM backend handles which call** across SkillOS. Complements
`orchestration/base.md` (skill routing) and `forge/base.md` (meta-layer rules).

## Tiers

| Tier | Backend | Default model | Role |
|------|---------|---------------|------|
| Hot  | Ollama (local) | `gemma4:e2b` | Execute user goals via cartridges + skills |
| Warm | Ollama (local) | `gemma4:e4b` | Fallback when E2B pass-rate is low for a skill family |
| Forge| Claude Code (cloud) | current | Only generate/evolve/validate artifacts; never user work |

Environment overrides:
- `GEMMA_MODEL` — override the hot-tier tag (e.g. `gemma4:e4b`, custom finetune).
- `OLLAMA_BASE_URL` — override host (default `http://localhost:11434`).
- `SKILLOS_FORGE_OFFLINE=1` — disable the forge tier entirely.

## Decision table

| Condition | Route to |
|-----------|----------|
| User goal + existing cartridge matches intent | **Hot** via `cartridge_runtime.py` |
| User goal + existing markdown skill with valid `gemma_compat` attestation | **Hot** via `agent_runtime.py --provider gemma` |
| Skill has `gemma_compat.attestation_strength: weak` OR `target_model != gemma4:e2b` | **Warm** (E4B) |
| Skill has no `gemma_compat` block or attestation is stale (model tag changed) | **Forge** (validate-only, mass re-attest) |
| Capability gap — no skill covers the sub-goal | **Forge** (generate) |
| Skill pass-rate in SmartMemory < 0.80 over last 10 invocations | **Forge** (evolve) |
| User requested a new skill/cartridge explicitly | **Forge** (generate) |
| Any forge request while `SKILLOS_FORGE_OFFLINE=1` | Return `forge_disabled`, surface gap to user |

## Never-route rules
- Claude Code (forge tier) **never** executes user goals. If the forge tier produces
  a draft answer while generating a skill, the draft is discarded — only the skill
  artifact is kept, and execution restarts on the hot tier.
- Hot/warm tiers **never** write into `system/skills/` or `cartridges/`.
  Only `forge/compile/forge-compile-cartridge-tool` has that privilege.
- Hot/warm tiers **never** call external LLMs (Claude, OpenAI, etc.). They talk only
  to Ollama. Forge tier may call external LLMs but is budget-capped.

## Budget ledger
Every forge invocation is metered. The running total is persisted in
`projects/[P]/forge/budget.yaml`:
```yaml
project: <name>
caps:
  max_claude_tokens_per_job: 200000
  max_claude_tokens_per_day: 2000000
  max_claude_usd_per_day: 10.00
usage:
  today_date: 2026-04-20
  today_tokens: 42300
  today_usd: 0.78
  all_time_tokens: 1_233_000
  all_time_usd: 19.21
```
The router refuses a forge call with `budget_exceeded` when a cap is hit.

## Forge-loop detector
Track `(gap_signature, day)` → count. Threshold default = 3. On trip, router returns
`forge_loop_detected` and escalates to the user with the full chain of forge jobs.

## Selection algorithm (pseudocode)
```
def route(goal, context):
    if SKILLOS_FORGE_OFFLINE and needs_forge(goal, context):
        return "forge_disabled"
    cart = match_cartridge(goal)
    if cart: return ("hot", "cartridge", cart)
    skill = match_skill(goal)
    if skill and attestation_ok(skill, model=GEMMA_MODEL):
        tier = "hot" if skill.attestation.strength == "strong" else "warm"
        return (tier, "skill", skill)
    if skill and attestation_stale(skill):
        return ("forge", "validate", skill)
    if not skill:
        return ("forge", "generate", goal)
    if skill and skill.recent_pass_rate() < 0.80:
        return ("forge", "evolve", skill)
    return ("escalate", "no_route", goal)
```

## Responsibilities by skill

| Concern | Owner |
|---------|-------|
| Decide tier per call | `orchestration/core/system-agent` (reads this file) |
| Track SmartMemory pass-rates | `memory/analysis/memory-analysis-agent` |
| Attestations | `forge/validate/forge-validate-agent` (sole writer) |
| Budget ledger | `forge/base` (enforced at router) |
| Offline gate | env var, checked at every forge entry point |
