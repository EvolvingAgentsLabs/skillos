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
python qwen_runtime.py "Run the RealWorld Research Task scenario"
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

The "Project Aorta" three-agent cognitive pipeline for quantum signal processing. Demonstrates specialized multi-agent collaboration with mathematical rigor.

**Agents in pipeline:**
1. **VisionaryAgent** — Defines the mathematical framework and vision
2. **ArchitectAgent** — Designs the implementation architecture
3. **ImplementationAgent** — Produces working code

**What it demonstrates:**
- Specialized agent creation for a domain (quantum signal processing)
- Sequential multi-agent pipeline with handoffs
- Technical depth: mathematical foundations + code

**Run it:**
```bash
skillos execute: "Run the Project Aorta scenario"
```

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
