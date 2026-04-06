---
name: operation-echo-q
version: v1
description: >
  Mathematically rigorous quantum computing scenario: design, prove, and implement
  a Quantum Cepstral Analysis algorithm. Forces Knowledge Wiki for LaTeX reasoning,
  strict invariant enforcement via sentient state constraints, and reflective error
  recovery against Qiskit validation.
delegation_pattern: hierarchical_decomposition_with_reflective_loop
error_recovery: strict_mathematical_validation
agents_required:
  - quantum-theorist-agent (created dynamically)
  - pure-mathematician-agent (created dynamically)
  - qiskit-engineer-agent (created dynamically)
  - system-architect-agent (created dynamically)
---

# Operation Echo-Q: Quantum Cepstral Deconvolution

## Scenario Overview

This scenario demonstrates the philosophical core of the Pure Markdown OS: **Markdown as a mathematical blackboard**. It forces the system to derive quantum algorithms in LaTeX wiki pages *before* writing any code, proving that the Knowledge Wiki provides a persistent "scratchpad memory" that enables LLMs to solve problems they could not handle in a single prompt.

### The Problem

Classical cepstral analysis separates convolved signals by mapping multiplication to addition via a logarithm:

$$c(t) = \text{IFFT}\bigl(\log|\text{FFT}(s(t))|\bigr)$$

Given a signal with an echo:

$$s(t) = p(t) + \alpha \cdot p(t - \tau)$$

where $p(t)$ is the primary pulse, $\alpha$ is the attenuation factor ($0 < \alpha < 1$), and $\tau$ is the echo delay, the cepstrum reveals a peak at quefrency $\tau$ corresponding to the echo.

### Why Quantum?

For massive real-time datasets (e.g., sonar arrays, seismic monitoring, arterial pressure waves), classical FFT becomes a bottleneck. The Quantum Fourier Transform (QFT) offers exponential speedup: $O(n \log n)$ classically vs. $O((\log n)^2)$ on a quantum computer for $n$-point transforms.

### The Core Challenge

The logarithm $\log(\cdot)$ is **non-unitary** — it cannot be implemented directly as a quantum gate. This is the central theoretical obstacle the agents must resolve, and it requires multi-page mathematical reasoning that exceeds what any LLM can hold in a single context window.

The wiki serves as the **external blackboard** where the proof is constructed incrementally across multiple agent invocations.

## Mathematical Context

### Signal Model

The composite signal received by a sensor:

$$s(t) = p(t) + \alpha \cdot p(t - \tau)$$

In the frequency domain via Fourier Transform:

$$S(\omega) = P(\omega) \cdot \bigl(1 + \alpha \cdot e^{-i\omega\tau}\bigr)$$

The echo introduces a **multiplicative ripple** $H(\omega) = 1 + \alpha \cdot e^{-i\omega\tau}$ across the spectrum.

### Homomorphic Decomposition

Taking the logarithm converts multiplication to addition:

$$\log|S(\omega)| = \log|P(\omega)| + \log|1 + \alpha \cdot e^{-i\omega\tau}|$$

The first term is the smooth spectral envelope of the pulse. The second term is a periodic function with period $2\pi/\tau$.

### Cepstral Domain

Applying the inverse Fourier Transform:

$$c(t_q) = \text{IFFT}\bigl\{\log|S(\omega)|\bigr\}$$

reveals a sharp peak at quefrency $t_q = \tau$, giving the echo delay.

### The Non-Unitarity Problem

Quantum gates must be unitary: $U^\dagger U = I$. The $\log(\cdot)$ function is:
- **Non-linear** — violates superposition
- **Non-unitary** — not norm-preserving
- **Singular at zero** — undefined for zero-amplitude components

**Resolution strategies** (to be derived in wiki):
1. **QSVT polynomial approximation** — approximate $\log(x)$ via a polynomial $p(x) \approx \log(x)$ on $[\epsilon, 1]$ encoded as a quantum singular value transformation
2. **Taylor series block-encoding** — encode $\log(1+x) = x - x^2/2 + x^3/3 - \cdots$ as a linear combination of unitaries (LCU)
3. **Hybrid classical-quantum** — perform QFT quantumly, extract amplitudes, compute $\log$ classically, re-encode

