---
concept: Homomorphic Signal Separation
type: concept
domain: quantum-computing
related: [[cepstral-analysis]], [[quantum-singular-value-transformation]], [[block-encoding]], [[quantum-fourier-transform]]
sources: [[entities/grand-unification-of-quantum-algorithms]]
skills: [knowledge-query-agent]
last_updated: "2026-04-06T00:05:00Z"
---

# Homomorphic Signal Separation

## Definition

Homomorphic signal separation is a technique that converts a **multiplicative** combination of signals into an **additive** combination via a logarithmic nonlinearity, enabling linear filtering to separate the components. For a signal $s(t) = p(t) * h(t)$ (convolution), the frequency domain gives $S(\omega) = P(\omega) \cdot H(\omega)$ (multiplication), and the logarithm yields $\log S(\omega) = \log P(\omega) + \log H(\omega)$ (addition).

This is the mathematical core of [[cepstral-analysis]] and the central challenge of the Echo-Q quantum algorithm.

## Key Properties

- **Multiplicative → Additive**: $\log(A \cdot B) = \log A + \log B$ enables linear separation of convolved components
- **Domain requirement**: The logarithm requires $|S(\omega)| > 0$ everywhere — spectral nulls cause singularities
- **Spectral envelope separation**: Slowly-varying components (source) separate from rapidly-varying components (channel/echo) in the cepstral domain
- **Invertibility**: The process is invertible via $\exp(\cdot)$ followed by inverse FFT

## The Non-Unitarity Problem

**This is the central theoretical obstacle of Operation Echo-Q.**

The logarithm $\log(\cdot)$ is fundamentally incompatible with quantum computing because:

### Problem 1: Non-Linearity
Quantum mechanics is **linear**: if $U|a\rangle = |b\rangle$ and $U|c\rangle = |d\rangle$, then $U(\alpha|a\rangle + \beta|c\rangle) = \alpha|b\rangle + \beta|d\rangle$. The logarithm violates this:

$$\log(\alpha x + \beta y) \neq \alpha \log(x) + \beta \log(y)$$

Therefore, $\log(\cdot)$ **cannot be implemented as a quantum gate** acting on superposition states in the standard sense.

### Problem 2: Non-Unitarity
All quantum gates must be unitary: $U^\dagger U = I$, preserving the $\ell_2$ norm of the state vector. The logarithm is not norm-preserving:

$$\|\log(\mathbf{x})\|_2 \neq \|\mathbf{x}\|_2 \quad \text{in general}$$

A non-unitary transformation cannot be applied directly as a quantum gate.

### Problem 3: Singularity at Zero
$\log(0) = -\infty$. Any quantum state with zero-amplitude components would produce undefined values. Since quantum states generically have components near zero, this is not an edge case — it is the typical situation.

## Resolution Strategies

The wiki identifies two viable approaches, both rooted in the [[quantum-singular-value-transformation]] + [[block-encoding]] framework:

### Strategy A: QSVT Polynomial Approximation (Preferred)

1. **Block-encode** the diagonal matrix of frequency amplitudes $D = \text{diag}(|\Psi_0|, |\Psi_1|, \ldots, |\Psi_{N-1}|)$ using [[block-encoding]] Construction 2
2. **Construct polynomial** $P_d(x) \approx c \cdot \log(x)$ on the restricted domain $[\epsilon, 1]$:
   - Normalization: $c = 1/|\log(\epsilon)|$
   - Degree: $d = O(\frac{1}{\delta}\log\frac{1}{\epsilon})$ for $\delta$-approximation error
   - Constraint: $|P_d(x)| \leq 1$ for all $x \in [0, 1]$ (required by QSVT)
3. **Compute QSVT phase angles** $\boldsymbol{\phi} = (\phi_0, \ldots, \phi_d)$ classically
4. **Apply QSVT circuit**: $d$ alternating applications of $U_D$ and $U_D^\dagger$ with interleaved phase rotations
5. **Result**: Singular values (frequency amplitudes) transformed by $P_d(\cdot) \approx c \cdot \log(\cdot)$

**Advantages**: Fully quantum, no intermediate measurement, respects unitarity via block-encoding.

**Constraint satisfaction**:
- C1 (Unitarity): Satisfied — QSVT is unitary by construction
- C3 (Log approximation): Satisfied — uses QSVT polynomial
- C4 (Polynomial depth): Satisfied — circuit depth is $O(d \cdot C_{U_D})$

### Strategy B: Taylor Series Block-Encoding (LCU)

1. **Express** $\log(1 + x) = \sum_{k=1}^{K} \frac{(-1)^{k+1}}{k} x^k$ truncated to $K$ terms
2. **Block-encode** each term $x^k$ as a product of $k$ block-encodings of $x$
3. **Combine** via Linear Combination of Unitaries ([[block-encoding]] Construction 1):
   - PREPARE oracle: $|0\rangle \mapsto \sum_{k=1}^{K} \sqrt{\frac{1/k}{\sum_{j} 1/j}} |k\rangle$
   - SELECT oracle: $|k\rangle|\psi\rangle \mapsto |k\rangle x^k|\psi\rangle$
4. **Subnormalization**: $\alpha = \sum_{k=1}^{K} 1/k = H_K \approx \ln K + \gamma$

**Advantages**: Conceptually transparent, directly maps the Taylor formula.

**Disadvantages**: Higher subnormalization factor, deeper circuits for same accuracy.

### Strategy C: Hybrid Classical-Quantum (Fallback)

1. Perform QFT on quantum computer → obtain frequency-domain state
2. **Measure** all qubits → extract classical frequency amplitudes
3. Compute $\log|\cdot|$ classically (trivially)
4. **Re-encode** the log-amplitudes into a new quantum state
5. Apply inverse QFT quantumly

**Advantages**: Avoids the non-unitarity problem entirely.

**Disadvantages**: Measurement destroys quantum coherence, requires exponential repetitions for amplitude estimation, and re-encoding is $O(N)$.

**This strategy violates the spirit of a fully quantum algorithm** but may be useful as a validation baseline.

## The Full Quantum Cepstrum Pipeline

```
Classical signal s[k]
       │
       ▼
┌─────────────────┐
│ State Preparation│  Encode s[k] as amplitudes: |ψ⟩ = Σ s[k]|k⟩ / ‖s‖
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   QFT            │  |Ψ⟩ = QFT|ψ⟩ — frequency domain
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Block-Encode +   │  Apply P(x) ≈ c·log(x) via QSVT
│ QSVT Log         │  Resolves non-unitarity via polynomial approximation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   QFT†           │  |c⟩ = QFT†|log Ψ⟩ — cepstral domain
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Measurement     │  Extract cepstral peak at quefrency τ
└─────────────────┘
```

## Related Concepts

- [[cepstral-analysis]] — Homomorphic separation is the mathematical foundation of cepstral analysis; the log is the core operation that cepstral analysis relies on
- [[quantum-singular-value-transformation]] — QSVT provides Strategy A for implementing the logarithm as a polynomial transformation of singular values within a unitary framework
- [[block-encoding]] — Block encoding is the prerequisite for both Strategy A (QSVT) and Strategy B (LCU), enabling non-unitary operations within a unitary circuit
- [[quantum-fourier-transform]] — QFT provides the spectral representation that homomorphic separation operates on

## Open Questions

- What is the minimum $\epsilon$ (domain restriction lower bound) that preserves echo detection accuracy for the Echo-Q test signal?
- Can Strategy A and Strategy C be combined: use QSVT for an approximate log, then classical refinement?
- How does the choice of polynomial degree $d$ in QSVT affect the width and amplitude of the cepstral peak at $\tau$?
