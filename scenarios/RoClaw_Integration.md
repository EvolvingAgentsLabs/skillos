---
name: roclaw-integration-scenario
description: End-to-end demonstration of SkillOS controlling the RoClaw robot — from high-level goal to physical navigation, obstacle recovery, and dream consolidation.
version: "1.0"
difficulty: intermediate
estimated_duration_minutes: 10
mode: EXECUTION
prerequisites:
  - evolving-memory server running on :8420
  - roclaw_bridge.py running on :8430
  - RoClaw hardware OR simulation mode
---

# RoClaw Integration Scenario

## Overview

This scenario demonstrates the full **Cognitive Trinity** architecture:
- **SkillOS** (Prefrontal Cortex) reasons about goals in markdown
- **RoClaw** (Cerebellum) executes reactive motor control
- **evolving-memory** (Hippocampus) stores and consolidates experiences

**Goal**: "Go get my shoes from the closet."

This deceptively simple command requires:
1. Querying memory for shoe location history
2. Planning a multi-room navigation route
3. Executing reactive motor control through RoClaw
4. Recovering from obstacles (cat in hallway, rug in bedroom)
5. Verifying arrival via scene analysis
6. Logging the experience for dream consolidation

---

## Stage 1: Goal Analysis and Memory Consultation

**Agent**: `system-agent` (SystemAgent)
**Pattern**: Sequential Pipeline

### Step 1.1: Parse Goal

```yaml
parsed_goal:
  action: "fetch"
  target_object: "shoes"
  target_location: "closet"
  constraints: []
  urgency: "normal"
```

### Step 1.2: Consult Memory

```markdown
Action: Task
Parameters:
  description: "Query memory for shoe location and closet navigation"
  prompt: "Query evolving-memory for: (1) last known location of shoes, (2) successful routes to closet, (3) any Negative Constraints for closet area"
  subagent_type: "roclaw-navigation-agent"
```

**Expected Memory Response**:
```yaml
shoe_location:
  last_seen: "closet, floor left side"
  confidence: 0.7
  last_updated: "2 days ago"
closet_routes:
  - route: "bedroom → hallway → closet"
    success_rate: 0.85
    avg_duration: 35s
  - route: "bedroom → living room → closet"
    success_rate: 0.60
    note: "Rug obstacle in living room"
negative_constraints:
  - "Hallway may have cat between 6-7 PM"
  - "Closet door sometimes partially closed — verify before entry"
```

### Step 1.3: Plan Execution

SystemAgent creates the execution plan:

```yaml
execution_plan:
  strategy: "Use hallway route (higher success rate)"
  steps:
    - phase: "navigate"
      agent: "roclaw-navigation-agent"
      goal: "Navigate to closet via hallway"
      constraints: ["check for cat in hallway", "verify closet door open"]
    - phase: "verify"
      agent: "roclaw-scene-analysis-agent"
      goal: "Confirm arrival at closet, locate shoes"
    - phase: "report"
      agent: "system-agent"
      goal: "Report result to user"
    - phase: "learn"
      agent: "roclaw-dream-agent"
      goal: "Log experience, update constraints if needed"
```

---

## Stage 2: Navigation Execution

**Agent**: `roclaw-navigation-agent`
**Pattern**: Sequential with Reactive Recovery

### Step 2.1: Pre-flight Check

```markdown
# Check robot status
Action: Bash
Command: curl -s http://localhost:8430/tool/robot.status
Expected: {pose: {...}, battery_level: 75, is_moving: false}

# Check current scene
Action: Bash
Command: curl -s -X POST http://localhost:8430/tool/robot.describe_scene
Expected: "Bedroom with desk, bed, and open doorway to hallway"

# Get semantic map for route planning
Action: Bash
Command: curl -s http://localhost:8430/tool/robot.get_map
Expected: {pose_map: [...], semantic_graph: {nodes: [...], edges: [...]}}
```

### Step 2.2: Execute Navigation (Step 1 — Exit Bedroom)

```markdown
Action: Bash
Command: curl -s -X POST http://localhost:8430/tool/robot.go_to \
  -H "Content-Type: application/json" \
  -d '{"location": "hallway", "constraints": "exit bedroom through doorway, avoid desk"}'
Expected: {success: true, trace_id: "tr_001", steps_taken: 2}
```

### Step 2.3: Execute Navigation (Step 2 — Traverse Hallway)

```markdown
# First check for cat (Negative Constraint)
Action: Bash
Command: curl -s -X POST http://localhost:8430/tool/robot.describe_scene
Expected: "Hallway with wooden floor. Cat sitting near the far end. Two doors on left."

# Cat detected! Adapt constraints
Action: Bash
Command: curl -s -X POST http://localhost:8430/tool/robot.go_to \
  -H "Content-Type: application/json" \
  -d '{"location": "closet", "constraints": "move slowly past the cat, maintain 30cm distance, do not startle"}'
```

**If cat blocks path** (obstacle recovery):

```markdown
# Robot gets stuck — cat won't move
Action: Bash
Command: curl -s -X POST http://localhost:8430/tool/robot.stop

# Wait 15 seconds for cat to move
# (Agent pauses)

# Re-check scene
Action: Bash
Command: curl -s -X POST http://localhost:8430/tool/robot.describe_scene
Expected: "Hallway. Cat has moved to doorway on left. Path ahead is clear."

# Resume navigation
Action: Bash
Command: curl -s -X POST http://localhost:8430/tool/robot.go_to \
  -H "Content-Type: application/json" \
  -d '{"location": "closet", "constraints": "path is now clear, proceed carefully"}'
Expected: {success: true, trace_id: "tr_002", steps_taken: 4}
```

---

## Stage 3: Scene Verification

