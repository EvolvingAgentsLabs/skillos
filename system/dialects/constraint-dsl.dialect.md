---
dialect_id: constraint-dsl
name: Constraint DSL
version: 1.0.0
domain_scope: [memory, robot, knowledge]
compression_type: symbolic
compression_ratio: "~55-70%"
reversible: true
input_format: natural-language
output_format: constraint-notation
---

# Constraint DSL Dialect

## Purpose

Compresses verbose constraint descriptions, preconditions, and negative rules into formal symbolic notation. Constraints written in prose can be misinterpreted by agents; formal notation is unambiguous and enables automated verification. Used for execution constraints, dream-generated negative constraints, strategy preconditions, and validation rules.

## Domain Scope

- **memory** — Compress negative constraints from dream consolidation (`_negative_constraints.md`) and execution constraints in `projects/*/state/constraints.md`.
- **robot** — Compress strategy preconditions, obstacle avoidance rules, and navigation constraints.
- **knowledge** — Compress wiki schema rules, cross-reference constraints, and compilation invariants.

## Compression Rules

1. **Constraint header**: `C[N]` for hard constraints, `S[N]` for soft constraints, `NC[N]` for negative constraints. Severity tag: `[H]`=HIGH, `[M]`=MEDIUM, `[L]`=LOW.
2. **MUST/MUST NOT → operators**: "MUST be" → predicate assertion. "MUST NOT" → `!` prefix.
3. **Implications → `⇒`**: "This means that..." / "Implication:" → `⇒ consequence`.
4. **Resolution strategies → `→ {}`**: "Can be resolved via A or B" → `→ {A | B}`.
5. **Wiki references → `@w[]`**: `[[page-name]] (Section: X)` → `@w[page-name#X]`.
6. **Trace references → `@tr[]`**: "Learned from trace_xyz" → `@tr[xyz]`.
7. **Dream references → `@d[]`**: "Dream ID: dream_20260312_f4c7" → `@d[20260312_f4c7]`.
8. **Mathematical expressions**: Preserve LaTeX inline but strip `$` delimiters for simple expressions. Keep `$...$` for complex formulas.
9. **Context tags → `ctx=`**: "Context: Navigation" → `ctx=nav`.
10. **Drop boilerplate**: Remove "The constraint states that", "It is required that", "This constraint ensures".

## Preservation Rules

1. **Mathematical expressions**: All formulas, equations, and numeric thresholds preserved exactly.
2. **Variable names**: All technical variable names preserved (e.g., `U†U=I`, `ε`, `τ̂`).
3. **Constraint identifiers**: IDs preserved or systematically abbreviated.
4. **Severity levels**: Always preserved.
5. **Causal relationships**: The if→then structure of implications must be preserved.
6. **Wiki/trace/dream references**: All source references preserved with section pointers.
7. **Threshold values**: Exact numbers preserved (e.g., `< 20%`, `> 0.7`, `≤ 2n`).

## Grammar / Syntax

```
CONSTRAINT  := TYPE "[" id "]" SEVERITY? SP predicate (SP "⇒" SP implication)? REFS?
TYPE        := "C" | "S" | "NC"
SEVERITY    := "[H]" | "[M]" | "[L]"
id          := integer | alphanumeric
predicate   := expression | "!" expression
expression  := term (SP operator SP term)*
operator    := "=" | "<" | ">" | "≤" | "≥" | "∈" | "∧" | "∨"
implication := consequence (SP "→" SP resolution)?
resolution  := "{" option (SP "|" SP option)* "}"
option      := snake_case_name ( "(" params ")" )?
REFS        := SP "@w[" ref_list "]" | SP "@tr[" ref "]" | SP "@d[" ref "]"
ref_list    := ref ("," SP ref)*
ref         := slug ("#" section)?
```

### Severity Abbreviations

| Verbose | Compressed |
|---------|-----------|
| HIGH | [H] |
| MEDIUM | [M] |
| LOW | [L] |
| CRITICAL | [H!] |

### Context Abbreviations

| Verbose | Compressed |
|---------|-----------|
| Navigation | ctx=nav |
| Memory | ctx=mem |
| Knowledge | ctx=kb |
| Execution | ctx=exec |
| General | ctx=gen |

