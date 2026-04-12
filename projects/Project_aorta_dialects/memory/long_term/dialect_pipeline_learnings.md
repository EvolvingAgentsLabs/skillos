---
timestamp: 2026-04-12
project: Project_aorta_dialects
type: consolidated_learnings
---

# Dialect Pipeline Learnings — Project Aorta

## Key Findings

1. **Dialect handoff works**: caveman-prose output from Stage 1 was successfully consumed by Stage 2 mathematician without information loss. Compressed input → formal proofs preserved all necessary scientific content.

2. **formal-proof forces rigor**: GIVEN/DERIVE/QED notation with [BY rule] annotations produced mathematically complete derivation chains. No hidden assumptions — every step cited its inference rule.

3. **system-dynamics reveals feedback**: Stock-flow notation made arterial hemodynamic loops explicit. The measurement-collapse balancing loop [FB-] and confidence-model reinforcing loop [FB+] would have been described vaguely in prose.

4. **exec-plan notation is effective for state tracking**: Pipeline state compressed to ~15 lines using exec-plan notation, replacing what would be ~100+ lines of verbose status reporting.

5. **No-dialect for code is correct**: Quantum implementation benefits from verbose, documented Python. Compression of executable code would reduce readability and debuggability.

## Dialect Compression Observations

| Artifact | Dialect | Approx Compression |
|----------|---------|-------------------|
| Vision document | caveman-prose | ~45-50% vs verbose |
| Math framework | formal-proof + system-dynamics | ~60-65% vs prose |
| Pipeline state | exec-plan | ~85% vs verbose |
| Python code | none | 0% (by design) |

## Patterns for Future Scenarios

- **Sequential pipelines with dialect stages**: Each agent reads compressed input from prior stage. Works well when downstream agent has domain expertise to expand compressed notation.
- **Mixed dialect documents**: Section 3 and Section 7 of math framework used system-dynamics within a predominantly formal-proof document. Clear section headers prevent confusion.
- **Quantum simulation without qiskit**: numpy-only QFT matrix construction works for proof-of-concept. Explicit unitary matrices make the quantum operations transparent for validation.

## Reusable Components

- `visionary-agent` + caveman-prose → good for any research concept compression
- `mathematician-agent` + formal-proof → good for any derivation-heavy task
- `system-dynamics` → good for any system with feedback loops (not just hemodynamics)
- Quantum cepstral pipeline → reusable for any echo detection / signal separation task
