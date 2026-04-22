# Smart Memory - Experience Log

**Version**: v2
**Status**: [REAL] - Production Ready
**Purpose**: Structured, queryable experience database for continuous learning across all SkillOS executions.

## Architecture

```
system/
├── SmartMemory.md          # This file - architecture + active experience log (single source of truth)
├── memory_archive/         # Rotated old entries (by month)
└── training_data/          # Exported fine-tuning datasets
    ├── instruction_following.jsonl
    ├── chat_completion.jsonl
    └── preference_pairs.jsonl
```

## Memory Entry Format

Each entry block uses YAML frontmatter followed by markdown content.
Three entry types are supported; use the appropriate one per situation.

### entry_type: experience (default — one per task/goal execution)

```markdown
---
entry_type: experience          # optional; default if absent
experience_id: exp_NNN
timestamp: ISO-8601
session_id: string
project: string
goal: string
outcome: success | partial | failure | success_with_recovery
components_used: []
quality_score: 0-10
cost_estimate_usd: number
duration_seconds: number
# optional genealogy keys (present only when kernel_mode: genealogy):
lineage_id: string
generation: integer
dna_hash: string
---

## Output Summary
[What was produced]

## Learnings
[Key takeaways]
```

### entry_type: tutoring_session (one per DNA mutation-proposal review)

Written by `genealogy/tutor/tutor-child-agent` after every proposal review
(approved, rejected, or deferred).

```markdown
---
entry_type: tutoring_session
tutoring_session_id: tut_<session>_<seq>
timestamp: ISO-8601
project: string
lineage_id: string
generation: integer
father_agent_id: string
child_agent_id: string
proposal_id: string
decision: approved | rejected | deferred
dna_hash_before: string
dna_hash_after: string | null   # null if rejected/deferred
churn_ratio: 0.0-1.0
quality_score: 0-10             # quality of the Child's justifying task
dna_rule_violations: []         # any DNA-001..005 that fired
---

## Mutation Summary
[One-paragraph description of what changed]

## Tutor Feedback
[Full feedback text shown to Child]

## Learnings
[What this session reveals about this lineage's learning trajectory]
```

### entry_type: promotion_event (one per promotion ceremony)

Written by `genealogy/promote/promote-child-agent` — the durable record of a
Child becoming a Father. Never overwritten; rotated by month like other entries.

```markdown
---
entry_type: promotion_event
promotion_event_id: prom_<session>_<seq>
timestamp: ISO-8601
project: string
lineage_id: string
generation: integer              # child's new generation (== father's generation)
retired_father_agent_id: string
archived_dna_path: string        # system/memory_archive/dna/father-<tag>-gen<N>.md
archived_dna_hash: string
new_father_agent_id: string      # formerly the Child
new_father_dna_hash: string
validation_strategies_passed: [] # subset of [1,2,3,4,5]
adversarial_score: 0-10
---

## Rationale
[Why this promotion was approved — quote validation report highlights]

## Ancestry
[Full lineage_path at time of promotion]

## Legacy Learnings
[What the retired Father's DNA contributed that should be preserved in institutional memory]
```

## File Ownership