## Phase 1: Theoretical Grounding (Math Wiki)

**Agent**: `quantum-theorist-agent`
**Goal**: Build a cross-referenced knowledge wiki with the mathematical foundations
**Tools**: Read, Write, WebFetch, Glob

### Instructions

1. Initialize the wiki from `templates/wiki/_schema.template.md`, customized for quantum computing
2. Research and compile the following concept pages in `wiki/concepts/`:

| Wiki Page | Content |
|---|---|
| `quantum-fourier-transform.md` | QFT circuit, complexity $O((\log n)^2)$, comparison with classical FFT |
| `quantum-singular-value-transformation.md` | QSVT framework, polynomial transformations of singular values, signal processing conventions |
| `block-encoding.md` | Definition, constructions (LCU, PREP/SEL), amplitude amplification connection |
| `cepstral-analysis.md` | Classical algorithm, signal model $s(t) = p(t) + \alpha p(t-\tau)$, quefrency domain |
| `homomorphic-signal-separation.md` | Log-based separation, multiplicative-to-additive conversion, quantum challenges |

3. Create entity pages in `wiki/entities/`:

| Wiki Page | Content |
|---|---|
| `grand-unification-of-quantum-algorithms.md` | QSVT paper (Gilyen et al. 2019), key theorems, polynomial framework |

4. Cross-reference everything with `[[WikiLinks]]`:
   - Every concept MUST link to at least 2 related concepts
   - Every page MUST include LaTeX formulas with precise notation
   - The `[[homomorphic-signal-separation]]` page MUST explicitly state the non-unitarity problem and reference `[[quantum-singular-value-transformation]]` and `[[block-encoding]]` as resolution paths

5. Update `wiki/_index.md` and `wiki/_log.md`

### Wiki Page Format

Follow the schema from `templates/wiki/_schema.template.md`. Each concept page includes:
```markdown
---
concept: [concept name]
type: concept
domain: quantum-computing
related: [[concept-b]], [[concept-c]]
sources: [[summaries/source-slug]]
skills: [knowledge-query-agent]
last_updated: [ISO timestamp]
---
# [Concept Name]

## Definition
[1-3 sentences with LaTeX]

## Key Properties
- [Property with $formula$]

## How It Works
[Multi-paragraph explanation with LaTeX derivations]

## Related Concepts
- [[concept-b]] — [relationship]

## Open Questions
- [What the wiki doesn't yet answer]
```

## Phase 2: Invariant Enforcement (Sentient State)

**Agent**: `pure-mathematician-agent`
**Goal**: Read the math wiki and extract physical/mathematical constraints as enforceable invariants
**Tools**: Read, Write, Edit

### Instructions

1. Read all wiki concept pages from Phase 1
2. Identify every physical law and mathematical constraint
3. Write `state/constraints.md` with the following invariants:

