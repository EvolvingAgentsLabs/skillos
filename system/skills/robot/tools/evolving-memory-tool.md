---
name: evolving-memory-tool
description: Direct bridge to the evolving-memory Hippocampus REST API for trace ingestion, strategy queries, dream consolidation, and knowledge graph operations.
type: tool
version: "1.0"
status: "[REAL] - Production Ready"
last_updated: "2026-03-22"
tools: Bash, WebFetch, Read, Write
extends: robot/base
---

# Evolving Memory Tool

**Component Type**: Tool
**Version**: v1.0
**Status**: [REAL] - Production Ready
**Claude Tool Mapping**: Bash, WebFetch, Read, Write
**Reliability**: 92%

## Purpose

The EvolvingMemoryTool provides SkillOS agents with direct access to the evolving-memory server — the shared Hippocampus of the Cognitive Trinity. This enables:

- **Trace Ingestion**: Log execution experiences with hierarchical levels and fidelity weights
- **Strategy Queries**: Retrieve learned strategies for navigation, manipulation, and planning
- **Dream Consolidation**: Trigger bio-inspired memory consolidation (SWS → REM → Integration)
- **Knowledge Graph**: Query the hierarchical node graph for learned patterns

## Architecture

```
SkillOS Agent
  ↓ (curl / WebFetch to :8420)
evolving-memory REST API
  ↓ (SQLite + Pydantic v2)
Trace Store → Dream Engine → Strategy Graph
```

## Prerequisites

The evolving-memory server must be running:

```bash
# From the evolving-memory directory
cd /path/to/evolving-memory
python -m evolving_memory.server --port 8420
```

## API Reference

### POST /traces — Ingest a Trace

Record an execution experience for later dream consolidation.

```yaml
parameters:
  goal: string              # What was attempted
  hierarchyLevel: number    # 1=GOAL, 2=STRATEGY, 3=TACTICAL, 4=REACTIVE
  outcome: string           # SUCCESS, FAILURE, PARTIAL, ABORTED
  confidence: number        # 0.0-1.0
  source: string            # REAL_WORLD, SIM_3D, SIM_2D, DREAM_TEXT
  actions: object[]         # Array of {description, result, timestamp}
  tags: string[]            # Searchable tags
  domain: string            # Domain isolation key (default: "robotics")
returns:
  trace_id: string
  status: string
```

**Execution Pattern**:
```bash
curl -s -X POST http://localhost:8420/traces \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Navigate to kitchen",
    "hierarchyLevel": 1,
    "outcome": "SUCCESS",
    "confidence": 0.85,
    "source": "REAL_WORLD",
    "actions": [
      {"description": "Planned route via hallway", "result": "3-step plan created"},
      {"description": "Executed step 1: exit bedroom", "result": "arrived at hallway"},
      {"description": "Executed step 2: traverse hallway", "result": "arrived at kitchen entrance"},
      {"description": "Executed step 3: enter kitchen", "result": "goal reached"}
    ],
    "tags": ["navigation", "kitchen", "multi-step"],
    "domain": "robotics"
  }'
```

### POST /dream/run — Trigger Dream Consolidation

Run the bio-inspired 3-phase dream cycle over recent traces.

```yaml
parameters:
  domain: string          # Domain to consolidate (default: "robotics")
  max_traces: number      # Max traces to process (default: 50)
returns:
  dream_id: string
  phases_completed: string[]  # ["SWS", "REM", "CONSOLIDATION"]
  strategies_created: number
  strategies_updated: number
  insights: string[]
```

**Execution Pattern**:
```bash
curl -s -X POST http://localhost:8420/dream/run \
  -H "Content-Type: application/json" \
  -d '{"domain": "robotics", "max_traces": 50}'
```

**Dream Phases**:
1. **SWS (Slow-Wave Sleep)**: Replay traces, extract failure patterns, compress action sequences
2. **REM**: Abstract strategies from concrete experiences, generate hypothetical scenarios
3. **Consolidation**: Merge new strategies with existing knowledge, resolve contradictions

### GET /query — Query Memory

Semantic search across the knowledge base.

```yaml
parameters:
  q: string              # Natural language query
  domain: string         # Optional domain filter
  level: number          # Optional hierarchy level filter (1-4)
  limit: number          # Max results (default: 10)
returns:
  path: string           # Recommended approach
  reasoning: string      # Why this recommendation
  confidence: number     # 0.0-1.0
  entry_point: object    # Best matching node from knowledge graph
```

**Execution Pattern**:
```bash
curl -s "http://localhost:8420/query?q=navigate+to+kitchen&domain=robotics&limit=5"
```

### GET /nodes/{id} — Fetch Knowledge Node

Retrieve a specific node from the hierarchical knowledge graph.

```yaml
parameters:
  id: string             # Node UUID
returns:
  id: string
  goal: string
  level: number
  strategy: string
  confidence: number
  children: object[]
  parent_id: string
```

