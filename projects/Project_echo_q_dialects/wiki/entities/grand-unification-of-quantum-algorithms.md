---
entity: Grand Unification of Quantum Algorithms
type: paper
authors:
  - Andras Gilyen
  - Yuan Su
  - Guang Hao Low
  - Nathan Wiebe
year: 2019
venue: STOC 2019 (ACM Symposium on Theory of Computing)
arxiv: "1806.01838"
domain: quantum-computing
---

# A Grand Unification of Quantum Algorithms

## Summary

Gilyen et al. (2019) demonstrate that Quantum Singular Value Transformation (QSVT) provides a unified framework subsuming most known quantum algorithms. By showing that any bounded polynomial can be applied to the singular values of a block-encoded matrix, the paper establishes QSVT as the common mathematical foundation underlying quantum search, phase estimation, Hamiltonian simulation, and matrix arithmetic.

## Key Contributions

1. **QSVT Framework**: Formalized the quantum signal processing convention and extended it from single-qubit rotations to arbitrary block-encoded matrices
2. **Universality Theorem**: Proved that degree-d QSVT realizes any degree-d polynomial P: [-1,1] -> [-1,1] satisfying parity and boundedness constraints
3. **Optimality**: Showed d queries to the block-encoding oracle are both necessary and sufficient for degree-d polynomial transformation
4. **Unification**: Demonstrated that Grover search, quantum walks, phase estimation, Hamiltonian simulation, and linear systems algorithms are all special cases of QSVT with specific polynomial choices
5. **Block-Encoding Formalism**: Established the (alpha, a, epsilon)-block-encoding framework as the standard input model for quantum linear algebra

## Relevance to Echo-Q

The Echo-Q quantum cepstral pipeline relies directly on two core results from this paper:
- **Block-encoding** of spectral data after QFT (Section 3 of the paper)
- **QSVT polynomial approximation** of log(x) for the homomorphic separation step (Section 5 of the paper)

The non-unitarity of the logarithm -- the central obstacle in quantum cepstral analysis -- is resolved using the polynomial approximation machinery proved optimal in this work.

## Referenced By

- [[concepts/quantum-singular-value-transformation]] -- primary source for QSVT definition and properties
- [[concepts/block-encoding]] -- primary source for block-encoding formalism
- [[concepts/quantum-fourier-transform]] -- cited for QFT's role in the unified framework
- [[concepts/cepstral-analysis]] -- QSVT from this paper implements the log step
- [[concepts/homomorphic-signal-separation]] -- QSVT resolution strategy directly based on this paper's theorems