```markdown
# Mathematical Invariants — Operation Echo-Q

## Hard Constraints (MUST NOT violate)

### C1: Unitarity
All quantum operations MUST be unitary: $U^\dagger U = I$.
**Implication**: The $\log(\cdot)$ function cannot be applied directly as a gate.
**Wiki ref**: [[homomorphic-signal-separation]], [[block-encoding]]

### C2: No-Cloning
No quantum state may be copied: the no-cloning theorem prohibits $|ψ⟩ → |ψ⟩|ψ⟩$.
**Implication**: Intermediate states cannot be duplicated for classical post-processing.
**Wiki ref**: [[quantum-fourier-transform]]

### C3: Logarithm Approximation
The $\log(\cdot)$ approximation MUST use either:
  (a) QSVT polynomial encoding, OR
  (b) Taylor series block-encoding (LCU)
No other method satisfies C1.
**Wiki ref**: [[quantum-singular-value-transformation]], [[block-encoding]]

### C4: Polynomial Depth
Circuit depth MUST remain polynomial in qubit count $n$: $\text{depth} = O(\text{poly}(n))$.
**Implication**: Exponential-depth constructions are physically unrealizable.

### C5: Normalization
Quantum state amplitudes MUST satisfy $\sum_i |a_i|^2 = 1$.
**Implication**: Signal encoding must normalize input amplitudes.

## Soft Constraints (SHOULD satisfy)

### S1: Error Budget
Total approximation error from polynomial truncation SHOULD satisfy $\epsilon < 10^{-3}$.

### S2: Qubit Economy
Implementation SHOULD use $\leq 2n + O(\log n)$ qubits for an $n$-point signal.

### S3: Measurement Strategy
Final measurement SHOULD use amplitude estimation rather than naive sampling
to extract cepstral peaks with $O(1/\epsilon)$ queries rather than $O(1/\epsilon^2)$.
```

4. Each constraint MUST reference the wiki page where the underlying math is derived
5. The `qiskit-engineer-agent` in Phase 3 MUST read these constraints before writing any code

## Phase 3: Implementation & Validation (Reflective Loop)

**Agent**: `qiskit-engineer-agent` (primary), `error-recovery-agent` (on failure)
**Goal**: Implement the quantum cepstral algorithm in Qiskit, validated against constraints
**Tools**: Read, Write, Bash, Edit

### Instructions

1. Read all wiki concept pages from `wiki/concepts/`
2. Read `state/constraints.md` — verify every constraint is understood
3. Write `output/quantum_cepstrum.py` implementing:

```
Algorithm: Quantum Cepstral Analysis
─────────────────────────────────────
Input:  Classical signal s[k] for k = 0..N-1
Output: Cepstral coefficients c[q] for q = 0..N-1

Step 1: State Preparation
  Encode s[k] as amplitudes: |ψ⟩ = (1/‖s‖) Σ_k s[k]|k⟩

Step 2: Quantum Fourier Transform
  |Ψ⟩ = QFT|ψ⟩ → frequency domain amplitudes

Step 3: Block-Encoded Logarithm
  Apply log(·) via QSVT polynomial approximation:
  - Construct block-encoding of diagonal(|Ψ_k|)
  - Apply QSVT with polynomial p(x) ≈ log(x) on [ε, 1]
  - Result: amplitudes ≈ log|Ψ_k|

Step 4: Inverse QFT
  |c⟩ = QFT†|log Ψ⟩ → cepstral domain

Step 5: Measurement
  Measure |c⟩ to extract cepstral peak at quefrency τ
```

4. The implementation MUST:
   - Import `qiskit` and `numpy`
   - Create a synthetic test signal: `s(t) = sin(2π·5t) + 0.6·sin(2π·5·(t-0.3))` with known $\tau = 0.3$
   - Implement QFT using Qiskit's built-in `QFT` circuit
   - Implement a simplified QSVT or Taylor-series log approximation
   - Run on `AerSimulator` (statevector or qasm)
   - Print detected echo delay and compare with expected $\tau$
   - Validate against constraints C1-C5

5. Execute via Bash:
   ```bash
   cd projects/Project_echo_q && python output/quantum_cepstrum.py
   ```

### Reflective Error Recovery Loop

On execution failure, invoke `error-recovery-agent`:

```
reflective_loop:
  max_cycles: 3

  for cycle in 1..max_cycles:
    1. qiskit-engineer-agent writes/edits output/quantum_cepstrum.py
    2. Execute via Bash
    3. if SUCCESS:
         write state/validation_result.md (PASS)
         break
    4. if FAILURE:
         error-recovery-agent reads:
           - Error traceback
           - state/constraints.md (which constraint was violated?)
           - wiki/concepts/ (what does the math say?)
         error-recovery-agent writes:
           - state/error_diagnosis.md (root cause + fix strategy)
         qiskit-engineer-agent reads diagnosis and applies fix
         continue to next cycle

  if all cycles exhausted:
    write state/validation_result.md (PARTIAL — document what works)
```

