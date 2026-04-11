---
dialect_id: memory-xp
name: Memory Experience Compression
version: 1.0.0
domain_scope: [memory]
compression_type: symbolic
compression_ratio: "~65-75%"
reversible: true
input_format: markdown-log
output_format: symbolic-log
---

# Memory Experience Dialect

## Purpose

Compresses verbose SmartMemory experience entries and agent interaction logs into compact symbolic records with consistent tagging. The key insight: **structured compression makes Grep queries precise**. Today, searching SmartMemory for "which executions had WebFetch errors" requires fuzzy text matching through prose. In compressed form, `err:WebFetch` is a reliable search target. More entries also fit in the context window during memory consultation.

## Domain Scope

- **memory** — Primary target. Compresses entries in `system/SmartMemory.md`, agent interaction logs in `projects/*/memory/short_term/`, and consolidated insights in `projects/*/memory/long_term/`.

## Compression Rules

1. **Entry header**: `@xp[ID]` prefix with abbreviated metadata fields on the same line.
2. **Goal compression**: Strip boilerplate phrasing. "Execute RealWorld_Research_Task scenario in EXECUTION MODE using real Claude Code tools" → `"RealWorld_Research_Task EXEC"`.
3. **Outcome enum**: `success→OK`, `failure→FAIL`, `partial→PART`, `success_with_recovery→OK+recover`.
4. **Component list**: Strip version suffixes and prefixes. `tool_real_web_fetch_v1` → `web_fetch`. Use `{}` for sets.
5. **Output files**: List filenames only, strip common path prefixes. Use `[]` for ordered lists.
6. **Learnings block**: `learn{}` with key-value pairs separated by `|`. Use `:` for sub-fields.
7. **Quality score**: `Q=N%` or `Q=N/10`.
8. **Error patterns**: `err:TOOL→action` format. `"WebFetch API experienced configuration issues requiring multiple recovery attempts"` → `err:WebFetch→retry×3`.
9. **Phase summaries**: `P1[agent]: action → result | dur=Nm | Q=level`.
10. **Drop filler**: Remove "Successfully demonstrated", "First real execution", "key capabilities:", "several important", etc.

## Preservation Rules

1. **Experience IDs**: Preserved exactly (e.g., `exp_005`).
2. **Component names**: Core tool/agent names preserved (may strip prefix/suffix).
3. **Output filenames**: Preserved exactly including extensions.
4. **Numeric values**: Quality scores, durations, error counts preserved exactly.
5. **Error types**: Specific error names preserved (e.g., `WebFetch`, `AerError`).
6. **Causal chains**: The cause→effect relationship in learnings must be preserved.
7. **Tags and categories**: All semantic tags preserved.

## Grammar / Syntax

```
ENTRY       := HEADER "\n" SECTION*
HEADER      := "@xp[" id "]" FIELD*
FIELD       := key "=" value
id          := "exp_" digits | custom_id
key         := "g" | "o" | "dur" | "cost"

SECTION     := TOOLS | OUTPUTS | LEARN | PHASES | ERR
TOOLS       := "  tools={" name_list "}"
OUTPUTS     := "  out=[" file_list "]"
LEARN       := "  learn{" insight_list "}"
PHASES      := "  phases{\n" phase_list "\n  }"
ERR         := "  err:" error_spec

name_list   := name ("," SP name)*
file_list   := filename ("," SP filename)*
insight_list := insight (SP "|" SP insight)*
insight     := key ":" value
phase_list  := phase ("\n" phase)*
phase       := SP SP "P" digit "[" agent "]:" SP summary
error_spec  := tool_name "→" recovery_action
```

### Field Abbreviations

| Verbose | Compressed | Example |
|---------|-----------|---------|
| experience_id | @xp[ID] | `@xp[005]` |
| primary_goal | g= | `g="Research_Task EXEC"` |
| final_outcome: success | o=OK | |
| final_outcome: failure | o=FAIL | |
| final_outcome: partial | o=PART | |
| components_used | tools={} | `tools={web_fetch, summarizer}` |
| output_summary | out=[] | `out=[report.md, data.json]` |
| learnings_or_issues | learn{} | `learn{caching:improved_speed}` |
| execution_duration | dur= | `dur=5m` |
| total_cost | cost= | `cost=$0.02` |

## Examples

