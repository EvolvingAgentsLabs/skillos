---
skill_domain: genealogy
type: base-template
version: 1.0.0
---

# Genealogy Domain — Shared Behaviors

All skills in the `genealogy/` domain inherit these conventions.

## Biological Metaphor (Informs Naming Throughout)

An agent's **markdown definition files are its DNA** — the heritable material
copied from parent to child at spawn. Mutations to a Child's DNA are proposed
as diff files (somatic hypermutation), reviewed by the Father (germline-level
approval), and only then merged into the Child's active spec. Successive
validated mutations → promotion → reproductive maturity → next generation.

```
system-agent (gen-0, Grandfather / progenitor)
        │ spawn
        ▼
father-<tag>-gen1  ──► tutors ──►  child-<tag>-gen1  ──► executes tasks
                                          │
                                          │ accumulates wins; proposes DNA mutations
                                          ▼
                                 [validate-child-agent — 5 strategies]
                                          │  passes ≥3
                                          ▼
                                 [promote-child-agent]
                                          │
                                          ▼
                             child-<tag>-gen1 becomes father-<tag>-gen2
                                          │ spawn
                                          ▼
                                  child-<tag>-gen2 …
```

## Lineage File Ownership

| File | Written by | Read by |
|---|---|---|
| `projects/[Project]/state/lineage.json` | spawn, promote | all genealogy skills, validation-agent |
| `projects/[Project]/components/agents/<child>.md` | spawn (initial), tutor (on approved merge) | Claude Code (via `.claude/agents/` copy) |
| `projects/[Project]/components/agents/<child>.mutation-proposal.md` | child (during execution) | tutor-child-agent (review) |
| `system/memory_archive/dna/father-<tag>-gen<N>.md` | promote (snapshot) | memory-analysis-agent (historical lookup) |
| `system/SmartMemory.md` (genealogy entries) | tutor (tutoring_session), promote (promotion_event) | memory-analysis-agent, system-agent |

## Lineage Record Schema (`lineage.json`)

```json
{
  "lineage_id": "lin_<session>_<shortHash>",
  "kernel_mode": "genealogy",
  "members": [
    {
      "agent_id": "system-agent",
      "generation": 0,
      "parent_id": null,
      "spawn_timestamp": "2026-04-22T10:00:00Z",
      "dna_hash": "sha256:…",
      "status": "executing",
      "promotion_criteria_met": {
        "tasks_passed": 0,
        "quality_avg": 0.0,
        "cross_domain_passes": 0,
        "consecutive_failures": 0
      }
    }
  ],
  "lineage_path": ["system-agent@0"]
}
```

`status` ∈ `tutoring | executing | validated | promoted | retired`

## DNA Diff Convention (Mutation Proposals)

Mutation-proposal files are unified-diff-style deltas over the Child's current
DNA, with required fields in frontmatter:

```yaml
---
proposal_id: prop_<child>_<seq>
child_agent_id: child-<tag>-gen<N>
parent_agent_id: father-<tag>-gen<N-1>
proposed_at: ISO-8601
triggered_by: task-id or event
churn_ratio: 0.0–1.0   # (changed lines) / (total lines in current DNA)
rationale: "Why this mutation improves task performance"
---

# Proposed Changes
```diff
- old line
+ new line
```

## Validation Report
[result of validation-agent pre-screen if already run]
```

## Guardrails (DNA-* rules enforced by validation-agent)

| Rule | Name | Violation |
|---|---|---|
| DNA-001 | RationaleRequired | Proposal missing `rationale` field or empty rationale |
| DNA-002 | ChurnBudget | `churn_ratio` > 0.15 (per-generation mutation cap) |
| DNA-003 | ExtendsChain | `extends:` chain shortened / ancestral base class removed |
| DNA-004 | CapabilityRemoval | A declared capability in parent manifest removed without explicit `removes_capability: true` + rationale |
| DNA-005 | ToolsDrift | `tools:` field modified without `tutor_approved: true` in proposal |

## Promotion Criteria (shared threshold)

A Child is **eligible** for promotion when ALL hold:
- `tasks_passed >= 3`
- `quality_avg >= 7.5` (from SmartMemory `quality_score` 0–10)
- `cross_domain_passes >= 2` (succeeded on tasks from ≥2 distinct skill domains)
- `consecutive_failures == 0` across the last 3 tasks
- `validate-child-agent` reports ≥3/5 strategies pass, including the mandatory adversarial probe

## Kernel-Mode Activation

Genealogy is **opt-in**: activated by setting `kernel_mode: genealogy` in
`projects/[Project]/state/variables.json`. In default (classic) mode,
`system-agent` operates unchanged. No regression risk.

## Memory Entry Types (added to SmartMemory.md)

- `entry_type: tutoring_session` — one per tutor session; records parent→child DNA delta and effectiveness
- `entry_type: promotion_event` — one per promotion; records validation scores, archived DNA path, lineage_path

Both carry `lineage_id`, `generation`, `dna_hash` as extra frontmatter keys.

## Circular-Delegation Protection

A generation-aware circuit breaker (enforced by `error-recovery-agent`) refuses
any delegation where the target agent's `generation` >= caller's `generation`
within the same `lineage_id` — prevents gen-N Child delegating back up to its
own ancestors and deadlocking the lineage.

## Token Efficiency

All genealogy skills read `lineage.json` (compact JSON) before loading any DNA
file. Full DNA (.md) is loaded only when mutation, validation, or promotion
actually requires it.
