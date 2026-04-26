---
name: auto-improve-self-optimization-scenario
description: >
  End-to-end test of the AutoImprove self-optimization loop. Seeds SmartMemory
  with synthetic failure traces, populates the usage registry with stale skill
  entries, then exercises the full pipeline: usage-tracker record/staleness check,
  meta-agent spawn, evidence collection, root-cause analysis, improvement proposal,
  anti-overfitting gate, and pending review queue.
version: "1.0"
difficulty: intermediate
estimated_duration_minutes: 10
mode: EXECUTION
prerequisites:
  - PR #16 auto-improve domain merged
  - system/auto_improve/ directory exists with usage_registry.json and improvement_log.md
  - system/auto_improve/pending_improvements/ directory exists
---

# AutoImprove Self-Optimization Scenario

## Overview

This scenario validates the full auto-improve self-optimization loop introduced in PR #16. It tests three features:

1. **Usage Tracker** — record skill invocations, detect staleness
2. **Meta-Agent** — analyze failure traces and propose improvements
3. **SystemAgent Step 3.5 Hook** — the integration point that ties everything together

The test seeds synthetic data to create realistic conditions (stale skills, failure traces), then runs the pipeline and verifies each output artifact.

---

## Phase 0: Setup — Seed Test Data

### Step 0.1: Seed SmartMemory with failure traces

Append these synthetic failure entries to `system/SmartMemory.md`. These simulate a `knowledge-query-agent` that has been failing when users ask questions about topics not covered by the KB.

```markdown
Action: Read system/SmartMemory.md
Observation: [Current contents — note the last exp_NNN ID]

Action: Edit system/SmartMemory.md
Append after the last experience entry:

---
- **experience_id**: exp_TEST_AI_001
- **primary_goal**: Answer user question about quantum computing applications
- **final_outcome**: failure
- **components_used**: [knowledge-query-agent, knowledge-search-tool]
- **output_summary**: Agent returned "no relevant articles found" without attempting web search fallback or suggesting KB gaps to the user
- **learnings_or_issues**: knowledge-query-agent does not have a fallback path when the KB has no coverage for a topic. The spec says "search the knowledge base" but does not instruct the agent what to do when zero results are found.

---
- **experience_id**: exp_TEST_AI_002
- **primary_goal**: Summarize latest developments in RISC-V ecosystem
- **final_outcome**: failure
- **components_used**: [knowledge-query-agent, knowledge-search-tool]
- **output_summary**: Agent searched KB, found 1 tangentially related article about chip architectures, and returned a summary that was mostly about ARM — not RISC-V
- **learnings_or_issues**: When knowledge-search-tool returns low-relevance results, knowledge-query-agent does not assess relevance before summarizing. It treats any hit as authoritative. Needs a relevance threshold or "insufficient coverage" escape hatch.

---
- **experience_id**: exp_TEST_AI_003
- **primary_goal**: Compare serverless vs container deployment strategies
- **final_outcome**: partial
- **components_used**: [knowledge-query-agent, knowledge-search-tool]
- **output_summary**: Agent found KB articles about containers but nothing about serverless. Produced a one-sided comparison flagged as incomplete by the user.
- **learnings_or_issues**: knowledge-query-agent spec does not require balanced coverage across comparison axes. When one side has data and the other does not, it should either flag the gap or invoke a web search to fill it.

---
- **experience_id**: exp_TEST_AI_004
- **primary_goal**: Explain how SkillOS handles error recovery
- **final_outcome**: failure
- **components_used**: [knowledge-query-agent, knowledge-search-tool]
- **output_summary**: Agent searched for "error recovery" but did not find the recovery domain skills. Returned a generic answer instead of pointing to system/skills/recovery/
- **learnings_or_issues**: knowledge-query-agent searches SmartMemory and KB articles but does not search the SkillIndex itself. When the query is about SkillOS internals, the agent should consult SkillIndex.md as a knowledge source.
```

### Step 0.2: Seed the usage registry with a stale entry

Write a pre-populated `usage_registry.json` that simulates `knowledge-query-agent` having been used 5 times, but the last use was 96 hours ago (exceeding the 72h default threshold).

