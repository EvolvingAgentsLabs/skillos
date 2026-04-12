---
skill_domain: orchestration
type: base-template
version: 1.0.0
---

# Orchestration Domain — Shared Behaviors

All skills in the `orchestration/` domain inherit these conventions.

## Role
Orchestration skills are responsible for decomposing goals into sub-tasks, selecting the right
downstream skills, delegating via the Task tool, and assembling results into a coherent output.

## Delegation Protocol
1. Read `system/skills/SkillIndex.md` to identify the relevant domain.
2. Read the domain's `index.md` to select the best skill.
3. Load the skill's `.manifest.md` to confirm fit.
4. Load the full spec only when ready to invoke.
5. Invoke via Task tool using the `subagent_type` field from the manifest.

## State Management
- Maintain execution state in `projects/[Project]/state/`
- Files: `plan.md`, `context.md`, `variables.json`, `history.md`, `constraints.md`
- Update only the relevant state file per step (atomic updates).

## Agent Interaction Logging
Log every sub-agent invocation to `projects/[Project]/memory/short_term/` using format:
`YYYY-MM-DD_HH-MM-SS_[agent-name]_interaction.md`

## Error Escalation
On sub-task failure, delegate to `recovery/error/error-recovery-agent` before retrying.

## Dialect Protocol
When the orchestration layer touches content that will be stored or passed between agents:
1. At ingress: delegate to intent-compiler-agent to compile user input into internal dialect
2. Between agents: prefer dialect-compressed forms (exec-plan, strategy-pointer, constraint-dsl)
3. At egress: delegate to human-renderer-agent to expand internal output to readable prose
4. Memory writes: always store in the most compressed applicable dialect