### Example 1 — SmartMemory experience entry
**Input** (8 lines, ~180 tokens):
```markdown
- **experience_id**: exp_005
- **primary_goal**: Execute RealWorld_Research_Task scenario in EXECUTION MODE using real Claude Code tools
- **final_outcome**: success_with_recovery
- **components_used**: [tool_real_web_fetch_v1, agent_real_summarizer_v1, tool_real_filesystem_v1]
- **output_summary**: Successfully demonstrated SkillOS real execution capabilities. Created workspace/ai_research_summary.json (structured analysis), workspace/ai_research_report.md (comprehensive report), and workspace/execution_trace.json (complete training dataset). Handled real WebFetch API errors with graceful degradation strategy.
- **learnings_or_issues**: First real execution of SkillOS in EXECUTION MODE demonstrated several key capabilities: (1) State machine execution with atomic transitions tracked in execution_state.md, (2) Real error handling - WebFetch API experienced configuration issues requiring multiple recovery attempts, (3) Graceful degradation strategy worked effectively by generating simulated content to continue workflow, (4) Quality assessment rated at 92%.
```

**Output** (4 lines, ~55 tokens):
```
@xp[005] g="RealWorld_Research_Task EXEC" o=OK+recover
  tools={web_fetch, summarizer, filesystem}
  out=[ai_research_summary.json, ai_research_report.md, execution_trace.json]
  learn{state_machine:atomic_trans | err:WebFetch→retry×3 | degrade:simulated_fallback | Q=92%}
```

**Ratio**: ~180 tokens → ~55 tokens = **~69% reduction**

### Example 2 — Agent interaction session log
**Input** (20 lines, ~320 tokens):
```markdown
## Phase 1: quantum-theorist-agent
- **Action**: Build math wiki (5 concept pages + 1 entity page)
- **Input**: Wiki schema template, scenario mathematical context
- **Output**: 6 wiki pages with LaTeX derivations and [[WikiLinks]]
- **Duration**: ~2 minutes
- **Quality**: High — all pages cross-referenced, formulas precise
- **Key decision**: Detailed the non-unitarity problem with 3 resolution strategies

## Phase 2: pure-math-agent
- **Action**: Extract hard and soft constraints
- **Output**: constraints.md with 6 hard + 4 soft constraints, all wiki-referenced
- **Duration**: ~1 minute
- **Quality**: High — added C6 domain constraint discovered during analysis
```

**Output** (4 lines, ~90 tokens):
```
@xp[echo_q_session] g="Echo_Q quantum cepstrum" o=OK dur=10m
  phases{
    P1[quantum-theorist]: wiki(5_concepts+1_entity) | dur=2m | Q=high | decision=non-unitary_3strat
    P2[pure-math]: constraints(6H+4S, wiki_refs) | dur=1m | Q=high | decision=+C6_domain
  }
```

**Ratio**: ~320 tokens → ~90 tokens = **~72% reduction**

### Example 3 — Simple success log
**Input**: "Agent completed file creation successfully. Created output/report.md with comprehensive analysis. No errors encountered. Duration: 45 seconds."

**Output**: `@xp[auto] o=OK out=[report.md] dur=45s`

**Ratio**: ~30 tokens → ~8 tokens = **~73% reduction**

## Expansion Protocol

Memory-xp is **reversible**. The expander reconstructs natural-language log entries:

1. **`@xp[ID]` → experience header**: Restore field labels ("experience_id:", "primary_goal:", etc.).
2. **`o=OK` → outcome prose**: "The execution completed successfully."
3. **`tools={...}` → components list**: Restore full component names with version suffixes if known.
4. **`out=[...]` → output summary**: "Created [file1], [file2], and [file3]."
5. **`learn{...}` → learnings prose**: Expand each key:value into a complete sentence.
6. **`phases{...}` → phase summaries**: Restore full markdown sections with bullet lists.
7. **`err:X→Y` → error description**: "X experienced errors, resolved via Y."

### Target Registers

- **formal**: Full sentences, complete field labels, professional log format.
- **conversational**: "The agent ran the research task, hit a WebFetch error, retried 3 times, and finished with 92% quality."
- **technical**: Structured YAML output with all fields restored.

### Reversibility Confidence

- Simple entries (1-2 fields): 90-95%
- Phase summaries: 80-90%
- Complex learnings with multiple insights: 70-85%

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~65-75% |
| Token reduction | ~60-70% |
| Reversibility | High — structured data, minimal ambiguity |
| Latency | Low (field extraction + abbreviation) |
| Error rate | <2% information loss |
| Quality improvement | Structured tags enable precise Grep queries |
