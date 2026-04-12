---
name: operation-echo-q-dialects
version: v1
description: >
  Dialect-enhanced variant of Operation Echo-Q for A/B token comparison.
  Same quantum cepstral analysis pipeline but with full dialect compression
  on internal artifacts (wiki derivations, constraints, state tracking).
  Final deliverables (code, whitepaper) remain verbose for human consumption.
delegation_pattern: sequential
error_recovery: strict_mathematical_validation
requires_dialects:
  - formal-proof
  - constraint-dsl
  - exec-plan
pipeline:
  - step: 1
    deliverable: "Wiki concept pages with derivations"
    dialect: formal-proof
  - step: 2
    deliverable: "Mathematical invariants and constraints"
    dialect: constraint-dsl
  - step: 3
    deliverable: "Qiskit implementation"
    dialect: none
  - step: 4
    deliverable: "Synthesis whitepaper"
    dialect: formal-proof
agents_required:
  - quantum-theorist-agent (created dynamically)
  - pure-mathematician-agent (created dynamically)
  - qiskit-engineer-agent (created dynamically)
  - system-architect-agent (created dynamically)
---

# Operation Echo-Q (Dialects): Quantum Cepstral Deconvolution

## Scenario Overview

This is the **dialect-enhanced variant** of Operation Echo-Q, designed for A/B token comparison against the original. The quantum cepstral analysis pipeline is identical, but internal artifacts use SkillOS dialect compression:

- **Wiki derivations** use `formal-proof` notation (GIVEN:/DERIVE:/QED) instead of verbose LaTeX prose
- **Constraints** use `constraint-dsl` notation (C[N][H/M/L]) instead of free-form markdown
- **State tracking** uses `exec-plan` notation for pipeline progress
- **Code and whitepaper** remain uncompressed — these are human-facing deliverables

**Expected token reduction**: 40-60% on internal artifacts (wiki pages, constraints, state files).

### The Problem

Classical cepstral analysis separates convolved signals by mapping multiplication to addition via a logarithm:

$$c(t) = \text{IFFT}\bigl(\log|\text{FFT}(s(t))|\bigr)$$

Given a signal with an echo:

$$s(t) = p(t) + \alpha \cdot p(t - \tau)$$

where $p(t)$ is the primary pulse, $\alpha$ is the attenuation factor ($0 < \alpha < 1$), and $\tau$ is the echo delay, the cepstrum reveals a peak at quefrency $\tau$ corresponding to the echo.

### The Core Challenge

The logarithm $\log(\cdot)$ is **non-unitary** — it cannot be implemented directly as a quantum gate. This is the central theoretical obstacle the agents must resolve.

## Dialect Protocol

Before producing each deliverable, agents MUST load the corresponding dialect definition from `system/dialects/`:

| Phase | Deliverable | Dialect | Dialect File |
|---|---|---|---|
| 1 | Wiki concept pages | `formal-proof` | `system/dialects/formal-proof.dialect.md` |
| 2 | Constraints | `constraint-dsl` | `system/dialects/constraint-dsl.dialect.md` |
| 3 | Qiskit code | none | — |
| 4 | Whitepaper (internal) | `formal-proof` | `system/dialects/formal-proof.dialect.md` |

## Phase 1: Theoretical Grounding (Math Wiki + formal-proof)

**Agent**: `quantum-theorist-agent`
**Goal**: Build a cross-referenced knowledge wiki with mathematical foundations
**Dialect**: `formal-proof` — all derivation sections MUST use GIVEN:/DERIVE:/QED notation
**Tools**: Read, Write, WebFetch, Glob

### Instructions

1. Load `system/dialects/formal-proof.dialect.md` before writing any wiki page
2. Initialize the wiki from `templates/wiki/_schema.template.md`, customized for quantum computing
3. Research and compile the following concept pages in `wiki/concepts/`:

| Wiki Page | Content |
|---|---|
| `quantum-fourier-transform.md` | QFT circuit, complexity $O((\log n)^2)$, comparison with classical FFT |
| `quantum-singular-value-transformation.md` | QSVT framework, polynomial transformations of singular values |
| `block-encoding.md` | Definition, constructions (LCU, PREP/SEL), amplitude amplification connection |
| `cepstral-analysis.md` | Classical algorithm, signal model, quefrency domain |
| `homomorphic-signal-separation.md` | Log-based separation, quantum challenges |

4. **Dialect requirement**: Each wiki page's "How It Works" section MUST contain at least one `formal-proof` block:

