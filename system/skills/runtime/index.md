---
domain: runtime
skill_count: 3
base: system/skills/runtime/base.md
---

# Runtime Domain Index

SkillOS is **runtime-agnostic**. This domain lists all available execution runtimes.
Each runtime is a swappable adapter — SkillOS agents, skills, and memory are fully
portable across all of them. Choose based on environment, LLM provider, or deployment target.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| claude-code-runtime-agent | claude-code | claude-code-runtime-agent | default runtime, Anthropic native, no runtime configured, Claude Code CLI | runtime/claude-code/claude-code-runtime-agent.manifest.md |
| pi-mono-runtime-agent | pi-mono | pi-mono-runtime-agent | TypeScript runtime, Node.js deployment, multi-provider LLM, web UI, Slack bot, pi-mono | runtime/pi-mono/pi-mono-runtime-agent.manifest.md |
| codex-runtime-agent | codex | codex-runtime-agent | OpenAI Codex CLI, Azure OpenAI, sandboxed execution, GPT-4o | runtime/codex/codex-runtime-agent.manifest.md |

## Runtime Comparison at a Glance

| | Claude Code | pi-mono | Codex CLI |
|--|-------------|---------|-----------|
| **Default** | ✅ yes | no | no |
| **Language** | — (LLM native) | TypeScript | — (LLM native) |
| **LLM providers** | Anthropic | OpenAI, Anthropic, Google, OpenRouter | OpenAI, Azure |
| **Web / Slack UI** | no | ✅ yes | no |
| **Azure OpenAI** | no | via OpenRouter | ✅ native |
| **Sandboxed exec** | no | no | ✅ yes |
| **Setup required** | none | npm install | npm install |

## Routing Notes

- **Default path**: If no `runtime_config.json` exists, SkillOS runs on `claude-code` (this process) — no setup needed.
- **Switch runtime**: Create/update `projects/[Project]/state/runtime_config.json` with `active_runtime` set to the desired runtime, then invoke the corresponding agent to complete setup.
- **All runtimes share**: the same skill tree, memory system, project structure, and agent markdown specs. Nothing changes except the execution engine.
- Token cost: low for claude-code (already loaded), medium for others (require setup steps).
