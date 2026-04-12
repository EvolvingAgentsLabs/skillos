---
type: wiki-index
project: Echo-Q Dialects
dialect: formal-proof
last_updated: 2026-04-12
---

# Wiki Index: Echo-Q Dialects (formal-proof)

## Concepts (5)

| Concept | File | Formal-Proof Blocks | Related Links |
|---|---|---|---|
| Quantum Fourier Transform | [[concepts/quantum-fourier-transform]] | 2 (circuit construction, product representation) | cepstral-analysis, block-encoding, homomorphic-signal-separation |
| Quantum Singular Value Transformation | [[concepts/quantum-singular-value-transformation]] | 3 (signal processing, block-encoded extension, log approximation) | block-encoding, homomorphic-signal-separation, quantum-fourier-transform |
| Block Encoding | [[concepts/block-encoding]] | 4 (LCU construction, QSVT-compatible, composition, Echo-Q pipeline) | quantum-singular-value-transformation, homomorphic-signal-separation, quantum-fourier-transform |
| Cepstral Analysis | [[concepts/cepstral-analysis]] | 2 (three-step pipeline, echo detection) | homomorphic-signal-separation, quantum-fourier-transform, block-encoding |
| Homomorphic Signal Separation | [[concepts/homomorphic-signal-separation]] | 2 (non-unitarity problem, QSVT resolution) | cepstral-analysis, quantum-fourier-transform, block-encoding, quantum-singular-value-transformation |

## Entities (1)

| Entity | File | Type |
|---|---|---|
| Grand Unification of Quantum Algorithms | [[entities/grand-unification-of-quantum-algorithms]] | Paper (Gilyen et al. 2019) |

## Dependency Graph

```
quantum-fourier-transform
    |
    v
block-encoding  <------+
    |                   |
    v                   |
quantum-singular-value-transformation
    |
    v
homomorphic-signal-separation
    |
    v
cepstral-analysis
```

## Statistics

- Total concept pages: 5
- Total entity pages: 1
- Total formal-proof blocks: 13
- Dialect: formal-proof
- Domain: quantum-computing
