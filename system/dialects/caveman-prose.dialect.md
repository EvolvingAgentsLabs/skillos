---
dialect_id: caveman-prose
name: Caveman Prose Compression
version: 1.0.0
domain_scope: [memory, knowledge]
compression_type: lexical
compression_ratio: "~46-75%"
reversible: true
input_format: natural-language
output_format: compressed-natural-language
---

# Caveman Prose Dialect

## Purpose

Compresses verbose English prose into terse, information-dense fragments by stripping articles, filler words, hedging language, and unnecessary verbosity. The output remains human-readable natural language — just shorter. Inspired by the caveman project's compression skills.

## Domain Scope

- **memory** — Compress execution logs, trace narratives, and learning summaries before storage. Reduces SmartMemory token footprint.
- **knowledge** — Compress wiki page content, summaries, and query outputs. Keeps knowledge base lean.

## Compression Rules

### Core Deletions
1. **Articles**: Drop "the", "a", "an" unless critical for disambiguation.
2. **Filler words**: Drop "just", "really", "very", "quite", "simply", "basically", "actually", "literally".
3. **Hedging**: Drop "I think", "it seems", "perhaps", "maybe", "might be", "could potentially".
4. **Weak verbs**: Replace "is going to" → "will", "is able to" → "can", "in order to" → "to".
5. **Redundant phrases**: "at this point in time" → "now", "due to the fact that" → "because", "in the event that" → "if".
6. **Passive voice**: Convert to active where possible. "The file was read by the agent" → "Agent read file."

### Fragment Rules
7. **Fragments OK**: Complete sentences not required. "Run tests before push." is valid.
8. **Short synonyms**: Prefer shorter words. "utilize" → "use", "implement" → "build", "approximately" → "~".
9. **Abbreviations**: Common abbreviations allowed: "config", "deps", "env", "repo", "dir", "fn".
10. **Punctuation**: Periods optional at end of fragments. Commas only when needed for clarity.

### Intensity Levels

| Level | Description | Target Reduction |
|-------|-------------|-----------------|
| lite | Drop filler and hedging only | ~30-46% |
| full | All core deletions + fragments + short synonyms | ~46-65% |
| ultra | Maximum compression — telegraphic style, aggressive abbreviation | ~65-75% |

## Preservation Rules

These elements must **never** be compressed or modified:

1. **Code blocks**: Anything inside backticks (`` ` `` or `` ``` ``) passes through verbatim.
2. **URLs**: All URLs preserved exactly.
3. **File paths**: `/path/to/file.md` preserved exactly.
4. **Commands**: Shell commands, CLI invocations preserved exactly.
5. **Technical terms**: Domain-specific jargon, API names, tool names preserved.
6. **Numbers and measurements**: Exact values preserved. "128 bytes" stays "128 bytes".
7. **Proper nouns**: Names of people, projects, organizations preserved.
8. **Quoted strings**: Anything in quotes preserved verbatim.

## Grammar / Syntax

Caveman prose has no formal grammar — it produces natural language fragments. Guidelines:

```
FRAGMENT  := SUBJECT? VERB OBJECT? MODIFIER?
SUBJECT   := noun | proper_noun | pronoun
VERB      := active_voice, present_tense preferred
OBJECT    := noun_phrase (compressed)
MODIFIER  := only if essential for meaning
CONNECTOR := "→" | "," | ";" | "then" | "if" | "when"
```

Sentence boundaries are optional. Use "→" for causal chains.

## Examples

### Example 1
**Input**: "You should always make sure to run the complete test suite before pushing any changes to the remote repository."
**Output (full)**: "Run tests before push."
**Ratio**: 109 chars → 22 chars = ~80% reduction

### Example 2
**Input**: "The memory consolidation agent is responsible for analyzing all of the short-term memory entries and extracting the most important patterns and insights for long-term storage."
**Output (full)**: "Consolidation agent analyzes short-term entries → extracts key patterns for long-term storage."
**Ratio**: 186 chars → 91 chars = ~51% reduction

### Example 3
**Input**: "I think it might be a good idea to perhaps consider implementing some kind of caching mechanism in order to improve the overall performance of the system."
**Output (full)**: "Add caching → improve performance."
**Ratio**: 155 chars → 34 chars = ~78% reduction

### Example 4 (with preservation)
**Input**: "The `knowledge-compile-agent` at `system/skills/knowledge/compile/` should basically always read the `_schema.md` file before it starts processing."
**Output (full)**: "`knowledge-compile-agent` at `system/skills/knowledge/compile/` reads `_schema.md` before processing."
**Ratio**: 150 chars → 101 chars = ~33% reduction (paths and code preserved)

## Expansion Protocol

Caveman prose is **reversible** — compressed fragments can be expanded back to full prose. The expander:

1. **Restores articles**: Add "the"/"a" where grammatically needed.
2. **Completes fragments**: Convert fragments to full sentences.
3. **Restores voice**: May use passive voice where appropriate for the target register.
4. **Expands abbreviations**: "config" → "configuration", "deps" → "dependencies".
5. **Adds connectives**: Restore transition words between sentences.

### Target Registers

- **formal**: Full sentences, no contractions, professional tone.
- **conversational**: Natural sentences, contractions OK, friendly tone.
- **technical**: Full sentences, domain jargon preferred, precise.

### Reversibility Confidence

- **lite**: 90-95% — minimal information loss
- **full**: 75-85% — some nuance lost but core meaning preserved
- **ultra**: 55-70% — significant rephrasing needed, some ambiguity

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~46-75% depending on intensity |
| Token reduction | ~40-70% |
| Reversibility | High (lite), Medium (full), Low (ultra) |
| Latency | Low (rule-based transforms) |
| Error rate | <2% information loss at lite/full levels |
