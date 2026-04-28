---
name: roclaw-dream-consolidation-scenario
description: Bio-inspired dream consolidation over RoClaw trace files. Reads local .md traces, runs SWS/REM/Consolidation phases, and writes strategies and dream journal entries. Replaces the evolving-memory HTTP dream cycle.
version: "2.0"
difficulty: beginner
estimated_duration_minutes: 5
mode: EXECUTION
prerequisites:
  - RoClaw trace files exist in traces/sim3d/, traces/real_world/, or traces/dream_sim/
---

# RoClaw Dream Consolidation Scenario

## Overview

This scenario performs the robot's dream consolidation cycle — transforming raw execution traces into refined navigation strategies. It replaces the former evolving-memory server-based dream cycle with a pure filesystem approach.

**Architecture**: RoClaw writes `.md` trace files during navigation. This scenario reads those traces and produces strategies + dream journal entries.

**Agent**: `roclaw-dream-consolidation-agent`

---

## Phase 1: Collect — Gather Unconsolidated Traces

### Step 1.1: Discover trace files

```markdown
Action: Glob
Pattern: skillos_robot/traces/sim3d/*.md
Observation: [List of sim3d trace files]

Action: Glob
Pattern: skillos_robot/traces/real_world/*.md
Observation: [List of real_world trace files]

Action: Glob
Pattern: skillos_robot/traces/dream_sim/*.md
Observation: [List of dream_sim trace files]
```

### Step 1.2: Check for already-consolidated traces

```markdown
Action: Glob
Pattern: skillos_robot/traces/dreams/*.md
Observation: [Previous dream journal entries — check timestamps to skip already-processed traces]
```

### Step 1.3: Read and classify traces

For each trace file:
```markdown
Action: Read
File: skillos_robot/traces/sim3d/{filename}.md
Observation: [YAML frontmatter with outcome, source, fidelity, confidence + action body]
```

Classify into buckets:
```yaml
trace_summary:
  total: 15
  by_outcome:
    success: 9
    failure: 4
    partial: 2
  by_source:
    sim_3d: 10
    real_world: 3
    dream_text: 2
  fidelity_weighted_count: 11.6  # sum of (count * fidelity)
```

**Decision**: Skip if < 3 unconsolidated traces (not enough data to learn from).

---

## Phase 2: Consolidate — SWS, REM, Consolidation

### Step 2.1: SWS (Slow-Wave Sleep) — Failure Analysis

For each failure trace, invoke the `roclaw-dream-consolidation-agent` with the **Failure Analysis** prompt:

```markdown
Action: Task
Parameters:
  description: "Analyze failure traces for negative constraints"
  prompt: |
    Read these failed robot traces and extract negative constraints.
    Use the Failure Analysis prompt template.

    Traces to analyze:
    - skillos_robot/traces/sim3d/2026-04-05_14-30-00_navigate-to-red-cube.md
    - skillos_robot/traces/real_world/2026-04-05_16-00-00_go-to-kitchen.md
  subagent_type: "roclaw-dream-consolidation-agent"
```

Expected output:
```yaml
negative_constraints:
  - description: "Do not attempt tight turns in narrow corridors"
    context: "narrow corridor navigation"
    severity: "high"
    evidence: "2 traces from sim3d"
  - description: "Reduce speed when approaching doorways"
    context: "doorway transit"
    severity: "medium"
    evidence: "1 trace from real_world"
```

### Step 2.2: REM — Strategy Abstraction

For each success trace group, invoke the agent with the **Strategy Abstraction** prompt:

```markdown
Action: Task
Parameters:
  description: "Abstract successful traces into strategies"
  prompt: |
    Read these successful robot traces and create reusable strategies.
    Use the Strategy Abstraction prompt template.
    Check existing strategies in skillos_robot/strategies/ for overlap.
    If overlap found, use Strategy Merge instead.

    Traces to analyze:
    - skillos_robot/traces/sim3d/2026-04-05_14-35-00_navigate-to-door.md
    - skillos_robot/traces/sim3d/2026-04-05_15-00-00_find-blue-box.md
    - skillos_robot/traces/real_world/2026-04-05_16-30-00_go-to-closet.md
  subagent_type: "roclaw-dream-consolidation-agent"
```

