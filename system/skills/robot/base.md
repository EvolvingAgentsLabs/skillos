---
skill_domain: robot
type: base-template
version: 1.0.0
---

# Robot Domain — Shared Behaviors

All skills in the `robot/` domain inherit these conventions.

## Cognitive Trinity
| Component | Role | Port |
|-----------|------|------|
| SkillOS (this system) | Prefrontal Cortex — planning, reasoning | — |
| RoClaw | Cerebellum — reactive motor control | WebSocket via bridge :8430 |
| evolving-memory | Hippocampus — shared memory, dreams | REST API :8420 |

## Bridge Communication
All physical robot actions go through `roclaw_bridge.py` (HTTP → WebSocket translator).
- Bridge base URL: `http://localhost:8430`
- Use `system/skills/robot/tools/roclaw-tool.md` for all robot tool invocations.

## Trace Fidelity Tags
Tag all robot action traces with source fidelity for dream weighting:
- `REAL_WORLD` (1.0) — actual hardware
- `SIM_3D` (0.8) — MuJoCo physics
- `SIM_2D` (0.5) — virtual_roclaw kinematics
- `DREAM_TEXT` (0.3) — text-only dream scenarios

## Action Logging
Log every robot action to `projects/[Project]/memory/short_term/` with fidelity tag.
Format: `YYYY-MM-DD_HH-MM-SS_robot_[action].md`

## Failure Recovery
On navigation failure:
1. Invoke `robot/scene/roclaw-scene-analysis-agent` to analyze obstacle.
2. Dynamically create a recovery tool as markdown if needed.
3. Log to evolving-memory for dream consolidation.

## Prerequisites Check
Before any robot execution, verify bridge is reachable:
`curl -s http://localhost:8430/health` — must return 200.
