---
dialect_id: exec-plan
name: Execution Plan Compression
version: 1.0.0
domain_scope: [orchestration, memory]
compression_type: symbolic
compression_ratio: "~70-85%"
reversible: true
input_format: markdown-scenario
output_format: plan-notation
---

# Execution Plan Dialect

## Purpose

Compresses verbose multi-phase execution plans, scenario definitions, and agent orchestration workflows into compact dependency-graph notation. An agent can see the entire execution plan at a glance — phase dependencies are explicit arrows, success criteria are formal predicates, and the instructional scaffolding is stripped to pure execution logic.

## Domain Scope

- **orchestration** — Primary target. Compresses scenario files from `scenarios/`, execution plans in `projects/*/state/plan.md`, and SystemAgent delegation graphs. Enables the SystemAgent to load the complete execution structure in minimal tokens.
- **memory** — Compress execution summaries and completed plan records for SmartMemory storage.

## Compression Rules

1. **Plan header**: `@plan[ID]` with key metadata: `pattern=`, `agents=`, `type=`.
2. **Phases → `P[N]`**: Each phase is one line. `P1[agent-name]: action_description`.
3. **Dependencies → `dep=`**: `dep=P1,P2` means "depends on phases 1 and 2 completing first".
4. **Parallel phases**: Phases without dependencies can execute in parallel (implicit).
5. **Action descriptions**: Compress to verb + target. "Build math wiki with 5 concept pages and 1 entity page" → `wiki(5_concepts+1_entity)`.
6. **Success criteria → `success:`**: Line with boolean predicates joined by `∧` (AND) or `∨` (OR).
7. **Error recovery → `on_err:`**: `on_err→action` within a phase or as a separate line.
8. **Reflective loops → `reflective{}`**: `reflective{max=N, on_err→update_action}`.
9. **Context blocks → `ctx{}`**: Domain context compressed into key-value block.
10. **Drop tutorial prose**: Remove "This phase is responsible for", "The agent should", "Make sure to", all explanatory paragraphs.
11. **Verification → `verify:`**: Post-phase checks. `verify: ≥5pages` instead of "Verify that at least 5 wiki pages were created".

## Preservation Rules

1. **Agent names**: Preserved exactly.
2. **Phase ordering and dependencies**: Must reflect original execution graph.
3. **Success criteria thresholds**: All numeric values preserved.
4. **Error recovery strategies**: Specific recovery actions preserved.
5. **Output paths**: File paths and output locations preserved.
6. **Domain-specific parameters**: Mathematical expressions, configuration values preserved.
7. **Verification conditions**: All post-conditions preserved as formal predicates.

## Grammar / Syntax

```
PLAN        := HEADER "\n" CONTEXT? PHASES SUCCESS? ERROR?
HEADER      := "@plan[" id "]" FIELD*
FIELD       := key "=" value
key         := "pattern" | "agents" | "type" | "dur_est"

CONTEXT     := "ctx{" key_value_list "}"
key_value_list := entry ("\n" SP SP entry)*
entry       := key ":" value

PHASES      := phase ("\n" phase)*
phase       := "P" digit "[" agent "]" deps? ":" SP action (SP "|" SP qualifier)*
deps        := SP "dep=" phase_list
phase_list  := "P" digit ("," "P" digit)*
action      := description (SP "+" SP description)*
qualifier   := "dur=" time | "Q=" level | "verify:" predicate
              | "reflective{" params "}" | "on_err→" action

SUCCESS     := "\nsuccess:" SP predicate (SP "∧" SP predicate)*
ERROR       := "\non_fail:" SP recovery_action
```

### Pattern Types

| Pattern | Meaning |
|---------|---------|
| sequential | Phases execute in order (P1→P2→P3) |
| parallel | Independent phases run concurrently |
| hierarchical | Phases have explicit dependencies |
| reflective | Includes feedback loops (on error, retry with updates) |
| hierarchical+reflective | Dependencies + feedback loops |

## Examples

### Example 1 — Quantum computing scenario (455 lines → 12 lines)
**Input** (Operation_Echo_Q.md, 455 lines):
```markdown
# Operation Echo Q: Quantum Cepstral Analysis
## Mathematical Context
The classical cepstrum is defined as: c(τ_q) = IFFT{ log|FFT(s)| }
Given a composite signal s(t) = p(t) + α·p(t−τ)...
## Stage 1: The Quantum Theorist
Create a comprehensive mathematical wiki...
(80 lines of detailed instructions)
## Stage 2: The Pure Mathematician
Extract hard and soft constraints...
(60 lines of detailed instructions)
...
```

