# Scenarios

Scenarios are pre-built task definitions in `scenarios/`. Each scenario demonstrates a SkillOS capability pattern and can be run directly.

---

## Running a Scenario

```bash
# Claude Code
claude --dangerously-skip-permissions "skillos execute: 'Run the [ScenarioName] scenario'"

# SkillOS Terminal
./skillos.sh
skillos$ Run the RealWorld_Research_Task scenario in EXECUTION MODE

# Qwen runtime
python agent_runtime.py "Run the RealWorld Research Task scenario"
```

---

## Available Scenarios

### RealWorld_Research_Task

**File:** `scenarios/RealWorld_Research_Task.md`
**Mode:** EXECUTION (real tool calls)

Live web research with real HTTP fetches, summarization, and structured output.

**What it demonstrates:**
- WebFetch with real URLs and error handling
- Multi-source content aggregation
- Sentient state management (constraints evolve during execution)
- Memory-driven planning (QueryMemoryTool before fetching)
- Structured output generation

**Run it:**
```bash
skillos execute: "Run the RealWorld_Research_Task scenario in EXECUTION MODE"
```

**Expected outputs:** `projects/Project_research/output/` — summary report, source list, execution trace

---

### CodeAnalysis_Task

**File:** `scenarios/CodeAnalysis_Task.md`
**Mode:** EXECUTION

Analyzes a codebase for architecture, quality, and improvement opportunities.

**What it demonstrates:**
- File tree traversal and pattern detection
- Multi-agent pipeline (discovery → analysis → recommendations)
- Structured code review output

**Run it:**
```bash
skillos execute: "Run the CodeAnalysis_Task scenario on this repository"
```

**Expected outputs:** Architecture overview, quality report, prioritized improvement list

---

### ProjectAortaScenario

**File:** `scenarios/ProjectAortaScenario.md`
**Mode:** EXECUTION
**Last validated:** 2026-04-12 (Opus 4.6)

The "Project Aorta" three-agent cognitive pipeline for quantum homomorphic signal processing of arterial pressure waves. Demonstrates specialized multi-agent collaboration with mathematical rigor.

**Agents in pipeline:**
1. **VisionaryAgent** — Transforms research concept into comprehensive project description (36KB output)
2. **MathematicianAgent** — Converts vision into rigorous mathematical framework (37KB output)
3. **QuantumEngineerAgent** — Implements quantum cepstral pipeline in code

**What it demonstrates:**
- Dynamic creation of 3 specialized agents as markdown at runtime
- Sequential multi-agent pipeline with handoffs
- Publication-grade technical depth: clinical motivation + mathematical foundations + quantum implementation

**Run it:**
```bash
skillos execute: "Run the Project Aorta scenario"
```

**Expected outputs:** `projects/Project_aorta/output/` — `project_vision.md`, `mathematical_framework.md`, quantum implementation

---

### AutoResearch_Task

**File:** `scenarios/AutoResearch_Task.md`
**Mode:** EXECUTION

Autonomous iterative research and improvement loop. Given an input program, runs N cycles of analysis → improvement → testing → commit.

**What it demonstrates:**
- Autonomous long-running task execution
- Git integration (commits improvements)
- Self-improving loop with memory persistence
- Time-windowed execution

**Run it:**
```bash
skillos execute: "Run autoresearch on input/train.py for 50 cycles — 5-minute windows, commit every improvement"
```

---

### ContentCreation_Task

**File:** `scenarios/ContentCreation_Task.md`
**Mode:** EXECUTION

Research → draft → review → publish pipeline for technical content.

**What it demonstrates:**
- Content generation with research grounding
- Review agent providing quality feedback
- Iterative refinement before final output

**Run it:**
```bash
skillos execute: "Run the ContentCreation_Task scenario for a post on AI safety"
```

---

### DataAnalysis_Task

**File:** `scenarios/DataAnalysis_Task.md`
**Mode:** EXECUTION

Data ingestion → cleaning → analysis → visualization pipeline.

**What it demonstrates:**
- CSV/JSON data processing
- Statistical analysis with Bash + Python
- Chart generation
- Summary report with findings

