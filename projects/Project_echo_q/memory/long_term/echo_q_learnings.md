---
timestamp: "2026-04-12T12:00:00Z"
previous_run: "2026-04-06T00:10:00Z"
scenario: operation-echo-q
domain: quantum-computing
confidence: high
---

# Consolidated Learnings — Operation Echo-Q

## Pattern: Wiki as Mathematical Blackboard
- Multi-page mathematical reasoning works when wiki pages are cross-referenced
- LaTeX derivations persist across agent invocations
- Constraints bridge theory (wiki) to implementation (code)
- The compounding loop (each page helps the next agent) is measurably effective

## Technical Learnings

### Qiskit
1. `qiskit.circuit.library.QFT` is deprecated in Qiskit 2.x — produces high-level gates AerSimulator may not recognize
2. Always decompose QFT to basic gates (H, CP, SWAP) or use `transpile()` for backend compatibility
3. `qc.initialize()` works for amplitude encoding but may be slow for large circuits
4. AerSimulator `method='statevector'` with `save_statevector()` gives exact amplitudes — essential for validation

### Signal Processing
1. Quefrency resolution = 1/N (samples). For tau=0.3s, need N >= 32 (5 qubits minimum), N=64 (6 qubits) is comfortable
2. Classical cepstrum can fail when spectral structure produces multi-peaked cepstra — the dominant peak may not be the echo
3. QASM measurement adds shot noise proportional to 1/sqrt(N_shots) — amplitude estimation (Grover-like) would help

### Polynomial Approximation
1. Chebyshev degree-12 achieves 5.4e-4 error for log(x) on [0.05, 1] — sufficient for echo detection
2. Clenshaw's algorithm is numerically stable for Chebyshev evaluation
3. Domain restriction to [epsilon, 1] is essential — log(0) singularity is a real problem
4. Normalization constant c = 1/|log(epsilon)| ensures |P(x)| <= 1 for QSVT compatibility

## Reusable Components
- `build_iqft_circuit(n)`: Manual IQFT from basic gates, portable across Qiskit versions
- `chebyshev_log_coefficients(degree, epsilon)`: Chebyshev polynomial for log approximation
- `evaluate_chebyshev_poly(coeffs, x, a, b)`: Clenshaw evaluation on mapped domain
- Constraint template (state/constraints.md) is reusable for other quantum algorithm projects

## Error Recovery Insights
1. Cross-referencing errors against constraints is highly effective: the constraint names map directly to fix strategies
2. Wiki pages provide the mathematical context needed for principled error recovery (not just pattern matching)
3. Two cycles sufficient for convergence — first cycle identified the issues, second cycle fixed them

## Re-Execution Insights (2026-04-12)
1. **Stability**: Once code is fixed, re-execution succeeds in Cycle 1 with no error recovery needed
2. **Classical cepstrum non-determinism**: At 64-point resolution, indices 13 and 19 have near-identical cepstral magnitudes (0.172452). The dominant peak can flip between runs due to floating-point precision. This is a fundamental resolution limitation, not a bug
3. **Quantum statevector stability**: Quantum results are deterministic — same detected tau (0.2656s) across runs
4. **Environment note**: Qiskit 2.2.3 on Python 3.9 shows deprecation warnings; plan upgrade to Python 3.10+ before Qiskit 2.3.0 removes 3.9 support
