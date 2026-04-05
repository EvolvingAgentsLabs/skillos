---
domain: runtime
skill_count: 1
base: system/skills/runtime/base.md
---

# Runtime Domain Index

Skills that bridge SkillOS markdown agent definitions to external code-execution runtimes,
providing multi-provider LLM access, tool-call translation, and process lifecycle management.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| pi-mono-runtime-agent | pi-mono | pi-mono-runtime-agent | run SkillOS on pi-mono, TypeScript agent runtime, multi-provider LLM, pi-mono integration | runtime/pi-mono/pi-mono-runtime-agent.manifest.md |

## Routing Notes
- Use `pi-mono-runtime-agent` when the goal requires executing SkillOS agents through the
  pi-mono TypeScript runtime (e.g. Node.js deployment, non-Python environments, or when the
  `@mariozechner/pi-agent-core` package is already in use).
- Token cost: medium — load full spec when runtime setup or invocation is required.
