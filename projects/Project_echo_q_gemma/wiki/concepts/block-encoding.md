---
topic: Block-Encoding
type: concept
domain: quantum-computing
related: [[quantum-singular-value-transformation]], [[quantum-fourier-transform]]
sources: [[standard-quantum-textbook]]
skills: quantum-theorist
last_updated: 2023-10-27T10:10:00Z
---

# Block-Encoding

## Definition
A block-encoding of a non-unitary matrix $A$ is a unitary $U$ such that $A$ is embedded in the upper-left block of $U$.

## Key Properties
- **Form**: $U = \begin{bmatrix} A/\alpha & \cdot \\ \cdot & \cdot \end{bmatrix}$ where $\alpha \geq \|A\|$.
- **Requirement**: Necessary for implementing non-unitary operators like $\log(x)$ on quantum hardware.

## How It Works
GIVEN: A matrix $A$ and a normalization factor $\alpha$.
DERIVE: Construction of $U$ using PREP and SEL gates or LCU (Linear Combination of Unitaries).
QED: Any operator $A$ can be block-encoded if it can be expressed as a sum of unitaries.

## Related Concepts
- [[quantum-singular-value-transformation]] — QSVT acts upon block-encoded matrices.
- [[quantum-fourier-transform]] — Often follows QFT in signal processing pipelines.

## Open Questions
- Minimizing the overhead $\alpha$ for complex operator constructions.