---
entity: "Grand Unification of Quantum Algorithms"
type: paper
domain: quantum-computing
appears_in: [[concepts/quantum-singular-value-transformation]], [[concepts/block-encoding]]
last_updated: "2026-04-06T00:06:00Z"
---

# Grand Unification of Quantum Algorithms

## Description

"A Grand Unification of Quantum Algorithms" by Gilyen, Su, Low, and Wiebe (2019) is a seminal paper that establishes the Quantum Singular Value Transformation (QSVT) as a unifying framework for quantum algorithms. The paper demonstrates that Hamiltonian simulation, quantum search (Grover), amplitude amplification, quantum walks, quantum linear systems (HHL), and many other quantum algorithms are all special cases of QSVT with appropriate polynomial choices.

The paper provides rigorous constructions for block-encoding matrices and proves that QSVT achieves optimal query complexity for polynomial transformations of singular values.

## Key Contributions

- **QSVT Framework**: Formalized the connection between quantum signal processing (QSP) for single qubits and block-encoded matrices, creating QSVT as a general-purpose quantum algorithmic primitive.
- **Block-Encoding Formalism**: Standardized the $(\alpha, a, \epsilon)$-block-encoding notation and provided multiple constructions (LCU, PREP/SEL, product decomposition).
- **Polynomial Universality Theorem**: Proved that any polynomial $P(x)$ with $|P(x)| \leq 1$ on $[-1,1]$ and the correct parity can be implemented by QSVT, and that this is query-optimal.
- **Unified Complexity Analysis**: Showed that the query complexity of many quantum algorithms reduces to the degree of the corresponding QSVT polynomial.
- **Constructive Phase Angles**: Provided algorithms for computing the QSVT phase angles $\boldsymbol{\phi}$ from the target polynomial $P$.

## Relevance to Echo-Q

This paper provides the theoretical foundation for resolving the **non-unitarity problem** in quantum cepstral analysis ([[concepts/homomorphic-signal-separation]]). Specifically:

1. The logarithm $\log(x)$ can be approximated by a polynomial $P_d(x)$ satisfying the QSVT constraints
2. This polynomial is applied to the singular values (frequency amplitudes) of the block-encoded diagonal operator after the QFT
3. The construction is unitary by design, satisfying constraint C1
4. The query complexity is exactly $d$ (the polynomial degree), satisfying constraint C4

**Key theorems used in Echo-Q**:
- Theorem 56 (Polynomial eigenvalue transformation): The core QSVT result
- Theorem 30 (Block-encoding of diagonal operators): Used for encoding frequency amplitudes
- Corollary 69 (Polynomial approximation of functions): Guarantees that $\log(x)$ can be $\epsilon$-approximated

## Appears In

- [[concepts/quantum-singular-value-transformation]] — The paper defines and proves the QSVT framework
- [[concepts/block-encoding]] — The paper formalizes block-encoding constructions

## Related Entities

- **Gilyen, Andras** — First author, quantum algorithms researcher
- **Su, Yuan** — Co-author, quantum simulation specialist
- **Low, Guang Hao** — Co-author, co-inventor of quantum signal processing
- **Wiebe, Nathan** — Co-author, quantum machine learning researcher

## Citation

Gilyen, A., Su, Y., Low, G. H., & Wiebe, N. (2019). Quantum singular value transformation and beyond: exponential improvements for quantum matrix arithmetics. *Proceedings of the 51st Annual ACM SIGACT Symposium on Theory of Computing (STOC 2019)*, pp. 193-204.

arXiv: 1806.01838
