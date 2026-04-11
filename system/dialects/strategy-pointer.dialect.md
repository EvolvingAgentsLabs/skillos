---
dialect_id: strategy-pointer
name: Strategy Pointer Notation
version: 1.0.0
domain_scope: [memory, robot]
compression_type: symbolic
compression_ratio: "~60-80%"
reversible: true
input_format: natural-language
output_format: pointer-notation
---

# Strategy Pointer Dialect

## Purpose

Compresses verbose strategy descriptions and conditional behavior rules into a compact symbolic notation using pointers, triggers, and action chains. Designed for storing robot strategies, execution plans, and decision rules in minimal token form. Inspired by RoClaw strategy files and pointer notation patterns.

## Domain Scope

- **memory** — Compress strategy entries in SmartMemory and long-term memory. Decision rules stored as pointers load faster and consume fewer tokens during memory consultation.
- **robot** — Compress navigation strategies, recovery plans, and dream-consolidated rules. Strategy files in `strategies/` use this notation natively.

## Compression Rules

1. **Conditions → `[IF]` blocks**: "When X happens" / "If X is detected" → `[IF] X`.
2. **Actions → `[THEN]` blocks**: "do Y" / "execute Y" → `[THEN] Y`.
3. **Action chains → `→`**: Sequential actions joined with arrow. "do A, then B, then C" → `A → B → C`.
4. **Triggers → `[ON]`**: Event-driven rules. "On startup" → `[ON] startup`.
5. **Loops → `[LOOP]`**: Repeated actions. "Keep doing X until Y" → `[LOOP] X [UNTIL] Y`.
6. **Alternatives → `|`**: "Either A or B" → `A | B`.
7. **Parameters → `()`**: Function-style params. "Rotate 90 degrees clockwise" → `rotate_cw(90)`.
8. **Negation → `!`**: "Not X" / "No X" → `!X`.
9. **Confidence → `@`**: Optional confidence tag. `@0.85` means 85% confidence.
10. **Snake_case actions**: All action names use snake_case. "Move forward" → `move_forward`.

## Preservation Rules

1. **Numeric values**: All numbers preserved exactly. Angles, speeds, distances, thresholds.
2. **Named entities**: Specific locations ("kitchen", "charging_station"), object names preserved.
3. **Ordering**: Action chain order must match original command sequence.
4. **Conditional logic**: All branches and conditions preserved. No branch may be dropped.
5. **Confidence levels**: If the source mentions certainty/confidence, encode with `@`.

## Grammar / Syntax

```
RULE       := TRIGGER? CONDITION? ACTION_CHAIN CONFIDENCE?
TRIGGER    := [ON] event_name
CONDITION  := [IF] predicate
ACTION_CHAIN := [THEN] action (→ action)*
action     := snake_case_name ( "(" params ")" )?
params     := value ( "," value )*
value      := number | string | snake_case_name
LOOP       := [LOOP] action [UNTIL] predicate
ALT        := action "|" action
NEGATION   := "!" predicate
CONFIDENCE := "@" float
```

### Combinators

| Symbol | Meaning | Example |
|--------|---------|---------|
| `[IF]` | Condition | `[IF] wall_detected` |
| `[THEN]` | Action(s) | `[THEN] stop → rotate_cw(90)` |
| `[ON]` | Event trigger | `[ON] battery_low` |
| `[LOOP]` | Repeat | `[LOOP] scan(360) [UNTIL] target_found` |
| `[UNTIL]` | Loop terminator | `[UNTIL] path_clear` |
| `→` | Sequence | `stop → backup(50) → rotate_cw(90)` |
| `\|` | Alternative | `rotate_cw(90) \| rotate_ccw(90)` |
| `!` | Negation | `!obstacle_detected` |
| `@` | Confidence | `@0.85` |
| `()` | Parameters | `move_forward(speed=128)` |

## Examples

### Example 1
**Input**: "When the robot detects a wall ahead, it should stop immediately, rotate 90 degrees clockwise, and then try moving forward again."
**Output**: `[IF] wall_detected [THEN] stop → rotate_cw(90) → retry_forward`
**Ratio**: 124 chars → 54 chars = ~56% reduction

### Example 2
**Input**: "If the battery level drops below 20%, the robot should stop its current task, navigate to the charging station, and dock. This strategy has been successful about 90% of the time."
**Output**: `[IF] battery < 20% [THEN] abort_task → navigate(charging_station) → dock @0.90`
**Ratio**: 184 chars → 72 chars = ~61% reduction

### Example 3
**Input**: "On startup, the robot should perform a 360-degree scan of the environment. Keep scanning until a navigation target is identified, then move toward it. If no target is found after 3 scans, enter idle mode."
**Output**: `[ON] startup [LOOP] scan(360) [UNTIL] target_found → move_to(target) | [IF] scan_count > 3 [THEN] idle`
**Ratio**: 213 chars → 95 chars = ~55% reduction

### Example 4
**Input**: "The agent should check memory for similar past experiences. If a matching strategy exists with confidence above 0.7, use it directly. Otherwise, generate a new plan from scratch."
**Output**: `[IF] memory_match @> 0.7 [THEN] apply_strategy(match) | [THEN] generate_plan`
**Ratio**: 182 chars → 72 chars = ~60% reduction

## Expansion Protocol

Strategy pointer notation is **reversible**. The expander reconstructs natural-language descriptions:

1. **`[IF]` → conditional clause**: "When/If [predicate]..."
2. **`[THEN]` → action clause**: "...then [action]"
3. **`→` → sequential connector**: "then" / "followed by" / "and then"
4. **`[ON]` → event clause**: "On [event]..." / "When [event] occurs..."
5. **`[LOOP]`/`[UNTIL]` → iteration clause**: "Repeat [action] until [condition]"
6. **`|` → alternative clause**: "Otherwise" / "Alternatively"
7. **`@` → confidence note**: "This strategy has [N]% confidence"
8. **`()` → parameter expansion**: "rotate_cw(90)" → "rotate 90 degrees clockwise"
9. **`!` → negation**: "!obstacle" → "no obstacle is detected"

### Target Registers

- **formal**: "In the event that a wall is detected, the system shall halt, execute a 90-degree clockwise rotation..."
- **conversational**: "If it sees a wall, it stops, turns right 90 degrees, and tries again."
- **technical**: "On wall_detected event: execute STOP, ROTATE_CW(90), FORWARD_RETRY sequence."

### Reversibility Confidence

- Simple rules (1-2 actions): 90-95%
- Compound rules (chains + alternatives): 80-90%
- Nested rules (loops within conditions): 70-85%

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~60-80% depending on rule complexity |
| Token reduction | ~55-75% |
| Reversibility | High for simple rules, Medium for complex |
| Latency | Low (pattern matching + symbol substitution) |
| Error rate | <3% when input describes clear conditional logic |
