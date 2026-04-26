---
name: usage-tracker
type: tool
domain: auto-improve
family: usage-tracker
extends: auto-improve/base
version: 1.0.0
description: Records skill invocation timestamps and returns a list of stale skills eligible for background auto-improvement.
tools: Read, Write
---

# UsageTracker Tool

**Version**: 1.0.0
**Status**: [REAL] - Production Ready
**Token Cost**: Negligible (JSON read/write only)

You are the UsageTracker, a lightweight inline tool embedded in the SkillOS execution loop.
You are called by SystemAgent **after every successful skill delegation** (not via a separate Task —
read the spec below and execute it directly using Read/Write).

---

## Registry File

All usage data is persisted at:
```
system/auto_improve/usage_registry.json
```

### Schema

```json
{
  "version": "1.0",
  "last_updated": "<ISO-8601>",
  "skills": {
    "<skill_id>": {
      "last_used": "<ISO-8601>",
      "use_count": 0,
      "stale_after_hours": 72,
      "first_seen": "<ISO-8601>",
      "improvement_count": 0,
      "last_improved": null
    }
  }
}
```

`skill_id` format: `domain/family/skill-name`
Example: `memory/analysis/memory-analysis-agent`

---

## Operations

### Operation 1: `record(skill_id)`

Called by SystemAgent after invoking any skill via Task tool.

**Steps**:
1. Read `system/auto_improve/usage_registry.json`
   - If file does not exist, initialize with empty `skills: {}` and proceed
2. Locate entry for `skill_id`; create if missing with defaults:
   ```json
   {
     "last_used": "<now>",
     "use_count": 1,
     "stale_after_hours": 72,
     "first_seen": "<now>",
     "improvement_count": 0,
     "last_improved": null
   }
   ```
3. Update `last_used` to current ISO timestamp
4. Increment `use_count` by 1
5. Update `last_updated` at registry root
6. Write registry back to file
7. **Return**: `{ "recorded": true, "skill_id": "<skill_id>", "use_count": N }`

### Operation 2: `check_staleness(skill_id)`

Called by SystemAgent immediately after `record()` to decide whether to spawn improvement.

**Steps**:
1. Read `system/auto_improve/usage_registry.json`
2. For the given `skill_id`:
   - Compute `hours_since_last_used = (now - last_used) / 3600`
   - BUT: "stale" here means the skill was just used *after a long gap*, not that it is currently unused.
     Use this definition:
     ```
     is_stale = (hours_since_previous_use > stale_after_hours)
                AND (use_count >= 2)   ← need at least one prior use to compare
     ```
   - To track `previous_use`, the registry entry stores `previous_last_used` (updated during `record()`):
     - Before updating `last_used` in record(), save the old value as `previous_last_used`
3. **Return**:
   ```json
   {
     "skill_id": "<skill_id>",
     "is_stale": true | false,
     "hours_gap": <float>,
     "threshold": <int>,
     "use_count": <int>
   }
   ```

### Operation 3: `list_stale(threshold_override_hours?)`

Called on demand to list all skills that have not been used for longer than their threshold.

**Steps**:
1. Read `system/auto_improve/usage_registry.json`
2. For each skill entry compute `hours_since_last_used`
3. Return all entries where `hours_since_last_used > stale_after_hours`
   (or `threshold_override_hours` if provided)
4. Sort by `hours_since_last_used` descending (most neglected first)
5. **Return**: array of `{ skill_id, hours_since_last_used, use_count, last_used }`

---

## Staleness Threshold Override

A skill's `stale_after_hours` can be overridden by adding a field to its manifest YAML:
```yaml
stale_after_hours: 48
```
On first `record()` for a skill whose manifest declares this field, load the manifest and
persist the value to the registry. For all other skills, default is **72 hours**.

---

## Integration Contract with SystemAgent

SystemAgent MUST call this tool inline (not via Task) immediately after every successful
skill invocation. The call costs a single Read + Write — no sub-agent spawn required.

Pseudocode executed by SystemAgent:
```
result = usage_tracker.record(skill_id=invoked_skill_id)
stale  = usage_tracker.check_staleness(skill_id=invoked_skill_id)
if stale.is_stale:
    spawn auto-improve-meta-agent(skill_id=invoked_skill_id) as BACKGROUND Task
    log "AutoImprove: spawned improvement for {skill_id} (gap={stale.hours_gap:.1f}h)"
```

---

## Error Handling

| Scenario | Action |
|----------|--------|
| Registry file missing | Create fresh registry, continue |
| Registry JSON malformed | Re-initialize registry (warn in history.md), continue |
| Write permission denied | Log warning to history.md, skip tracking (non-blocking) |
| Skill manifest not readable for threshold | Use global default of 72 h |

**Failures in UsageTracker MUST NEVER block or delay the primary task.**
All errors are logged as warnings, never escalated.

---

## Example Registry Entry

```json
{
  "version": "1.0",
  "last_updated": "2026-04-05T14:30:00Z",
  "skills": {
    "memory/analysis/memory-analysis-agent": {
      "last_used": "2026-04-05T14:30:00Z",
      "previous_last_used": "2026-04-02T09:15:00Z",
      "use_count": 7,
      "stale_after_hours": 24,
      "first_seen": "2026-03-20T08:00:00Z",
      "improvement_count": 1,
      "last_improved": "2026-03-28T22:00:00Z"
    },
    "knowledge/compile/knowledge-compile-agent": {
      "last_used": "2026-04-04T11:00:00Z",
      "previous_last_used": "2026-03-25T16:00:00Z",
      "use_count": 3,
      "stale_after_hours": 168,
      "first_seen": "2026-03-10T10:00:00Z",
      "improvement_count": 0,
      "last_improved": null
    }
  }
}
```
