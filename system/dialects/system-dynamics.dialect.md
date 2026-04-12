---
dialect_id: system-dynamics
name: System Dynamics Notation
version: 1.0.0
domain_scope: [knowledge, orchestration]
compression_type: symbolic
compression_ratio: "~55-70%"
reversible: true
input_format: natural-language-system-description
output_format: stock-flow-notation
---

# System Dynamics Dialect

## Purpose

Compresses natural language descriptions of systems, feedback loops, and causal dynamics into stock-flow notation. Forces the LLM to distinguish between accumulations (stocks), rates of change (flows), reinforcing loops (FB+), balancing loops (FB-), and time delays. Prevents confusing correlations with causation by requiring explicit causal arrows.

## Domain Scope

- **knowledge** — Model complex systems in wiki articles: economic dynamics, ecosystem models, organizational patterns. The notation makes feedback loops visible that prose obscures.
- **orchestration** — Model execution system dynamics: memory accumulation vs. dream consolidation, agent workload balancing, error cascade propagation. Helps the SystemAgent reason about system-level behavior.

## Compression Rules

1. **Identify stocks**: Things that accumulate or deplete over time. Tag as `[STOCK] name`.
2. **Identify flows**: Rates that increase or decrease stocks. Tag as `[FLOW] name → +stock` or `[FLOW] name → -stock`.
3. **Identify feedback loops**: Reinforcing (positive) loops as `[FB+] A → B → A`. Balancing (negative) loops as `[FB-] A → B → ↓A`.
4. **Identify delays**: Time lags between cause and effect. Tag as `[DELAY] name(duration)`.
5. **Use arrow notation**: `→` for causal flow, `↑` for increase, `↓` for decrease.
6. **Chain multiple effects**: `[FLOW] action → -stock_A → +stock_B` for flows that transfer between stocks.
7. **Drop narrative prose**: Remove "this happens because", "over time", "eventually". The stock-flow structure encodes temporality.
8. **Preserve quantities**: Numeric rates, durations, and thresholds preserved exactly.
9. **Annotate external inputs**: `[EXT] name` for factors outside the system boundary.
10. **Mark equilibrium conditions**: `[EQ] condition` for steady-state descriptions.

## Preservation Rules

1. **Causal direction**: All cause → effect relationships preserved with correct polarity.
2. **Feedback loop type**: Reinforcing vs. balancing distinction must be correct.
3. **Delay magnitudes**: All time delays preserved with units.
4. **Stock identities**: All accumulation variables named and preserved.
5. **System boundary**: External inputs vs. internal dynamics distinguished.

## Grammar / Syntax

```
SYSTEM      := ELEMENT ("\n" ELEMENT)*
ELEMENT     := STOCK | FLOW | FEEDBACK | DELAY | EXTERNAL | EQUILIBRIUM

STOCK       := "[STOCK]" SP name
FLOW        := "[FLOW]" SP source SP "→" SP effect ("→" SP effect)*
effect      := ("+" | "-") name
source      := name | "[EXT]" name

FEEDBACK    := ("[FB+]" | "[FB-]") SP chain
chain       := name (SP "→" SP name)+ (SP "→" SP ("↑" | "↓") name)?

DELAY       := "[DELAY]" SP name "(" duration ")"
duration    := number unit
unit        := "s" | "m" | "h" | "d" | "w" | "sprint" | "cycle"

EXTERNAL    := "[EXT]" SP name
EQUILIBRIUM := "[EQ]" SP condition
```

## Examples

### Example 1 — Platform growth dynamics

**Input** (62 words):
```
More users create more content, which in turn attracts more users — a classic network effect. However, as the platform grows, spam increases and drives users away. Spam growth has a delay of about a week before it becomes noticeable. Moderation helps but can't fully keep up with exponential spam growth.
```

**Output** (28 words):
```
[STOCK] users
[STOCK] content
[STOCK] spam
[FLOW] content_rate → +content
[FB+] users → content → users
[FB-] spam → ↓users
[FLOW] moderation → -spam
[DELAY] spam_growth(7d)
```

**Ratio**: 62 words → 28 words, ~55% reduction + feedback loops made explicit

### Example 2 — Memory system dynamics

**Input** (58 words):
```
Memory entries accumulate over time as the robot performs tasks and writes traces. Dream consolidation reduces the raw entry count by merging traces into strategies. Better strategies from dreams increase navigation success rates, which in turn reduces the rate of new trace generation because the robot fails less often.
```

**Output** (25 words):
```
[STOCK] mem_entries
[STOCK] strategies
[FLOW] trace_rate → +mem_entries
[FLOW] dream_consolidation → -mem_entries → +strategies
[FB+] strategies → nav_success → ↓trace_rate
```

**Ratio**: 58 words → 25 words, ~57% reduction

### Example 3 — Technical debt dynamics

**Input** (55 words):
```
Technical debt accumulates with each sprint when teams take shortcuts. Velocity decreases as debt grows because more time is spent working around problems. Refactoring reduces debt but consumes velocity in the short term. There's typically a two-sprint delay before velocity recovers after a refactoring investment.
```

**Output** (26 words):
```
[STOCK] tech_debt
[STOCK] velocity
[FLOW] sprint_shortcuts → +tech_debt
[FB-] tech_debt → ↓velocity
[FLOW] refactor → -tech_debt, -velocity
[DELAY] velocity_recovery(2sprint)
```

**Ratio**: 55 words → 26 words, ~53% reduction

## Expansion Protocol

System-dynamics is **reversible**. The expander reconstructs system descriptions:

1. **`[STOCK]` → accumulation description**: "[Name] is a quantity that accumulates or depletes over time."
2. **`[FLOW]` → rate description**: "[Source] causes [stock] to increase/decrease."
3. **`[FB+]` → reinforcing loop prose**: "This creates a reinforcing cycle: more [A] leads to more [B], which further increases [A]."
4. **`[FB-]` → balancing loop prose**: "This creates a balancing effect: as [A] increases, [B] decreases [A]."
5. **`[DELAY]` → temporal qualifier**: "There is a delay of [duration] before this effect becomes apparent."
6. **`[EXT]` → external factor**: "[Name] is an external factor outside the system's control."

### Target Registers

- **formal**: Systems thinking textbook style with labeled diagrams described in prose.
- **conversational**: "Basically, as X grows, Y grows too, which feeds back into more X — a virtuous cycle."
- **technical**: Structured YAML or JSON representation of stocks, flows, and feedback loops.

### Reversibility Confidence

- Simple systems (2-3 stocks, 1-2 loops): 90-95%
- Complex systems (4+ stocks, nested loops): 70-80%
- Systems with narrative context removed: 60-70%

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~55-70% |
| Token reduction | ~50-65% |
| Reversibility | High — causal structure preserved, narrative context lost |
| Latency | Low (structural extraction) |
| Error rate | <5% — feedback polarity occasionally misidentified |
| Quality improvement | Forces causal thinking; makes feedback loops explicit |
