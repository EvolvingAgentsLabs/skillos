---
concept: Quantum Singular Value Transformation
type: concept
domain: quantum-computing
dialect: formal-proof
related: [[block-encoding]], [[homomorphic-signal-separation]], [[quantum-fourier-transform]]
sources: [[entities/grand-unification-of-quantum-algorithms]]
---

# Quantum Singular Value Transformation (QSVT)

## Definition

QSVT applies a polynomial transformation P to the singular values of a block-encoded matrix A:

$$A = \sum_i \sigma_i |w_i\rangle\langle v_i| \;\;\Longrightarrow\;\; P^{(SV)}(A) = \sum_i P(\sigma_i) |w_i\rangle\langle v_i|$$

where P is specified by a sequence of phase angles (phi_0, phi_1, ..., phi_d) and realized via alternating applications of the block-encoding unitary and single-qubit phase rotations.

## Key Properties

| Property | Value |
|---|---|
| Universality | Any bounded polynomial P: [-1,1] -> [-1,1] achievable |
| Optimality | Degree-d polynomial requires exactly d queries to U_A |
| Phase angles | Sequence (phi_0, ..., phi_d) fully determines P |
| Composability | QSVT circuits compose: P1 composed with P2 via sequential application |
| Parity | Even-d -> even polynomial; odd-d -> odd polynomial |

## How It Works

### Signal Processing Convention

```
GIVEN:
  G1. Single-qubit signal rotation: U_signal(theta) = [[cos(theta), sin(theta)], [-sin(theta), cos(theta)]]
  G2. Signal processing phase: U_phi = [[e^{i phi}, 0], [0, e^{-i phi}]]
  G3. Alternating product: U_QSVT = U_{phi_0} . prod_{j=1}^{d} (U_signal(theta) . U_{phi_j})
DERIVE:
  D1. For d applications, the (0,0) entry of U_QSVT is a degree-d polynomial in cos(theta) [BY G1, G2, G3, Chebyshev composition]
  D2. The polynomial is P(cos(theta)) where P is determined by phases {phi_j} [BY D1]
  D3. |P(x)| <= 1 for all x in [-1,1] [BY unitarity of U_QSVT]
QED: QSVT realizes any bounded polynomial of degree d via d signal rotations and d+1 phases.
```

### Extension to Block-Encoded Matrices

```
GIVEN:
  G1. U_A is an (alpha, a, epsilon)-block-encoding of A (see [[block-encoding]])
  G2. A has singular value decomposition A = sum_i sigma_i |w_i><v_i|
  G3. Phase sequence (phi_0, ..., phi_d) defines polynomial P of degree d
DERIVE:
  D1. Each sigma_i plays the role of cos(theta_i) in the signal processing convention [BY G1, G2]
  D2. QSVT circuit applies P independently to each sigma_i [BY D1, G3]
  D3. Result: P^{(SV)}(A) = sum_i P(sigma_i) |w_i><v_i| [BY D2]
  D4. Total query complexity = d calls to U_A and U_A† [BY circuit structure]
QED: QSVT transforms singular values of block-encoded A via polynomial P using d queries.
```

### Polynomial Approximation of Logarithm (Echo-Q Application)

In the Echo-Q pipeline, QSVT implements the logarithm step of [[cepstral-analysis]] by approximating log(x) with a bounded polynomial.

```
GIVEN:
  G1. Target function: f(x) = log(x) on domain [epsilon, 1], with epsilon > 0
  G2. Normalization: c = 1/|log(epsilon)| so that c . log(x) in [-1, 0] for x in [epsilon, 1]
  G3. Polynomial approximation: ||P_d(x) - c . log(x)||_inf <= epsilon_approx on [epsilon, 1]
  G4. Chebyshev approximation theory for log on shifted/scaled intervals
DERIVE:
  D1. c . log(x) maps [epsilon, 1] -> [-1, 0] subset [-1, 1] [BY G1, G2]
  D2. Polynomial degree bound: d = O((1/epsilon_approx) . log(1/epsilon_domain)) [BY G4, Jackson's theorem variant]
  D3. Phase angles (phi_0, ..., phi_d) exist realizing P_d via QSVT [BY D2, QSVT universality from above]
  D4. The non-unitarity of log is resolved: P_d is a bounded polynomial [BY D3, |P_d(x)| <= 1]
QED: QSVT approximates c . log(x) to precision epsilon_approx using O((1/epsilon_approx) . log(1/epsilon_domain)) queries.
```

This resolves the central challenge identified in [[homomorphic-signal-separation]]: the logarithm is non-unitary but QSVT sidesteps this via polynomial approximation.

## Complexity

- **Query complexity**: d calls to U_A (optimal for degree-d polynomial)
- **Gate complexity**: O(d . C_{U_A}) where C_{U_A} is the gate cost of one call to U_A
- **Classical pre-processing**: Computing phase angles from target polynomial is O(poly(d))

## Related Concepts

- [[block-encoding]]: Provides the input format U_A that QSVT operates on
- [[homomorphic-signal-separation]]: QSVT resolves the non-unitarity problem of the log step
- [[quantum-fourier-transform]]: Precedes block-encoding in the Echo-Q pipeline
- [[cepstral-analysis]]: QSVT implements the log step of the cepstral pipeline

## Open Questions

1. What are the optimal phase angles for log-approximation at practically relevant precision levels?
2. Can QSVT polynomial degree be reduced for the specific spectral structure of echo signals?
3. How do phase-angle computation errors propagate to the final cepstral output?
