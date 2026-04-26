# SkillOS — Pure Markdown Operating System

SkillOS is a proof-of-concept OS where every component [agents, tools, memory, orchestration] is defined entirely in markdown documents. No code compilation. No complex APIs. Just markdown that any LLM interprets at runtime to become a composable problem-solving system.

> Evolved from [LLMos](https://github.com/EvolvingAgentsLabs/llmos) — testing Skills as basic programs.

![SkillOS running in Claude Code](docs/assets/skillos_claude_screen.png)

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/EvolvingAgentsLabs/skillos.git && cd skillos

# 2. Run Claude Code
claude --dangerously-skip-permissions

# 3. Boot SkillOS
boot skillos
```

### Full Setup (in case you want to explore alternative runtimes)

Initialize the agent discovery system before booting:

```bash
./setup_agents.sh    # Mac/Linux
.\setup_agents.ps1   # Windows
```

Requires: Python 3.11+, Git, Claude Code CLI. Optional: Node.js 18+ (for JS skills).

---

## Runtimes

### Option 1: SkillOS Terminal (Recommended)
**Best for:** Interactive use, the full Unix-like experience

```bash
./skillos.sh
# Or directly:
python3 skillos.py
```

```
skillos$ Create a tutorial on chaos theory
skillos$ Monitor tech news and generate a briefing
skillos$ help
```

> Requires: Python 3.11+, `rich` (auto-installed on first run), Claude Code CLI

### Option 2: Claude Code (Direct)
**Best for:** Scripting, CI/CD, single-command execution

```bash
claude --dangerously-skip-permissions "boot skillos"
claude --dangerously-skip-permissions "skillos execute: 'Your goal here'"
```

### Option 3: Agent Runtime (Multi-Provider)
**Best for:** Lightweight use, free-tier access, local/offline use

```bash
pip install openai python-dotenv

OPENROUTER_API_KEY=... python agent_runtime.py "Your goal here"            # Qwen (default)
GEMINI_API_KEY=... python agent_runtime.py --provider gemini "Your goal"   # Gemini
python agent_runtime.py --provider gemma "Your goal"                        # Gemma 4 (Ollama)
OPENROUTER_API_KEY=... python agent_runtime.py --provider gemma-openrouter "Your goal"  # Gemma 4 (OpenRouter)
python agent_runtime.py --sandbox e2b "Your goal"                           # E2B cloud sandbox
python agent_runtime.py interactive                                          # Interactive mode
```

**Run multi-agent scenarios with any provider:**

```bash
# Cognitive pipeline — forces step-by-step execution for mid-tier models
python run_scenario.py scenarios/Operation_Echo_Q.md "quantum cepstral analysis" \
    --provider gemma-openrouter --no-stream

# Strategy auto-selects based on model tier (or override manually)
python run_scenario.py scenarios/ProjectAortaScenario.md "quantum arterial navigation" \
    --provider gemma-openrouter --strategy cognitive_pipeline --no-stream
```

**Gemma 4 on a free Colab GPU** — no local GPU needed:

```bash
# 1. Open notebooks/skillos_gemma4_colab.ipynb in Google Colab (T4 GPU)
# 2. Run all cells — you'll get a Cloudflare tunnel URL
# 3. On your local machine:
OLLAMA_BASE_URL=https://xxx.trycloudflare.com/v1 python agent_runtime.py --provider gemma "Your goal"
```

See [docs/runtimes.md](docs/runtimes.md) for setup and comparison, and [docs/cognitive-pipeline.md](docs/cognitive-pipeline.md) for the cognitive pipeline architecture.

---

## Core Concept

Everything is either an **Agent** (decision maker) or a **Tool** (executor), defined in markdown:

```markdown
---
name: example-agent
type: agent
description: An agent that solves problems
tools: Read, Write, WebFetch
extends: orchestration/base
---

# ExampleAgent
You are a research specialist. Given a topic, you...
```

Skills are organized in a **3-level hierarchy** (Domain → Family → Skill) with a 4-step lazy loading protocol that reduces routing-phase token consumption by ~61% versus a flat registry.

```
Domain → Family → Skill
──────────────────────────────────────────────────
orchestration/  core/           system-agent
                ingress/        intent-compiler-agent
                egress/         human-renderer-agent
memory/         analysis/       memory-analysis-agent
                consolidation/  memory-consolidation-agent
                query/          query-memory-tool
robot/          navigation/     roclaw-navigation-agent
                scene/          roclaw-scene-analysis-agent
                dream/          roclaw-dream-agent
dialects/       compiler/       dialect-compiler-agent
                expander/       dialect-expander-agent
                registry/       dialect-registry-tool
validation/     system/         validation-agent
recovery/       error/          error-recovery-agent
project/        scaffold/       project-scaffold-tool
                packages/       skill-package-manager-tool
```

---

## Key Features

- **Pure Markdown** — No code compilation. The LLM is the interpreter.
- **Hierarchical Skills** — Domain → Family → Skill taxonomy with 4-step lazy loading
- **Token Efficient** — 61% reduction in routing-phase token consumption
- **Cognitive Pipeline** — Recursive Context Isolation gives mid-tier models the executive functioning of frontier models: 5K→28K output, 100% step pass rate ([docs](docs/cognitive-pipeline.md))
- **Dialects** — 14 domain-specific compression formats (50-99% token reduction) with Language Facade and cognitive scaffolding
- **Knowledge Wiki** — Compounding knowledge base inspired by Karpathy's LLM Wiki pattern
- **Memory System** — Every execution improves future runs via structured memory
- **Robot Integration** — SkillOS as Prefrontal Cortex for the RoClaw physical robot
- **Multi-Provider** — Works with Claude Code, Qwen, Gemini, Gemma 4 (Ollama + OpenRouter), or any OpenAI-compatible endpoint
- **Dynamic Agents** — New agents created as markdown at runtime, no restarts needed
- **Execution Sandboxing** — Path traversal prevention, restricted `exec()`, optional E2B cloud sandbox

---

## Dialects: Token Compression for Edge AI

SkillOS includes a **dialect framework** — 14 domain-specific compression formats that transform verbose content into minimal, actionable representations. Dialects reduce token cost by 50-99% while preserving (or improving) quality. A **Language Facade** (ingress/egress boundary agents) ensures agents never process verbose English internally, and 5 **cognitive scaffolding** dialects use formal notations (proofs, boolean logic, DAGs, stock-flow, SMILES) to improve reasoning quality.

**The three pillars:**

| Pillar | Dialect | Example | Reduction |
|--------|---------|---------|-----------|
| Hardware | `roclaw-bytecode` | `"Move forward"` → `AA 01 80 80 01 FF` | ~99% |
| Reasoning | `caveman-prose` | `"You should always run tests before pushing"` → `"Run tests before push."` | ~75% |
| Software | `strict-patch` | 500-line file rewrite → `[DEL:42]`/`[ADD:42]` (4 lines) | ~98% |

Plus 11 more: `strategy-pointer`, `trace-log`, `memory-xp`, `constraint-dsl`, `exec-plan`, `dom-nav`, `formal-proof`, `system-dynamics`, `boolean-logic`, `data-flow`, `smiles-chem`.

### Benchmark Results

Four automated benchmarks prove the architecture across three domains — code editing, mathematical reasoning, and scientific computation:

| Benchmark | Dialect | Token Reduction | Quality (Plain → SkillOS) | Key Result |
|-----------|---------|-----------------|---------------------------|------------|
| Code Editing (2 bug fixes in 993-line file) | `strict-patch` | **-97.5%** | 2/2 → 2/2 | 17x faster, 75% cheaper |
| Math (K_{3,4} spanning trees) | `formal-proof` | **-51.3%** | 90 → 90 /100 | Equal accuracy, 51% fewer tokens |
| Physiology (hemodynamics) | `system-dynamics` | **-61.1%** | 100 → 100 /100 | Identical accuracy, 61% fewer tokens |
| Analytical (cascade failure) | mixed | +251% (11 turns) | 100 → 100 /100 | Equal quality, multi-turn overhead |

All verification is automated (`ast.parse()` + regex + exact answer checks) — no LLM judge needed.

```bash
# Run benchmarks
python3 benchmarks/benchmark_patch.py        # Code editing: strict-patch
python3 benchmarks/benchmark_math.py         # Math: formal-proof
python3 benchmarks/benchmark_physiology.py   # Physiology: system-dynamics
python3 benchmarks/benchmark_dialects.py     # Analytical: mixed dialects
```

**Why it matters for small models:** Gemma 4B generates a strict-patch in 0.5s instead of 30s for a full rewrite — and gets it right. A 50,000-token HTML page becomes 80 tokens of interactive elements. The dialect removes the cognitive load, letting small models punch above their weight.

See [docs/dialects.md](docs/dialects.md) for the full guide.

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/architecture.md](docs/architecture.md) | Skill tree, lazy loading, agent discovery, execution flow |
| [docs/skills.md](docs/skills.md) | Authoring agents and tools, manifests, inheritance, best practices |
| [docs/cognitive-pipeline.md](docs/cognitive-pipeline.md) | Cognitive pipeline executor, strategy router, model capability tiers |
| [docs/dialects.md](docs/dialects.md) | Dialect framework, 14 compression formats, Language Facade, cognitive scaffolding |
| [docs/memory.md](docs/memory.md) | SmartMemory, short/long-term layers, memory-driven execution |
| [docs/runtimes.md](docs/runtimes.md) | Claude Code, Qwen/Gemini, Ollama, OpenRouter — setup and comparison |
| [docs/scenarios.md](docs/scenarios.md) | All built-in scenarios and how to run them |
| [docs/robot.md](docs/robot.md) | RoClaw physical robot integration, Cognitive Trinity |
| [docs/security.md](docs/security.md) | Skill package security scanning and threat model |
| [docs/tutorial-echo-q.md](docs/tutorial-echo-q.md) | Step-by-step: Operation Echo-Q quantum computing scenario |

---

## Related projects

- **[skillos_mini](https://github.com/EvolvingAgentsLabs/skillos_mini)** — SkillOS port for mobile + small local LLMs. Svelte/Capacitor app, on-device Gemma via LiteRT/wllama, the Cartridge architecture (Gemma-native subagents), and LLM-powered context compaction. Split from this repo on 2026-04-23.

---

## Validated Scenarios

Two complex multi-agent scenarios are validated end-to-end with each release, across both high-tier (Claude Opus 4.6) and mid-tier (Gemma 4 26B) models:

### Operation Echo-Q — Quantum Cepstral Deconvolution

4-agent pipeline: quantum theorist → pure mathematician → Qiskit engineer → system architect. Derives quantum algorithms in a LaTeX Knowledge Wiki before writing code, proving that markdown acts as a persistent mathematical blackboard.

```bash
# Claude Code
skillos execute: "Run the Operation Echo-Q scenario"

# Gemma 4 via OpenRouter (cognitive pipeline)
python run_scenario.py scenarios/Operation_Echo_Q.md "quantum cepstral analysis" \
    --provider gemma-openrouter --no-stream
```

**Results (Opus 4.6, 2026-04-12):** All 4 phases pass — 5 wiki concept pages with LaTeX, 6 hard + 4 soft mathematical constraints, working `quantum_cepstrum.py` (classical echo detection error 0.003s, quantum statevector 0.034s), synthesized whitepaper. 8,894 output tokens.

**Results (Gemma 4 26B, 2026-04-13):** All 4 phases pass — 28,009 chars total output, 0 retries. See cross-model comparison below.

### Project Aorta — Quantum Homomorphic Signal Processing

3-agent cognitive pipeline: visionary → mathematician → quantum engineer. Produces a 36KB clinical vision document and 37KB rigorous mathematical framework for radiation-free catheter navigation via pressure wave echo analysis.

```bash
# Claude Code
skillos execute: "Run the Project Aorta scenario"

# Gemma 4 via OpenRouter (cognitive pipeline)
python run_scenario.py scenarios/ProjectAortaScenario.md "quantum arterial navigation" \
    --provider gemma-openrouter --no-stream
```

**Results (Opus 4.6, 2026-04-12):** Vision and mathematical framework stages produce publication-grade outputs. Three specialized agents created dynamically as markdown at runtime.

**Results (Gemma 4 26B, 2026-04-13):** All 3 stages pass — 28,120 chars total output, 0 retries.

### Cross-Model Comparison: Recursive Context Isolation

The cognitive pipeline uses **Recursive Context Isolation** — the same pattern behind Claude Code's subagent architecture — to give mid-tier models the executive functioning of frontier models. Each delegated agent gets its own fresh context window with only its spec and task, runs a bounded tool loop, and returns results. Five learned mechanisms (tool-call scaffolding, file injection, auto-wrap prose, output validation, dynamic agent generation) compensate for mid-tier model weaknesses:

| Metric | Claude Opus 4.6 | Gemma 4 26B (cognitive pipeline) | Ratio |
|--------|-----------------|----------------------------------|-------|
| **Aorta total output** | 464 KB | 28 KB | 17x |
| **Aorta steps passing** | 3/3 | 3/3 | Equal |
| **Echo-Q total output** | 136 KB | 28 KB | 5x |
| **Echo-Q steps passing** | 4/4 | 4/4 | Equal |
| **Code depth** | 1,208 lines | ~180 lines | 7x |
| **Image generation** | Yes (PNG plots) | No | - |
| **Cost** | Claude pricing | ~$0.05/run (OpenRouter) | 50-100x cheaper |

Claude produces deeper, publication-grade content with code execution and visualization. Gemma 4 with the cognitive pipeline produces structurally complete output suitable for prototyping and first-pass exploration at a fraction of the cost.

**The core insight:** Mid-tier models produce good content when isolated to a single focused task, but can't self-orchestrate. The cognitive pipeline imposes the decomposition externally — parsing scenarios into steps, giving each agent an isolated context window with tool access, and chaining results between steps. This brought Gemma 4 from unusable (5K chars, collapsed single-turn) to fully passing (28K chars, step-by-step) — a **5.2x improvement** through architectural compensation alone. See [docs/cognitive-pipeline.md](docs/cognitive-pipeline.md) for the full architecture.

### Dialect-Enhanced Variants (A/B Token Comparison)

Both validated scenarios have dialect-enhanced variants that compress internal artifacts with SkillOS dialects while keeping final deliverables (code, whitepapers) verbose for human consumption:

| Variant | Dialects | Internal Artifact Reduction | Result |
|---------|----------|---------------------------|--------|
| **Echo-Q Dialects** | `formal-proof` + `constraint-dsl` | **-23%** overall (wiki -13%, constraints **-65%**) | All 4 phases pass, echo PASS |
| **Aorta Dialects** | `caveman-prose` + `formal-proof` + `system-dynamics` | **-47%** overall (vision **-85%**, math -26%) | All 3 stages pass, 0ms error |

```bash
skillos execute: "Run the Operation Echo-Q Dialects scenario"
skillos execute: "Run the Project Aorta Dialects scenario"
```

**Results (Opus 4.6, 2026-04-12):** Dialect compression strongest on prose-heavy artifacts (caveman-prose: -85%) and structured constraints (constraint-dsl: -65%). formal-proof notation adds mechanical traceability via `[BY rule]` annotations. Both variants produce identical-quality outputs to their originals.

---

## Example Commands

```bash
# Research and content
skillos execute: "Research the latest AI developments and create a report"
skillos execute: "Write a technical blog post about quantum computing"

# Development
skillos execute: "Create a data pipeline for processing CSV files"
skillos execute: "Analyze this codebase and suggest improvements"

# Knowledge base (Karpathy LLM Wiki pattern)
skillos execute: "Initialize a knowledge base on transformer architectures"
skillos execute: "What are the key differences between MHA and MLA attention?"

# Physical robot
skillos execute: "Navigate to the kitchen and describe what you see"

# Built-in scenarios
skillos execute: "Run the Operation Echo-Q scenario"
skillos execute: "Run the RealWorld_Research_Task scenario in EXECUTION MODE"
```

---

## License

Apache License 2.0 — see [LICENSE](LICENSE)

---

*Built by [Evolving Agents Labs Initiative](https://evolvingagentslabs.github.io)*