```markdown
Action: Write system/auto_improve/usage_registry.json

{
  "version": "1.0",
  "last_updated": "2026-04-22T10:00:00Z",
  "skills": {
    "knowledge/query/knowledge-query-agent": {
      "last_used": "2026-04-22T10:00:00Z",
      "previous_last_used": "2026-04-19T14:30:00Z",
      "use_count": 5,
      "stale_after_hours": 72,
      "first_seen": "2026-04-01T08:00:00Z",
      "improvement_count": 0,
      "last_improved": null
    },
    "memory/analysis/memory-analysis-agent": {
      "last_used": "2026-04-25T18:00:00Z",
      "previous_last_used": "2026-04-25T12:00:00Z",
      "use_count": 12,
      "stale_after_hours": 24,
      "first_seen": "2026-04-01T08:00:00Z",
      "improvement_count": 0,
      "last_improved": null
    }
  }
}
```

Note: `memory-analysis-agent` is non-stale (used 6h ago) — serves as control.

### Step 0.3: Ensure clean state

```markdown
Action: Read system/auto_improve/improvement_log.md
Observation: [Should be empty / initialized template]

Action: Glob pattern="system/auto_improve/pending_improvements/*.md"
Observation: [Should be empty — no prior proposals]
```

---

## Phase 1: Usage Tracker — Record and Staleness Detection

### Step 1.1: Test `record()` for a non-stale skill

Simulate SystemAgent invoking `memory-analysis-agent`:

```markdown
Action: Read system/auto_improve/usage_registry.json
Observation: [registry contents]

# Execute record() inline:
# 1. Save old last_used as previous_last_used
# 2. Update last_used to NOW
# 3. Increment use_count
# 4. Write back

Action: Write system/auto_improve/usage_registry.json
# memory-analysis-agent.use_count → 13, last_used → NOW

# Execute check_staleness() inline:
# hours_gap = (NOW - previous_last_used) / 3600
# For memory-analysis-agent: gap ≈ 6h, threshold = 24h
# is_stale = (6 > 24) AND (use_count >= 2) = FALSE

Expected result:
{
  "skill_id": "memory/analysis/memory-analysis-agent",
  "is_stale": false,
  "hours_gap": 6.0,
  "threshold": 24,
  "use_count": 13
}
```

**Verification**: No background Task should be spawned. The primary execution continues without delay.

### Step 1.2: Test `record()` for a stale skill

Simulate SystemAgent invoking `knowledge-query-agent` after a 96h gap:

```markdown
Action: Read system/auto_improve/usage_registry.json

# Execute record() inline:
# 1. Save old last_used ("2026-04-22T10:00:00Z") as previous_last_used
# 2. Update last_used to NOW
# 3. Increment use_count → 6
# 4. Write back

# Execute check_staleness() inline:
# hours_gap = (NOW - previous_last_used) / 3600
# For knowledge-query-agent: gap ≈ 96h, threshold = 72h
# is_stale = (96 > 72) AND (use_count >= 2) = TRUE

Expected result:
{
  "skill_id": "knowledge/query/knowledge-query-agent",
  "is_stale": true,
  "hours_gap": 96.0,
  "threshold": 72,
  "use_count": 6
}
```

**Verification**: `is_stale = true` should trigger a background Task.

### Step 1.3: Test `list_stale()` operation

```markdown
Action: Read system/auto_improve/usage_registry.json

# For each skill, compute hours_since_last_used:
# - knowledge-query-agent: ~96h (stale, threshold 72h) — BUT after Step 1.2 it was just used, so 0h now
# - memory-analysis-agent: ~6h (not stale, threshold 24h) — also just used

# After Steps 1.1 and 1.2, list_stale should return EMPTY (both skills just used)

Expected result: []
```

**Verification**: Confirms that `record()` resets the staleness clock.

---

## Phase 2: Meta-Agent — Background Improvement Proposal

### Step 2.1: Spawn the meta-agent

This simulates the background Task that SystemAgent would spawn when staleness is detected in Step 1.2.

