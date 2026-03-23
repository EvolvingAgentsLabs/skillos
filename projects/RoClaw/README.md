# Project RoClaw — SkillOS Physical Robot Integration

## Overview

This project connects SkillOS (the Prefrontal Cortex) to the RoClaw physical robot (the Cerebellum) through the evolving-memory server (the Hippocampus), forming the **Cognitive Trinity** architecture.

## Architecture

```
SkillOS (this project)
  ├── RoClawNavigationAgent → Plans and executes physical navigation
  ├── RoClawSceneAnalysisAgent → Interprets VLM camera feeds
  ├── RoClawDreamAgent → Consolidates experiences into strategies
  ├── RoClawTool → HTTP bridge to robot hardware
  └── EvolvingMemoryTool → Bridge to shared memory server

        ↓ HTTP (:8430)              ↓ HTTP (:8420)

RoClaw Bridge (roclaw_bridge.py)    evolving-memory server
        ↓ WebSocket (:8080)
OpenClaw Gateway
        ↓
RoClaw CortexNode → VisionLoop → BytecodeCompiler → UDP → ESP32-S3
```

## Quick Start

```bash
# 1. Start evolving-memory server
cd /path/to/evolving-memory
python -m evolving_memory.server --port 8420

# 2. Start RoClaw bridge (simulation mode for testing)
cd /path/to/skillos
python roclaw_bridge.py --port 8430 --simulate

# 3. Run a navigation task
python skillos.py
# > skillos execute: "Navigate to the kitchen and describe what you see"
```

## Components

### System Agents (in system/agents/)
- **RoClawNavigationAgent** — Route planning, obstacle recovery, trace logging
- **RoClawDreamAgent** — Dream consolidation, Negative Constraint generation
- **RoClawSceneAnalysisAgent** — Scene interpretation, semantic mapping

### System Tools (in system/tools/)
- **RoClawTool** — HTTP bridge to RoClaw's 9 robot tools
- **EvolvingMemoryTool** — REST bridge to evolving-memory API

### Project Memory
- `memory/long_term/strategies.md` — Learned navigation strategies
- `memory/long_term/negative_constraints.md` — Learned prohibitions
- `memory/short_term/` — Session-level interaction logs

## Scenarios

Run the integration demo:
```
skillos execute: "Run the RoClaw Integration scenario from scenarios/RoClaw_Integration.md"
```
