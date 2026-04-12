---
concept: Homomorphic Signal Separation
type: concept
domain: quantum-computing
dialect: formal-proof
related: [[cepstral-analysis]], [[quantum-fourier-transform]], [[block-encoding]], [[quantum-singular-value-transformation]]
sources: [[entities/grand-unification-of-quantum-algorithms]]
---

# Homomorphic Signal Separation

## Definition

Homomorphic signal separation converts multiplicative signal combinations into additive ones via a logarithmic mapping, enabling linear techniques (filtering, separation) on originally non-linear mixtures:

$$s(t) = p(t) * h(t) \;\;\xrightarrow{\text{FFT}}\;\; S(\omega) = P(\omega) \cdot H(\omega) \;\;\xrightarrow{\log}\;\; \log S = \log P + \log H$$

where * denotes convolution and . denotes pointwise multiplication.

## The Non-Unitarity Problem (CRITICAL)

This is the central theoretical obstacle for quantum implementation of homomorphic separation.

```
GIVEN:
  G1. Quantum gates must be linear: U(alpha|a⟩ + beta|b⟩) = alpha U|a⟩ + beta U|b⟩
  G2. Quantum gates must be unitary: U† U = I (norm-preserving, invertible)
  G3. Logarithm is nonlinear: log(a + b) != log(a) + log(b)
  G4. Logarithm is non-norm-preserving: ||log(x)|| != ||x|| in general
  G5. Logarithm maps 0 -> -infinity (unbounded)
DERIVE:
  D1. log violates linearity [BY G1, G3]
  D2. log violates unitarity [BY G2, G4]
  D3. log is undefined/unbounded at zero [BY G5]
  D4. No unitary matrix U_log exists such that U_log|x⟩ = |log(x)⟩ [BY D1, D2, D3]
QED: Direct implementation of log(.) as a quantum gate is impossible.
```

This means the log step of [[cepstral-analysis]] cannot be naively quantized. Three resolution strategies exist.

## Resolution Strategies

### Strategy A: QSVT Polynomial Approximation (Primary)

```
GIVEN:
  G1. QSVT can apply any bounded polynomial P: [-1,1] -> [-1,1] to singular values (see [[quantum-singular-value-transformation]])
  G2. log(x) can be approximated by polynomial P_d(x) on [epsilon, 1] to error epsilon_approx
  G3. Normalization c = 1/|log(epsilon)| ensures c . log(x) in [-1, 0] subset [-1, 1]
  G4. Spectral magnitudes |S(omega)| are block-encoded via [[block-encoding]] with subnormalization alpha
DERIVE:
  D1. Singular values of block-encoded spectrum are sigma_i = |S(omega_i)| / alpha in [0, 1] [BY G4]
  D2. Restrict to sigma_i in [epsilon/alpha, 1] (discard near-zero components) [BY G3, numerical stability]
  D3. P_d approximates c . log(alpha . sigma_i) to precision epsilon_approx [BY G2, D2]
  D4. QSVT realizes P_d using d queries to block-encoding unitary [BY G1, D3]
  D5. d = O((1/epsilon_approx) . log(1/epsilon_domain)) [BY Chebyshev approximation theory]
  D6. P_d is a bounded polynomial -> unitarity of QSVT circuit is preserved [BY G1, |P_d| <= 1]
QED: QSVT resolves non-unitarity by replacing log with bounded polynomial approximation P_d.
```

### Strategy B: LCU Taylor Series

Expand log(1 + x) = x - x^2/2 + x^3/3 - ... as a Linear Combination of Unitaries:
- Each term x^k corresponds to k applications of the block-encoding unitary
- LCU framework (see [[block-encoding]]) combines terms with appropriate coefficients
- Truncation at degree d gives O(d) query complexity
- Less efficient than Strategy A for high precision but simpler to analyze

### Strategy C: Hybrid Classical-Quantum Fallback

- Perform QFT on quantum hardware for the O((log N)^2) speedup
- Measure spectral magnitudes via amplitude estimation
- Compute log classically
- Re-encode and perform IQFT on quantum hardware
- Trades away full quantum coherence for guaranteed correctness

## Full Pipeline Diagram

```
|s(t)⟩ --[QFT]--> |S(omega)⟩ --[block-encode]--> U_S --[QSVT(P_log)]--> |log|S|⟩ --[IQFT]--> |c(t_q)⟩
  ^                                                                                                 |
  |                     quantum-fourier-transform                                                   |
  |                                    block-encoding                                               |
  |                                              quantum-singular-value-transformation              |
  |                                                                            cepstral-analysis    |
  +--- input signal                                                            output cepstrum -----+
```

Each arrow corresponds to a quantum subroutine:
1. **QFT**: [[quantum-fourier-transform]] -- O((log N)^2) gates
2. **Block-encode**: [[block-encoding]] -- embeds spectrum into unitary
3. **QSVT(P_log)**: [[quantum-singular-value-transformation]] -- polynomial log approximation
4. **IQFT**: Inverse [[quantum-fourier-transform]] -- O((log N)^2) gates

## Key Properties

| Property | Value |
|---|---|
| Core operation | log converts multiplicative mixing to additive |
| Quantum obstacle | log is non-linear and non-unitary |
| Primary resolution | QSVT polynomial approximation (Strategy A) |
| Precision parameter | epsilon_approx controls polynomial degree |
| Domain restriction | [epsilon, 1]; values near 0 must be truncated |

## Related Concepts

- [[cepstral-analysis]]: Homomorphic separation is the theoretical foundation of cepstral processing
- [[quantum-fourier-transform]]: Provides the frequency-domain representation where multiplicative structure appears
- [[block-encoding]]: Embeds spectral magnitudes into unitary form for QSVT processing
- [[quantum-singular-value-transformation]]: Implements the polynomial log approximation that resolves non-unitarity

## Open Questions

1. What is the practical impact of the epsilon truncation (discarding near-zero spectral components) on echo detection?
2. Can the three strategies be composed -- e.g., QSVT for the bulk, LCU for boundary corrections?
3. Is there a quantum-native alternative to homomorphic separation that avoids the log entirely?
