---
concept: Block Encoding
type: concept
domain: quantum-computing
dialect: formal-proof
related: [[quantum-singular-value-transformation]], [[homomorphic-signal-separation]], [[quantum-fourier-transform]]
sources: [[entities/grand-unification-of-quantum-algorithms]]
---

# Block Encoding

## Definition

A unitary U_A is an (alpha, a, epsilon)-block-encoding of matrix A if:

$$(\langle 0|^a \otimes I) \, U_A \, (|0\rangle^a \otimes I) = A/\alpha$$

up to error epsilon in operator norm. Here alpha >= ||A|| is the subnormalization factor and a is the number of ancilla qubits.

Equivalently, A/alpha is embedded as the top-left block of the larger unitary U_A.

## Key Properties

| Property | Value |
|---|---|
| Universality | Any matrix with ||A|| <= alpha can be block-encoded |
| Unitarity | U_A is unitary; A/alpha need not be |
| Subnormalization | alpha >= ||A||; controls success probability ~ 1/alpha^2 |
| Ancilla cost | a qubits of overhead |
| Composability | Block-encodings compose via multiplication and addition |

## How It Works

### LCU (Linear Combination of Unitaries) Construction

```
GIVEN:
  G1. A = sum_{j=0}^{L-1} c_j V_j where V_j are unitaries and c_j >= 0
  G2. alpha = sum_j c_j (1-norm of coefficients)
  G3. Prepare oracle: PREP|0⟩ = sum_j sqrt(c_j / alpha) |j⟩
  G4. Select oracle: SEL|j⟩|psi⟩ = |j⟩ V_j|psi⟩
DERIVE:
  D1. U_A = PREP† . SEL . PREP [BY G3, G4, LCU lemma]
  D2. (⟨0|^a tensor I) U_A (|0⟩^a tensor I) = (1/alpha) sum_j c_j V_j = A/alpha [BY D1, G1, G2]
  D3. U_A is unitary since PREP and SEL are unitary [BY unitarity closure]
QED: LCU yields an (alpha, a, 0)-block-encoding of A with alpha = sum_j c_j.
```

### QSVT-Compatible Encoding

```
GIVEN:
  G1. U_A is an (alpha, a, epsilon)-block-encoding of A
  G2. QSVT requires interleaved applications of U_A and U_A† with phase rotations
  G3. Signal subspace: span of (|0⟩^a tensor |v_i⟩) for right singular vectors v_i of A
DERIVE:
  D1. In the signal subspace, U_A acts as rotation by arccos(sigma_i / alpha) [BY G1, SVD of A]
  D2. U_A† acts as the inverse rotation [BY unitarity, D1]
  D3. Alternating U_A, U_A† with phase gates realizes QSVT polynomial on {sigma_i / alpha} [BY D1, D2, G2]
QED: Block-encoding provides the signal-rotation structure QSVT requires.
```

### Composition Rules

```
GIVEN:
  G1. U_A is (alpha, a, epsilon_A)-block-encoding of A
  G2. U_B is (beta, b, epsilon_B)-block-encoding of B
DERIVE:
  D1. Product: exists (alpha . beta, a+b, alpha . epsilon_B + beta . epsilon_A)-block-encoding of A . B [BY sequential application]
  D2. Sum: exists (alpha + beta, a+1, epsilon_A + epsilon_B)-block-encoding of A + B [BY controlled selection + LCU]
  D3. Scalar: (c . alpha, a, c . epsilon_A)-block-encoding of c . A for c > 0 [BY rescaling PREP]
QED: Block-encodings are closed under product, sum, and scalar multiplication.
```

### Echo-Q Pipeline Integration

The full Echo-Q pipeline chains block-encoding with other quantum primitives:

```
GIVEN:
  G1. Signal s(t) loaded into quantum state |s⟩ via amplitude encoding
  G2. QFT maps |s⟩ to frequency-domain state |S(omega)⟩ (see [[quantum-fourier-transform]])
  G3. Spectral magnitudes |S(omega)| must be block-encoded for QSVT processing
DERIVE:
  D1. Construct diagonal unitary D_S with |S(omega)|/alpha on diagonal [BY G2, G3, amplitude encoding]
  D2. D_S is a (alpha, 0, epsilon)-block-encoding of diag(|S(omega)|) [BY D1, definition]
  D3. QSVT applies P_log approximating log to singular values of D_S [BY D2, [[quantum-singular-value-transformation]]]
  D4. IQFT (inverse QFT) maps result back to quefrency domain [BY [[quantum-fourier-transform]]]
QED: Pipeline is QFT -> block-encode -> QSVT(P_log) -> IQFT, yielding quantum cepstrum.
```

## Related Concepts

- [[quantum-singular-value-transformation]]: Operates on block-encoded matrices to apply polynomial transformations
- [[homomorphic-signal-separation]]: Block-encoding enables the non-unitary log to be implemented via QSVT
- [[quantum-fourier-transform]]: Produces the frequency-domain state that gets block-encoded
- [[cepstral-analysis]]: Block-encoding bridges the QFT and QSVT stages of the cepstral pipeline

## Open Questions

1. What is the optimal subnormalization factor alpha for echo signal spectra?
2. Can structured sparsity of echo spectra reduce ancilla overhead?
3. How does block-encoding error epsilon propagate through the QSVT polynomial?