**Run it:**
```bash
skillos execute: "Run the DataAnalysis_Task scenario on the data in input/"
```

---

### KnowledgeSynthesis_Task

**File:** `scenarios/KnowledgeSynthesis_Task.md`
**Mode:** EXECUTION

Multi-source knowledge aggregation and synthesis into a structured knowledge base.

**What it demonstrates:**
- Aggregating knowledge from multiple documents
- Entity extraction and relationship mapping
- Knowledge base construction

---

### GitRepoAudit_Task

**File:** `scenarios/GitRepoAudit_Task.md`
**Mode:** EXECUTION

Full git repository audit: commit history, contributor patterns, code churn, and risk assessment.

**What it demonstrates:**
- Git history analysis via Bash
- Pattern detection across commits
- Risk scoring and recommendations

**Run it:**
```bash
skillos execute: "Run the GitRepoAudit_Task on this repository"
```

---

### RoClaw_Integration

**File:** `scenarios/RoClaw_Integration.md`
**Mode:** EXECUTION (requires robot bridge)

Full end-to-end physical robot demonstration. See [docs/robot.md](robot.md) for prerequisites.

**What it demonstrates:**
- Cognitive Trinity integration (SkillOS + RoClaw + evolving-memory)
- Navigation with memory-guided route planning
- Scene analysis and semantic mapping
- Dream consolidation cycle
- Dynamic recovery agent creation

**Run it:**
```bash
# Start prerequisites first (see docs/robot.md)
skillos execute: "Run the RoClaw Integration scenario"
```

---

### Operation_Echo_Q

**File:** `scenarios/Operation_Echo_Q.md`
**Mode:** EXECUTION
**Tutorial:** [docs/tutorial-echo-q.md](tutorial-echo-q.md)
**Last validated:** 2026-04-12 (Opus 4.6)

Mathematically rigorous quantum computing scenario: derive, prove, and implement a Quantum Cepstral Analysis algorithm. The "Markdown as mathematical blackboard" demonstration.

**Agents in pipeline:**
1. **quantum-theorist-agent** — Builds LaTeX wiki with QFT, QSVT, block-encoding concepts (5 concept pages + 1 entity page)
2. **pure-mathematician-agent** — Extracts mathematical invariants as enforceable constraints (6 hard + 4 soft)
3. **qiskit-engineer-agent** — Implements algorithm with reflective error-recovery loop (classical echo error 0.003s, quantum statevector 0.034s)
4. **system-architect-agent** — Synthesizes whitepaper with wiki citations

**What it demonstrates:**
- Knowledge Wiki as persistent mathematical scratchpad (compounding loop)
- Sentient state constraints derived from physics (unitarity, no-cloning, polynomial depth)
- Reflective error recovery cross-referenced against wiki math
- 4-agent hierarchical decomposition with wiki handoffs

**Validated results (2026-04-12):** All 4 phases pass. Hard constraints C1-C6 all pass. Chebyshev polynomial error 5.43e-4 (within 1e-3 budget). Echo detection PASS (0.003s error < 0.05s threshold). 8,894 output tokens.

**Run it:**
```bash
skillos execute: "Run the Operation Echo-Q scenario"
```

---

### Operation_Echo_Q_Dialects

**File:** `scenarios/Operation_Echo_Q_Dialects.md`
**Mode:** EXECUTION
**Variant of:** Operation_Echo_Q (dialect-enhanced for A/B token comparison)
**Last validated:** 2026-04-12 (Opus 4.6)

Dialect-enhanced version of Operation Echo-Q. Same 4-agent quantum cepstral analysis pipeline, but internal artifacts use SkillOS dialect compression: wiki derivations in `formal-proof` notation, constraints in `constraint-dsl` notation, state tracking in `exec-plan`. Code and whitepaper remain verbose for human consumption.

**Dialects used:**
- `formal-proof` — GIVEN:/DERIVE:/QED notation for wiki derivation sections (13 proof blocks across 5 pages)
- `constraint-dsl` — C[N][H/M/L] format for mathematical invariants
- `exec-plan` — Pipeline state tracking

