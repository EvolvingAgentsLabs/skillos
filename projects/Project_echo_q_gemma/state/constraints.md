# Mathematical Invariants — Operation Echo-Q

## Hard Constraints (MUST NOT violate)

### C1: Unitarity
All quantum operations MUST be unitary: $U^\dagger U = I$.
**Implication**: The $\log(\cdot)$ function cannot be applied directly as a gate.
**Wiki ref**: [[homomorphic-signal-separation]], [[block-encoding]]

### C2: No-Cloning
No quantum state may be copied: the no-cloning theorem prohibits $|\psi\rangle \to |\psi\rangle|\psi\rangle$.
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
Final measurement SHOULD use amplitude estimation rather than naive sampling.