The error-recovery-agent cross-references errors against the wiki math and constraints. For example:
- `TypeError: log of zero` → constraint C3 violated → wiki says use $[\epsilon, 1]$ domain restriction
- `Non-unitary gate` → constraint C1 violated → wiki says use block-encoding
- `Qubit count exceeded` → constraint S2 violated → reduce polynomial degree

## Phase 4: Final Synthesis

**Agent**: `system-architect-agent`
**Goal**: Synthesize all artifacts into a final whitepaper
**Tools**: Read, Write

### Instructions

1. Read all project artifacts:
   - `wiki/concepts/*.md` — theoretical foundations
   - `wiki/entities/*.md` — paper references
   - `state/constraints.md` — mathematical invariants
   - `output/quantum_cepstrum.py` — implementation
   - `state/validation_result.md` — test results
   - `state/error_diagnosis.md` — error recovery log (if any)

2. Write `output/Echo_Q_Whitepaper.md` containing:
   - **Abstract**: Problem statement, approach, results
   - **Theoretical Foundation**: Curated from wiki pages with LaTeX
   - **Algorithm Design**: Step-by-step with circuit diagrams (ASCII)
   - **Constraint Verification**: Table showing each invariant C1-C5 and its status
   - **Implementation Notes**: Key Qiskit patterns and workarounds
   - **Results**: Echo detection accuracy, circuit depth, qubit count
   - **Error Recovery Journal**: What broke, why, and how it was fixed
   - **Citations**: All `[[WikiLink]]` references resolved to full citations

3. Cross-validate: every claim in the whitepaper MUST have a wiki citation

## Expected Project Structure

```
projects/Project_echo_q/
├── components/
│   ├── agents/
│   │   ├── quantum-theorist-agent.md
│   │   ├── pure-mathematician-agent.md
│   │   ├── qiskit-engineer-agent.md
│   │   └── system-architect-agent.md
│   └── tools/
├── input/
├── raw/                              # Immutable source material (papers, references)
├── wiki/
│   ├── _schema.md                    # Wiki constitution (quantum computing domain)
│   ├── _index.md                     # Auto-maintained catalog
│   ├── _log.md                       # Append-only operation log
│   ├── concepts/
│   │   ├── quantum-fourier-transform.md
│   │   ├── quantum-singular-value-transformation.md
│   │   ├── block-encoding.md
│   │   ├── cepstral-analysis.md
│   │   └── homomorphic-signal-separation.md
│   ├── entities/
│   │   └── grand-unification-of-quantum-algorithms.md
│   ├── summaries/
│   └── queries/
├── output/
│   ├── quantum_cepstrum.py           # Qiskit implementation
│   └── Echo_Q_Whitepaper.md          # Final synthesis document
├── state/
│   ├── constraints.md                # Mathematical invariants (sentient state)
│   ├── validation_result.md          # Pass/fail from reflective loop
│   └── error_diagnosis.md            # Error recovery log (if errors occurred)
└── memory/
    ├── short_term/                   # Agent interaction logs
    └── long_term/                    # Consolidated learnings
```

## Loop Orchestration

**SystemAgent** controls the four-phase pipeline:

```
initialize:
  - create projects/Project_echo_q/ directory structure
  - copy wiki schema from templates/wiki/_schema.template.md
  - initialize wiki/_index.md, wiki/_log.md

phase_1_theory:
  - invoke quantum-theorist-agent
  - verify: wiki/concepts/ has >= 5 pages with LaTeX and [[WikiLinks]]
  - verify: wiki/_index.md updated

phase_2_constraints:
  - invoke pure-mathematician-agent
  - verify: state/constraints.md has >= 5 hard constraints
  - verify: each constraint references a wiki page

phase_3_implementation:
  - cycle = 0
  - while cycle < 3:
      invoke qiskit-engineer-agent
      execute output/quantum_cepstrum.py
      if success:
        write state/validation_result.md (PASS)
        break
      else:
        invoke error-recovery-agent
        cycle += 1
  - if cycle == 3:
      write state/validation_result.md (PARTIAL)

phase_4_synthesis:
  - invoke system-architect-agent
  - verify: output/Echo_Q_Whitepaper.md exists
  - verify: whitepaper cites wiki pages

finalize:
  - log agent interactions to memory/short_term/
  - consolidate learnings to memory/long_term/
  - update system/SmartMemory.md
```

