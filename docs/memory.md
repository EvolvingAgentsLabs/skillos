# Memory System

SkillOS has a persistent, structured memory system that makes the OS learn over time. Every execution contributes experiences; future executions query those experiences to make better decisions.

---

## Memory Layers

| Layer | File / Location | Scope | Purpose |
|-------|----------------|-------|---------|
| **SmartMemory** | `system/SmartMemory.md` | Global | Single source of truth — structured experience database |
| **Project short-term** | `projects/[name]/memory/short_term/` | Per-project, per-session | Agent interaction logs, intermediate state |
| **Project long-term** | `projects/[name]/memory/long_term/` | Per-project, persistent | Consolidated insights across sessions |

---

## SmartMemory

`system/SmartMemory.md` is the global experience database. Every completed execution writes a structured entry here. Future executions query it before planning to avoid re-learning known patterns.

### Entry Format

```markdown
---
timestamp: 2026-04-01T14:30:00Z
task: research-quantum-computing
goal: "Research quantum computing applications in medicine"
outcome: success
quality_score: 9/10
agents_used: [system-agent, research-assistant, memory-consolidation-agent]
tools_used: [WebFetch, Read, Write]
execution_time_s: 120
cost_estimate: low
tags: [research, web-fetch, report-generation]
user_sentiment: satisfied
---

## Task: Research Quantum Computing in Medicine

### What Worked
- Breaking research into subtopics before fetching improved coherence
- Writing intermediate summaries before the final report reduced redundancy

### What Failed
- First WebFetch attempt timed out — retry with 30s timeout succeeded

### Learnings
- For research tasks: fetch → summarize → synthesize works better than fetch all → synthesize
- MIT Tech Review is more reliable than direct arxiv for medicine+quantum content

### Reusable Pattern
Research pipeline: topic decomposition → parallel fetch → per-source summary → synthesis → report
```

### Querying SmartMemory

The `query-memory-tool` provides a standardized interface:

```
skillos execute: "Query memory for past research tasks and apply lessons to this new goal"
```

Internally, `QueryMemoryTool` delegates to `memory-analysis-agent`, which:
1. Parses SmartMemory entries by tags, task type, and outcome
2. Identifies patterns across executions
3. Returns actionable recommendations for the current task

---

## Project Short-Term Memory

Short-term memory logs every agent interaction within a session. These are raw, timestamped records — not yet consolidated.

**Location:** `projects/[ProjectName]/memory/short_term/`

**Naming:** `YYYY-MM-DD_HH-MM-SS_{agent-name}_interaction.md`

### Log Format

```markdown
---
timestamp: 2026-04-01T14:30:00Z
agent: research-assistant
action: fetch_and_summarize
project: Project_quantum_medicine
session_id: abc123
---

## Request
Fetch and summarize content from MIT Tech Review on quantum computing in medicine.

## Agent Response
Fetched 3 articles. Key findings:
- Quantum annealing shows promise for protein folding (2025 paper)
- IBM Q Network has 2 active medical research partnerships
- Error correction remains the primary barrier to clinical use

## Tools Used
- WebFetch: https://www.technologyreview.com/... → 200 OK, 4.2KB
- Write: projects/.../output/mit_summary.md

## Outcome
Summary written. Quality: high. Execution: 12s.

## Observations
The site's pagination required fetching /page/2 for full content.
```

---

## Project Long-Term Memory

After execution completes, `memory-consolidation-agent` processes the session's short-term logs and writes consolidated insights to long-term memory.

**Location:** `projects/[ProjectName]/memory/long_term/`

Long-term memory contains:
- Patterns that emerged across multiple agents in the session
- Strategies that worked or failed
- Reusable approaches for similar future goals
- Parameter choices and their outcomes

---

## Memory Skills

### memory-analysis-agent

Analyzes historical execution logs to find patterns and generate recommendations.

```
Domain: memory / family: analysis
Invoke when: "what worked before", "learn from past", "memory query"
```

**Capabilities:**
- Cross-execution pattern detection
- Success/failure rate analysis by strategy
- User sentiment trend analysis
- Behavioral constraint recommendations

### memory-consolidation-agent

Runs after each execution to extract durable insights from short-term logs.

```
Domain: memory / family: consolidation
Invoke when: end of execution, "consolidate memory", "update learnings"
```

**Process:**
1. Read all short-term logs from the session
2. Identify patterns: what was tried, what succeeded, what failed
3. Extract reusable strategies
4. Write structured entry to `long_term/` and `system/SmartMemory.md`

### query-memory-tool

Standardized interface for memory-driven decision making.

```
Domain: memory / family: query
Invoke when: planning phase, "what do we know about X", capability gap detected
```

**Usage pattern** (SystemAgent calls this at the start of planning):
```
QueryMemoryTool(
  query: "research tasks with web fetching",
  tags: ["research", "web-fetch"],
  outcome_filter: "success",
  max_results: 3
)
→ Returns: top 3 matching experiences with extracted recommendations
```

### memory-trace-manager

Manages the raw trace log — records every tool call, result, and decision during execution. Used for fine-tuning dataset generation and debugging.

```
Domain: memory / family: trace
```

---

## Memory-Driven Execution

The full memory loop during a SkillOS execution:

```
1. Boot / Goal received
       ↓
2. QueryMemoryTool → find relevant past experiences
       ↓
3. SystemAgent uses recommendations to inform planning
   (e.g., "last time this strategy failed — try alternate approach")
       ↓
4. Execution proceeds
       ↓
5. memory-trace-manager logs every action
       ↓
6. short_term logs written per agent interaction
       ↓
7. memory-consolidation-agent processes session
       ↓
8. SmartMemory updated with new experience
       ↓
9. Next execution starts at Step 2 — smarter
```

---

## Behavioral Learning

Beyond task outcomes, memory captures **behavioral patterns**:

- **User sentiment** — was the user satisfied, frustrated, neutral?
- **Constraint evolution** — which behavioral constraints were effective?
- **Adaptation history** — how did execution strategy change mid-run?

This enables **sentient state management**: the system adapts its behavior in real-time based on detected user sentiment and past adaptation history, not just task success/failure.

---

## Resetting Memory

```bash
# Clear short-term for a specific project (keeps long-term)
rm projects/[ProjectName]/memory/short_term/*

# Archive and reset SmartMemory (start fresh globally)
cp system/SmartMemory.md system/SmartMemory.archive.$(date +%Y%m%d).md
echo "# SmartMemory\n" > system/SmartMemory.md
```