**Execution Pattern**:
```bash
curl -s http://localhost:8420/nodes/{node_id}
```

### GET /domains — List Domains

List all available knowledge domains.

```bash
curl -s http://localhost:8420/domains
```

### GET /stats — Memory Statistics

Get aggregate statistics about the knowledge base.

```yaml
returns:
  total_traces: number
  total_nodes: number
  domains: string[]
  traces_by_outcome: object
  traces_by_level: object
  average_confidence: number
```

**Execution Pattern**:
```bash
curl -s http://localhost:8420/stats
```

### POST /route — Router Query

Ask the intelligent router for the best approach to a goal.

```yaml
parameters:
  goal: string
  context: object        # Current context (scene, constraints, etc.)
  domain: string
returns:
  recommended_strategy: string
  confidence: number
  alternative_strategies: string[]
  reasoning: string
```

**Execution Pattern**:
```bash
curl -s -X POST http://localhost:8420/route \
  -H "Content-Type: application/json" \
  -d '{"goal": "fetch water from kitchen", "domain": "robotics", "context": {"current_location": "bedroom"}}'
```

## Hierarchy Levels

| Level | Name | Description | Example |
|---|---|---|---|
| 1 | GOAL | High-level intent | "Fetch a drink" |
| 2 | STRATEGY | Multi-step plan | "bedroom → hallway → kitchen" |
| 3 | TACTICAL | Constraint-aware sub-goal | "navigate around couch" |
| 4 | REACTIVE | Sub-second motor corrections | Bytecode sequences |

## Trace Source Fidelity

| Source | Weight | Description |
|---|---|---|
| REAL_WORLD | 1.0 | Ground truth from physical robot |
| SIM_3D | 0.8 | MuJoCo physics simulation |
| SIM_2D | 0.5 | Kinematic simulation (virtual_roclaw) |
| DREAM_TEXT | 0.3 | Pure text-based dream scenarios |

Higher fidelity traces receive stronger confidence boosts during dream consolidation.

## Error Modes

```yaml
error_modes:
  SERVER_UNAVAILABLE:
    description: "evolving-memory server not running"
    probability: 5%
    recovery: "Start server: python -m evolving_memory.server --port 8420"

  DOMAIN_NOT_FOUND:
    description: "Queried domain has no data yet"
    probability: 10%
    recovery: "Ingest traces first, or use default domain"

  DREAM_IN_PROGRESS:
    description: "Dream cycle already running"
    probability: 3%
    recovery: "Wait for completion, check /stats for status"
```

## Integration with SkillOS Memory

This tool bridges SkillOS's SmartMemory.md (markdown-based) with evolving-memory's SQLite-backed knowledge graph:

| Feature | SmartMemory.md | evolving-memory |
|---|---|---|
| **Format** | Markdown with YAML frontmatter | SQLite + Pydantic models |
| **Scope** | SkillOS execution traces | Cross-system traces (robot + agents) |
| **Learning** | Pattern extraction via LLM | Bio-inspired dream consolidation |
| **Query** | Grep + LLM analysis | Semantic search + router |
| **Best For** | SkillOS-specific workflows | Robot navigation + shared knowledge |

**Sync Pattern**: After SkillOS executes a robot task, log the experience to BOTH:
1. SmartMemory.md (via MemoryTraceManager) — for SkillOS learning
2. evolving-memory /traces (via this tool) — for robot dream consolidation

## Example: Full Navigation Cycle

```markdown
# 1. Query memory for known strategies
Action: Bash
Command: curl -s "http://localhost:8420/query?q=navigate+to+kitchen&domain=robotics"
Observation: {path: "hallway route", confidence: 0.82, reasoning: "3 successful traces"}

# 2. Execute navigation via RoClawTool
Action: Bash
Command: curl -s -X POST http://localhost:8430/tool/robot.go_to \
  -H "Content-Type: application/json" \
  -d '{"location": "kitchen", "constraints": "use hallway route"}'
Observation: {success: true, trace_id: "tr_abc123", steps_taken: 3}

# 3. Log trace to evolving-memory
Action: Bash
Command: curl -s -X POST http://localhost:8420/traces \
  -H "Content-Type: application/json" \
  -d '{"goal": "Navigate to kitchen", "hierarchyLevel": 1, "outcome": "SUCCESS", "confidence": 0.85, "source": "REAL_WORLD", "domain": "robotics"}'
Observation: {trace_id: "tr_def456", status: "ingested"}

# 4. Trigger dream consolidation (optional, typically nightly)
Action: Bash
Command: curl -s -X POST http://localhost:8420/dream/run \
  -d '{"domain": "robotics"}'
Observation: {strategies_created: 1, strategies_updated: 2, insights: ["hallway route is most reliable"]}
```
