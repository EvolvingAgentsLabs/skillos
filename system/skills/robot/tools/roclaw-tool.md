---
name: roclaw-tool
description: Bridge between SkillOS agents and RoClaw physical robot. Maps high-level navigation and interaction commands to RoClaw's 9 robot tools via the RoClaw Bridge API.
type: tool
version: "1.0"
status: "[REAL] - Production Ready"
last_updated: "2026-03-22"
tools: Bash, Read, Write
depends_on:
  - roclaw_bridge.py
extends: robot/base
---

# RoClaw Tool

**Component Type**: Tool
**Version**: v1.0
**Status**: [REAL] - Production Ready
**Claude Tool Mapping**: Bash, Read, Write
**Reliability**: 88%

## Purpose

The RoClawTool is the bridge that makes the physical robot (RoClaw) available as a "skill" within the SkillOS markdown universe. It translates high-level SkillOS agent commands into RoClaw's 9 robot tool invocations via the RoClaw Bridge HTTP API.

This tool realizes the **Cognitive Trinity** architecture:
- **SkillOS** = Prefrontal Cortex (planning, reasoning, dynamic agent creation, dream consolidation)
- **RoClaw** = Cerebellum (reactive motor control, VLM-powered navigation, trace file writer)

## Architecture

```
SkillOS Agent (e.g., RoClawNavigationAgent)
  ↓ (Bash curl to :8430)
roclaw_bridge.py (HTTP :8430)
  ↓ (WebSocket to OpenClaw Gateway :8080)
RoClaw CortexNode
  ↓ (tool invocation)
VisionLoop + BytecodeCompiler + UDP → ESP32-S3
```

## Prerequisites

Start the RoClaw Bridge before using this tool:

```bash
# Start the bridge server (connects to OpenClaw Gateway)
python roclaw_bridge.py --port 8430 --gateway ws://localhost:8080

# Or with simulation mode (uses virtual_roclaw instead of real hardware)
python roclaw_bridge.py --port 8430 --simulate
```

## Robot Tool Definitions

### 1. robot.go_to
**Purpose**: Navigate to a named location using hierarchical planning.
**Latency**: 10s-5min (depends on distance and obstacles)
**Cost**: Low (local inference)

```yaml
parameters:
  location: string     # Target location name (e.g., "kitchen", "closet")
  constraints: string  # Optional navigation constraints (e.g., "avoid the cat")
returns:
  success: boolean
  message: string
  trace_id: string     # Hierarchical trace ID for memory logging
  steps_taken: number
```

**Execution Pattern**:
```bash
curl -s -X POST http://localhost:8430/tool/robot.go_to \
  -H "Content-Type: application/json" \
  -d '{"location": "kitchen", "constraints": "avoid obstacles, prefer left wall"}'
```

### 2. robot.explore
**Purpose**: Autonomous exploration with strategy-guided wandering.
**Latency**: 30s-10min
**Cost**: Low

```yaml
parameters:
  constraints: string  # Optional exploration constraints
  duration_seconds: number  # Max exploration time (default: 120)
returns:
  success: boolean
  locations_discovered: string[]
  map_updates: number
  trace_id: string
```

**Execution Pattern**:
```bash
curl -s -X POST http://localhost:8430/tool/robot.explore \
  -H "Content-Type: application/json" \
  -d '{"constraints": "map the living room", "duration_seconds": 60}'
```

### 3. robot.describe_scene
**Purpose**: Get a VLM-powered description of what the robot currently sees.
**Latency**: 1-3s
**Cost**: Low (single VLM inference)

```yaml
parameters: {}  # No parameters needed
returns:
  success: boolean
  description: string    # Natural language scene description
  objects: string[]      # Detected objects
  spatial_layout: string # Spatial relationship description
```

**Execution Pattern**:
```bash
curl -s -X POST http://localhost:8430/tool/robot.describe_scene
```

### 4. robot.stop
**Purpose**: Emergency halt - immediately stops all motor activity.
**Latency**: <100ms
**Cost**: Free

```yaml
parameters: {}
returns:
  success: boolean
  message: string
```

**Execution Pattern**:
```bash
curl -s -X POST http://localhost:8430/tool/robot.stop
```

### 5. robot.status
**Purpose**: Query current robot state (pose, motor state, battery).
**Latency**: <500ms
**Cost**: Free

```yaml
parameters: {}
returns:
  success: boolean
  pose: {x: number, y: number, heading: number}
  motor_state: string
  battery_level: number
  is_moving: boolean
```

**Execution Pattern**:
```bash
curl -s http://localhost:8430/tool/robot.status
```

### 6. robot.read_memory
**Purpose**: Read the robot's full memory context (hardware profile, strategies, identity).
**Latency**: <200ms
**Cost**: Free

```yaml
parameters: {}
returns:
  success: boolean
  memory: string  # Full markdown memory context
  sections: string[]  # Available memory sections
```

**Execution Pattern**:
```bash
curl -s http://localhost:8430/tool/robot.read_memory
```

### 7. robot.record_observation
**Purpose**: Label the current location in the semantic map.
**Latency**: <500ms
**Cost**: Free

```yaml
parameters:
  label: string       # Location name (e.g., "charging_station")
  confidence: number  # Confidence score 0-1 (default: 0.8)
returns:
  success: boolean
  pose: {x: number, y: number, heading: number}
```

