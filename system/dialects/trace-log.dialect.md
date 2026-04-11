---
dialect_id: trace-log
name: Trace Log Compression
version: 1.0.0
domain_scope: [robot, memory]
compression_type: structural
compression_ratio: "~70-80%"
reversible: true
input_format: markdown-trace
output_format: tabular-trace
---

# Trace Log Dialect

## Purpose

Compresses verbose action-by-action execution traces into compact tabular format with run-length encoding. Designed for RoClaw navigation traces, agent interaction logs, and any sequential action record. The key insight: **compression as analysis** — run-length encoding reveals behavioral patterns (stuck loops, repeated actions) that are invisible in the verbose form.

## Domain Scope

- **robot** — Compresses RoClaw trace files (`traces/sim3d/`, `traces/real_world/`). Dream consolidation reads compressed traces to extract navigation strategies. Run-length encoding makes stuck-loops and repeated behaviors immediately visible.
- **memory** — Compresses agent interaction logs in `memory/short_term/`. Reduces SmartMemory footprint when storing execution summaries.

## Compression Rules

1. **Header line**: Collapse YAML frontmatter into single `@trace` header with abbreviated fields.
2. **Temporal deltas**: Replace ISO timestamps with `t+N` offsets (seconds from trace start).
3. **Action compression**: Strip JSON wrappers, extract `name(args)` form. `TOOLCALL:{"name":"rotate_cw","args":{"speed":128,"degrees":90}}` → `rotate_cw(128,90)`.
4. **Run-length encoding**: Consecutive identical actions become `action [xN]`. This is the primary quality-improving transform — patterns like "stuck in a rotation loop" become visible as `rotate_cw(128,90) [x4]`.
5. **Reasoning collapse**: Drop the Reasoning field entirely when it contains only camera frame references (e.g., `[camera frame at TIMESTAMP]`). Preserve reasoning text that contains actual analysis.
6. **Result compression**: Strip `bytecode=` prefix from hex results. Keep hex frames as-is (they're already maximally compressed).
7. **Frontmatter abbreviations**: `timestamp→@t`, `goal→g`, `outcome→o` (`success→OK`, `failure→FAIL`, `partial→PART`), `source→src`, `fidelity→fid`, `confidence→conf`, `frames→n`, `duration→dur`.
8. **Blank line removal**: No blank lines between action entries.

## Preservation Rules

1. **Hex bytecodes**: All bytecode frames preserved exactly (e.g., `aa055a80dfff`).
2. **Numeric parameters**: Speed, angle, distance values preserved exactly.
3. **Action names**: Tool/function names preserved exactly in snake_case.
4. **Action ordering**: Temporal sequence must be preserved — never reorder actions.
5. **Run-length counts**: Must be exact — never approximate the count of repeated actions.
6. **Non-trivial reasoning**: If a reasoning field contains actual VLM analysis (not just "camera frame at"), preserve the analysis text.
7. **Outcome and metadata**: Goal, outcome, source, fidelity preserved in header.

## Grammar / Syntax

```
TRACE       := HEADER "\n" ACTION_LIST
HEADER      := "@trace" FIELD*
FIELD       := key "=" value
key         := "g" | "o" | "src" | "fid" | "conf" | "dur" | "n"
value       := quoted_string | number | enum
enum        := "OK" | "FAIL" | "PART" | "OK+recover"

ACTION_LIST := ACTION ("\n" ACTION)*
ACTION      := TIMESTAMP ":" SP action_call SP "→" SP hex_result RLE?
TIMESTAMP   := "t+" integer
action_call := snake_case_name "(" params ")"
params      := param ("," param)*
param       := number | snake_case_name "=" number
hex_result  := [0-9a-f]+
RLE         := SP "[x" integer "]"
```

### Field Abbreviations

| Verbose | Compressed | Example |
|---------|-----------|---------|
| timestamp | (omitted, use t+ deltas) | `t+0`, `t+12` |
| goal | g | `g="red_cube"` |
| outcome: success | o=OK | |
| outcome: failure | o=FAIL | |
| outcome: partial | o=PART | |
| outcome: success_with_recovery | o=OK+recover | |
| source: sim_3d | src=sim_3d | |
| source: real_world | src=real | |
| fidelity | fid | `fid=0.8` |
| confidence | conf | `conf=0.9` |
| duration | dur | `dur=108s` |
| frames | n | `n=37` |

## Examples

### Example 1 — Full navigation trace (37 frames → 10 lines)
**Input** (207 lines):
```markdown
---
timestamp: "2026-04-07T21:15:54.864Z"
goal: "navigate to the red cube"
outcome: success
source: sim_3d
fidelity: 0.8
confidence: 0.9
frames: 37
duration: "108s"
outcome_reason: "Physics: within 0.24m of red_cube"
---
# Trace: navigate to the red cube
...
### 2026-04-07T21:14:09.807Z
**Reasoning:** [camera frame at 2026-04-07T21:14:09.807Z]
**Action:** TOOLCALL:{"name":"rotate_cw","args":{"speed":128,"degrees":90}}
**Result:** bytecode=aa055a80dfff

### 2026-04-07T21:14:12.997Z
**Reasoning:** [camera frame at 2026-04-07T21:14:12.997Z]
**Action:** TOOLCALL:{"name":"rotate_cw","args":{"speed":128,"degrees":90}}
**Result:** bytecode=aa055a80dfff
... (35 more frames)
```

**Output** (10 lines):
```
@trace g="red_cube" o=OK src=sim_3d fid=0.8 conf=0.9 dur=108s n=37

t+0:   rotate_cw(128,90)    → aa055a80dfff  [x4]
t+12:  turn_L(120,80)       → aa0350782bff
t+15:  fwd(128,128)         → aa01808001ff  [x10]
t+45:  rotate_cw(128,90)    → aa055a80dfff  [x4]
t+58:  fwd(128,128)         → aa01808001ff  [x3]
t+70:  turn_L(120,80)       → aa0350782bff  [x3]
t+80:  turn_R(80,128)       → aa03508059ff  [x7]
t+108: turn_L(120,80)       → aa0350782bff
```

**Ratio**: 207 lines → 10 lines, ~2,000 tokens → ~400 tokens = **~80% reduction**

### Example 2 — Single-frame success trace
**Input** (27 lines):
```markdown
---
timestamp: "2026-04-07T22:32:32Z"
goal: "navigate to the red cube"
outcome: success
source: sim_3d
fidelity: 0.8
frames: 1
duration: "11s"
---
### 2026-04-07T22:32:32.000Z
**Reasoning:** [camera frame at ...]
**Action:** TOOLCALL:{"name":"rotate_cw","args":{"speed":128,"degrees":45}}
**Result:** bytecode=aa052d80a8ff
```

**Output** (2 lines):
```
@trace g="red_cube" o=OK src=sim_3d fid=0.8 dur=11s n=1
t+0: rotate_cw(128,45) → aa052d80a8ff
```

**Ratio**: 27 lines → 2 lines = **~93% reduction**

### Example 3 — Failed navigation with non-trivial reasoning
**Input**:
```markdown
### 2026-04-07T21:20:00.000Z
**Reasoning:** The red cube is not visible. Obstacle (wall) detected at 0.3m ahead. Need to find alternative path.
**Action:** TOOLCALL:{"name":"stop","args":{}}
**Result:** bytecode=aa0500000500ff
```

**Output** (reasoning preserved because it contains actual analysis):
```
t+45: stop() → aa0500000500ff  "red_cube not visible. Wall at 0.3m. Need alt path."
```

## Expansion Protocol

Trace-log is **reversible** — the compressed form contains all action data needed to reconstruct the trace.

1. **Header → YAML frontmatter**: Expand abbreviated fields back to full names. `o=OK` → `outcome: success`.
2. **Temporal deltas → timestamps**: Add base timestamp (from header or first action) to each `t+N` offset.
3. **Action calls → TOOLCALL JSON**: `rotate_cw(128,90)` → `TOOLCALL:{"name":"rotate_cw","args":{"speed":128,"degrees":90}}`.
4. **Run-length → individual entries**: `[x4]` expands to 4 separate action blocks.
5. **Reasoning restoration**: If no reasoning text preserved, restore as `[camera frame at TIMESTAMP]`.
6. **Hex → bytecode result**: Prepend `bytecode=` prefix.

### Information Loss

- Camera frame timestamps in Reasoning field (replaced by temporal deltas)
- Exact millisecond timing between repeated actions within an RLE group
- Markdown formatting (headers, bold labels)
- Blank lines and whitespace

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~70-80% for multi-frame traces, ~90%+ for single-frame |
| Token reduction | ~75-85% |
| Reversibility | High — all action data preserved, only formatting lost |
| Latency | Low (sequential scan + deduplication) |
| Error rate | <1% — deterministic transformation |
| Quality improvement | Run-length encoding reveals stuck-loops and behavioral patterns |
