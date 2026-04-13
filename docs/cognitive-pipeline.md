# Cognitive Pipeline Executor

The cognitive pipeline is a capability-aware execution strategy that enables mid-tier LLMs (like Gemma 4 26B) to complete multi-agent scenarios that would otherwise require high-tier models (like Claude Opus 4.6). It works by imposing external structure on the execution flow rather than relying on the model to self-orchestrate.

---

## The Problem

When running multi-agent scenarios with mid-tier models in agentic mode (`run_goal()`), the model collapses the entire pipeline into a single turn:

- Produces all outputs at once with significantly lower quality
- Doesn't delegate to subagents or use tools effectively
- Generates ~5K chars instead of the expected ~30K+
- Loses the tool call format after the first few turns

**Root cause:** Mid-tier models can't reliably decompose work into delegation steps, can't self-correct, and produce shallow output when asked to generate everything at once. However, when properly constrained to a single focused task, they produce good-quality content.

---

## The Solution: Strategy Router

`execute_scenario()` automatically picks the right execution mode based on the model's capabilities:

```
┌─────────────────┐     ┌───────────────────┐     ┌────────────────────┐
│   High Tier     │     │    Mid Tier        │     │    Low Tier         │
│  (Claude, etc.) │     │  (Gemma 4 26B)     │     │  (Small models)     │
│                 │     │                    │     │                     │
│  → run_goal()   │     │  → run_cognitive_  │     │  → run_pipeline()   │
│    (agentic)    │     │    pipeline()      │     │    (deterministic)  │
└─────────────────┘     └───────────────────┘     └────────────────────┘
```

### Model Capability Registry

```python
MODEL_CAPABILITIES = {
    "claude-opus-4-6":             {"tier": "high", "recommended_strategy": "agentic"},
    "gemini-2.5-flash":            {"tier": "high", "recommended_strategy": "agentic"},
    "gemini-2.5-pro":              {"tier": "high", "recommended_strategy": "agentic"},
    "google/gemma-4-26b-a4b-it":   {"tier": "mid",  "recommended_strategy": "cognitive_pipeline"},
    "gemma4":                      {"tier": "mid",  "recommended_strategy": "cognitive_pipeline"},
    "qwen/qwen3.6-plus:free":      {"tier": "low",  "recommended_strategy": "pipeline"},
}
```

Unknown models default to `mid` tier with `cognitive_pipeline` strategy.

You can override the auto-selected strategy with `--strategy`:

```bash
# Force agentic mode on a mid-tier model
python run_scenario.py scenarios/Operation_Echo_Q.md "context" \
    --provider gemma-openrouter --strategy agentic

# Force cognitive pipeline on a high-tier model
python run_scenario.py scenarios/ProjectAortaScenario.md "context" \
    --provider gemini --strategy cognitive_pipeline
```

---

## How the Cognitive Pipeline Works

### Step-by-Step Execution

Instead of giving the model the entire scenario and hoping it orchestrates, the pipeline:

1. **Parses** the scenario markdown into structured steps (agents, goals, output files)
2. **Creates** the project directory structure
3. **For each step:**
   - Loads the agent's markdown definition (or generates one dynamically)
   - Injects prior step outputs as file context
   - Runs a mini agentic loop with tool access
   - Validates output quality
   - Retries with feedback if below threshold
4. **Chains** output between steps

```
Step 1: quantum-theorist-agent    →  wiki pages (6K chars)
    ↓ (output injected into next step)
Step 2: pure-mathematician-agent  →  constraints (5K chars)
    ↓ (wiki + constraints injected)
Step 3: qiskit-engineer-agent     →  Python code (8K chars)
    ↓ (all prior output injected)
Step 4: system-architect-agent    →  whitepaper (7K chars)
```

### Key Mechanisms

#### 1. Tool-Call Scaffolding

Mid-tier models lose the tool call format after a few turns. The pipeline injects a concrete XML example as a few-shot assistant+user message pair before each step:

```
[user]   "Here is your task..."
[assistant] '<tool_call name="write_file">{"path": "output/step_1.md", ...}</tool_call>'
[user]   "Good format. Now execute the task for real."
```

This anchors the model to the correct format.

#### 2. Prior-Output File Injection

Instead of requiring the model to call `read_file` to see prior work, the pipeline pre-reads all files from the project's output directory and injects them directly into the prompt (truncated to 3K chars each, max 10 files).

#### 3. Dynamic Subagent Creation

When `_find_agent()` can't locate an agent definition, `_generate_agent_spec()` creates a markdown agent spec from the scenario body:

- Extracts the relevant Stage/Phase section from the scenario
- Generates proper YAML frontmatter with capabilities and tools
- Saves to `components/agents/` and `.claude/agents/`
- Includes `Bash` tool for `.py` outputs, `WebFetch` for wiki/research tasks

#### 4. Auto-Wrap Prose Output

When the model produces 500+ characters of content but doesn't call `write_file`, the pipeline automatically saves the prose to the expected output file. This catches cases where the model "forgets" to use tools but still produces useful content.

#### 5. Output Validation

Each step is validated against configurable thresholds:

| Check | Default | Description |
|-------|---------|-------------|
| Minimum chars | 2000 (md), 3000 (py) | Catches collapsed/shallow output |
| File written | Required | Ensures `write_file` was called |
| Required sections | Optional | Verifies specific headings present |

On validation failure, the step retries with a feedback message explaining what was missing (up to `max_retries_per_step` times). Steps are never aborted — they're marked PARTIAL after max retries.

---

## Enhanced Agent Delegation

The `delegate_to_agent` tool (used in agentic mode) has been upgraded from a single prose-only LLM call to a full multi-turn tool loop:

**Before:**
```
LLM calls delegate_to_agent → single _call_llm() → prose response (no tools)
```

**After:**
```
LLM calls delegate_to_agent → agent spec loaded → tool format injected →
  bounded tool loop (5 turns) → tool calls parsed & executed →
  file context injected → final_answer extracted
```

This means delegated agents can:
- Use all tools (write_file, read_file, list_files, etc.)
- Execute over multiple turns with tool feedback
- Access project context files
- Be generated dynamically when not found
- Go through permission policy checks

The active project directory is propagated via `self._active_project_dir` so delegation always has file context.

---

## Scenario Parsing

The pipeline parser handles two scenario formats:

### Format A: YAML `pipeline` field

```yaml
---
name: my-scenario
pipeline:
  - step: 1
    agent: research-agent
    goal: Research the topic
    output: research.md
---
```

### Format B: Markdown headings (auto-detected)

```markdown
### Stage 1: Vision (VisionaryAgent)
**Agent**: `visionary-agent`
**Goal**: Transform the research idea into a project description
**Output**: `project_vision.md`

## Phase 2: Mathematics
**Agent**: `mathematician-agent`
**Goal**: Convert description into mathematical framework
```

The parser matches `### Stage N:`, `## Phase N:`, or `## Step N:` patterns and extracts `**Agent**:`, `**Goal**:`, and `**Output**:` fields.

---

## Results: V1 → V4 Evolution

Each version added a specific architectural improvement:

| Version | Changes | Echo-Q Result | Aorta Result |
|---------|---------|---------------|--------------|
| V1 | Single-turn `run_goal()` | 5,363 chars (1 blob) | 10,686 chars (1 blob) |
| V2 | Cognitive pipeline | 15,361 chars (2/4 PASS) | 20,071 chars (3/3 PASS) |
| V3 | + scaffolding + file injection + dynamic agents | 25,334 chars (4/4 PASS) | 20,865 chars (3/3 PASS) |
| V4 | + enhanced delegation | 28,009 chars (4/4 PASS) | 28,120 chars (3/3 PASS) |

### Gemma 4 vs Claude Opus

| Metric | Claude Opus 4.6 | Gemma 4 26B | Ratio |
|--------|-----------------|-------------|-------|
| Aorta total output | 464 KB | 28 KB | 17x |
| Aorta steps passing | 3/3 | 3/3 | Equal |
| Echo-Q total output | 136 KB | 28 KB | 5x |
| Echo-Q steps passing | 4/4 | 4/4 | Equal |
| Code depth | ~1,200 lines | ~180 lines | 7x |
| Image generation | Yes (PNG plots) | No | - |
| Cost per scenario | Claude pricing | ~$0.05 (OpenRouter) | 50-100x cheaper |

**Bottom line:** The cognitive pipeline brings Gemma 4 from *unusable* to *structurally complete* — roughly 20-25% of Claude's output quality at a fraction of the cost. It's viable for prototyping, drafts, and cost-sensitive workflows.

---

## Usage

### Generic Scenario Runner

```bash
# Auto-select strategy based on model tier
python run_scenario.py scenarios/Operation_Echo_Q.md "quantum cepstral analysis" \
    --provider gemma-openrouter --no-stream

# Override strategy
python run_scenario.py scenarios/ProjectAortaScenario.md "quantum arterial navigation" \
    --provider gemma-openrouter --strategy cognitive_pipeline --no-stream

# Custom project directory
python run_scenario.py scenarios/Operation_Echo_Q.md "context" \
    --provider gemma-openrouter --project-dir projects/MyProject --no-stream
```

### CLI Flags

```bash
python agent_runtime.py --scenario scenarios/Operation_Echo_Q.md \
    --provider gemma-openrouter \
    --strategy cognitive_pipeline \
    --project-dir projects/Project_echo_q_test \
    --no-stream \
    "quantum cepstral analysis"
```

### Programmatic API

```python
from agent_runtime import AgentRuntime

rt = AgentRuntime(provider="gemma-openrouter", stream=False)

result = rt.execute_scenario(
    "scenarios/Operation_Echo_Q.md",
    "quantum cepstral analysis",
    strategy_override="cognitive_pipeline",  # or None for auto-select
    project_dir="projects/Project_echo_q_test",
)
```

---

## Tests

59 unit tests in `tests/test_cognitive_pipeline.py` covering:

- Model capability lookup and fallback
- Pipeline parsing (Format A and B)
- Strategy routing (high/mid/low tier)
- Output validation (char count, file writes, sections)
- Tool call extraction (all 4 formats)
- Dynamic subagent creation
- Tool-call scaffolding
- Prior-output file injection
- Enhanced delegation (14 tests)

```bash
pytest tests/test_cognitive_pipeline.py -v
```