**What it demonstrates:**
- Full dialect pipeline integration with existing complex scenarios
- A/B token comparison vs original with measured compression
- Dialect notation preserves logical structure while compressing prose
- Human-renderer-agent expansion at egress for final deliverables

**Validated results (2026-04-12):** All 4 phases pass. Wiki concepts: 26,621 → 23,146 bytes (-13%, ~50% in derivation sections). Constraints: 5,119 → 1,796 bytes (**-65%**). Echo detection PASS (classical 0.003s, quantum 0.034s). 6/6 hard constraints pass. Internal artifacts: **-23%** overall.

**Run it:**
```bash
skillos execute: "Run the Operation Echo-Q Dialects scenario"
```

**Expected outputs:** `projects/Project_echo_q_dialects/` — dialect-compressed wiki, constraint-dsl state, whitepaper with expanded prose, working quantum code

---

### ProjectAorta_Dialects

**File:** `scenarios/ProjectAorta_Dialects.md`
**Mode:** EXECUTION
**Variant of:** ProjectAortaScenario (dialect-enhanced for A/B token comparison)
**Last validated:** 2026-04-12 (Opus 4.6)

Dialect-enhanced version of Project Aorta. Same 3-agent cognitive pipeline, but with dialect compression: vision document in `caveman-prose`, mathematical framework in `formal-proof` + `system-dynamics`, code remains verbose.

**Dialects used:**
- `caveman-prose` — Compressed narrative for vision document
- `formal-proof` — GIVEN:/DERIVE:/QED for mathematical derivations
- `system-dynamics` — Stock-flow notation ([STOCK], [FLOW], [FB+], [FB-]) for hemodynamic models
- `exec-plan` — Pipeline state tracking

**What it demonstrates:**
- Multi-dialect pipeline (different dialects per stage)
- caveman-prose for narrative compression
- system-dynamics for domain-specific modeling
- A/B token comparison vs original with measured compression

**Validated results (2026-04-12):** All 3 stages pass. Vision: 36,187 → 5,424 bytes (**-85%** via caveman-prose). Math framework: 37,410 → 27,622 bytes (**-26%** via formal-proof + system-dynamics). Echo delay detected at 50.000ms (0.000ms error). Clinical threshold PASS. Total pipeline: **-47%**.

**Run it:**
```bash
skillos execute: "Run the Project Aorta Dialects scenario"
```

**Expected outputs:** `projects/Project_aorta_dialects/` — caveman-prose vision, formal-proof + system-dynamics math framework, working quantum code, exec-plan pipeline state. Use `human-renderer-agent` to expand compressed outputs for reading.

---

### KnowledgeBase_Research_Task

**File:** `scenarios/KnowledgeBase_Research_Task.md`
**Mode:** EXECUTION

LLM Knowledge Base demonstration (Karpathy pattern): compounding wiki with ingest, query, lint, and output generation cycles.

**Run it:**
```bash
skillos execute: "Run the KnowledgeBase_Research_Task scenario"
```

---

## Writing Custom Scenarios

A scenario file is a markdown document describing a goal and context for SkillOS to execute:

```markdown
# MyScenario

## Goal
Describe what this scenario achieves and why.

## Context
Any background information SystemAgent needs.

## Execution Mode
EXECUTION  # or SIMULATION

## Steps
The expected execution flow (optional — SystemAgent can plan its own).

1. Step one description
2. Step two description
3. ...

## Expected Outputs
- output/result.md
- output/report.md

## Success Criteria
How to tell if the scenario completed successfully.
```

Place the file in `scenarios/` and run it:

```bash
skillos execute: "Run the MyScenario scenario"
```

---

## Simulation Mode

Any scenario can be run in SIMULATION MODE for generating training data without making real tool calls:

```bash
skillos simulate: "Research task workflow for fine-tuning dataset"
```

In simulation mode:
- WebFetch returns synthetic but realistic content
- File operations are logged but not persisted
- The full execution trace is recorded as training data
- Memory entries are tagged `source: DREAM_TEXT` with fidelity `0.3`
