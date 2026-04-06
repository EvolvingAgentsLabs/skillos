---
concept: Quantum Singular Value Transformation
type: concept
domain: quantum-computing
related: [[block-encoding]], [[homomorphic-signal-separation]], [[quantum-fourier-transform]]
sources: [[entities/grand-unification-of-quantum-algorithms]]
skills: [knowledge-query-agent]
last_updated: "2026-04-06T00:02:00Z"
---

# Quantum Singular Value Transformation (QSVT)

## Definition

Quantum Singular Value Transformation (QSVT) is a unified framework for applying polynomial transformations to the singular values of a block-encoded matrix. Given a block-encoding of a matrix $A$ with singular value decomposition $A = \sum_i \sigma_i |w_i\rangle\langle v_i|$, QSVT implements:

$$A \mapsto \sum_i P(\sigma_i) |w_i\rangle\langle v_i|$$

where $P(x)$ is a polynomial of degree $d$ satisfying $|P(x)| \leq 1$ for $x \in [-1, 1]$, using $d$ applications of the block-encoding and its inverse plus $d$ single-qubit phase rotations.

## Key Properties

- **Universality**: QSVT can implement any bounded polynomial transformation of singular values, unifying Hamiltonian simulation, amplitude amplification, quantum linear algebra, and more.
- **Optimality**: Uses exactly $d$ queries to the block-encoding for a degree-$d$ polynomial — this is query-optimal.
- **Phase angles**: The transformation is parameterized by a sequence of phase angles $\boldsymbol{\phi} = (\phi_0, \phi_1, \ldots, \phi_d) \in \mathbb{R}^{d+1}$. Finding these angles is a classical preprocessing step.
- **Composability**: QSVT polynomials can be composed: if $P$ and $Q$ are achievable, so is $P \circ Q$ (with degree multiplication).
- **Parity constraint**: QSVT naturally implements polynomials of definite parity — even or odd polynomials depending on the convention.

## How It Works

### The Signal Processing Convention

QSVT operates in the "signal processing" or "QSP" convention. For a single-qubit signal operator $W(\theta)$ parameterized by angle $\theta$ (where $\cos\theta = x$ is the "signal"):

$$U_{\boldsymbol{\phi}}(\theta) = e^{i\phi_0 Z} \prod_{k=1}^{d} \left[ W(\theta) \cdot e^{i\phi_k Z} \right]$$

The $(0,0)$ block of this unitary equals $P(\cos\theta)$ where $P$ is a degree-$d$ polynomial determined by the phases $\boldsymbol{\phi}$.

### Extension to Block-Encoded Matrices

For a matrix $A$ with block-encoding $U_A$ (so that $(\langle 0| \otimes I) U_A (|0\rangle \otimes I) = A$), QSVT constructs:

$$U_{\boldsymbol{\phi}} = e^{i\phi_0 \Pi} \prod_{k=1}^{d} \left[ U_A^{(\dagger)^k} \cdot e^{i\phi_k \Pi} \right]$$

where $\Pi = (2|0\rangle\langle 0| - I) \otimes I$ is the projector-controlled phase, and $U_A^{(\dagger)^k}$ alternates between $U_A$ and $U_A^\dagger$.

The result: the singular values $\sigma_i$ of $A$ are each independently transformed by $P(\sigma_i)$.

### Polynomial Approximation of Logarithm

For Echo-Q, we need $P(x) \approx c \cdot \log(x)$ on $[\epsilon, 1]$ where $c$ is a normalization constant ensuring $|P(x)| \leq 1$. The construction:

1. **Domain restriction**: Work on $x \in [\epsilon, 1]$ to avoid the singularity at $x = 0$
2. **Normalization**: Set $c = 1 / |\log(\epsilon)|$ so $|c \cdot \log(x)| \leq 1$ on the domain
3. **Polynomial fit**: Find a degree-$d$ polynomial $P_d(x)$ that $\epsilon$-approximates $c \cdot \log(x)$ on $[\epsilon, 1]$
4. **Degree bound**: The required degree is $d = O(\frac{1}{\epsilon_{\text{approx}}} \log \frac{1}{\epsilon_{\text{domain}}})$
5. **Phase computation**: Use a classical algorithm (e.g., Prony's method or optimization) to find the QSVT phase angles $\boldsymbol{\phi}$

### Circuit Structure

```
|0⟩ ─── e^{iφ₀Z} ─── [U_A] ─── e^{iφ₁Z} ─── [U_A†] ─── e^{iφ₂Z} ─── ... ─── e^{iφ_dZ} ───
|ψ⟩ ─────────────── [    ] ──────────────── [     ] ──────────────── ... ──────────────────
```

Each application of $U_A$ or $U_A^\dagger$ costs one query. The single-qubit rotations $e^{i\phi_k Z}$ are essentially free.

### Complexity

- **Queries to $U_A$**: $d$ (the polynomial degree)
- **Ancilla qubits**: Same as block-encoding (typically 1-2 ancillas)
- **Classical preprocessing**: $O(d \cdot \text{poly}(\log d))$ for phase angle computation
- **Total quantum complexity**: $O(d \cdot C_{U_A})$ where $C_{U_A}$ is the gate complexity of $U_A$

## Related Concepts

- [[block-encoding]] — QSVT requires the input matrix to be block-encoded; the quality of this encoding directly affects the overall algorithm
- [[homomorphic-signal-separation]] — QSVT provides the mechanism to implement the non-unitary logarithm that homomorphic signal separation requires
- [[quantum-fourier-transform]] — In the Echo-Q pipeline, QFT precedes QSVT and QFT$^\dagger$ follows it

## Open Questions

- What is the minimum polynomial degree needed for the logarithm approximation to achieve $\epsilon < 10^{-3}$ error in the cepstral peak location?
- Can we compose the QFT and QSVT into a single optimized circuit, or must they remain separate stages?
- How do errors in the QSVT phase angle computation propagate to the final cepstral coefficients?
