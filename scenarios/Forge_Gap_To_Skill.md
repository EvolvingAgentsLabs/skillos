# Forge — Gap-to-Skill End-to-End Scenario

**Status**: v1 — reference walkthrough
**Primary runtime**: Ollama + `gemma4:e2b`
**Forge backend**: Claude Code (cloud)
**Requires**: `ollama pull gemma4:e2b`, an `ANTHROPIC_API_KEY` in `.env` (or skip forge steps with `SKILLOS_FORGE_OFFLINE=1`)

---

## What this scenario demonstrates

The self-evolving loop end-to-end:

1. A user goal arrives that no existing skill covers.
2. Hot-tier Gemma detects the gap and returns `insufficient_capability`.
3. The **forge** tier generates a candidate skill + JS helper + test cases via Claude Code.
4. The **validator** runs the candidate through the real Gemma 4 runtime and writes a `gemma_compat` attestation.
5. The **compiler** promotes the validated artifacts to the hot path.
6. The original goal is re-executed — this time entirely on Gemma 4 — and succeeds.
7. Everything is logged, versioned, and reversible.

---

## The goal

```
skillos execute: "Given a list of SemVer strings, return them sorted with pre-release tags ordered per SemVer 2.0"
```

No existing skill does this. Forge must produce one.

## Expected file artifacts

After a successful run, the following new files exist:

```
projects/Project_semver_sort/
├── forge/
│   ├── jobs/<job_id>.yaml                       # original forge job spec
│   ├── candidates/<job_id>/
│   │   ├── manifest.md                          # with gemma_compat block (after validate)
│   │   ├── skill.md                             # markdown instructions for Gemma
│   │   ├── skill.js                             # deterministic sort, uses `fetch`-free pure JS
│   │   ├── tests/cases.yaml                     # ≥3 cases incl. edge + adversarial
│   │   ├── forge_meta.yaml                      # rationale, token usage
│   │   └── validation_report.md                 # per-case trace
│   ├── budget.yaml                              # claude tokens + $ ledger
│   └── journal.md                               # append-only forge log
├── state/plan.md
├── memory/short_term/<ts>_system-agent.md
├── memory/short_term/<ts>_forge-generate-agent.md
├── memory/short_term/<ts>_forge-validate-agent.md
├── memory/long_term/semver_sort_learnings.md
└── output/
    └── sorted_semvers.json                      # actual task output (hot-tier run)

system/skills/utility/
├── index.md                                      # new domain row added
└── semver/
    ├── semver-sort.manifest.md                   # promoted by compile tool
    ├── semver-sort.md
    └── semver-sort.js
system/packages.lock                              # new entry with job_id + hash
```

---

## Step-by-step trace (what system-agent does)

### Step 1 — Intake
```
system-agent reads SkillIndex.md
             reads orchestration/provider-router.md
             routes to Hot tier (Gemma)
```

### Step 2 — Hot-tier attempt
```
gemma4:e2b via Ollama
  searches for matching skill → none found in utility/, project/, memory/, …
  returns: { gap: "no skill covers semver-sort" }
```

### Step 3 — Gap → forge
```
system-agent queues forge job:
  trigger: gap
  goal: "sort SemVer strings with SemVer 2.0 ordering"
  constraints:
    target_model: gemma4:e2b
    max_skill_tokens: 2500
    allow_js: true
    allow_new_tools: false
  budget: { max_claude_tokens: 150_000, max_wall_clock_s: 300 }
```

### Step 4 — Forge generate (Claude Code)
```
forge-generate-agent drafts:
  - kind: js-skill (deterministic, Gemma shouldn't do version parsing)
  - skill.md with 6 imperative steps + 2 few-shot examples
  - skill.js using pure JS: parse → compare → sort
  - tests/cases.yaml:
      · happy: ["1.0.0", "0.9.0", "1.0.0-beta"] → sorted
      · edge: [] → []
      · adversarial: ["1.0", "not-a-version", "1.0.0"] → graceful partial
```

### Step 5 — Forge validate (Gemma 4)
```
forge-validate-agent:
  preflight: curl ollama → OK, gemma4:e2b available
  runs skill.js test cases directly in QuickJS-equivalent sandbox
  runs skill.md through agent_runtime.py --provider gemma for LLM-framing cases
  results: 3/3 passed
  writes attestation:
    pass_rate: 1.00, attestation_strength: strong,
    median_latency_ms: 180 (JS path), 620 (md+llm path)
```

### Step 6 — Compile + promote
```
forge-compile-cartridge-tool:
  archive: (nothing to replace)
  install:
    system/skills/utility/semver/semver-sort.md
    system/skills/utility/semver/semver-sort.manifest.md
    system/skills/utility/semver/semver-sort.js
  update: system/skills/utility/index.md (new row)
           system/packages.lock (forge source, job_id, hash)
           projects/Project_semver_sort/forge/journal.md
  refresh: .claude/agents/semver-sort.md (symlink/copy)
```

### Step 7 — Re-run original goal (hot tier)
```
system-agent re-routes → Hot tier → matches semver-sort
gemma4:e2b invokes semver-sort (JS path — deterministic, 1 token LLM cost)
writes output/sorted_semvers.json
appends SmartMemory entry (success, pass)
```

### Step 8 — Consolidate
```
memory-consolidation-agent writes:
  projects/Project_semver_sort/memory/long_term/semver_sort_learnings.md
    - JS skills outperform markdown+LLM for deterministic tasks
    - Forge E2B-first validation works for small utilities
    - No model-tier escalation needed
```

---

## Assertions (demo passes iff all true)

- [ ] `system/skills/utility/semver/semver-sort.md` exists and has a `gemma_compat` block.
- [ ] `system/packages.lock` contains an entry with `source: forge` and a non-empty `job_id`.
- [ ] `projects/Project_semver_sort/output/sorted_semvers.json` is a correctly sorted array.
- [ ] `projects/Project_semver_sort/forge/journal.md` has exactly one `outcome: pass` entry.
- [ ] The hot-tier run (Step 7) never calls any cloud LLM — all calls go to
      `http://localhost:11434`.
- [ ] With `SKILLOS_FORGE_OFFLINE=1`, Steps 4–6 are skipped and the user sees a
      structured `forge_disabled` error at Step 3.

## Running it

```bash
# Prereqs
ollama pull gemma4:e2b
export GEMMA_MODEL=gemma4:e2b
export OLLAMA_BASE_URL=http://localhost:11434
# For the forge step:
echo "ANTHROPIC_API_KEY=sk-..." >> .env

# Go
python skillos.py
skillos$ skillos execute: "Given a list of SemVer strings, return them sorted with pre-release tags ordered per SemVer 2.0"
```

## Offline variant

```bash
export SKILLOS_FORGE_OFFLINE=1
# same command — system will stop at Step 3 with a forge_disabled error,
# listing the gap so a human can hand-author the skill.
```

## Rollback

```bash
python -c "from system.skills.forge.compile import rollback; rollback('<job_id>')"
# restores archive, removes promoted files, updates packages.lock + journal
```

## Why this scenario is the right smoke test

It touches every moving part:
- Tier selection (Hot → gap → Forge → back to Hot).
- Both artifact kinds (markdown + JS) in one skill.
- Validation (deterministic JS + LLM-framing path both exercised).
- Registry + hot-path promotion.
- SmartMemory write-through.
- Offline-mode gate.
- Rollback.

If this scenario passes end-to-end, the self-evolving platform claim is real.
