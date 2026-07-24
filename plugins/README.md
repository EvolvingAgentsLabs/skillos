# plugins

The two Claude Code plugins, absorbed from their own repositories on 2026-07-24.

| Directory | Command | What it does |
|---|---|---|
| `skillos-plugin/` | `/skillos` | Decomposes a goal, creates agents, runs them, writes traces |
| `skillos-systemcontrol-plugin/` | `/sysctl` | Audits, scores, evolves and prunes what `/skillos` created |

They lived apart as `EvolvingAgentsLabs/skillos_plugin` (2 commits) and
`EvolvingAgentsLabs/skillos_systemcontrol_plugin` (1 commit). Neither is useful
without the other — `/sysctl` only operates on projects `/skillos` creates — and
both are prompt corpora drawn from this repo. Keeping three homes for one corpus
produced exactly the drift you would predict: `SmartMemory.md` existed in three
divergent copies.

`skillos_plugin` is itself a brand-swap of the older `llmunix-marketplace`
plugin; the long-form guide that never made the rename is preserved as
`skillos-plugin/DOCS.md`.

The systemcontrol prompts are the sharpest writing in the set — the
Anti-Overfitting Gate ("if the failures that motivated this change disappeared,
would it still be a good change?"), a seven-type failure taxonomy, cascading
prune-and-verify. None of it has an implementation or any evidence of having
been run.
