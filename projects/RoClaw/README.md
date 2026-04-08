# Project RoClaw — SkillOS Physical Robot Integration

## Overview

This project connects SkillOS (the Prefrontal Cortex) to the RoClaw physical robot (the Cerebellum). SkillOS handles planning, reasoning, and dream consolidation; RoClaw handles reactive motor control and VLM navigation. Strategy memory is stored as local `.md` files — no external memory server required.

## Architecture

```
SkillOS (this project)
  ├── RoClawNavigationAgent    → Plans and executes physical navigation
  ├── RoClawSceneAnalysisAgent → Interprets VLM camera feeds
  ├── RoClawDreamAgent         → Consolidates experiences to local .md traces
  └── RoClawTool               → HTTP bridge to robot hardware

        ↓ HTTP (:8430)

RoClaw Bridge (roclaw_bridge.py)
        ↓ WebSocket
OpenClaw Gateway
        ↓
RoClaw CortexNode → VisionLoop → BytecodeCompiler → UDP → ESP32-S3
```

## Quick Start

```bash
# 1. Start RoClaw bridge (simulation mode for testing)
python roclaw_bridge.py --port 8430 --simulate

# 2. Run a navigation task
python skillos.py
# > skillos execute: "Navigate to the kitchen and describe what you see"
```

## Components

### System Agents (in system/agents/)
- **RoClawNavigationAgent** — Route planning, obstacle recovery, trace logging
- **RoClawDreamAgent** — Dream consolidation, Negative Constraint generation
- **RoClawSceneAnalysisAgent** — Scene interpretation, semantic mapping

### System Tools (in system/tools/)
- **RoClawTool** — HTTP bridge to RoClaw's robot tools

### Project Memory
- `memory/long_term/strategies.md` — Learned navigation strategies
- `memory/long_term/negative_constraints.md` — Learned prohibitions
- `memory/short_term/` — Session-level interaction logs

## Scenarios

Run the integration demo:
```
skillos execute: "Run the RoClaw Integration scenario from scenarios/RoClaw_Integration.md"
```

For full documentation see [docs/robot.md](../../docs/robot.md).
