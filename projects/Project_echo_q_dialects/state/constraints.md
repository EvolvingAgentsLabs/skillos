# Mathematical Invariants — Operation Echo-Q (Dialect Mode)

## Hard Constraints

C[1][H] Unitarity
  pred: ∀ U ∈ gates(circuit): U†U = I
  impl: log(·) cannot be applied directly as a gate → {QSVT_poly | LCU_taylor}
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

C[6][H] Domain-Restriction
  pred: x ∈ [ε, 1], ε > 0
  impl: log(0) = -∞; must clip magnitudes below ε before QSVT
  wiki: [[homomorphic-signal-separation]], [[quantum-singular-value-transformation]]

## Soft Constraints

S[1][M] Error-Budget
  pred: ε_total < 10⁻³
  impl: Polynomial degree d must be large enough for approximation accuracy
  wiki: [[quantum-singular-value-transformation]]

S[2][M] Qubit-Economy
  pred: qubits ≤ 2n + O(log n)
  impl: Minimize block-encoding ancilla count
  wiki: [[block-encoding]]

S[3][L] Measurement-Strategy
  pred: method = amplitude_estimation
  impl: O(1/ε) queries vs O(1/ε²) naive sampling
  wiki: [[cepstral-analysis]]

S[4][M] Test-Signal-Fidelity
  pred: |τ̂ - 0.3| < 0.05
  impl: Detected echo must match expected delay within threshold
  wiki: [[cepstral-analysis]]
