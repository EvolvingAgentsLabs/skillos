# Strategic Portfolio Analysis: skillos / skillos_mini / RoClaw / llm_os

**Date**: 2026-04-26
**Analyst**: LLMunix DreamOS Kernel — Triad Decomposition
**Goal**: Determine what to cut, keep, and improve across the 4-project portfolio
**Vision anchor**: llm_os = universal kernel where the LLM IS the OS; skillos = markdown OS layer that still runs on top of another OS

---

## 1. PROJECT MATURITY ASSESSMENT

| Project | Maturity | LOC (est.) | Tests | Active Development | Revenue Path |
|---|---|---|---|---|---|
| **llm_os** | **Alpha (v0.5-rc1)** | ~3K Rust + grammar + 6 carts | 12 grammar fixtures, ~11 Rust tests | Very active (fast-forward landed Apr 25) | Open-source foundation |
| **skillos** | **Beta** | ~68 skill .md files, 424K skills dir, 1.2M projects | Minimal (cartridge_runtime.py tests only) | Moderate (desktop focus, PRs #15/#16 pending) | None directly |
| **skillos_mini** | **Pre-Alpha → Alpha pivot** | Svelte app + 129 vitest tests + 3 cartridges | 129 tests passing | Active (trade-app pivot Apr 25) | **Yes — Play Store app for oficios** |
| **RoClaw** | **Beta** | ~15K TS, 459 tests in 26 suites | 459 passing, 2 skipped (API keys) | Moderate (scene-graph PR#20 merged, sim traces) | Hardware demo + dataset |

### Key Observations

1. **llm_os has the strongest architectural thesis** but the least running code. v0.5-rc1 shipped scheduler, multitask, capability, subagent — but the v0.5-final gate has 5 unchecked items. No real-hardware validation yet.

2. **skillos is the most feature-rich but the least focused**. 68 skill files, 6+ domains (orchestration, memory, robot, validation, recovery, project, knowledge), knowledge compilation wiki system, package management, multiple agent patterns. It's a Swiss Army knife that does everything and ships nothing.

3. **skillos_mini has the clearest product vision** — on-device trade-app for oficios in Uruguay. The CLAUDE.md is the best strategic doc in the portfolio (557 lines of decisions, non-goals, quality gates, privacy invariants). But it's pre-M1 — no real-user validation yet.

4. **RoClaw is the most mature engineering-wise** — 459 tests, 21 negative constraints from dream consolidation, working Gemini VLM navigation, 25+ sim traces. But it's a demo platform, not a product.

---

## 2. BLUE OCEAN STRATEGY MATRIX

### 2.1 llm_os — The Kernel

#### ELIMINATE
- **The "v0.01 exists on disk" fiction.** The refinement doc (design/llm-os-refinement-2026-04-24.md) caught this: README claimed `runtime/` and `scripts/` before they existed. This is now resolved (v0.5 landed), but the lesson stands: don't document what doesn't exist.
- **The "13 opcodes match RoClaw" narrative.** RoClaw has 14 opcodes in v1.1. llm_os has 13 ISA opcodes. It's a coincidence. Stop conflating them.

#### REDUCE
- **Cartridge count.** 6 cartridges (system/summarize, system/demo, io/roclaw, sim/sim_world, domestic/cooking, domestic/residential-electrical) is too many for a kernel that hasn't proven its dispatch loop on hardware. Focus on 2: `system.demo` (proof of ISA) and `io.roclaw` (proof of real I/O). The domestic cartridges belong in skillos_mini.
- **Design doc proliferation.** 4 docs (ARCHITECTURE, NEXT_STEPS, USAGE, TUTORIAL) + 2 release notes + multiple design/ files. Consolidate to: ARCHITECTURE (the map), NEXT_STEPS (the roadmap), TUTORIAL (onboarding). Kill USAGE (merge into TUTORIAL).

#### RAISE
- **§1 Grammar swap (highest priority).** 3 HTTP requests per syscall is a 15% latency tax. This is the #1 blocker for the "LLM as CPU" thesis. The multi-grammar stack patch to llama.cpp is the most important work in the entire portfolio.
- **§2 ISA-aware compactor.** Silent state corruption on KV compaction invalidates every trace. This is the #1 correctness risk. The `<|state|>` 14th opcode is elegant — ship it.
- **The self-hosting trace pipeline.** `scripts/promote_traces.py` (JSONL → DPO triples) is the "Linux 0.11 moment" — the OS curates its own training data. This is the differentiator. Push to collect 5000+ traces.
- **Cartridge-as-universal-interface.** The cartridge model (manifest.json + schemas/ + dialect.gbnf + handler) is the best abstraction in the portfolio. It maps cleanly to: skillos_mini's cartridges (same shape), skillos's skills (same concept), RoClaw's motor opcodes (direct translation). Make this THE interface standard.

#### CREATE
- **A "kernel test harness" that doesn't need Pi 5.** Right now testing requires real hardware. Create a `mock_llama_server` that replays recorded token streams, so CI can validate the dispatch loop on GitHub Actions.
- **Cartridge SDK documentation.** The TUTORIAL is a start, but a proper SDK (scaffold command, test harness, example carts) would make the "anyone can write a cartridge" vision real.
- **The dream/trace → strategy → cartridge promotion pipeline.** RoClaw has this at the markdown level; llm_os has `promote_traces.py`. Connect them: traces from any project → DPO triples → fine-tune → better kernel model → better traces. This is the flywheel.

---

### 2.2 skillos — The Markdown OS

#### ELIMINATE
- **The generic "execute any goal" ambition.** skillos trying to be a universal agent framework dilutes the real value. Claude Code already does "execute any goal" natively. What skillos uniquely provides is: (1) hierarchical skill tree, (2) knowledge compilation, (3) dream consolidation, (4) RoClaw integration.
- **Backward-compat redirect stubs** in `system/agents/` and `system/tools/`. The skill tree (v3.0) is the canonical path. Remove the stubs.
- **SmartLibrary.md (deprecated)**, memory_log.md (deprecated redirect). Delete them.
- **The `cartridge_runtime.py` and `compactor.py`** remnants in skillos. These were already meant to move to skillos_mini. The git branch `chore/remove-cartridge-compactor` exists but wasn't merged. Merge it.
- **The Boot.md still references `evolving-memory` at :8420.** RoClaw was decoupled 2026-04-06. Remove this reference.
- **Simulation mode for training data.** This was the original pitch but hasn't produced usable fine-tuning data. Either invest seriously or drop it.
- **`agent_runtime.py` multi-provider Python runtime.** skillos runs on Claude Code. The Python runtime is unused complexity.

#### REDUCE
- **Scope of the skill tree to 3 domains max.** Currently: orchestration, memory, robot, validation, recovery, project, knowledge = 7 domains. Reduce to: **orchestration** (the core), **memory/dream** (the differentiator), **robot** (the integration point). Move validation/recovery into orchestration. Move project into orchestration. Move knowledge into a separate optional package.
- **Project output accumulation.** `projects/` has 1.2M of output from various demo runs (echo_q, aorta, patch_benchmark, chaos_theory). These are demo artifacts, not reusable assets. Archive or delete.

#### RAISE
- **The hierarchical skill tree + lazy loading.** 61% token reduction in routing is real. This is THE contribution skillos makes to llm_os. The skill tree pattern should become the standard for how llm_os discovers and loads cartridges.
- **Dream consolidation for RoClaw.** The dream agent + dream consolidation agent + trace reading pipeline is unique and valuable. This is the "hippocampus" that no other system has.
- **Knowledge compilation (Karpathy wiki pattern).** The wiki compile → ingest → query → lint loop is genuinely novel. But it's currently buried under all the other features. Extract it as a standalone capability.

#### CREATE
- **A clear "skillos as llm_os userland" integration.** Right now skillos and llm_os are conceptually related but have zero shared code. Define the interface: skillos skills = llm_os cartridges at the markdown level. The ISA `<|call|>` maps to a skill invocation. The `<|think|>` maps to skillos's planning phase. Make this mapping explicit.
- **A "dream as cronjob" pattern.** The `/llmunix dream` command exists but it's manual. Build a lightweight cron-style scheduler that runs dream consolidation on a schedule (the `/loop` pattern in the llmunix skill is the right idea).

---

### 2.3 skillos_mini — The Trade App

#### ELIMINATE
- **The `experiments/gemma4-skills/` directory.** This was a spike to bridge Google AI Edge Gallery JS skills. It proved the concept but isn't on the M1-M6 critical path. It adds complexity to the repo. Archive it.
- **The `projects/Project_aorta_gemma*` and `Project_echo_q_gemma*` outputs (8 dirs).** These are demo outputs from the skillos era. They're irrelevant to the trade-app pivot. Delete them.
- **`compactor.py` (Python compactor).** The mobile app uses `compactor.ts`. The Python version is dead code. Already noted in memory but still present.
- **`cartridges/cooking/` and `cartridges/learn/`** — These don't align with the oficios pivot. The cooking cartridge was a demo; learn is generic. Neither is on the M1-M6 roadmap. Archive or delete.

#### REDUCE
- **Feature ambition before M1 validation.** The CLAUDE.md lays out 12 weeks and 6 milestones. But M1 (validation + lock decisions) hasn't happened yet. The 3 real interviews haven't been logged. Don't build M2+ features until M1 validates the premise.
- **The 3-trade scope for MVP.** The CLAUDE.md says "three trades stress-test genericity." But shipping ONE trade well (electricista) is better than three trades poorly. Consider: M2 = electricista-only, M3 = add plomero only if electricista works.

#### RAISE
- **The cartridge-with-deterministic-validator pattern.** This IS the moat. The combination of LLM + JSON Schema + deterministic validators (compliance_checker, plumbing_checker, painting_sanity) is what makes this safe for regulated trades. This is the pattern llm_os should adopt wholesale.
- **The `_shared/` cartridge infrastructure.** 4 shared agents (vision-diagnoser, quote-builder, report-composer, client-message-writer) + 7 shared schemas. This is the real runtime reusable core. Invest here.
- **PDF generation + WhatsApp share.** This is the ENTIRE user value loop: take photos → diagnose → quote → PDF → WhatsApp. If this works flawlessly, the app ships. Everything else is secondary.

#### CREATE
- **The M1 validation artifacts.** 3 real interviews, naming decision, advisor network. This blocks everything. Do it first.
- **A cartridge test harness** that runs validation logic without the full mobile app. This would let CI catch cartridge regressions.

---

### 2.4 RoClaw — The Cerebellum

#### ELIMINATE
- **The `src/2_qwen_cerebellum/` naming.** Qwen was replaced by Gemini. The directory still carries the old name. Rename to `cerebellum/` or `motor_cortex/`.
- **The bytecode/hex emission path.** The primary path is now Gemini structured tool calls. The hex bytecode GBNF emission is a fallback for Ollama models. It should be marked as deprecated/legacy, not maintained alongside the primary path.
- **evolving-memory references.** Boot.md in skillos still references :8420. RoClaw was decoupled Apr 6. Clean up all references across repos.

#### REDUCE
- **The 4 compilation modes.** tool-call, grammar, few-shot, host-text — this is over-engineered. Gemini structured tool calls work. Keep ONE primary mode (tool-call) and ONE fallback (grammar for GBNF-capable local models). Drop few-shot and host-text.
- **Uncommitted sim traces.** 25+ untracked sim3d traces from Apr 7 and Apr 16 sitting in git status. Either commit them (they're training data!) or clean them up. They're cluttering the working tree.

#### RAISE
- **The scene-graph + ReactiveController pipeline.** PR#20 (hierarchical spatial-semantic engine) is the most sophisticated addition. Vision projector (Gemini box_2d → arena cm) + SceneGraph + ReactiveController + ReflexGuard. This is genuinely useful robotics infrastructure.
- **The dream consolidation system.** 5 dream sessions, 21 constraints, 24 strategies across L1-L4. This is the only project with a REAL working dream engine producing real artifacts. The strategies are actionable (oscillation detection, stuck detection, model selection). Invest more.
- **The sim stack (mjswan + build_scene.py).** Browser-based MuJoCo simulation is a powerful demo/development tool. Make it easier to run (one-command setup).

#### CREATE
- **An llm_os `io.roclaw` cartridge that maps the 7 motor opcodes to the llm_os ISA.** Right now RoClaw has its own ISA (14 opcodes, 6-byte frames). llm_os has its own ISA (13 opcodes, GBNF tokens). The `io.roclaw` cartridge should translate: `<|call|>io.roclaw.forward {"speed":150}` → RoClaw motor command. This proves llm_os can control real hardware.
- **Trace format standardization.** RoClaw traces are YAML frontmatter + markdown. llm_os traces are JSONL. skillos traces are SmartMemory entries. Standardize on ONE trace format that all projects can read/write and the dream engine can consolidate.

---

## 3. THE CONVERGENCE THESIS

### 3.1 The Layer Cake

```
┌─────────────────────────────────────────────────────┐
│  skillos_mini (trade-app)                            │  ← PRODUCT (revenue)
│  - 3 trade cartridges (electricista, plomero, pintor)│
│  - Android app, on-device Gemma 4, WhatsApp share    │
├─────────────────────────────────────────────────────┤
│  skillos (markdown OS)                               │  ← PLATFORM (middleware)
│  - Skill tree (routing, lazy loading)                │
│  - Dream engine (consolidation, strategies)          │
│  - Knowledge compilation (wiki pattern)              │
├─────────────────────────────────────────────────────┤
│  llm_os (kernel)                                     │  ← INFRASTRUCTURE (foundation)
│  - 13-opcode ISA + GBNF grammar enforcement          │
│  - Cartridge system (manifest + schema + handler)    │
│  - KV compaction (swap daemon)                       │
│  - Capability enforcement (logit bias + daemon)      │
├─────────────────────────────────────────────────────┤
│  RoClaw (cerebellum)                                 │  ← IO DEVICE (peripheral)
│  - VLM motor control (Gemini structured tool calls)  │
│  - Scene graph + reactive controller                 │
│  - Dream consolidation (trace → strategy → behavior) │
└─────────────────────────────────────────────────────┘
```

### 3.2 What Must Converge

| Interface | From | To | Format Today | Should Be |
|---|---|---|---|---|
| Cartridge manifest | llm_os | skillos_mini | `manifest.json` | Same — already aligned |
| Cartridge validator | skillos_mini | llm_os | Python/TS validators | `post_validators` in manifest |
| Skill routing | skillos | llm_os | Skill tree → manifest | Lazy-loading index for cartridges |
| Trace format | all | dream engine | YAML/JSONL/SmartMemory | One format (YAML frontmatter + md body) |
| Dream artifacts | RoClaw | skillos | strategies/*.md | Same — already aligned |
| Motor control | llm_os | RoClaw | Not connected | `<\|call\|>io.roclaw.*` cartridge |
| Dialect compression | skillos | llm_os | 14 domain dialects | Per-cartridge `dialect.gbnf` |

### 3.3 The Vision: llm_os as Universal Kernel

The user's vision: **llm_os should be the kernel of ANY system — a new concept where the LLM boots and IS the OS of the hardware, and what it generates can inject new input, generate and process new data, and generate control logic.**

This is mechanically sound. The architecture already maps it:

- **LLM boots** = `bootloader.c` mmaps GGUF → llama.cpp starts → GBNF grammar loaded → `<|halt|>` only at depth 0
- **IS the OS** = The sampler loop IS the CPU. Every token is an instruction. GBNF IS the type system.
- **Generates new input** = `<|call|>` emits a syscall → handler runs → `<|result|>` injected back → model processes new data
- **Generates control logic** = `<|loop|>` + `<|break|>` = control flow. `<|fork|>` = concurrency. `<|think|>` = planning.
- **Not just existing projects** = Any cartridge can be plugged in. The ISA is domain-agnostic.

**What's missing to make this real:**
1. The grammar swap (§1) — without it, syscalls are too slow to be practical
2. The ISA-aware compactor (§2) — without it, long tasks corrupt state
3. A fine-tuned kernel model — the bootstrap Qwen/Gemma tokenizes opcodes inconsistently
4. Real-world validation — nobody has run this on a Pi 5 for more than a benchmark

### 3.4 The Vision: skillos as Markdown OS

The user's vision: **skillos operates at a level where the operational layer is markdown and it still runs on top of another OS.**

This is already true. skillos IS a markdown OS. Claude Code IS the host OS. The question is: what's the relationship to llm_os?

**Answer:** skillos is the **userland** of llm_os. When llm_os runs on Pi 5 with llama.cpp, skillos's skill definitions become cartridge manifests. When llm_os runs on a cloud model via Claude Code, skillos IS the runtime. They're the same concept at different abstraction levels.

The key insight from the `llm-os-refinement-2026-04-24.md` doc: skillos already has primitives llm_os needs:
- **Hierarchical skill tree** → cartridge discovery
- **Lazy loading (61% token reduction)** → essential for 8K context on Pi 5
- **Dialect framework (-51% to -97% compression)** → essential for 8 Hz token budget
- **Tool map with cost/latency/error modes** → missing from ISA spec
- **Dream consolidation** → trace → strategy → behavior improvement loop

---

## 4. PRIORITY-ORDERED RECOMMENDATIONS

### TIER 1: DO IMMEDIATELY (next 2 weeks)

1. **llm_os §1: Grammar swap.** The multi-grammar stack patch to llama.cpp. Without this, the kernel can't hit 8 Hz on Pi 5. Everything else depends on this.

2. **skillos_mini M1: Validation interviews.** 3 real interviews with electricistas in Uruguay. Without this, the trade-app is building on assumptions.

3. **RoClaw: Commit the 25 sim traces.** They're sitting untracked in git status. They're training data for the dream engine AND for llm_os trace promotion.

4. **Cross-repo: Standardize trace format.** Agree on YAML frontmatter + markdown body (RoClaw's format). All projects adopt it.

### TIER 2: DO THIS MONTH (next 4 weeks)

5. **llm_os §2: ISA-aware compactor.** Add `<|state|>` opcode. Prevent silent state corruption.

6. **skillos: Prune to 3 domains.** Orchestration + Memory/Dream + Robot. Archive the rest.

7. **skillos: Delete deprecated stubs.** SmartLibrary.md redirect, memory_log.md redirect, system/agents/ stubs, system/tools/ stubs.

8. **skillos_mini: Delete non-trade artifacts.** experiments/gemma4-skills/, Project_*_gemma* outputs, cartridges/cooking/, cartridges/learn/.

9. **llm_os: Adopt skillos lazy-loading for cartridge discovery.** `/cart/index.md` → domain indexes → manifests.

10. **llm_os: Add cost/latency/error-mode columns to ISA spec** (from skillos's claude-code-tool-map.md pattern).

### TIER 3: DO THIS QUARTER (next 12 weeks)

11. **llm_os §3: Three-strikes recovery.** Break retry loops, add cloud escalation.

12. **llm_os §6: Single-token fine-tune.** Publish `qwen-2.5-3b-roclaw-isa-v1.gguf` with all 18 ISA tokens as single tokens.

13. **llm_os: Build the `io.roclaw` cartridge bridge.** Prove the kernel controls real hardware.

14. **skillos_mini M2: Electricista MVP.** PhotoCapture, Gemma 4 vision, PDF generation, WhatsApp share. Tag v0.1.0.

15. **Connect dream engines.** RoClaw dreams → strategies → llm_os cartridge promotions. The flywheel.

### TIER 4: DEFER OR DROP

16. **llm_os §4: WASM cartridge sandbox.** Nice to have but not needed for v1.0 validation. In-process handlers work fine for trusted cartridges.

17. **skillos knowledge compilation wiki.** Powerful but orthogonal to the kernel+trade-app convergence. Extract as standalone package, maintain separately.

18. **skillos `agent_runtime.py` Python runtime.** Dead code. Claude Code is the runtime. Remove.

19. **RoClaw few-shot and host-text compilation modes.** Maintain tool-call (primary) + grammar (fallback) only.

20. **evolving-memory standalone server.** RoClaw was decoupled Apr 6. Unless there's a new use case, this is maintenance-only.

---

## 5. THE 90-DAY INTEGRATED ROADMAP

```
WEEK  llm_os              skillos              skillos_mini         RoClaw
────  ──────              ──────              ────────────         ──────
 1-2  §1 Grammar swap     Prune to 3 domains  M1 Interviews       Commit traces
      (llama.cpp patch)   Delete deprecated    Lock naming          Trace format std
                          stubs
 3-4  §2 ISA-aware        Lazy-loading for     M2 start:           Scene-graph
      compactor           cartridge discovery  PhotoCapture         polish
      (<|state|> opcode)                       Vision pipeline
 5-6  §3 Three-strikes    Dream cron pattern   M2 cont:            io.roclaw
      recovery            Trace format std     PDF generation       cartridge bridge
                                               WhatsApp share
 7-8  §6 Fine-tune        Dream ↔ llm_os       M2 ship:            Dream → llm_os
      recipe              integration          Tag v0.1.0           trace promotion
      (LoRA + tokenizer)                       Firebase distro
 9-10 E2E validation      Knowledge pkg        M3 Plomero           A/B testing with
      (Pi 5 hardware)     extraction           + Pintor carts       new strategies
                          (standalone)
11-12 v1.0-rc1 tag        v2.0 release         M4 Onboarding       v2.0 release
      (if gates pass)     (focused, clean)     + polish
```

---

## 6. SUMMARY VERDICT

### What to CUT (immediately stop investing)
- `agent_runtime.py` (Python multi-provider runtime in skillos)
- `experiments/gemma4-skills/` (spike complete, move on)
- `cartridges/cooking/` and `cartridges/learn/` (off-pivot)
- Project demo outputs (Project_aorta_gemma*, Project_echo_q_gemma*, etc.)
- Deprecated stubs and redirect files in skillos
- RoClaw few-shot and host-text compilation modes
- The "13 opcodes = RoClaw's 13 opcodes" narrative

### What to KEEP (maintain, don't expand)
- evolving-memory (standalone, maintenance-only)
- RoClaw's 4 compilation modes (reduce to 2 but keep working)
- skillos's knowledge compilation (extract as package)
- llm_os §4 WASM sandbox (defer to post-v1.0)
- llm_os §5 daemon-side opcode reject (defer to post-v1.0)

### What to IMPROVE (double down)
- **llm_os grammar swap** — the #1 priority in the entire portfolio
- **llm_os ISA-aware compactor** — the #1 correctness risk
- **llm_os self-hosting trace pipeline** — the flywheel
- **skillos hierarchical skill tree** — adopt for llm_os cartridge discovery
- **skillos dream consolidation** — the differentiator
- **skillos_mini cartridge-with-validator pattern** — the moat
- **skillos_mini PDF+WhatsApp value loop** — the product
- **RoClaw dream engine** — the only working dream producing real artifacts
- **RoClaw scene-graph pipeline** — real robotics infrastructure

### The Big Bet
**llm_os IS the right bet.** The "LLM as CPU" thesis is mechanically sound. The architecture is coherent. The 6-item roadmap to v1.0 is bounded and achievable. If §1 (grammar swap) and §2 (compactor) land, you have a genuinely novel OS architecture that can:
- Control hardware (via RoClaw cartridge)
- Run regulated trade workflows (via skillos_mini cartridges)
- Learn from experience (via dream engine → trace promotion → fine-tune)
- Scale from Pi 5 edge to cloud (via dual-brain routing)

This is the investment thesis. Everything else should serve it.
