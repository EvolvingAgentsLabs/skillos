---
name: memory-trace-manager
type: tool
version: v2
status: "[REAL] - Production Ready"
description: >
  Manages execution traces, structured logging, and training data generation for SkillOS.
  Records agent communications, rotates memory logs, exports training datasets,
  computes performance metrics, and validates log integrity.
tools: Read, Write, Grep, Bash
---

# MemoryTraceManager Tool

**Version**: v2
**Status**: [REAL] - Production Ready

## Purpose

Manages volatile memory traces of agent communications during SkillOS task execution sessions. Captures, analyzes, and consolidates agent interactions for learning and pattern recognition. Provides structured export for fine-tuning datasets.

## Core Functions

### 1. record_experience

Records a complete execution experience to `system/SmartMemory.md`.

**Parameters**:
```yaml
session_id: string          # Unique session identifier
project: string             # Project name
goal: string                # High-level goal
outcome: "success" | "partial" | "failure"
components_used: []         # List of agents/tools invoked
output_summary: string      # What was produced
learnings: string           # Key takeaways
quality_score: number       # 0-10 quality rating
cost_estimate_usd: number   # Estimated cost
duration_seconds: number    # Wall-clock time
error_events: []            # Any errors encountered
```

**Memory Entry Format**:
```markdown
---
experience_id: exp_NNN
timestamp: 2026-03-12T14:30:00Z
session_id: string
project: string
goal: string
outcome: string
components_used: []
quality_score: number
cost_estimate_usd: number
duration_seconds: number
---

## Output Summary
[What was produced]

## Learnings
[Key takeaways and patterns discovered]

## Error Events
[Any errors and how they were handled]
```

### 2. rotate_memory

Maintains memory log health by archiving old entries and pruning low-value records.

**Policy**:
```yaml
retention:
  keep_recent: 50           # Always keep the 50 most recent entries
  keep_high_quality: true    # Keep entries with quality_score >= 8.0 regardless of age
  archive_threshold_days: 90 # Archive entries older than 90 days
  archive_path: "system/memory_archive/"
pruning:
  max_entries: 200           # Hard cap on active memory log entries
  priority: "quality_score DESC, timestamp DESC"
```

**Execution**:
1. Read `system/memory_log.md` and parse all experience blocks
2. Identify entries older than `archive_threshold_days`
3. Move low-quality old entries to `system/memory_archive/YYYY-MM.md`
4. Keep high-quality entries regardless of age
5. Write updated `system/memory_log.md`

### 3. export_training_data

Exports memory log entries as structured training datasets for LLM fine-tuning.

**Export Formats**:

```yaml
formats:
  instruction_following:
    description: "Goal → execution trace → output pairs"
    file: "system/training_data/instruction_following.jsonl"
    schema:
      instruction: string    # The goal
      input: string          # Context and constraints
      output: string         # Execution trace and result

  chat_completion:
    description: "Multi-turn agent dialogue sequences"
    file: "system/training_data/chat_completion.jsonl"
    schema:
      messages:
        - role: "system"     # SystemAgent context
        - role: "user"       # Goal/delegation prompt
        - role: "assistant"  # Agent response

  preference_pairs:
    description: "Chosen/rejected pairs from quality_score comparisons"
    file: "system/training_data/preference_pairs.jsonl"
    schema:
      prompt: string
      chosen: string         # Higher quality_score execution
      rejected: string       # Lower quality_score execution
```

### 4. compute_metrics

Calculates aggregate performance metrics from the memory log.

**Output Metrics**:
```yaml
metrics:
  total_executions: number
  success_rate: number       # percentage
  average_quality_score: number
  average_cost_usd: number
  average_duration_seconds: number
  most_used_components: []
  most_common_errors: []
  quality_trend:             # Last 10 vs previous 10
    direction: "improving" | "stable" | "declining"
    delta: number
  cost_efficiency:           # quality_score / cost ratio
    current: number
    trend: "improving" | "stable" | "declining"
```

### 5. validate_log

Validates memory log structural integrity.

**Checks**:
- Every experience block has YAML frontmatter with required keys: `experience_id`, `timestamp`, `project`, `goal`, `outcome`
- Timestamps are valid ISO 8601
- `experience_id` values are unique
- `quality_score` is in range 0-10
- No orphaned frontmatter delimiters

**Output**: List of findings with severity (FAIL/WARN) per ValidationAgent rule MEM-001 and MEM-002.

## Trace Recording (Session-Level)

### record_agent_communication

Captures agent-to-agent communications during task execution.

**Parameters**:
```yaml
session_id: string
from_agent: string
to_agent: string
message_type: "request" | "response" | "notification" | "error" | "delegation"
message_content: string
context: string
timestamp: string           # ISO 8601
execution_step: integer
```

### Session Storage Structure

```
projects/{project_name}/memory/short_term/
├── {session_id}/
│   ├── session_metadata.md
│   ├── communication_log.jsonl
│   ├── agent_states.md
│   ├── context_evolution.md
│   └── execution_flow.md
```

### Session Consolidation

At session end, `analyze_session_for_learning` extracts:
- Successful collaboration patterns
- Communication bottlenecks
- Knowledge gaps discovered
- Emergent problem-solving approaches

Writes consolidated learnings to:
- `projects/{project}/memory/long_term/learned_patterns.md`
- `projects/{project}/memory/long_term/agent_collaboration_map.md`

## Integration

### Connection to System Memory Log
- Consolidation results feed into `system/memory_log.md`
- Cross-project patterns stored at system level

### QueryMemoryTool Integration
- Provides communication pattern data to QueryMemoryTool
- Historical agent interaction success rates inform future agent selection

## Claude Tool Mapping

- **Read**: Load memory log, parse experience blocks, read session traces
- **Write**: Create memory entries, write exports, update archive
- **Grep**: Search memory for patterns, count entries for rotation decisions
- **Bash**: Date calculations for rotation, JSONL export formatting
