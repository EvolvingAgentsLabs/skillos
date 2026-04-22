---
domain: genealogy
skill_count: 4
base: system/skills/genealogy/base.md
---

# Genealogy Domain Index

Parent–child agent spawning, tutoring, validation, and promotion.
An agent's markdown definition is treated as **DNA** — copied at spawn,
mutated under guardrails during life, and archived at promotion.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| spawn-child-agent | spawn | spawn-child-agent | boot with kernel_mode:genealogy, after promotion, new child needed | genealogy/spawn/spawn-child-agent.manifest.md |
| tutor-child-agent | tutor | tutor-child-agent | child executed task, mutation proposal filed, review cycle | genealogy/tutor/tutor-child-agent.manifest.md |
| validate-child-agent | validate | validate-child-agent | child meets eligibility, pre-promotion check, quality audit | genealogy/validate/validate-child-agent.manifest.md |
| promote-child-agent | promote | promote-child-agent | validate-child-agent returned 3/5 pass + adversarial pass | genealogy/promote/promote-child-agent.manifest.md |

## Routing Notes

- **Activation gate**: these skills are only invoked when `kernel_mode: genealogy`
  is set in `projects/[Project]/state/variables.json`. Otherwise system-agent
  operates in classic single-kernel mode.
- **Cycle order**: spawn → (tutor ⇄ child executes) × N → validate → promote → spawn…
- **Authority**: `system-agent` (gen-0 Grandfather) owns the promotion decision
  until the first promotion; thereafter the current-generation Father is the
  proximate authority but system-agent retains veto via SmartMemory audit.
- **Validation is mandatory** before promotion: the adversarial probe (strategy 3)
  must pass; ≥3 of 5 strategies total.
- **Failure paths**: rejected mutation → tutor logs rejection, child continues
  with unchanged DNA. Failed promotion → lineage.json status stays `tutoring`;
  eligibility counters reset if `consecutive_failures` triggered.

## Related Skills (cross-domain)

- `validation/system/validation-agent` — enforces `DNA-001..005` rules on proposals
- `memory/consolidation/memory-consolidation-agent` — end-of-session learning
- `memory/analysis/memory-analysis-agent` — historical lineage queries
- `recovery/error/error-recovery-agent` — circular-delegation circuit breaker
- `orchestration/core/system-agent` — kernel; hosts `GENEALOGY` Operating Mode