**Agent**: `roclaw-scene-analysis-agent`
**Pattern**: Deep Analysis

### Step 3.1: Verify Arrival at Closet

```markdown
Action: Bash
Command: curl -s -X POST http://localhost:8430/tool/robot.analyze_scene
Expected: {
  analysis: "Small room with hanging clothes on left, shelves on right. Shoes visible on floor near left wall. Door frame behind robot.",
  features: [
    {"name": "hanging_clothes", "bbox": [10, 20, 200, 300], "confidence": 0.94},
    {"name": "shoes", "bbox": [30, 260, 120, 300], "confidence": 0.87},
    {"name": "shelf", "bbox": [300, 40, 470, 280], "confidence": 0.91}
  ]
}
```

### Step 3.2: Confirm Location and Object

```yaml
verification_result:
  location_verified: true
  location: "closet"
  location_confidence: 0.92
  matching_features: ["hanging_clothes", "shelves", "small_space", "shoes"]
  target_object_found: true
  object: "shoes"
  object_confidence: 0.87
  object_location: "Floor, left side of closet"
  assessment: "CONFIRMED — shoes located in closet as expected"
```

---

## Stage 4: Report and Learning

**Agent**: `system-agent` + `roclaw-dream-agent`

### Step 4.1: Report to User

```markdown
## Navigation Complete ✓

**Goal**: Get shoes from closet
**Status**: SUCCESS
**Duration**: ~45 seconds
**Route**: Bedroom → Hallway (cat detour) → Closet

**Shoes located**: Floor, left side of closet (confidence: 87%)

**Notable events**:
- Cat encountered in hallway — waited 15s for it to move
- Closet door was open — no recovery needed

**Tip**: The shoes are on the floor to the left as you enter the closet.
```

### Step 4.2: Log Experience

```markdown
# Log to evolving-memory
Action: Bash
Command: curl -s -X POST http://localhost:8420/traces \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Fetch shoes from closet",
    "hierarchyLevel": 1,
    "outcome": "SUCCESS",
    "confidence": 0.87,
    "source": "REAL_WORLD",
    "actions": [
      {"description": "Planned hallway route based on memory", "result": "Plan created"},
      {"description": "Navigated bedroom to hallway", "result": "Success, 2 steps"},
      {"description": "Cat obstacle in hallway — waited 15s", "result": "Cat moved, path cleared"},
      {"description": "Navigated hallway to closet", "result": "Success, 4 steps"},
      {"description": "Verified arrival and located shoes", "result": "Shoes found, confidence 0.87"}
    ],
    "tags": ["navigation", "fetch", "closet", "shoes", "cat-obstacle", "success"],
    "domain": "robotics"
  }'
```

### Step 4.3: Update Constraints

```markdown
# Cat encounter creates a soft constraint update
Action: Write
File: projects/RoClaw/workspace/state/constraints.md
Content: |
  execution_status: COMPLETED
  last_obstacle: "cat in hallway"
  constraint_update: "Cat encountered in hallway at current time — may recur"
  navigation_note: "Hallway route successful despite cat; wait strategy effective"
```

---

## Stage 5: Dream Consolidation (Post-Session)

**Agent**: `roclaw-dream-agent`
**Trigger**: Post-session (>3 new traces)

### Expected Dream Output

```yaml
dream_results:
  traces_processed: 5
  phases: ["SWS", "REM", "CONSOLIDATION"]

  insights:
    - "Cat obstacle in hallway is a recurring pattern (3 occurrences this week)"
    - "Wait strategy for cat has 80% success rate (vs. re-route at 60%)"
    - "Closet shoe location is consistent — update confidence to 0.90"

  new_negative_constraints:
    - "Cat is frequently in hallway — always check before traversing"

  strategy_updates:
    - strategy: "Hallway traversal"
      update: "Add cat check step before full-speed navigation"
      new_confidence: 0.88
    - strategy: "Shoe fetch from closet"
      update: "New dedicated strategy created from 3 successful traces"
      confidence: 0.85
```

---

## Success Criteria

| Criterion | Threshold | Measurement |
|---|---|---|
| Goal completed | Yes | Shoes located in closet |
| Navigation success | ≥1 of 2 routes works | robot.go_to returns success |
| Obstacle recovery | Graceful handling | No crashes, no stuck state |
| Scene verification | Confidence ≥ 0.80 | analyze_scene confidence |
| Trace logged | Complete trace ingested | evolving-memory /traces response |
| Memory consulted | Strategy used | Query response influenced route choice |
| Execution time | <120 seconds | Total wall clock time |
| Cost | <$0.10 | LLM inference costs |

---

## Simulation Mode

To run this scenario without hardware:

```bash
# Terminal 1: Start evolving-memory
cd /path/to/evolving-memory && python -m evolving_memory.server --port 8420

# Terminal 2: Start bridge in simulation mode
cd /path/to/skillos && python roclaw_bridge.py --port 8430 --simulate

# Terminal 3: Run scenario
cd /path/to/skillos && python skillos.py
# Then: skillos execute: "Run the RoClaw Integration scenario"
```

The simulation client provides realistic-looking responses for all 9 robot tools, with simulated pose tracking and semantic map building.

---

## Extensions

After mastering this scenario, try these variations:

1. **Multi-object fetch**: "Get my shoes AND my jacket from the closet"
2. **Unknown location**: "Find my keys" (no memory of last location — requires exploration)
3. **Time-pressure**: "Quickly get my shoes — I'm in a hurry" (urgency=high, prioritize speed)
4. **Night mode**: Reduced lighting → lower VLM confidence → more cautious navigation
5. **Multi-room sweep**: "Check all rooms for the cat" (parallel exploration + reporting)