## Examples

### Example 1 — Hard constraint with mathematical expression
**Input**:
```markdown
### C1: Unitarity
All quantum operations MUST be unitary: $U^\dagger U = I$.
**Implication**: The $\log(\cdot)$ function cannot be applied directly as a gate. It must be implemented via block-encoding + QSVT polynomial approximation or LCU Taylor series.
**Wiki ref**: [[homomorphic-signal-separation]] (Section: The Non-Unitarity Problem), [[block-encoding]] (Section: Definition), [[quantum-singular-value-transformation]] (Section: Extension)
```

**Output**:
```
C[1][H] unitary(U†U=I) ⇒ log_blocked → {QSVT_poly | LCU_taylor} @w[homomorphic#non-unitary, block-enc#def, qsvt#ext]
```

**Ratio**: ~120 tokens → ~25 tokens = **~79% reduction**

### Example 2 — Negative constraint from dream consolidation
**Input**:
```markdown
## Constraint 12
- **Description**: Do not persist with the same opcode repeated more than 3 times without spatial progress. Require spatial progress check after repeated opcodes.
- **Context**: Navigation
- **Severity**: HIGH
- **Learned From**: trace_ab_analysis_20260312
- **Dream ID**: dream_20260312_f4c7
```

**Output**:
```
NC[12][H] !repeat_opcode(>3, !spatial_progress) ctx=nav @tr[ab_analysis_20260312] @d[20260312_f4c7]
```

**Ratio**: ~70 tokens → ~15 tokens = **~79% reduction**

### Example 3 — Soft constraint with threshold
**Input**:
```markdown
### S1: Approximation Error
The polynomial approximation error SHOULD be less than 1e-3 for the logarithm function across the valid domain.
**Wiki ref**: [[quantum-singular-value-transformation]] (Section: Polynomial Logarithm Approximation)
```

**Output**:
```
S[1][M] poly_approx_err < 1e-3 @w[qsvt#poly_log]
```

**Ratio**: ~45 tokens → ~10 tokens = **~78% reduction**

### Example 4 — Robot navigation constraint
**Input**: "When battery level is below 15%, the robot must immediately stop all tasks and return to the charging station. This has medium severity."

**Output**:
```
C[auto][M] battery < 15% ⇒ abort_all → {navigate(charging_station)}
```

**Ratio**: ~30 tokens → ~10 tokens = **~67% reduction**

## Expansion Protocol

Constraint DSL is **reversible**. The expander reconstructs natural-language constraint descriptions:

1. **`C[N]` → "Constraint N" header**: Restore full section header with name if available.
2. **`[H]`/`[M]`/`[L]` → severity prose**: "This is a HIGH severity constraint."
3. **Predicate → description**: `unitary(U†U=I)` → "All operations must be unitary: U†U = I."
4. **`!` → negation prose**: "Must NOT" / "Do not".
5. **`⇒` → implication**: "This means that..." / "As a consequence...".
6. **`→ {}` → resolution**: "Can be resolved via A or B."
7. **`@w[...]` → wiki references**: Restore `[[page-name]] (Section: X)` format.
8. **`@tr[...]` → trace citation**: "Learned from trace [ref]."
9. **`@d[...]` → dream citation**: "Discovered during dream session [ref]."

### Target Registers

- **formal**: "Constraint C1 (Unitarity): All quantum operations shall satisfy the unitarity condition U†U = I..."
- **conversational**: "The operations need to be unitary — that means you can't just apply log directly."
- **technical**: "C1: UNITARY — U†U=I. Implication: log(·) requires QSVT or LCU encoding."

### Reversibility Confidence

- Single predicate constraints: 90-95%
- Constraints with implications and resolutions: 80-90%
- Complex nested constraints: 70-85%

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~55-70% (simple), ~75-80% (verbose with references) |
| Token reduction | ~60-75% |
| Reversibility | High — formal structure preserves meaning |
| Latency | Low (pattern matching + symbol substitution) |
| Error rate | <2% for well-structured constraint prose |
| Quality improvement | Unambiguous formal notation enables automated verification |
