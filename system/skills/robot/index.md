---
domain: robot
skill_count: 5
base: system/skills/robot/base.md
---

# Robot Domain Index

Skills for physical robot control, scene understanding, and bio-inspired learning.

**Prerequisite**: Bridge server must be running at `http://localhost:8430`.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| roclaw-navigation-agent | navigation | roclaw-navigation-agent | physical movement, navigate to location, path planning | robot/navigation/roclaw-navigation-agent.manifest.md |
| roclaw-scene-analysis-agent | scene | roclaw-scene-analysis-agent | camera analysis, obstacle encountered, semantic mapping | robot/scene/roclaw-scene-analysis-agent.manifest.md |
| roclaw-dream-agent | dream | roclaw-dream-agent | nightly learning, dream consolidation, strategy evolution | robot/dream/roclaw-dream-agent.manifest.md |
| roclaw-tool | tools | _(tool, no subagent)_ | send robot command, go_to, explore, stop, get_status | robot/tools/roclaw-tool.manifest.md |
| evolving-memory-tool | tools | _(tool, no subagent)_ | store trace, query strategy, hippocampus access | robot/tools/evolving-memory-tool.manifest.md |

## Routing Notes
- Physical actions → `roclaw-tool` (direct HTTP bridge).
- Before navigation → `roclaw-scene-analysis-agent` for awareness.
- After session → `roclaw-dream-agent` for consolidation.
- Traces → `evolving-memory-tool` for hippocampus storage.