### Step 2.3: Consolidation — Merge & Resolve

For overlapping strategies, invoke with the **Strategy Merge** prompt:

```markdown
Action: Task
Parameters:
  description: "Merge new evidence into existing strategies"
  prompt: |
    Read the existing strategy at skillos_robot/strategies/level_2_routes/wall_following.md
    and the new trace evidence. Produce an updated strategy.

    Existing strategy: skillos_robot/strategies/level_2_routes/wall_following.md
    New evidence traces:
    - skillos_robot/traces/sim3d/2026-04-05_15-10-00_follow-wall.md
  subagent_type: "roclaw-dream-consolidation-agent"
```

---

## Phase 3: Distill — Write Outputs

### Step 3.1: Write new/updated strategy files

```markdown
Action: Write
File: skillos_robot/strategies/level_2_routes/doorway_transit.md
Content: |
  ---
  title: "Doorway Transit"
  level: 2
  trigger_goals: ["go through door", "enter room", "exit room"]
  confidence: 0.82
  source: dream
  created: "2026-04-06"
  evidence_count: 4
  ---

  # Doorway Transit

  ## Preconditions
  - Doorway detected in VLM scene analysis
  - Door is open or ajar

  ## Steps
  1. Slow approach — reduce speed to 100
  2. Center alignment — use VLM bbox to center on doorway
  3. Verify clearance via scene description
  4. Pass through at reduced speed

  ## Negative Constraints
  - Do not attempt full-speed approach to doorways
  - Do not turn sharply while in doorframe
```

### Step 3.2: Write dream journal entry

```markdown
Action: Write
File: skillos_robot/traces/dreams/2026-04-06_dream.md
Content: |
  ---
  timestamp: "2026-04-06T03:00:00Z"
  traces_processed: 15
  failures_analyzed: 4
  strategies_created: 1
  strategies_updated: 2
  constraints_extracted: 3
  sources: [sim_3d, real_world, dream_text]
  ---

  # Dream Journal: 2026-04-06

  Analyzed 15 traces (10 sim3d, 3 real-world, 2 dream). Created a new
  "Doorway Transit" strategy from 4 successful doorway passages. Updated
  "Wall Following" and "Target Approach" strategies with refined spatial
  rules. Extracted 3 negative constraints: avoid tight corridor turns,
  reduce doorway approach speed, and check for moving obstacles before
  hallway traversal.
```

### Step 3.3: (Optional) Archive processed traces

Move processed traces to prevent reprocessing:
```markdown
Action: Bash
Command: mkdir -p skillos_robot/traces/consolidated/sim3d && mv skillos_robot/traces/sim3d/2026-04-05_*.md skillos_robot/traces/consolidated/sim3d/
```

---

## Success Criteria

| Criterion | Threshold | Measurement |
|---|---|---|
| Traces read | All unconsolidated | Glob count matches processed count |
| Failures analyzed | 100% of failure traces | Constraint generated per failure |
| Strategies created/updated | >= 1 | Strategy .md files written |
| Dream journal written | Yes | File exists in traces/dreams/ |
| No data loss | Zero traces deleted | Source traces preserved |
| Execution time | < 5 minutes | Wall clock time |

---

## Running This Scenario

```bash
# From skillos:
skillos execute: "Run the RoClaw Dream Consolidation scenario"

# Or directly invoke the agent:
skillos execute: "Invoke roclaw-dream-consolidation-agent to consolidate today's navigation traces"

# Targeted consolidation (specific source):
skillos execute: "Run dream consolidation on RoClaw sim3d traces only"
```

---

## Scheduling

For automated nightly dreams:
```bash
# Cron or launchd:
0 3 * * * cd /path/to/skillos && skillos execute: "Run the RoClaw Dream Consolidation scenario"
```

Or via SkillOS scheduler:
```
schedule every 24h dream consolidation for RoClaw navigation
```
