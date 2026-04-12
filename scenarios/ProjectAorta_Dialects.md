---
name: project-aorta-dialects
version: v1
description: >
  Dialect-enhanced variant of Project Aorta for A/B token comparison.
  Same three-agent cognitive pipeline for quantum homomorphic signal processing
  but with dialect compression on internal artifacts. Vision uses caveman-prose,
  math framework uses formal-proof + system-dynamics. Code remains verbose.
delegation_pattern: sequential
requires_dialects:
  - formal-proof
  - system-dynamics
  - caveman-prose
  - exec-plan
pipeline:
  - step: 1
    deliverable: "Project vision document"
    dialect: caveman-prose
  - step: 2
    deliverable: "Mathematical framework"
    dialect: formal-proof
  - step: 3
    deliverable: "Quantum implementation"
    dialect: none
agents_required:
  - visionary-agent (created dynamically)
  - mathematician-agent (created dynamically)
  - quantum-engineer-agent (created dynamically)
---

# Project Aorta (Dialects): Quantum Homomorphic Signal Processing

## Scenario Overview

This is the **dialect-enhanced variant** of Project Aorta, designed for A/B token comparison against the original. The three-agent cognitive pipeline is identical, but internal artifacts use SkillOS dialect compression:

- **Vision document** uses `caveman-prose` — compressed narrative (~50% reduction) that preserves all key concepts
- **Mathematical framework** uses `formal-proof` + `system-dynamics` — structured proofs and stock-flow models
- **Pipeline state** uses `exec-plan` notation for progress tracking
- **Quantum code** remains uncompressed — executable Python is a human-facing deliverable

**Expected token reduction**: 40-60% on internal artifacts (vision, math framework, state files).

**Important**: Compressed outputs need `human-renderer-agent` to expand for human reading.

## Dialect Protocol

Before producing each deliverable, agents MUST load the corresponding dialect definition from `system/dialects/`:

| Stage | Deliverable | Dialect(s) | Dialect File(s) |
|---|---|---|---|
| 1 | Project vision | `caveman-prose` | `system/dialects/caveman-prose.dialect.md` |
| 2 | Math framework | `formal-proof` + `system-dynamics` | `system/dialects/formal-proof.dialect.md`, `system/dialects/system-dynamics.dialect.md` |
| 3 | Quantum code | none | — |

## The Challenge

Recreate a biomedical engineering project that originally aimed to navigate arterial systems by analyzing pressure wave echoes, but implement it using quantum homomorphic analysis instead of classical signal processing.

### Signal Model

```
s(t) = p(t) + α * p(t - τ)
```

Where `p(t)` is the cardiac pressure pulse, `α` is attenuation, and `τ` is the echo delay from arterial bifurcation reflections.

## Three-Agent Pipeline

### Stage 1: Vision and Context (caveman-prose)

**Agent**: `visionary-agent`
**Goal**: Transform the research concept into a compressed project description
**Dialect**: `caveman-prose` — drop filler words, compress to essential meaning
**Input**: Research concept about quantum arterial navigation
**Output**: `project_vision.md` — Compressed narrative with full scientific context

#### Instructions

1. Load `system/dialects/caveman-prose.dialect.md` before writing
2. Produce the vision document using caveman-prose rules:
   - Drop articles, filler words, hedging language
   - Use short declarative sentences
   - Preserve all technical terms, numbers, and equations
   - Target ~50% token reduction vs verbose prose
3. Cover all key areas:
   - Radiation-free catheter navigation concept
   - Pressure wave propagation and impedance mismatch physics
   - Echo formation at arterial bifurcations
   - Homomorphic (cepstral) analysis for echo detection
   - Quantum advantage potential
   - Clinical applications and system architecture
4. Save to `projects/Project_aorta_dialects/output/project_vision.md`

#### Example caveman-prose output

```
# Project Aorta: Quantum Arterial Navigation

## Core Innovation
Catheter navigation without X-ray. Pressure wave echoes from bifurcations
reveal catheter position. Cepstral analysis separates overlapping echoes.
Quantum implementation: QFT for frequency analysis, QSVT for log approx.

## Signal Model
s(t) = p(t) + α·p(t-τ). Echo NOT high-freq — same freq content as primary
pulse. Impedance mismatch at bifurcations creates reflections.
...
```

### Stage 2: Mathematical Formalization (formal-proof + system-dynamics)

**Agent**: `mathematician-agent`
**Goal**: Convert vision into rigorous mathematical framework using dialect notation
**Dialect**: `formal-proof` for derivations, `system-dynamics` for hemodynamic models
**Input**: Project vision document (in caveman-prose)
**Output**: `mathematical_framework.md` — Formal proofs + stock-flow models

#### Instructions

1. Load both `system/dialects/formal-proof.dialect.md` and `system/dialects/system-dynamics.dialect.md`
2. Read the caveman-prose vision document — expand as needed to understand intent
3. Produce the mathematical framework with two notation systems:

