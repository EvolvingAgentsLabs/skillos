---
domain: forge
skill_count: 4
base: system/skills/forge/base.md
---

# Forge Domain Index

Meta-layer skills that generate, evolve, and validate artifacts (markdown skills, JS skills,
cartridges, subagents) for the Gemma-4 + cartridge execution layer. Claude Code is the
forge's LLM backend; Gemma 4 is the validator and runtime target.

| Skill | Family | subagent_type | invoke_when | manifest |
|-------|--------|---------------|-------------|----------|
| forge-generate-agent | generate | forge-generate-agent | capability gap detected, no existing skill matches goal | forge/generate/forge-generate-agent.manifest.md |
| forge-evolve-agent | evolve | forge-evolve-agent | skill pass-rate degraded, model upgrade, user requests improvement | forge/evolve/forge-evolve-agent.manifest.md |
| forge-validate-agent | validate | forge-validate-agent | after generate/evolve, before cartridge compile, after model upgrade | forge/validate/forge-validate-agent.manifest.md |
| forge-compile-cartridge-tool | compile | _(tool)_ | validated artifact set ready to enter hot path | forge/compile/forge-compile-cartridge-tool.manifest.md |

## Routing Notes
- Forge skills are invoked by `orchestration/core/system-agent` when a `GapEvent` fires.
- Default forge backend is Claude Code via the `Task` tool (subagent_type inherited).
- Forge never writes directly to `system/skills/` — it writes to
  `projects/[P]/forge/candidates/` then, on successful validation, promotes to the
  active skill tree with version-stamped replace.
- Offline mode (`SKILLOS_FORGE_OFFLINE=1`): all forge invocations return
  `forge_disabled` and the gap surfaces to the user.

## Flow: gap → forge → validate → execute
```
GapEvent → forge-generate-agent (Claude Code)
         → draft md/js + test cases in projects/[P]/forge/candidates/
         → forge-validate-agent (runs artifacts on Gemma 4 via Ollama)
           └─ pass → forge-compile-cartridge-tool → promote → re-run original goal
           └─ fail → retry ≤ max_retries → else escalate to user
```

## Flow: evolve
```
SmartMemory degradation alert → forge-evolve-agent (Claude Code)
         → diff against current skill + proposed improvement
         → forge-validate-agent (A/B test old vs new on real tasks)
           └─ new better → archive old, promote new, recompile cartridge
           └─ new worse or tie → drop, log rationale
```
