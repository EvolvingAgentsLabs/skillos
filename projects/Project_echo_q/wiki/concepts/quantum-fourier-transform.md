---
concept: Quantum Fourier Transform
type: concept
domain: quantum-computing
related: [[cepstral-analysis]], [[block-encoding]], [[homomorphic-signal-separation]]
sources: [[entities/grand-unification-of-quantum-algorithms]]
skills: [knowledge-query-agent]
last_updated: "2026-04-06T00:01:00Z"
---

# Quantum Fourier Transform

## Definition

The Quantum Fourier Transform (QFT) is the quantum analogue of the discrete Fourier transform (DFT). Acting on an $n$-qubit computational basis state $|j\rangle$, it produces:

$$\text{QFT}|j\rangle = \frac{1}{\sqrt{N}} \sum_{k=0}^{N-1} e^{2\pi i j k / N} |k\rangle$$

where $N = 2^n$. The QFT is a **unitary** operation and can be implemented with $O(n^2) = O((\log N)^2)$ gates, providing an exponential speedup over the classical FFT's $O(N \log N)$ complexity.

## Key Properties

- **Unitarity**: $\text{QFT}^\dagger \cdot \text{QFT} = I$. The QFT is exactly unitary, no approximation needed.
- **Gate complexity**: $O(n^2)$ where $n = \log_2 N$ is the number of qubits. Uses Hadamard gates and controlled phase rotations $R_k = \text{diag}(1, e^{2\pi i / 2^k})$.
- **Circuit depth**: $O(n^2)$ in serial, $O(n \log n)$ with parallelization (approximate QFT).
- **Inverse**: $\text{QFT}^\dagger$ is obtained by reversing the circuit and conjugating all phases.
- **No amplitude readout**: QFT transforms amplitudes but does not directly reveal them — measurement collapses to a single basis state.

## How It Works

### Circuit Construction

For $n$ qubits, the QFT circuit applies:

1. **Hadamard** on qubit 1: creates superposition $\frac{1}{\sqrt{2}}(|0\rangle + e^{2\pi i \cdot 0.j_1}|1\rangle)$
2. **Controlled-$R_2$** from qubit 2 to qubit 1: adds phase $e^{2\pi i \cdot 0.j_1 j_2}$
3. Continue controlled rotations $R_3, R_4, \ldots, R_n$ on qubit 1
4. Repeat pattern for qubits 2 through $n$ with decreasing rotation counts
5. **Swap** qubits to reverse bit order

The total gate count is $\sum_{k=1}^{n} k = n(n+1)/2 = O(n^2)$.

### Product Representation

The QFT output state factors as a tensor product:

$$\text{QFT}|j\rangle = \frac{1}{\sqrt{N}} \bigotimes_{l=1}^{n} \left(|0\rangle + e^{2\pi i j / 2^l} |1\rangle\right)$$

This product form is what makes the efficient circuit possible — each qubit's state depends only on a subset of the input bits.

### Comparison with Classical FFT

| Property | Classical FFT | Quantum QFT |
|----------|--------------|-------------|
| Input | $N$ complex numbers | $n = \log_2 N$ qubits |
| Output | $N$ complex numbers (readable) | $n$ qubits (amplitudes not directly readable) |
| Complexity | $O(N \log N)$ | $O((\log N)^2)$ |
| Readout | Direct | Requires measurement or amplitude estimation |

**Critical caveat for Echo-Q**: The QFT speedup is real but the output amplitudes are encoded in quantum state amplitudes. Extracting individual frequency components requires additional techniques like **amplitude estimation** (see [[block-encoding]] for related constructions).

### Approximate QFT

For practical implementations, rotations $R_k$ with $k > m$ for some cutoff $m$ can be dropped. This yields an approximate QFT with:
- Gate count: $O(n \cdot m)$
- Error: $O(n \cdot 2^{-m})$

Setting $m = O(\log n)$ gives $O(n \log n)$ gates with polynomially small error — sufficient for most applications.

## Related Concepts

- [[cepstral-analysis]] — The QFT replaces the classical FFT as the first and last steps of cepstral analysis, providing exponential speedup for large signal arrays
- [[block-encoding]] — Block-encoding provides the framework to apply non-unitary operations (like the logarithm) between the QFT and inverse QFT steps
- [[homomorphic-signal-separation]] — The QFT enables the frequency-domain representation where homomorphic decomposition is applied

## Open Questions

- Can the approximate QFT ($O(n \log n)$ gates) provide sufficient precision for the cepstral analysis pipeline, or does the logarithm approximation error compound?
- What is the optimal measurement strategy after the inverse QFT to extract cepstral peaks without exponential sampling overhead?