**Execution Pattern**:
```bash
curl -s -X POST http://localhost:8430/tool/robot.record_observation \
  -H "Content-Type: application/json" \
  -d '{"label": "charging_station", "confidence": 0.9}'
```

### 8. robot.analyze_scene
**Purpose**: Deep VLM analysis of the current camera view with bounding boxes.
**Latency**: 2-5s
**Cost**: Low

```yaml
parameters: {}
returns:
  success: boolean
  analysis: string
  features: {name: string, bbox: number[], confidence: number}[]
```

**Execution Pattern**:
```bash
curl -s -X POST http://localhost:8430/tool/robot.analyze_scene
```

### 9. robot.get_map
**Purpose**: Retrieve the current topological semantic map.
**Latency**: <200ms
**Cost**: Free

```yaml
parameters: {}
returns:
  success: boolean
  pose_map: {label: string, pose: object, timestamp: string}[]
  semantic_graph: {nodes: object[], edges: object[]}
```

**Execution Pattern**:
```bash
curl -s http://localhost:8430/tool/robot.get_map
```

## Decision Matrix

| Situation | Tool | Reason |
|---|---|---|
| Navigate to known location | robot.go_to | Hierarchical planning + reactive control |
| Discover new areas | robot.explore | Strategy-guided autonomous wandering |
| Check surroundings before moving | robot.describe_scene | Quick VLM snapshot |
| Detailed scene understanding | robot.analyze_scene | Deep analysis with bounding boxes |
| Emergency | robot.stop | Immediate halt, <100ms |
| Check robot state | robot.status | Pose, battery, motor state |
| Build spatial knowledge | robot.record_observation | Label current location |
| Plan routes | robot.get_map | Full topological graph |
| Understand robot capabilities | robot.read_memory | Hardware profile + strategies |

## Error Modes

```yaml
error_modes:
  BRIDGE_UNAVAILABLE:
    description: "roclaw_bridge.py not running or unreachable"
    probability: 5%
    recovery: "Start bridge with: python roclaw_bridge.py --port 8430"

  GATEWAY_DISCONNECTED:
    description: "OpenClaw Gateway not available"
    probability: 8%
    recovery: "Check OpenClaw Gateway status, retry after 5s"

  ROBOT_STUCK:
    description: "Robot physically stuck, vision loop detecting low entropy"
    probability: 15%
    recovery: "robot.stop, then robot.describe_scene, then re-plan with constraints"

  NAVIGATION_TIMEOUT:
    description: "Navigation did not reach destination within timeout"
    probability: 10%
    recovery: "robot.stop, robot.get_map, re-plan via roclaw-navigation-agent"

  HARDWARE_ERROR:
    description: "ESP32 communication failure"
    probability: 3%
    recovery: "robot.status to diagnose, escalate if persistent"
```

## Retry Policy

```yaml
retry_policy:
  robot.go_to: {max_attempts: 2, backoff: 5s, on_failure: "re-plan with fresh scene"}
  robot.explore: {max_attempts: 1, on_failure: "reduce scope, try smaller area"}
  robot.describe_scene: {max_attempts: 3, backoff: 2s}
  robot.stop: {max_attempts: 3, backoff: 0s, critical: true}
  robot.status: {max_attempts: 2, backoff: 1s}
```

## Cost Tiers

```yaml
tier_0_free: [robot.stop, robot.status, robot.read_memory, robot.get_map]
tier_1_low: [robot.describe_scene, robot.record_observation, robot.analyze_scene]
tier_2_medium: [robot.go_to, robot.explore]  # VLM inference cycles
```

## Integration with SkillOS Agents

### Navigation Agent Pattern
```markdown
Action: Bash
Command: curl -s http://localhost:8430/tool/robot.describe_scene
Observation: [Scene description from VLM]

Action: Bash
Command: curl -s -X POST http://localhost:8430/tool/robot.go_to \
  -H "Content-Type: application/json" \
  -d '{"location": "kitchen", "constraints": "avoid the cat near the couch"}'
Observation: [Navigation result with trace_id]
```

### Dream Consolidation Pattern
```markdown
# After navigation sessions, trigger dream consolidation via skillos scenario
# RoClaw writes trace .md files automatically during navigation
# Run the dream consolidation scenario to process them:
skillos execute: "Run the RoClaw Dream Consolidation scenario"
```

## Simulation Mode

For testing without hardware, use the `--simulate` flag on the bridge:

```bash
python roclaw_bridge.py --port 8430 --simulate
```

This uses `virtual_roclaw.ts` internally, providing:
- Virtual ESP32-S3 (kinematic simulation)
- Virtual ESP32-CAM (minimal MJPEG stream)
- Full tool compatibility with simulated responses
- Trace logging to local .md files (with source=SIM_2D)

## Trace Fidelity

All actions through this tool are tagged with `TraceSource` for dream weighting:

| Mode | TraceSource | Fidelity Weight |
|---|---|---|
| Real hardware | REAL_WORLD | 1.0 |
| MuJoCo 3D sim | SIM_3D | 0.8 |
| Virtual RoClaw | SIM_2D | 0.5 |
| SkillOS text planning | DREAM_TEXT | 0.3 |
