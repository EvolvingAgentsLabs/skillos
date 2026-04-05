---
skill_domain: runtime
type: base-template
version: 1.0.0
---

# Runtime Domain — Shared Behaviors

All skills in the `runtime/` domain inherit these conventions.

## Role
Runtime skills bridge SkillOS's pure-markdown agent definitions to an external code execution
engine. They are responsible for: adapting SkillOS tool-call semantics to the target runtime's
API, managing process lifecycle, and surfacing the runtime's multi-provider LLM abstraction to
SkillOS agents.

## Adapter Contract
Every runtime skill MUST implement the following operations:

| Operation | Description |
|-----------|-------------|
| `start`   | Launch the runtime process (or connect to a running instance) |
| `invoke`  | Send a SkillOS goal / tool-call to the runtime and return the result |
| `status`  | Report whether the runtime is healthy / reachable |
| `stop`    | Gracefully shut down the runtime process |

## Tool-Call Translation
SkillOS agents emit tool calls in the `<tool_call name="...">` XML format.
Runtime skills translate these to the target runtime's native invocation mechanism
(e.g., OpenAI-compatible `tool_calls` array, REST endpoints, TypeScript function calls).

## State & Logging
- Log every runtime invocation to `projects/[Project]/memory/short_term/` using format:
  `YYYY-MM-DD_HH-MM-SS_runtime_interaction.md`
- Persist runtime health metrics in `projects/[Project]/state/runtime_status.json`

## Error Escalation
On runtime failure, delegate to `recovery/error/error-recovery-agent` before retrying.
Always propagate the raw error message from the runtime for diagnostics.