```markdown
Action: Task (subagent_type: auto-improve-meta-agent — or read the spec and use it as prompt)

Prompt:
  You are the AutoImprove Meta-Agent. Execute your full improvement loop for:

  skill_id: "knowledge/query/knowledge-query-agent"
  trigger: "staleness"
  staleness_hours_gap: 96.0

  Phase 1: Load the skill spec via SkillIndex → knowledge domain → query skill.
           Query SmartMemory for failure traces mentioning "knowledge-query-agent".
  Phase 2: Classify failures using the 7-type taxonomy.
  Phase 3: Propose a minimal targeted improvement. Pass the anti-overfitting gate.
  Phase 4: Write proposal to pending_improvements/ and log to improvement_log.md.
```

### Step 2.2: Verify Phase 1 — Evidence Collection

The meta-agent should:
- Read `system/skills/SkillIndex.md` → find knowledge domain
- Read `system/skills/knowledge/index.md` → find knowledge-query-agent manifest
- Read the manifest → find full spec path
- Read the full spec
- Grep `system/SmartMemory.md` for `knowledge-query-agent` → find exp_TEST_AI_001 through exp_TEST_AI_004
- Read `system/auto_improve/improvement_log.md` → confirm no prior rejections

**Verification**: The agent identifies 4 traces (3 failure + 1 partial) with `evidence_quality: medium` or `high`.

### Step 2.3: Verify Phase 2 — Root Cause Analysis

Expected classification:
| Trace | Failure Type |
|-------|-------------|
| exp_TEST_AI_001 | MISSING_RECOVERY — no fallback when KB returns zero results |
| exp_TEST_AI_002 | INSTRUCTION_AMBIGUITY — no relevance threshold before summarizing |
| exp_TEST_AI_003 | MISSING_RECOVERY — no gap-detection for comparison queries |
| exp_TEST_AI_004 | STALE_ASSUMPTION — does not search SkillIndex as knowledge source |

Expected cluster: exp_TEST_AI_001, 002, 003 share a root cause — **the spec has no "insufficient coverage" escape hatch**.

**Verification**: The meta-agent groups at least 2 failures under the same root cause.

### Step 2.4: Verify Phase 3 — Improvement Proposal

The meta-agent should propose a **minimal change** such as:

```diff
- Search the knowledge base for articles relevant to the user's query.
+ Search the knowledge base for articles relevant to the user's query.
+ If zero results are found OR all results have low relevance:
+   1. Report to the user that the KB has no coverage for this topic
+   2. If WebSearch/WebFetch tools are available, attempt a web fallback
+   3. Log the coverage gap to SmartMemory for future KB expansion
```

**Anti-overfitting gate**: "Would adding an insufficient-coverage fallback help even if these 4 tasks never existed?" — **YES**. Any KB-query agent benefits from handling zero-result scenarios.

**Verification**:
```markdown
Action: Glob pattern="system/auto_improve/pending_improvements/imp_*.md"
Observation: [Should find exactly 1 new proposal file]

Action: Read <the proposal file>
Verify it contains:
  - proposal_id matching imp_YYYYMMDD_HHMMSS_knowledge_query
  - skill_id: knowledge/query/knowledge-query-agent
  - triggered_by: staleness
  - failure_trace_refs including exp_TEST_AI_001 through exp_TEST_AI_004
  - anti_overfitting_passed: true
  - status: pending
  - Before/After diff sections
  - Expected Impact section
  - Risks section
```

### Step 2.5: Verify Phase 4 — Logging

```markdown
Action: Read system/auto_improve/improvement_log.md
Verify a new entry exists with:
  - Timestamp
  - Skill ID: knowledge/query/knowledge-query-agent
  - Trigger: staleness
  - Evidence quality: medium or high (4 traces)
  - Change type: MISSING_RECOVERY (or the identified type)
  - Anti-overfitting: passed
  - Proposal file reference
```

---

## Phase 3: Integration — SystemAgent Step 3.5 Hook

### Step 3.1: Verify per-session dedup

The auto-improve hook should not spawn a second meta-agent for the same skill in the same session.

```markdown
# Simulate SystemAgent invoking knowledge-query-agent again in the same session

Action: Read projects/[ProjectName]/state/auto_improve_spawned.json
Observation: Should contain {"knowledge/query/knowledge-query-agent": true}

# Since already spawned this session, skip the background Task
Expected behavior: No second meta-agent spawned
```

