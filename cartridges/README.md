# SkillOS Cartridges

A **cartridge** is a self-contained domain package that brings
Claude-Code-style subagent orchestration to open-weights models
(Gemma 4, Qwen, Llama) by pre-sealing the plan space.

- Full design document: [`docs/cartridges.md`](../docs/cartridges.md)
- Runtime module: [`cartridge_runtime.py`](../cartridge_runtime.py)

## Quickstart — run a cartridge

```bash
# List available cartridges
python -m cartridge_runtime --list

# Run one directly (Gemma via OpenRouter, the default provider)
python -m cartridge_runtime cooking \
    "Plan meals for next week, 2 adults, vegetarian, Mediterranean"

# Force a specific flow
python -m cartridge_runtime cooking \
    --flow quick-shopping-list \
    "Just give me a shopping list for next week, 3 people"
```

From the SkillOS REPL:

```
skillos$ cartridges                               # list
skillos$ cartridge cooking "plan meals for 2"     # explicit
skillos$ cartridge auto "design electrical ..."   # intent-match
skillos$ plan meals for the week, family of 4     # auto-dispatch
```

## Reference cartridges in this repo

| Cartridge               | Agents | Validator highlight                      |
|-------------------------|-------:|------------------------------------------|
| `cooking/`              | 3      | Structural completeness (7 days × 3)    |
| `residential-electrical/`| 2     | IEC 60364 subset compliance (pure Py)    |

## Authoring a cartridge — 30-second version

```
cartridges/<name>/
├── cartridge.yaml         name, entry_intents, flows, validators
├── router.md              (optional) intent classifier prompt
├── agents/                one .md per subagent — needs/produces frontmatter
├── flows/                 (optional) human-readable flow docs
├── schemas/               JSON Schemas for every blackboard key
├── validators/            pure-Python post-flow checks (the safety net)
└── evals/cases.yaml       regression set — 10–20 goals
```

Rules of thumb:

1. **One flow ≤ 6 agents.** Gemma drifts beyond that.
2. **Every produced key has a JSON Schema.** Validation catches
   shape drift on every step.
3. **Hard rules live in `validators/*.py`.** Not in prompts.
4. **Each agent ships a fully worked `<produces>{…}</produces>` example.**
   This is the cheapest way to make Gemma reliable.
5. **Run `evals/cases.yaml` before you ship.** A cartridge that doesn't
   pass 85% of its eval set is not production-ready.

See `docs/cartridges.md` for the complete authoring guide.

## FAQ

**Why not just use Claude Code for everything?**
You can. Cartridges exist so the same SkillOS stack runs Gemma-only —
useful for offline setups, cost control, data-sovereignty, or simply
wanting open-weights for a specific domain.

**Can a cartridge use real tools (Bash, Read, Write)?**
Yes — any tool exposed by `AgentRuntime` is available. Whitelist them
per-agent via the `tools:` frontmatter field.

**Where does memory live?**
Unchanged — `system/SmartMemory.md` and `projects/<name>/state/`.
Cartridges are an execution layer, not a memory layer.
