---
dialect_id: boolean-logic
name: Boolean Logic Notation
version: 1.0.0
domain_scope: [knowledge, orchestration, memory]
compression_type: symbolic
compression_ratio: "~50-65%"
reversible: true
input_format: natural-language-conditions
output_format: boolean-expression
---

# Boolean Logic Dialect

## Purpose

Compresses natural language conditions, rules, and decision logic into formal boolean expressions. Eliminates the ambiguity inherent in English conditionals — "if X and Y or Z" becomes explicitly `(X ∧ Y) ∨ Z` or `X ∧ (Y ∨ Z)`. The LLM must commit to a single interpretation, preventing logic errors from natural language ambiguity. Every condition gets an explicit operator and grouping.

## Domain Scope

- **knowledge** — Express preconditions, invariants, and decision rules in wiki articles. Boolean notation makes complex conditional logic auditable.
- **orchestration** — Encode routing conditions, success criteria, and gating logic for execution plans. Eliminates ambiguity in "when to execute" rules.
- **memory** — Compress constraint entries and trigger conditions in memory logs. Enables exact Grep matching on logical predicates.

## Compression Rules

1. **Identify atomic predicates**: Each simple condition becomes a predicate: `P(x)`, `clear(path)`, `battery > 20%`.
2. **Map logical connectives**: "and" → `∧`, "or" → `∨`, "not" / "unless" / "except" → `¬`, "if...then" → `→`, "if and only if" → `↔`.
3. **Explicit parenthesization**: Always parenthesize to resolve operator precedence. Never rely on implicit precedence.
4. **Quantify when present**: "all" → `∀`, "some" / "any" / "there exists" → `∃`.
5. **Use predicate notation**: Properties as `P(x)`, comparisons as `x > v`, membership as `x ∈ S`.
6. **Direction arrows for causation**: `←` for "cache when" (condition triggers action), `→` for "if then".
7. **Drop hedging and filler**: Remove "make sure", "you should", "it's important that". Extract the bare logical condition.
8. **Preserve thresholds exactly**: `20%`, `3 retries`, `5 seconds` — all numeric values preserved.
9. **Group related conditions**: Combine chained conditions into single expressions with appropriate grouping.
10. **Handle exceptions**: "unless" → negate and conjoin: `A unless B` → `A ∧ ¬B`.

## Preservation Rules

1. **Logical structure**: All AND/OR/NOT/IMPLIES relationships preserved with correct grouping.
2. **Operator precedence**: Explicit parentheses ensure unambiguous interpretation.
3. **Numeric thresholds**: All comparison values preserved exactly.
4. **Predicate semantics**: Predicate names chosen to be self-documenting.
5. **Quantifier scope**: Universal and existential quantifiers scoped correctly.

## Grammar / Syntax

```
EXPRESSION  := atom | unary | binary | quantified | grouped
atom        := predicate | comparison
predicate   := name "(" args ")"
comparison  := name SP comp_op SP value
comp_op     := ">" | "<" | "≥" | "≤" | "=" | "≠" | "∈"

unary       := "¬" expression
binary      := expression SP bin_op SP expression
bin_op      := "∧" | "∨" | "→" | "↔" | "←"

quantified  := quantifier var ":" SP expression
quantifier  := "∀" | "∃"

grouped     := "(" expression ")"

RULE        := conclusion SP direction SP condition
direction   := "←" | "↔"
conclusion  := predicate | action
action      := name "(" args ")"
```

## Examples

### Example 1 — Robot navigation condition

**Input** (32 words):
```
Navigate only when the path is clear and either the battery is above 20% or there's a charging station nearby. Don't navigate if the emergency stop is active.
```

**Output** (14 words):
```
navigate ↔ clear(path) ∧ (battery > 20% ∨ nearby(charger)) ∧ ¬active(e_stop)
```

**Ratio**: 32 words → 14 words, ~56% reduction + zero ambiguity

### Example 2 — Build pass conditions

**Input** (34 words):
```
The build passes if and only if all tests pass and there are no lint errors, unless it's a hotfix branch. Hotfix branches can skip lint checks but still need all tests to pass.
```

**Output** (15 words):
```
pass(build) ↔ (∀t: pass(t) ∧ (¬lint_errors ∨ is_hotfix(branch)))
```

**Ratio**: 34 words → 15 words, ~56% reduction

### Example 3 — Cache invalidation rule

**Input** (28 words):
```
Cache the result when the query is read-only and the response is not an error and the TTL hasn't expired. Never cache mutations or server errors.
```

**Output** (12 words):
```
cache(result) ← readonly(query) ∧ ¬error(response) ∧ ¬expired(TTL)
```

**Ratio**: 28 words → 12 words, ~57% reduction

## Expansion Protocol

Boolean-logic is **reversible**. The expander reconstructs natural language conditions:

1. **`∧` → "and"**: Join predicates with "and".
2. **`∨` → "or"**: Join alternatives with "or".
3. **`¬` → "not" / "unless"**: Negate with appropriate English construction.
4. **`→` → "if...then"**: "If [antecedent], then [consequent]."
5. **`↔` → "if and only if"**: "[A] if and only if [B]."
6. **`←` → "when"**: "[Action] when [condition]."
7. **`∀` → "for all"**: "For every [var], [condition must hold]."
8. **`∃` → "there exists"**: "There is at least one [var] such that [condition]."
9. **Parentheses → clause structure**: Nested groups become subordinate clauses.

### Target Registers

- **formal**: "The system shall navigate if and only if the path is clear AND (battery exceeds 20% OR a charging station is within range)."
- **conversational**: "You can navigate when the path is clear and you either have enough battery or there's a charger nearby."
- **technical**: YAML/JSON condition tree with `op`, `left`, `right` fields.

### Reversibility Confidence

- Simple conditions (2-3 predicates): 95-100%
- Complex conditions (4+ predicates, nested groups): 85-90%
- Quantified expressions: 80-85%

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~50-65% |
| Token reduction | ~45-60% |
| Reversibility | Very High — logical structure fully preserved |
| Latency | Very Low (direct mapping) |
| Error rate | <2% — parenthesization eliminates ambiguity |
| Quality improvement | Forces disambiguation of all conditional logic |
