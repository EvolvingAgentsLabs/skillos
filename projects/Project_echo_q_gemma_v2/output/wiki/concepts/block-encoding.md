# Block-Encoding

## Definition
Block-encoding is a technique used to embed a non-unitary matrix $A$ into a larger unitary matrix $U$. This is a fundamental building block for performing general linear algebra on quantum computers.

## Mathematical Derivation
A matrix $A$ is said to be block-encoded in a unitary $U$ if:

$$U = \begin|0\rangle\langle 0| \otimes A + \dots$$

More formally, we seek a unitary $U$ such that:

$$\langle 0\rangle^a U \ket{0\rangle^a = A$$

where $\ket{0\rangle^a$ is an ancilla state. For the Project Echo-Q goal, we need to block-encode the convolution operator $H$ (the arterial impulse response) to facilitate deconvolution.

## Key Properties
1. **Normalization:** The singular values of $A$ must be bounded by $1/\alpha$ to ensure the embedding is valid.
2. **Ancilla Dependence:** The precision of the encoding is tied to the number of ancilla qubits.

## How It Works
Block-encoding allows us to use algorithms like [[concepts/quantum-singular-value-transformation]] (QSVT) on matrices that are not naturally unitary, such as the frequency-domain representations of pressure waves.

## Open Questions
- What is the optimal ancilla overhead for encoding the specific sparse matrices arising from arterial pulse wave reflections?
- Connection to [[entities/grand-unification-of-quantum-algorithms]].