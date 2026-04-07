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
| roclaw-dream-consolidation-agent | dream | roclaw-dream-consolidation-agent | consolidate traces to strategies, filesystem dream cycle | robot/dream/roclaw-dream-consolidation-agent.md |
| roclaw-tool | tools | _(tool, no subagent)_ | send robot command, go_to, explore, stop, get_status | robot/tools/roclaw-tool.manifest.md |

## Routing Notes
- Physical actions: `roclaw-tool` (direct HTTP bridge).
- Before navigation: `roclaw-scene-analysis-agent` for awareness.
- After session: `roclaw-dream-consolidation-agent` for filesystem-based dream consolidation.
- Traces: RoClaw writes `.md` trace files locally; agents read them via Read/Glob/Grep.
- Legacy dream agent (`roclaw-dream-agent`) still available for real-time post-recovery learning.