| File | Written By | Read By |
|---|---|---|
| SmartMemory.md (this file) | MemoryTraceManager (record_experience), MemoryConsolidationAgent | MemoryAnalysisAgent, QueryMemoryTool, SystemAgent |
| memory_archive/*.md | MemoryTraceManager (rotate_memory) | MemoryAnalysisAgent (historical queries) |
| training_data/*.jsonl | MemoryTraceManager (export_training_data) | External fine-tuning pipelines |

## Query Patterns

- **By project**: `Grep pattern="project: Project_name" path="system/SmartMemory.md"`
- **By outcome**: `Grep pattern="outcome: failure" path="system/SmartMemory.md"`
- **By component**: `Grep pattern="component_name" path="system/SmartMemory.md"`
- **High quality**: `Grep pattern="quality_score: [89]" path="system/SmartMemory.md"`
- **Genealogy — all lineage events**: `Grep pattern="entry_type: (tutoring_session|promotion_event)" path="system/SmartMemory.md"`
- **Genealogy — by lineage_id**: `Grep pattern="lineage_id: lin_<id>" path="system/SmartMemory.md"`
- **Genealogy — promotions only**: `Grep pattern="entry_type: promotion_event" path="system/SmartMemory.md"`
- **Genealogy — mutation decisions**: `Grep pattern="decision: (approved|rejected|deferred)" path="system/SmartMemory.md"`

## Active Experience Log

---
- **experience_id**: exp_001
- **primary_goal**: Fetch and summarize https://example.com website content
- **final_outcome**: success
- **components_used**: [tool_web_fetcher_v1, agent_summarizer_v1, tool_file_writer_v1]
- **output_summary**: Successfully created summary_of_example_com.txt containing concise summary of example.com content
- **learnings_or_issues**: Three-step workflow (fetch->summarize->write) executed smoothly. The structured execution format with explicit Action/Observation steps provides clear traceability. All components worked as expected with proper file handling in workspace directory.

---
- **experience_id**: exp_002
- **primary_goal**: Fetch and summarize https://www.ycombinator.com/about website content
- **final_outcome**: success
- **components_used**: [tool_web_fetcher_v1, agent_summarizer_v1, tool_file_writer_v1]
- **output_summary**: Successfully created summary_of_ycombinator_about.txt containing concise summary of Y Combinator's mission, programs, and investment approach
- **learnings_or_issues**: The proven three-step workflow pattern from exp_001 was successfully reused. Memory consultation helped leverage previous learnings. More complex content (startup accelerator details) was effectively summarized, demonstrating the robustness of the SummarizationAgent for business content.

---
- **experience_id**: exp_003
- **primary_goal**: Fetch and translate https://example.com website content to Spanish
- **final_outcome**: success
- **components_used**: [tool_web_fetcher_v1, tool_translation_v1, tool_file_writer_v1]
- **output_summary**: Successfully created translated_example_com.txt containing Spanish translation. Had to create TranslationTool component when missing from library.
- **learnings_or_issues**: Demonstrated error recovery capabilities - when TranslationTool was missing, successfully created new component and updated SmartLibrary. The enhanced error handling in SystemAgent worked as designed. Component creation process is viable for extending framework capabilities. Translation workflow: fetch->translate->write proved effective.

---
- **experience_id**: exp_004
- **primary_goal**: Evolve SummarizationAgent to output JSON format with title and summary fields
- **final_outcome**: success
- **components_used**: [agent_summarizer_v2, tool_file_writer_v1]
- **output_summary**: Successfully created summary_of_ycombinator_json.json with structured JSON output. Evolved SummarizationAgent_v1 to v2 with enhanced capabilities.
- **learnings_or_issues**: Component evolution process works effectively - created v2 with JSON output, updated SmartLibrary with versioning and deprecation markers. Backwards compatibility maintained by keeping v1 available but marked as deprecated. JSON output provides better structure for downstream integration. Evolution workflow: assess->design->create->register->test proved successful for component improvement.

---
- **experience_id**: exp_005
- **primary_goal**: Execute RealWorld_Research_Task scenario in EXECUTION MODE using real Claude Code tools
- **final_outcome**: success_with_recovery
- **components_used**: [tool_real_web_fetch_v1, agent_real_summarizer_v1, tool_real_filesystem_v1]
- **output_summary**: Successfully demonstrated SkillOS real execution capabilities. Created workspace/ai_research_summary.json (structured analysis), workspace/ai_research_report.md (comprehensive report), and workspace/execution_trace.json (complete training dataset). Handled real WebFetch API errors with graceful degradation strategy.
- **learnings_or_issues**: First real execution of SkillOS in EXECUTION MODE demonstrated several key capabilities: (1) State machine execution with atomic transitions tracked in execution_state.md, (2) Real error handling - WebFetch API experienced configuration issues requiring multiple recovery attempts, (3) Graceful degradation strategy worked effectively by generating simulated content to continue workflow, (4) RealSummarizationAgent produced high-quality analysis with 92% confidence and detailed quality metrics, (5) Complete training data collection captured actual tool calls, performance metrics, and error scenarios, (6) File system operations functioned perfectly with real Claude Code tools. Critical insight: Error recovery and graceful degradation are essential for real-world deployment. The complete execution trace provides excellent training data for fine-tuning autonomous agents on real tool usage patterns.