```
GIVEN:
  G1. [premise]
  G2. [premise]
DERIVE:
  D1. [step] [BY rule_name]
  D2. [step] [BY D1, G2]
QED: [conclusion]
```

5. Cross-reference everything with `[[WikiLinks]]`:
   - Every concept MUST link to at least 2 related concepts
   - The `[[homomorphic-signal-separation]]` page MUST explicitly state the non-unitarity problem

6. Update `wiki/_index.md` and `wiki/_log.md`

### Expected Token Savings

Wiki derivation sections in `formal-proof` notation are ~50% shorter than equivalent LaTeX prose while preserving logical structure and traceability via [BY rule] annotations.

## Phase 2: Invariant Enforcement (constraint-dsl)

**Agent**: `pure-mathematician-agent`
**Goal**: Read the math wiki and extract constraints using `constraint-dsl` notation
**Dialect**: `constraint-dsl` — all constraints MUST use C[N][severity] / S[N][severity] format
**Tools**: Read, Write, Edit

### Instructions

1. Load `system/dialects/constraint-dsl.dialect.md` before writing constraints
2. Read all wiki concept pages from Phase 1
3. Identify every physical law and mathematical constraint
4. Write `state/constraints.md` using strict `constraint-dsl` notation:

```markdown
# Mathematical Invariants — Operation Echo-Q (Dialect Mode)

## Hard Constraints

C[1][H] Unitarity
  pred: ∀ U ∈ gates(circuit): U†U = I
  impl: log(·) cannot be applied directly as a gate
  wiki: [[homomorphic-signal-separation]], [[block-encoding]]

C[2][H] No-Cloning
  pred: ¬∃ op: |ψ⟩ → |ψ⟩|ψ⟩
  impl: Intermediate states cannot be duplicated for classical post-processing
  wiki: [[quantum-fourier-transform]]

C[3][H] Log-Approximation
  pred: log_method ∈ {QSVT_poly, Taylor_LCU}
  impl: Only methods satisfying C[1] are permitted
  wiki: [[quantum-singular-value-transformation]], [[block-encoding]]

C[4][H] Poly-Depth
  pred: depth(circuit) = O(poly(n))
  impl: Exponential-depth constructions are physically unrealizable
  wiki: [[quantum-fourier-transform]]

C[5][H] Normalization
  pred: Σ_i |a_i|² = 1
  impl: Signal encoding must normalize input amplitudes
  wiki: [[cepstral-analysis]]

## Soft Constraints

S[1][M] Error-Budget
  pred: ε_total < 10⁻³
  wiki: [[quantum-singular-value-transformation]]

S[2][M] Qubit-Economy
  pred: qubits ≤ 2n + O(log n)
  wiki: [[block-encoding]]

S[3][L] Measurement-Strategy
  pred: method = amplitude_estimation
  impl: O(1/ε) queries vs O(1/ε²) naive sampling
  wiki: [[cepstral-analysis]]
```

5. Each constraint MUST have `pred:`, `impl:` (optional), and `wiki:` fields
6. The `qiskit-engineer-agent` in Phase 3 MUST read these constraints before writing any code

### Expected Token Savings

`constraint-dsl` format is ~40% shorter than the verbose prose format used in the original scenario, while adding machine-parseable structure (severity levels, predicate fields).

## Phase 3: Implementation & Validation (No Dialect)

**Agent**: `qiskit-engineer-agent` (primary), `error-recovery-agent` (on failure)
**Goal**: Implement the quantum cepstral algorithm in Qiskit
**Dialect**: none — executable Python code must remain verbose and readable
**Tools**: Read, Write, Bash, Edit

### Instructions

1. Read all wiki concept pages from `wiki/concepts/`
2. Read `state/constraints.md` — parse the `constraint-dsl` notation to understand each invariant
3. Write `output/quantum_cepstrum.py` implementing:

```
Algorithm: Quantum Cepstral Analysis
─────────────────────────────────────
Input:  Classical signal s[k] for k = 0..N-1
Output: Cepstral coefficients c[q] for q = 0..N-1

Step 1: State Preparation — encode s[k] as amplitudes
Step 2: Quantum Fourier Transform
Step 3: Block-Encoded Logarithm via QSVT polynomial approximation
Step 4: Inverse QFT → cepstral domain
Step 5: Measurement → extract cepstral peak at quefrency τ
```