## Error Recovery

| Error | Phase | Agent | Action |
|---|---|---|---|
| WebFetch fails for paper | 1 | quantum-theorist-agent | Use cached knowledge; derive from first principles |
| Wiki page missing cross-refs | 1 | quantum-theorist-agent | Run `knowledge-lint-agent` to detect orphans |
| Constraint references broken wiki link | 2 | pure-mathematician-agent | Re-read wiki/_index.md, fix references |
| Qiskit import error | 3 | qiskit-engineer-agent | Install via `pip install qiskit qiskit-aer` |
| Non-unitary gate error | 3 | error-recovery-agent | Cross-ref constraint C1 + wiki `[[block-encoding]]` |
| Log of zero / NaN | 3 | error-recovery-agent | Cross-ref constraint C3 + wiki `[[homomorphic-signal-separation]]` |
| Circuit too deep / timeout | 3 | error-recovery-agent | Cross-ref constraint C4, reduce polynomial degree |
| Qubit count exceeded | 3 | error-recovery-agent | Cross-ref constraint S2, simplify encoding |
| Whitepaper missing citation | 4 | system-architect-agent | Re-read wiki, add missing references |

## Success Criteria

1. **Wiki completeness**: All 5 concept pages + 1 entity page exist with LaTeX formulas and `[[WikiLinks]]`
2. **Constraint enforcement**: `state/constraints.md` contains >= 5 constraints, each referencing a wiki page
3. **Code execution**: `output/quantum_cepstrum.py` runs without error (or PARTIAL with documented blockers)
4. **Echo detection**: Detected quefrency $\hat{\tau}$ satisfies $|\hat{\tau} - \tau| < 0.05$ for the synthetic test signal
5. **Whitepaper quality**: `output/Echo_Q_Whitepaper.md` cites wiki pages for every mathematical claim

## Why Markdown Wins

This scenario is deliberately designed to be **impossible without persistent external memory**.

The mathematical reasoning chain — from QFT properties through QSVT polynomial construction to block-encoded logarithm approximation — spans thousands of tokens of dense LaTeX. No LLM can hold this entire derivation in a single context window while simultaneously writing correct Qiskit code.

The Knowledge Wiki solves this by serving as a **mathematical blackboard**:
- Phase 1 writes the theorems and derivations to wiki pages
- Phase 2 reads the wiki and extracts invariants — a different agent benefits from Phase 1's work
- Phase 3 reads both the wiki and the constraints — the code is grounded in verified math
- Phase 4 reads everything and synthesizes — citations trace back to wiki derivations

Each agent works within its context window but builds on the persistent wiki. The wiki **compounds**: every page written makes the next agent's task easier. This is the compounding loop that makes Markdown a mathematical instrument, not just a document format.

## Usage

```bash
# Full scenario execution
skillos execute: "Run the Operation Echo-Q scenario: derive and implement a quantum cepstral analysis algorithm using the wiki as a mathematical blackboard"

# Theory-only (Phase 1-2)
skillos execute: "Run Operation Echo-Q Phases 1-2: build the quantum computing wiki and extract mathematical constraints"

# Implementation-only (assumes wiki exists)
skillos execute: "Run Operation Echo-Q Phase 3: implement quantum_cepstrum.py from the existing wiki and constraints"

# Whitepaper-only (assumes all phases complete)
skillos execute: "Run Operation Echo-Q Phase 4: synthesize the Echo-Q whitepaper from wiki, code, and validation results"
```