**Output**:
```
@plan[echo_q] pattern=hierarchical+reflective agents=4 type=quantum_proof

ctx{
  signal: s(t)=p(t)+α·p(t-τ) → cepstrum: c(τq)=IFFT{log|FFT(s)|}
  problem: log non-unitary → need quantum encoding
}

P1[quantum-theorist]: wiki(≥5_concepts+1_entity, LaTeX+WikiLinks) | verify: ≥5pages ∧ all_crossref
P2[pure-math] dep=P1: constraints(≥5_hard+soft, wiki_refs) | verify: refs_valid ∧ C6_domain
P3[qiskit-eng] dep=P1,P2: qcepstrum.py(QFT→log_approx→IQFT) | reflective{max=3, on_err→update_wiki+constraints} | verify: |τ̂-0.3|<0.05
P4[sys-architect] dep=P1,P2,P3: whitepaper(wiki_synthesis+citations) | verify: all_claims_cited

success: wiki_complete ∧ constraints≥5 ∧ code_runs ∧ echo_detect ∧ whitepaper_cited
```

**Ratio**: 455 lines → 12 lines, ~3,600 tokens → ~250 tokens = **~93% reduction**

### Example 2 — Simple research pipeline
**Input** (118 lines):
```markdown
# RealWorld Research Task
## Phase 1: Web Fetching
Use WebFetch to retrieve content from the specified URL...
Handle errors with retry logic and graceful degradation...
## Phase 2: Summarization
The summarization agent should analyze the fetched content...
## Phase 3: Report Generation
Save structured outputs to the project directory...
```

**Output**:
```
@plan[research_task] pattern=sequential agents=3 type=research

P1[web_fetch]: fetch(target_url) | on_err→retry×3+degrade
P2[summarizer] dep=P1: analyze(fetched_content) → structured_summary
P3[filesystem] dep=P2: save([summary.json, report.md, trace.json])

success: content_fetched ∧ summary_complete ∧ files_saved
```

**Ratio**: 118 lines → 7 lines = **~94% reduction**

### Example 3 — Dream consolidation scenario
**Input** (262 lines):
```markdown
# RoClaw Dream Consolidation
## Phase 1: Trace Collection
Read all trace files from RoClaw/traces/ directories...
## Phase 2: Pattern Analysis
Analyze traces for common patterns, failures, stuck loops...
## Phase 3: Strategy Generation
Generate or update strategies based on discovered patterns...
```

**Output**:
```
@plan[dream_consolidation] pattern=sequential agents=2 type=dream

P1[dream-agent]: collect_traces(RoClaw/traces/**/*.md) | filter: fid≥0.5
P2[dream-agent] dep=P1: analyze_patterns(stuck_loops, failures, successes)
P3[consolidation-agent] dep=P2: update_strategies + gen_negative_constraints

success: traces_processed ∧ strategies_updated ∧ constraints_logged
```

**Ratio**: 262 lines → 7 lines = **~97% reduction**

## Expansion Protocol

Exec-plan is **reversible**. The expander reconstructs full scenario descriptions:

1. **`@plan[ID]` → scenario header**: Restore title, pattern description, agent list.
2. **`ctx{...}` → context section**: Expand domain context into explanatory paragraphs.
3. **`P[N][agent]` → phase section**: Restore full "## Phase N: Agent Name" header with detailed instructions.
4. **`dep=` → dependency prose**: "This phase depends on the completion of Phase 1 and Phase 2."
5. **`verify:` → verification section**: "After completion, verify that..."
6. **`reflective{}` → loop description**: "If errors occur, update [targets] and retry up to N times."
7. **`success:` → success criteria**: Restore as bullet list with full descriptions.
8. **`on_err→` → error handling section**: Restore recovery strategy descriptions.

### Target Registers

- **formal**: Full scenario document with detailed phase instructions and academic context.
- **conversational**: Step-by-step guide with plain language. "First, the wiki agent builds 5 pages..."
- **technical**: YAML execution config with structured phase definitions.

### Reversibility Confidence

- Simple sequential plans: 85-95%
- Hierarchical plans with dependencies: 75-85%
- Plans with context and mathematical notation: 60-75% (tutorial prose is largely lost)

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~70-85% (simple), ~90-97% (verbose scenarios with tutorial prose) |
| Token reduction | ~75-95% |
| Reversibility | Medium-High — execution logic preserved, tutorial prose lost |
| Latency | Low (structural extraction) |
| Error rate | <3% — dependency graph always preserved |
| Quality improvement | Full execution graph visible at a glance, dependencies explicit |