4. The implementation MUST:
   - Import `qiskit` and `numpy`
   - Create a synthetic test signal: `s(t) = sin(2π·5t) + 0.6·sin(2π·5·(t-0.3))` with known $\tau = 0.3$
   - Implement QFT using Qiskit's built-in `QFT` circuit
   - Implement a simplified QSVT or Taylor-series log approximation
   - Run on `AerSimulator`
   - Print detected echo delay and compare with expected $\tau$
   - Validate against constraints C[1]-C[5]

5. Execute via Bash:
   ```bash
   cd projects/Project_echo_q_dialects && python output/quantum_cepstrum.py
   ```

### Reflective Error Recovery Loop

On execution failure, invoke `error-recovery-agent`:

```
reflective_loop:
  max_cycles: 3

  for cycle in 1..max_cycles:
    1. qiskit-engineer-agent writes/edits output/quantum_cepstrum.py
    2. Execute via Bash
    3. if SUCCESS: write state/validation_result.md (PASS), break
    4. if FAILURE:
         error-recovery-agent reads:
           - Error traceback
           - state/constraints.md (which C[N] was violated?)
           - wiki/concepts/ (what does the formal-proof say?)
         error-recovery-agent writes state/error_diagnosis.md
         continue to next cycle

  if all cycles exhausted:
    write state/validation_result.md (PARTIAL)
```

## Phase 4: Final Synthesis (formal-proof internal, verbose output)

**Agent**: `system-architect-agent`
**Goal**: Synthesize all artifacts into a final whitepaper
**Dialect**: `formal-proof` for internal reasoning; final output expanded to verbose prose via `human-renderer-agent` at egress
**Tools**: Read, Write

### Instructions

1. Read all project artifacts:
   - `wiki/concepts/*.md` — theoretical foundations (in `formal-proof` notation)
   - `state/constraints.md` — invariants (in `constraint-dsl` notation)
   - `output/quantum_cepstrum.py` — implementation
   - `state/validation_result.md` — test results

2. Write `output/Echo_Q_Whitepaper.md` containing:
   - **Abstract**: Problem statement, approach, results
   - **Theoretical Foundation**: Expand `formal-proof` blocks from wiki into readable LaTeX prose
   - **Algorithm Design**: Step-by-step with circuit diagrams (ASCII)
   - **Constraint Verification**: Table showing each C[N] and S[N] with pass/fail status
   - **Implementation Notes**: Key Qiskit patterns
   - **Results**: Echo detection accuracy, circuit depth, qubit count
   - **Error Recovery Journal**: What broke and how it was fixed

3. The whitepaper is a human-facing deliverable — all dialect notation MUST be expanded to verbose prose in the final output. Use `human-renderer-agent` if available, or expand manually.

## Expected Project Structure

```
projects/Project_echo_q_dialects/
├── components/agents/
├── wiki/
│   ├── _schema.md
│   ├── _index.md
│   ├── _log.md
│   ├── concepts/           # formal-proof notation in derivation sections
│   ├── entities/
│   └── summaries/
├── output/
│   ├── quantum_cepstrum.py # No dialect — executable Python
│   └── Echo_Q_Whitepaper.md # Expanded to verbose prose
├── state/
│   ├── constraints.md      # constraint-dsl notation
│   ├── validation_result.md
│   └── error_diagnosis.md
└── memory/
```

## Success Criteria

1. **Wiki completeness**: All 5 concept pages exist with `formal-proof` derivation blocks and `[[WikiLinks]]`
2. **Dialect notation used**: Wiki derivations use GIVEN:/DERIVE:/QED; constraints use C[N][severity] format
3. **Constraint enforcement**: `state/constraints.md` in `constraint-dsl` with >= 5 hard constraints
4. **Code execution**: `output/quantum_cepstrum.py` runs without error (or PARTIAL with documented blockers)
5. **Echo detection**: Detected quefrency $\hat{\tau}$ satisfies $|\hat{\tau} - \tau| < 0.05$
6. **Whitepaper quality**: All dialect notation expanded to readable prose in final deliverable
7. **Token comparison**: Internal artifacts measurably shorter than original Echo-Q equivalents

## A/B Comparison

Run both variants and compare:

```bash
# Original (no dialects)
skillos execute: "Run the Operation Echo-Q scenario"

# Dialect-enhanced
skillos execute: "Run the Operation Echo-Q Dialects scenario"

# Compare: internal artifact token counts should show 40-60% reduction
```

## Usage

```bash
# Full scenario execution
skillos execute: "Run the Operation Echo-Q Dialects scenario"

# Theory-only (Phase 1-2)
skillos execute: "Run Operation Echo-Q Dialects Phases 1-2: build wiki with formal-proof notation and extract constraint-dsl invariants"
```
