# Mathematical Invariants — Operation Echo-Q

## Hard Constraints (MUST NOT violate)

### C1: Unitarity
All quantum operations MUST be unitary: $U^\dagger U = I$.
**Implication**: The $\log(\cdot)$ function cannot be applied directly as a gate. It must be implemented via block-encoding + QSVT polynomial approximation or LCU Taylor series, both of which embed the non-unitary operation within a larger unitary circuit.
**Wiki ref**: [[homomorphic-signal-separation]] (Section: The Non-Unitarity Problem), [[block-encoding]] (Section: Definition), [[quantum-singular-value-transformation]] (Section: Extension to Block-Encoded Matrices)

### C2: No-Cloning
No quantum state may be copied: the no-cloning theorem prohibits $|\psi\rangle \to |\psi\rangle|\psi\rangle$.
**Implication**: Intermediate quantum states (e.g., the QFT output) cannot be duplicated for classical post-processing. The pipeline must be fully coherent from state preparation through measurement, or accept the cost of re-preparation.
**Wiki ref**: [[quantum-fourier-transform]] (Section: No amplitude readout)

### C3: Logarithm Approximation Method
The $\log(\cdot)$ approximation MUST use one of:
  (a) **QSVT polynomial encoding**: approximate $\log(x)$ by a degree-$d$ polynomial $P_d(x)$ satisfying $|P_d(x)| \leq 1$ for $x \in [0,1]$, with domain restricted to $[\epsilon, 1]$ to avoid the singularity at zero, OR
  (b) **Taylor series block-encoding (LCU)**: encode $\log(1+x) = x - x^2/2 + x^3/3 - \cdots$ truncated to $K$ terms as a linear combination of unitaries.
No other method satisfies C1 within a fully quantum pipeline.
**Wiki ref**: [[quantum-singular-value-transformation]] (Section: Polynomial Approximation of Logarithm), [[block-encoding]] (Section: Construction 1: LCU), [[homomorphic-signal-separation]] (Section: Resolution Strategies)

### C4: Polynomial Circuit Depth
Circuit depth MUST remain polynomial in qubit count $n$: $\text{depth} = O(\text{poly}(n))$.
**Implication**: Exponential-depth constructions are physically unrealizable. The QSVT polynomial degree $d$ must be at most polynomial in $n$ and $1/\epsilon$. The total circuit depth is $O(d \cdot C_{U_D})$ where $C_{U_D}$ is the gate complexity of the block-encoding unitary.
**Wiki ref**: [[quantum-singular-value-transformation]] (Section: Complexity), [[block-encoding]] (Section: Composition Rules)

### C5: Normalization
Quantum state amplitudes MUST satisfy $\sum_i |a_i|^2 = 1$.
**Implication**: The signal encoding step must normalize input amplitudes: $|ψ\rangle = (1/\|s\|) \sum_k s[k]|k\rangle$. Block-encoding introduces a subnormalization factor $\alpha \geq \|A\|$, so the effective operation is $A/\alpha$ rather than $A$. The final cepstral coefficients must be rescaled by $\alpha$ to recover physical units.
**Wiki ref**: [[block-encoding]] (Section: Subnormalization), [[cepstral-analysis]] (Section: The Three-Step Pipeline)

### C6: Domain Restriction for Logarithm
The polynomial approximation of $\log(x)$ MUST operate on the restricted domain $[\epsilon, 1]$ where $\epsilon > 0$.
**Implication**: Frequency amplitudes below $\epsilon$ must be clipped or regularized before the QSVT step. The normalization constant $c = 1/|\log(\epsilon)|$ ensures $|P_d(x)| \leq 1$.
**Wiki ref**: [[homomorphic-signal-separation]] (Section: Strategy A, point 1-2), [[quantum-singular-value-transformation]] (Section: Polynomial Approximation of Logarithm)

## Soft Constraints (SHOULD satisfy)

### S1: Error Budget
Total approximation error from polynomial truncation SHOULD satisfy $\epsilon_{\text{approx}} < 10^{-3}$.
**Implication**: The QSVT polynomial degree $d$ must be large enough that $\|P_d(x) - c\log(x)\|_\infty < 10^{-3}$ on $[\epsilon, 1]$.
**Wiki ref**: [[quantum-singular-value-transformation]] (Section: Polynomial Approximation of Logarithm, point 4)

### S2: Qubit Economy
Implementation SHOULD use $\leq 2n + O(\log n)$ qubits for an $n$-point signal (where the signal has $N = 2^n$ samples).
**Implication**: The block-encoding ancilla count should be minimized. QSVT typically adds only 1-2 ancilla qubits beyond what the block-encoding requires.
**Wiki ref**: [[block-encoding]] (Section: Open Questions), [[quantum-singular-value-transformation]] (Section: Complexity)

### S3: Measurement Strategy
Final measurement SHOULD use amplitude estimation rather than naive sampling to extract cepstral peaks with $O(1/\epsilon)$ queries rather than $O(1/\epsilon^2)$.
**Implication**: Post-QFT$^\dagger$ measurement benefits from Grover-like amplitude amplification if the cepstral peak amplitude is small.
**Wiki ref**: [[quantum-fourier-transform]] (Section: Comparison with Classical FFT), [[block-encoding]] (Section: Success probability)

### S4: Test Signal Fidelity
The synthetic test signal SHOULD match the specification: $s(t) = \sin(2\pi \cdot 5 \cdot t) + 0.6 \cdot \sin(2\pi \cdot 5 \cdot (t - 0.3))$ with expected echo at quefrency $\tau = 0.3$.
**Implication**: The detected peak $\hat{\tau}$ should satisfy $|\hat{\tau} - 0.3| < 0.05$.
**Wiki ref**: [[cepstral-analysis]] (Section: Test Signal Specification)
