---
skill_domain: runtime
type: base-template
version: 2.0.0
---

# Runtime Domain — Pluggable Runtime Interface

## Concept

SkillOS is **runtime-agnostic**. The markdown agent definitions, skill tree, and memory system
are portable across any code-execution engine. The `runtime/` domain defines the **swappable
runtime layer** — users choose which runtime hosts SkillOS based on their environment,
language preference, LLM provider, or deployment target.

```
┌─────────────────────────────────────────────────────────────────┐
│                       SkillOS Core Layer                        │
│   Markdown agents · SkillIndex · Memory · Project structure     │
│   (100% portable — no dependency on any specific runtime)       │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │    Runtime Interface         │   ← this domain
              │  (pluggable adapter layer)   │
              └──┬──────────┬──────────┬────┘
                 │          │          │
        ┌────────▼──┐  ┌────▼────┐  ┌─▼──────────┐
        │ Claude     │  │ pi-mono │  │  Codex CLI  │  … and more
        │ Code (CLI) │  │ (TS/JS) │  │  (Node.js)  │
        │ [default]  │  │         │  │             │
        └────────────┘  └─────────┘  └─────────────┘
```

## Runtime Interface Contract

Every runtime skill MUST implement these five operations:

| Operation | Description |
|-----------|-------------|
| `install` | Set up the runtime (clone repo, install deps, configure env vars) |
| `start`   | Launch the runtime process or connect to a running instance |
| `invoke`  | Send a SkillOS goal or tool-call to the runtime; return result |
| `status`  | Report whether the runtime is healthy / reachable |
| `stop`    | Gracefully shut down the runtime process |

## Switching Runtimes

The active runtime is declared in `projects/[Project]/state/runtime_config.json`:

```json
{
  "active_runtime": "claude-code",
  "available_runtimes": ["claude-code", "pi-mono", "codex"],
  "runtime_config": {
    "provider": "anthropic",
    "model": "claude-sonnet-4-6"
  }
}
```

To switch runtimes, update `active_runtime` and invoke the corresponding runtime agent
from the `runtime/` domain. All SkillOS skills, agents, and memory remain unchanged.

## Tool-Call Translation

SkillOS agents emit tool calls using a canonical XML format:

```xml
<tool_call name="ToolName">{"param": "value"}</tool_call>
```

Each runtime skill is responsible for translating this to its native invocation mechanism:

| Runtime | Native format |
|---------|--------------|
| Claude Code | Native Claude Code tool calls (Read, Write, Bash, Task, …) |
| pi-mono | `@mariozechner/pi-agent-core` Tool schema (JSON Schema + execute fn) |
| Codex CLI | `--tool` flag / OpenAI function-calling JSON |
| Custom | Any format — implement the adapter in the runtime skill |

## LLM Provider Portability

Each runtime exposes its own LLM configuration. SkillOS goals are provider-agnostic —
the runtime skill handles model selection and API key management.

| Runtime | Supported providers |
|---------|-------------------|
| Claude Code | Anthropic (native) |
| pi-mono | Anthropic, OpenAI, Google, OpenRouter, + more via `pi-ai` |
| Codex CLI | OpenAI (native), Azure OpenAI |
| Custom | Any OpenAI-compatible endpoint |

## State & Logging

- Log every runtime invocation to `projects/[Project]/memory/short_term/`:
  `YYYY-MM-DD_HH-MM-SS_[runtime-name]_interaction.md`
- Persist active runtime config and health in `projects/[Project]/state/runtime_config.json`
- On runtime switch, archive the previous config snapshot with a timestamp suffix

## Error Escalation

On runtime failure, delegate to `recovery/error/error-recovery-agent` before retrying.
Always propagate the raw error message and runtime name for diagnostics.
If the active runtime is unreachable, the error-recovery-agent MAY suggest switching
to an alternative runtime from `available_runtimes`.