**Verification**: Only 1 proposal file exists in `pending_improvements/` (not 2).

### Step 3.2: Verify non-blocking behavior

Measure that the usage-tracker inline operations (Steps 1.1 and 1.2) complete in under 2 seconds total. The meta-agent runs as a background Task and does NOT block the primary execution.

```markdown
# The following should happen in rapid succession:
1. record() — Read + Write of usage_registry.json
2. check_staleness() — computation on in-memory data
3. spawn background Task — non-blocking launch
4. Primary execution continues IMMEDIATELY

Verification: The primary task's history.md should show the next step
executing within seconds of the auto-improve hook, not waiting for the
meta-agent to complete.
```

---

## Phase 4: Edge Cases

### Step 4.1: Skill with no failure traces

Test the meta-agent on a skill that has never failed:

```markdown
Action: Task (auto-improve-meta-agent)

  skill_id: "validation/system/validation-agent"
  trigger: "manual"

Expected: Meta-agent finds zero failure traces in SmartMemory.
  Sets evidence_quality: none.
  Writes an observation-only entry to improvement_log.md (no proposal).
  No file created in pending_improvements/.
```

**Verification**: `improvement_log.md` has a new entry with `Proposal: DISCARDED` or `observation only`.

### Step 4.2: Anti-overfitting gate rejection

Seed a failure trace that is too task-specific:

```markdown
Action: Edit system/SmartMemory.md
Append:

---
- **experience_id**: exp_TEST_AI_005
- **primary_goal**: Generate a haiku about the color blue
- **final_outcome**: failure
- **components_used**: [knowledge-query-agent]
- **output_summary**: Agent searched KB for "haiku blue" and returned no results. Did not generate creative content directly.
- **learnings_or_issues**: knowledge-query-agent is not a creative writing tool. The failure is a routing error (wrong agent selected), not a spec deficiency in knowledge-query-agent.
```

If the meta-agent encounters only this type of trace, the anti-overfitting gate should **reject** the proposal:
> "Would adding haiku-generation fallback help even if haiku tasks never existed?" — **NO**.

**Verification**: `improvement_log.md` entry shows `Anti-overfitting: discarded`.

---

## Phase 5: Cleanup

### Step 5.1: Remove synthetic test data

```markdown
Action: Edit system/SmartMemory.md
Remove all exp_TEST_AI_* entries

Action: Write system/auto_improve/usage_registry.json
Restore to clean state: {"version": "1.0", "last_updated": null, "skills": {}}

Action: Bash rm system/auto_improve/pending_improvements/imp_*_knowledge_query*.md
(Remove test proposals only)
```

### Step 5.2: Preserve improvement_log.md entries

The improvement log entries from the test are useful as examples. Optionally keep them with a `[TEST]` prefix or remove them for a clean slate.

---

## Success Criteria

| Check | Pass Condition |
|-------|---------------|
| Usage registry updates | `record()` correctly increments `use_count` and rotates `previous_last_used` |
| Staleness detection | `check_staleness()` returns `is_stale: true` for 96h gap on 72h threshold |
| Non-stale detection | `check_staleness()` returns `is_stale: false` for 6h gap on 24h threshold |
| Meta-agent evidence collection | Agent finds all 4 seeded failure traces |
| Root cause classification | Failures classified using the 7-type taxonomy with at least 1 cluster |
| Improvement proposal written | Exactly 1 `.md` file in `pending_improvements/` with correct schema |
| Anti-overfitting gate passed | Proposal has `anti_overfitting_passed: true` with reasoning |
| Anti-overfitting gate rejected | Task-specific trace produces `discarded` result |
| Improvement log updated | `improvement_log.md` has entries for both passed and discarded proposals |
| Per-session dedup | Second invocation for same skill does NOT spawn a second meta-agent |
| Non-blocking | Primary execution is not delayed by meta-agent background Task |
| No-evidence graceful exit | Skill with zero failures produces observation-only log entry |
| No direct spec modification | `system/skills/knowledge/` files are UNCHANGED after the test |
