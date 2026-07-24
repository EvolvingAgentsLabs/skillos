# Lifecycle Protocol

## Overview
The Lifecycle Protocol defines how agents and memory artifacts are deprecated, merged, deleted, and compacted within SkillOS projects. Every operation follows the cascading prune-and-verify pattern to prevent broken references.

## Agent Lifecycle States

```
CREATED → ACTIVE → [EVOLVING] → DEPRECATED → DELETED
                       ↑              |
                       └──────────────┘
                    (if evolution fails)
```

### State Definitions

| State | Description | Allowed Operations |
|-------|-------------|-------------------|
| **CREATED** | Agent spec written but never executed | Execute, Delete |
| **ACTIVE** | Agent has been executed at least once | Execute, Evolve, Score, Audit |
| **EVOLVING** | Agent has pending evolution proposals | Execute, Review proposals |
| **DEPRECATED** | Agent marked for retirement | Read-only, Delete after grace period |
| **DELETED** | Agent removed from project | N/A — references cleaned up |

## Deprecation Protocol

### When to Deprecate

An agent enters DEPRECATED state when ANY of these criteria are met:

| Criterion | Threshold | Evidence Required |
|-----------|-----------|-------------------|
| Zero execution | Created > 7 days ago, 0 traces | Glob for traces mentioning agent |
| Total failure | >= 5 traces, 100% failure rate | Scorecard data |
| Superseded | Another agent handles same tasks with higher score | Score comparison |
| Stale | Not used in 30+ days AND score < 0.5 | Trace timestamps + scorecard |
| Redundant | Capabilities are strict subset of another agent | Capability comparison |

### Deprecation Process

1. **Mark as deprecated**: Add `status: deprecated` to agent's YAML frontmatter and `deprecated_date: YYYY-MM-DD`
2. **Grace period**: Agent remains readable for 7 days (other agents may reference it)
3. **Reference notification**: Log which agents or memory artifacts reference the deprecated agent
4. **After grace period**: Eligible for deletion via the deletion protocol

## Deletion Protocol

### Cascading Prune-and-Verify

**NEVER skip any step.** This protocol prevents broken references (NC-8).

#### Step 1: Inventory Target
```
Target: [AgentName].md
Location: projects/[Project]/components/agents/[AgentName].md
```

#### Step 2: Reference Scan
Use `Grep` to find ALL references to the agent across the project:

```
Search paths:
  - projects/[Project]/components/agents/*.md    (other agents)
  - projects/[Project]/memory/short_term/*.md    (traces)
  - projects/[Project]/memory/long_term/*.md     (learnings)
  - projects/[Project]/output/**                 (deliverables)
```

#### Step 3: Classify References

| Classification | Examples | Required Action |
|----------------|----------|----------------|
| **Routing-Critical** | Agent delegation in system prompt, dependency declaration, orchestration flow | MUST update before deletion |
| **Runtime-Affecting** | Error handling fallback, conditional logic, recovery chain | MUST update before deletion |
| **Documentation-Only** | Comments, README mentions, learning artifacts | DEFER — log as doc debt |

#### Step 4: Plan Reference Updates
For each routing-critical and runtime-affecting reference:
- Determine replacement: redirect to another agent, remove the reference, or restructure the flow
- Draft the exact edit (old_string → new_string)
- Verify the edit doesn't break the referencing file's logic

#### Step 5: Execute
- Apply all reference updates first
- Delete the agent file last
- Log all changes as a single trace entry

#### Step 6: Verify
- Re-run `Grep` for the deleted agent name — should return 0 results
- Verify project structure integrity (no orphaned references)
- Update any project-level inventories or registries

## Merge Protocol

### When to Merge

Two agents should be merged when:
- They share > 60% of their capabilities
- They handle overlapping task types (evidenced by similar trace goals)
- One consistently outperforms the other on shared tasks
- Maintaining both creates confusion about which to delegate to

### Merge Process

1. **Analyze both agents**: Compare YAML frontmatter and system prompts side-by-side
2. **Identify unique value**: What does each agent contribute that the other doesn't?
3. **Draft unified spec**: Combine the best elements of both:
   - Union of capabilities (if non-conflicting)
   - Union of tools (apply minimal-access principle)
   - Merge system prompts, preferring the higher-scoring agent's structure
   - Include recovery rules from both
4. **Proposal format**:
   ```markdown
   ### Merge Proposal: [AgentA] + [AgentB] → [MergedAgent]
   - **AgentA score**: [score] ([tier])
   - **AgentB score**: [score] ([tier])
   - **Overlap**: [percentage] capability overlap
   - **Unified spec**: [attached or inline]
   - **Agents to deprecate**: [AgentA], [AgentB]
   - **References to update**: [count]
   ```
5. **After approval**: Create the merged agent, run deprecation protocol on both originals

## Memory Lifecycle

### Short-Term Memory Compaction

Short-term traces accumulate during project execution. Compaction criteria:

| Condition | Action |
|-----------|--------|
| Duplicate traces (same agent, same task, same outcome, within 24h) | Merge into single representative trace |
| Traces older than 30 days that have been consolidated into long-term memory | Archive (move to `memory/archive/`) |
| Orphaned traces (parent_trace_id references a deleted trace) | Reparent to root or archive |
| Traces with status: pending (never completed) | Mark as abandoned, archive |

### Long-Term Memory Compaction

Long-term artifacts should be periodically reviewed:

| Condition | Action |
|-----------|--------|
| Duplicate strategies (> 80% trigger_goals overlap) | Merge into single strategy, sum success_counts |
| Contradictory strategies (same trigger, opposite advice) | Flag for resolution — keep higher confidence |
| Stale strategies (confidence < 0.3, no recent traces) | Archive |
| Orphaned templates (reference agents that no longer exist) | Archive or update references |

### Memory Compaction Rules

- **Never delete long-term memory without archival** — move to `memory/archive/`, don't destroy
- **Always recount after compaction** (NC-21) — never trust incremental counts
- **Log compaction as a trace** — the Dream Engine should know what was compacted
- **Preserve high-confidence strategies** (>= 0.8) regardless of age

## Lifecycle Reporting

All lifecycle operations produce reports saved to `projects/[Project]/output/sysctl/`:

- `prune_candidates_YYYYMMDD.md` — deprecation/deletion proposals
- `merge_proposals_YYYYMMDD.md` — merge proposals
- `compaction_report_YYYYMMDD.md` — memory compaction results
- `lifecycle_log_YYYYMMDD.md` — audit trail of all operations

## Constraints

- **NC-8**: Never prune files without cascading reference updates
- **NC-9**: Always classify references (routing-critical vs doc-debt vs runtime-affecting)
- **NC-10**: Never let registries drift from canonical definitions
- **NC-13**: Always grep for deleted paths after operations
- **NC-14**: Never assume clean operations mean semantic consistency
- **NC-21**: Never compute totals by increments — recount from source

## Integration with Dream Engine

Lifecycle operations generate valuable traces for dream consolidation:
- **Successful merges**: Dream Engine learns which capability combinations work well together
- **Failed evolution → pruning**: Dream Engine learns when evolution should be abandoned
- **Memory compaction**: Dream Engine learns which strategies persist and which are ephemeral
- Over time, the system develops meta-strategies about its own lifecycle management
