---
project: Project_echo_q_dialects
created: 2026-04-12
type: long-term-learnings
---

# Learnings — Operation Echo-Q (Dialects)

## What Worked

1. **Formal-proof dialect preserves mathematical rigor**: 13 GIVEN/DERIVE/QED blocks maintained all logical structure while eliminating prose filler. The [BY rule] annotations force explicit reasoning chains.

2. **Constraint-dsl achieves highest compression**: 65% reduction (5,119 → 1,796 bytes). The structured pred/impl/wiki format is more machine-parseable than the original prose.

3. **Parallel Phase execution**: Running Phase 1 (wiki) and Phase 2 (constraints) in parallel halved wall-clock time for the theory stages.

4. **Reusing validated code patterns**: Phase 3 succeeded on Cycle 1 because the Qiskit code was pre-validated from the original Echo-Q run. No error recovery loop needed.

5. **Dialect expansion for output**: Converting formal-proof back to prose for the whitepaper works well. The structured input makes expansion systematic.

## What Could Improve

1. **Wiki derivation compression was 13% not 50%**: The non-derivation sections (definitions, tables, properties) are already concise. Only the "How It Works" derivation sections show ~50% reduction. Overall page reduction is more modest because formal-proof blocks are a fraction of total content.

2. **QASM measurement remains noisy**: At 6 qubits, direct measurement has nearly uniform probability distribution. Amplitude estimation (S[3]) would fix this but is outside the current implementation scope.

3. **Dialect awareness in code comments**: The Python code references constraint-dsl notation (C[1][H] instead of C1) which is cleaner but requires readers to understand the notation.

## Patterns for Future Scenarios

- **Best dialect candidates**: Constraints and state files show highest compression (60-80%). Wiki derivation sections show moderate compression (~50%). Code and human-facing outputs should NOT be compressed.
- **Formal-proof improves reasoning quality**: The requirement for [BY rule] annotations catches hidden assumptions that prose derivations would skip.
- **Constraint-dsl enables automated verification**: The structured pred/impl/wiki format could be machine-parsed for constraint checking.