**Derivations** use `formal-proof`:
```
GIVEN:
  G1. s(t) = p(t) + α·p(t-τ), 0 < α < 1
  G2. S(ω) = P(ω)·(1 + α·e^{-iωτ})
DERIVE:
  D1. log|S(ω)| = log|P(ω)| + log|1 + α·e^{-iωτ}| [BY log_product_rule]
  D2. Second term periodic with period 2π/τ [BY Euler_formula, G2]
  D3. IFFT{log|S(ω)|} has peak at quefrency t_q = τ [BY D2, Fourier_periodicity]
QED: Cepstral analysis recovers echo delay τ from composite signal
```

**Hemodynamic models** use `system-dynamics`:
```
[STOCK] arterial_pressure: Pressure in vessel segment
[STOCK] echo_amplitude: Reflected wave energy at bifurcation
[FLOW] pulse_propagation: Heart → aorta → branches (velocity ~5 m/s)
[FLOW] reflection_rate: Proportional to impedance mismatch ratio
[FB+] resonance_loop: Multiple reflections amplify standing waves
[FB-] damping_loop: Viscous losses attenuate echoes over distance
[DELAY] propagation_delay: τ = 2·distance / wave_velocity
[EXT] cardiac_output: Heart rate and stroke volume drive input
```

4. Include quantum implementation math:
   - QFT complexity analysis
   - QSVT polynomial approximation for log(x)
   - Block-encoding construction
   - Error budget derivation

5. Save to `projects/Project_aorta_dialects/output/mathematical_framework.md`
6. Track pipeline progress in `state/pipeline.md` using `exec-plan` notation

### Stage 3: Quantum Implementation (No Dialect)

**Agent**: `quantum-engineer-agent`
**Goal**: Translate mathematical framework into executable Qiskit code
**Dialect**: none — executable Python must remain verbose and readable
**Input**: Mathematical framework document (in formal-proof + system-dynamics notation)
**Output**: `quantum_aorta_implementation.py` — Complete working implementation

#### Instructions

1. Read `mathematical_framework.md` — parse `formal-proof` blocks for algorithm steps, parse `system-dynamics` blocks for system model understanding
2. Implement the full quantum cepstral pipeline:
   - State preparation: encode signal amplitudes
   - QFT: frequency domain transformation
   - Log approximation: QSVT or Taylor-series block-encoding
   - Inverse QFT: cepstral domain
   - Measurement: extract echo delay peak
3. Include synthetic arterial signal test case
4. Validate against the formal-proof derivations
5. Save to `projects/Project_aorta_dialects/output/quantum_aorta_implementation.py`

## Execution Flow

```markdown
1. **Initialize Project Context**
   - Create projects/Project_aorta_dialects/ directory structure
   - Track pipeline with exec-plan notation in state/pipeline.md

2. **Stage 1: Visionary Analysis (caveman-prose)**
   - Load caveman-prose dialect
   - Invoke visionary-agent with project concept
   - Generate compressed project description
   - Save to output/project_vision.md

3. **Stage 2: Mathematical Formalization (formal-proof + system-dynamics)**
   - Load both dialect definitions
   - Invoke mathematician-agent with compressed vision
   - Generate formal proofs + stock-flow hemodynamic models
   - Save to output/mathematical_framework.md

4. **Stage 3: Quantum Implementation (no dialect)**
   - Invoke quantum-engineer-agent with math framework
   - Parse dialect notation to understand algorithm
   - Generate complete Qiskit implementation
   - Save to output/quantum_aorta_implementation.py

5. **Validation and Execution**
   - Execute the generated quantum code
   - Compare results with classical baseline
   - Generate final analysis report
```

## Expected Project Structure

```
projects/Project_aorta_dialects/
├── components/agents/
├── output/
│   ├── project_vision.md                # caveman-prose (compressed)
│   ├── mathematical_framework.md        # formal-proof + system-dynamics
│   └── quantum_aorta_implementation.py  # No dialect — executable Python
├── state/
│   └── pipeline.md                      # exec-plan notation
└── memory/
```

## Success Criteria

- Each agent produces high-quality output using the specified dialect
- Vision document is measurably shorter than original (~50% token reduction)
- Mathematical framework contains `formal-proof` blocks with GIVEN:/DERIVE:/QED notation
- Hemodynamic models use `system-dynamics` stock-flow notation
- Quantum implementation successfully executes and produces meaningful results
- Pipeline demonstrates seamless handoff between dialect-compressed stages
- Dialect notation used consistently in wiki/constraints (compare with original)

## A/B Comparison

Run both variants and compare:

```bash
# Original (no dialects)
skillos execute: "Run the Project Aorta scenario"

# Dialect-enhanced
skillos execute: "Run the Project Aorta Dialects scenario"

# Compare: internal artifact token counts should show 40-60% reduction
# Note: dialect outputs need human-renderer-agent to expand for reading
```

## Usage

```bash
# Full scenario execution
skillos execute: "Run the Project Aorta Dialects scenario"

# To read compressed outputs in human-friendly format:
skillos execute: "Expand the Project Aorta Dialects outputs using human-renderer-agent"
```
