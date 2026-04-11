---
dialect_id: roclaw-bytecode
name: RoClaw Bytecode
version: 1.0.0
domain_scope: [robot]
compression_type: structural
compression_ratio: "~99%"
reversible: false
input_format: natural-language
output_format: hex-bytecode
---

# RoClaw Bytecode Dialect

## Purpose

Compresses natural-language motor commands into 6-byte hexadecimal frames that the RoClaw cerebellum can execute directly. This is the most aggressive compression dialect — it discards all semantic nuance and produces a fixed-width binary representation.

## Domain Scope

- **robot** — Used exclusively for RoClaw motor control output. The bytecode frames are sent over the OpenClaw Gateway to the physical robot or MuJoCo simulation.

## Compression Rules

1. **Map to opcode**: Match the natural-language intent to one of 13 motor opcodes.
2. **Encode parameters**: Convert speed/angle/duration to left-byte (L) and right-byte (R) values (0x00–0xFF).
3. **Frame structure**: Every output is exactly 6 bytes: `[0xAA] [OPCODE] [L] [R] [CHECKSUM] [0xFF]`
4. **Checksum**: XOR of bytes 1–3 (OPCODE ^ L ^ R), masked to 0x00–0xFF.
5. **One command per frame**: Compound commands produce multiple frames separated by spaces.

## Preservation Rules

- **Opcode fidelity**: The selected opcode must match the original intent (forward, backward, rotate, stop, etc.).
- **Parameter accuracy**: Speed and angle values must map to the correct byte range. Moderate speed = 0x80, full speed = 0xFF, stop = 0x00.
- **Ordering**: Multi-frame sequences preserve the original command order.

## Grammar / Syntax

```
FRAME     := 0xAA OPCODE L R CHECKSUM 0xFF
OPCODE    := 0x01 | 0x02 | 0x03 | 0x04 | 0x05 | 0x06 | 0x07
             0x08 | 0x09 | 0x0A | 0x0B | 0x0C | 0x0D
L         := 0x00..0xFF    # left motor / primary parameter
R         := 0x00..0xFF    # right motor / secondary parameter
CHECKSUM  := OPCODE ^ L ^ R
```

### Opcode Table

| Opcode | Name | L meaning | R meaning |
|--------|------|-----------|-----------|
| 0x01 | FORWARD | speed | speed |
| 0x02 | BACKWARD | speed | speed |
| 0x03 | ROTATE_CW | angle | speed |
| 0x04 | ROTATE_CCW | angle | speed |
| 0x05 | STOP | 0x00 | 0x00 |
| 0x06 | SPEED_SET | left_speed | right_speed |
| 0x07 | LOOK_AT | pan | tilt |
| 0x08 | GRAB | grip_force | 0x00 |
| 0x09 | RELEASE | 0x00 | 0x00 |
| 0x0A | SCAN | sweep_angle | speed |
| 0x0B | DOCK | 0x00 | 0x00 |
| 0x0C | UNDOCK | 0x00 | 0x00 |
| 0x0D | BEEP | frequency | duration |

## Examples

### Example 1
**Input**: "Move forward at moderate speed"
**Output**: `AA 01 80 80 01 FF`
**Ratio**: 35 chars → 18 chars (frame) → ~99% semantic compression

### Example 2
**Input**: "Stop immediately"
**Output**: `AA 05 00 00 05 FF`

### Example 3
**Input**: "Rotate clockwise 90 degrees at half speed"
**Output**: `AA 03 5A 80 59 FF`

### Example 4
**Input**: "Move forward then stop"
**Output**: `AA 01 80 80 01 FF AA 05 00 00 05 FF`

## Expansion Protocol

This dialect is **not reversible**. Natural-language nuance (hedging, emphasis, context) is permanently lost during compression. Expansion produces a **structured description**, not the original text:

```
Frame: AA 01 80 80 01 FF
Expansion: FORWARD command, left_speed=128, right_speed=128
```

### Information Loss

- Adverbs and qualifiers ("carefully", "quickly") → lost
- Conditional context ("if the path is clear") → lost
- Intent explanation ("to reach the kitchen") → lost
- Only the motor opcode and parameters survive

## Metrics

| Metric | Value |
|--------|-------|
| Compression ratio | ~99% (natural language → 6-byte frame) |
| Token reduction | ~95-99% depending on input verbosity |
| Reversibility | None — structural transformation |
| Latency | Negligible (lookup table) |
| Error rate | <1% when input maps cleanly to an opcode |
