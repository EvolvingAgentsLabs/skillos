# Forge — Self-Evolving Skill Factory

**Status**: v1 — spec + skill tree (runtime wiring in progress)
**Skill root**: `system/skills/forge/`
**Router**: `system/skills/orchestration/provider-router.md`

---

## What forge is

SkillOS runs user work on **Gemma 4** (via Ollama, default tag `gemma4:e2b`) plus
cartridges and JS skills. Gemma is small, fast, and local — but it can't do
everything. When it can't, SkillOS falls back to **Claude Code** not to finish the
user's task, but to **generate or evolve a new skill/cartridge/subagent** that
Gemma *can* then run.

This two-tier design keeps three properties:
1. **Local-first execution** — user goals never leak to the cloud once a skill exists.
2. **Self-extension** — the system grows its own capabilities without human edits.
3. **Audit & rollback** — every new artifact is versioned, attested, and reversible.

## Tiers at a glance

| Tier | Backend | Default model | What it does |
|------|---------|---------------|--------------|
| Hot  | Ollama (local) | `gemma4:e2b` | Executes user goals via cartridges + markdown/JS skills |
| Warm | Ollama (local) | `gemma4:e4b` | Fallback for skills that need more than E2B can handle |
| Forge| Claude Code (cloud) | current | **Only** makes/evolves/validates artifacts |

The forge tier is invoked by `orchestration/core/system-agent` based on the
decision table in `orchestration/provider-router.md`.

## The forge skill family

```
system/skills/forge/
├── base.md                                 # shared guardrails, budget, offline mode
├── index.md                                # domain index
├── generate/
│   ├── forge-generate-agent.manifest.md
│   └── forge-generate-agent.md             # drafts new md/JS skills + cartridges
├── evolve/
│   ├── forge-evolve-agent.manifest.md
│   └── forge-evolve-agent.md               # proposes diffs for degraded skills
├── validate/
│   ├── forge-validate-agent.manifest.md
│   └── forge-validate-agent.md             # runs candidate on Gemma, emits gemma_compat
└── compile/
    ├── forge-compile-cartridge-tool.manifest.md
    └── forge-compile-cartridge-tool.md     # deterministic promote + rollback
```

## The gap → forge → validate → execute loop

```
User goal
   │
   ▼
system-agent ── match skill? ── yes ──▶ Hot: Gemma runs it
   │                       no
   ▼
provider-router ──▶ forge-generate-agent  (Claude Code)
                       │
                       ▼
           projects/[P]/forge/candidates/<job_id>/
              manifest.md + skill.md / skill.js + tests/
                       │
                       ▼
                 forge-validate-agent      (Gemma via Ollama)
                       │
            ┌──────────┴──────────┐
            │                     │
          pass                   fail (retry ≤ N → escalate)
            │
            ▼
    forge-compile-cartridge-tool
            │
            ▼
  system/skills/…, cartridges/…, packages.lock updated
            │
            ▼
      re-run original goal on Hot tier
```

## The evolution loop

```
SmartMemory: pass-rate for skill X drops below 0.80
          │
          ▼
memory-analysis-agent emits degradation signal
          │
          ▼
forge-evolve-agent  (Claude Code)
    · reads failure cluster
    · drafts smallest diff
    · writes candidate under projects/[P]/forge/candidates/
          │
          ▼
forge-validate-agent (A/B mode: new vs old on Gemma)
          │
          ▼
  new better → compile → hot-path replace, old archived
  new worse  → drop candidate, journal the attempt
```

## The `gemma_compat` attestation

No artifact enters the hot path without this block in its manifest:

```yaml
gemma_compat:
  model: gemma4:e2b
  validated_at: 2026-04-20T12:34:56Z
  validator_version: 1.0.0
  cases_total: 10
  cases_passed: 9
  pass_rate: 0.90
  max_tokens_observed: 2400
  median_latency_ms: 380
  attestation_strength: strong      # strong ≥0.95, weak 0.80–0.94
```

The block is written **only** by `forge/validate/forge-validate-agent`. A stale
attestation (wrong model tag, older than config-specified age) triggers
re-validation — not deletion — so the system self-heals on model upgrades.

## Guardrails (non-optional)

1. **Budget ledger**: `projects/[P]/forge/budget.yaml` caps tokens/$ per-job and per-day.
2. **Validation gate**: mandatory. No `gemma_compat` → stays in `candidates/`.
3. **Rollback**: every compile archives the previous version. One-command revert.
4. **Forge-loop detector**: same gap re-triggering forge >3× in 24 h halts and escalates.
5. **Offline mode**: `SKILLOS_FORGE_OFFLINE=1` disables cloud calls; gaps surface as
   user-fixable errors.
6. **Tool allow-list**: candidates that request tools outside
   `projects/[P]/state/allowed_tools.json` are refused at validation.

## Using forge

### Trigger manually
```
skillos execute: "forge generate a skill that scrapes a given arXiv paper ID and stores the abstract + authors as a summary"
```

### Trigger implicitly
Just issue any goal. If no skill covers it, the router queues a forge job
automatically (unless offline mode is set).

### Trigger evolution
```
skillos execute: "forge evolve memory/analysis/memory-analysis-agent — pattern clustering misses near-duplicates"
```

### Mass re-attestation after Gemma upgrade
```bash
ollama pull gemma4:e4b
SKILLOS_FORGE_MASS_REVALIDATE=1 GEMMA_MODEL=gemma4:e4b python skillos.py
```

## Relation to Multica features

Forge is the piece that lets SkillOS play the Multica role of a **managed agents
platform** without a cloud backend for execution:

- Multica's "skill library" → `system/skills/` + cartridges, grown by forge.
- Multica's "task assignment" → SkillOS projects + system-agent, run on Gemma.
- Multica's "skill evolution via team use" → SmartMemory + forge-evolve-agent.
- Multica's "multi-provider runtime" → redefined as **tier selection** (Hot/Warm/Forge),
  not vendor choice.
- Multica's "self-hostable" → one binary + Ollama + Claude API key (optional).

## Roadmap
- [x] `forge/router.py` — `ProviderRouter` reads `provider-router.md` and dispatches.
- [x] `forge/budget.py` — ledger with per-job and per-day caps.
- [x] `forge/journal.py` — append-only log + loop-detector query.
- [x] `forge/attestation.py` — `gemma_compat` parse + freshness/model checks.
- [x] `forge/cli.py` — `python -m forge {log, budget, audit, route, serve}`.
- [x] `forge/claude_bridge.py` — Anthropic SDK / Claude CLI / mock backends.
- [x] `forge/executor.py` — end-to-end forge job runner (prompt → artifacts → budget → journal).
- [x] `forge/server.py` — HTTP API (`/api/route`, `/api/forge/run`, …).
- [x] `cartridge_runtime.py` — `gemma_compat` hook + `check_attestations`.
- [x] `agent_runtime.AgentRuntime.route_and_execute` — runtime entry point.
- [x] Desktop shell scaffold — `desktop/` (Tauri 2 + vanilla JS UI).
- [ ] Desktop packaging (bundled Ollama + Gemma4:e2b weights).
- [ ] Cartridge precompile hook invoked by `forge/compile/forge-compile-cartridge-tool`.
- [ ] Board view in the UI (Multica-style task list).
