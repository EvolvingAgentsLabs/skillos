---
concept: Quantum Fourier Transform
type: concept
domain: quantum-computing
dialect: formal-proof
related: [[cepstral-analysis]], [[block-encoding]], [[homomorphic-signal-separation]]
sources: [[entities/grand-unification-of-quantum-algorithms]]
---

# Quantum Fourier Transform (QFT)

## Definition

The QFT maps computational basis states to frequency basis states:

$$\text{QFT}|j\rangle = \frac{1}{\sqrt{N}} \sum_{k=0}^{N-1} e^{2\pi i j k / N} |k\rangle, \quad N = 2^n$$

This is the quantum analogue of the classical Discrete Fourier Transform, acting on amplitudes of a quantum state rather than on classical data vectors.

## Key Properties

| Property | Value |
|---|---|
| Unitarity | QFT† . QFT = I |
| Gate complexity | O(n^2) |
| Circuit depth | O(n^2) ; O(n log n) with approximate decomposition |
| Inverse | Reverse gate order + conjugate all phases |
| Input/Output | n-qubit computational basis <-> frequency basis |

## How It Works

### Circuit Construction

```
GIVEN:
  G1. H gate on qubit j: |0⟩ -> (|0⟩+|1⟩)/sqrt(2), |1⟩ -> (|0⟩-|1⟩)/sqrt(2)
  G2. Controlled-R_k gate: |1⟩ -> e^{2 pi i / 2^k} |1⟩ on target, conditioned on control=|1⟩
  G3. n-qubit register, qubits indexed 1..n
DERIVE:
  D1. Qubit j requires 1 Hadamard + (n-j) controlled rotations [BY G1, G2]
  D2. Total gates = sum_{j=1}^{n} (1 + (n-j)) = n + n(n-1)/2 = n(n+1)/2 [BY D1, arithmetic]
  D3. n(n+1)/2 = O(n^2) [BY D2, asymptotic bound]
  D4. Final SWAP layer requires floor(n/2) gates [BY bit-reversal requirement]
  D5. Total = O(n^2) + O(n) = O(n^2) [BY D3, D4]
QED: QFT circuit uses O(n^2) gates on n qubits.
```

### Product Representation

```
GIVEN:
  G1. QFT|j⟩ = (1/sqrt(N)) tensor_{l=1}^{n} (|0⟩ + e^{2 pi i j / 2^l} |1⟩)
  G2. j = j_1 j_2 ... j_n in binary
DERIVE:
  D1. Each qubit l in the output depends only on bits j_l, j_{l+1}, ..., j_n [BY G1, G2]
  D2. The state factors as a tensor product of n single-qubit states [BY D1]
  D3. Each factor is produced by 1 Hadamard + controlled rotations on qubit l [BY D2, circuit structure]
QED: QFT admits an efficient tensor-product factorization enabling the O(n^2) circuit.
```

### Classical vs. Quantum Comparison

| | Classical FFT | Quantum QFT |
|---|---|---|
| Input size | N = 2^n values | n qubits |
| Operations | O(N log N) = O(n . 2^n) | O(n^2) = O((log N)^2) |
| Output | Explicit frequency values | Amplitudes (not directly readable) |
| Readout | Direct | Requires measurement / amplitude estimation |

## Critical Caveat

The exponential speedup of QFT over FFT in gate count is real, but the result is encoded in quantum amplitudes. Direct measurement yields only a single sampled outcome. Extracting full spectral information requires amplitude estimation or repeated sampling, which partially offsets the gate-count advantage. In [[cepstral-analysis]], QFT serves as a subroutine inside a larger pipeline where this limitation is managed via [[block-encoding]] and QSVT polynomial processing.

## Related Concepts

- [[cepstral-analysis]]: QFT implements the FFT and IFFT steps of the cepstral pipeline
- [[block-encoding]]: QFT output is block-encoded before QSVT polynomial application
- [[homomorphic-signal-separation]]: QFT enables the frequency-domain transformation that makes homomorphic separation possible
- [[quantum-singular-value-transformation]]: Processes block-encoded QFT output via polynomial transformations

## Open Questions

1. Can approximate QFT (O(n log n) gates) maintain sufficient fidelity for Echo-Q cepstral pipelines?
2. What is the optimal trade-off between QFT precision and QSVT polynomial degree in the Echo-Q pipeline?
3. How does QFT error propagate through the block-encoding and QSVT stages?
