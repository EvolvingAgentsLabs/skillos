---
concept: Block Encoding
type: concept
domain: quantum-computing
related: [[quantum-singular-value-transformation]], [[homomorphic-signal-separation]], [[quantum-fourier-transform]]
sources: [[entities/grand-unification-of-quantum-algorithms]]
skills: [knowledge-query-agent]
last_updated: "2026-04-06T00:03:00Z"
---

# Block Encoding

## Definition

A **block encoding** of a matrix $A$ (not necessarily unitary) is a unitary $U_A$ acting on a larger Hilbert space such that $A$ is embedded in a block:

$$(\langle 0|^{\otimes a} \otimes I_s) \; U_A \; (|0\rangle^{\otimes a} \otimes I_s) = \frac{A}{\alpha}$$

where $a$ is the number of ancilla qubits, $\alpha \geq \|A\|$ is the **subnormalization factor**, and $I_s$ is the identity on the system register. We say $U_A$ is an $(\alpha, a, \epsilon)$-block-encoding of $A$ if the above holds to within error $\epsilon$.

## Key Properties

- **Universality**: Any matrix with $\|A\| \leq \alpha$ can be block-encoded (existence is guaranteed, though efficiency varies).
- **Unitarity preserved**: $U_A$ is unitary even though $A$ is not — the "missing" norm is absorbed by the ancilla states.
- **Subnormalization**: The factor $\alpha$ means we implement $A/\alpha$ rather than $A$ directly. This is the price of embedding a non-unitary operator in a unitary.
- **Success probability**: When we measure the ancilla and post-select on $|0\rangle^{\otimes a}$, the success probability is $\|A|\psi\rangle\|^2 / \alpha^2$. Amplitude amplification can boost this.
- **Composability**: Block encodings compose naturally — products, sums, and polynomial transformations (via [[quantum-singular-value-transformation]]) of block-encoded matrices are all achievable.

## How It Works

### Construction 1: Linear Combination of Unitaries (LCU)

Given $A = \sum_{j=0}^{m-1} \beta_j U_j$ where each $U_j$ is unitary:

1. **PREPARE oracle** $G$: maps $|0\rangle \mapsto \sum_j \sqrt{\beta_j / \alpha} |j\rangle$ where $\alpha = \sum_j |\beta_j|$
2. **SELECT oracle** $V$: maps $|j\rangle|\psi\rangle \mapsto |j\rangle U_j|\psi\rangle$
3. **Block encoding**: $U_A = G^\dagger \cdot V \cdot G$

Then $(\langle 0| \otimes I) U_A (|0\rangle \otimes I) = A / \alpha$.

**For the logarithm**: Express the Taylor series $\log(1+x) = x - x^2/2 + x^3/3 - \cdots$ as a linear combination. Each term $x^k$ is a product of $k$ copies of the block-encoding of $x$, which can be computed via repeated application.

### Construction 2: QSVT-Compatible Encoding

For diagonal matrices $D = \text{diag}(d_1, \ldots, d_N)$:

1. Prepare a signal operator $W$ such that $\langle 0|W|0\rangle = D / \|D\|$
2. This diagonal block-encoding is naturally compatible with QSVT

**For Echo-Q**: After the QFT, the frequency-domain amplitudes form a diagonal operator. Block-encoding this diagonal allows QSVT to apply the polynomial approximation of $\log(\cdot)$.

### Construction 3: Amplitude Encoding as Block-Encoding

A state preparation unitary $U_{\text{prep}}$ that maps $|0\rangle \mapsto \sum_k a_k |k\rangle$ can be viewed as a $(1, n, 0)$-block-encoding of the row vector $(a_0, a_1, \ldots, a_{N-1})$, since:

$$\langle 0|^{\otimes n} U_{\text{prep}}|0\rangle^{\otimes n} = \sum_k a_k \langle 0|k\rangle = a_0$$

More usefully, the **density operator** $\rho = U_{\text{prep}}|0\rangle\langle 0|U_{\text{prep}}^\dagger$ block-encodes the outer product of the amplitude vector.

### Composition Rules

| Operation | Block Encoding | Subnormalization |
|-----------|---------------|-----------------|
| $A + B$ | LCU of $U_A, U_B$ | $\alpha_A + \alpha_B$ |
| $A \cdot B$ | $U_A \cdot U_B$ (with ancilla management) | $\alpha_A \cdot \alpha_B$ |
| $P(A)$ for polynomial $P$ | QSVT with phases | $\alpha^{\deg P}$ (improved by QSVT) |
| $A^{-1}$ | QSVT with $P(x) \approx 1/x$ | depends on condition number |

### Echo-Q Pipeline

In the quantum cepstrum algorithm:

1. **After QFT**: Frequency amplitudes $|\Psi_k|$ are embedded in the quantum state
2. **Block-encode diagonal**: Create $U_D$ such that $\langle 0|U_D|0\rangle = \text{diag}(|\Psi_k|) / \alpha$
3. **Apply QSVT**: Transform $|\Psi_k| / \alpha \mapsto P(|\Psi_k| / \alpha) \approx c \cdot \log(|\Psi_k| / \alpha)$
4. **Feed to inverse QFT**: The log-transformed amplitudes yield cepstral coefficients

The block-encoding step is the **bridge** between the unitary QFT and the non-unitary logarithm.

## Related Concepts

- [[quantum-singular-value-transformation]] — QSVT operates on block-encoded matrices; the block encoding is the input format that QSVT requires
- [[homomorphic-signal-separation]] — Block encoding enables the logarithm step in the homomorphic pipeline by embedding the non-unitary $\log(\cdot)$ within a unitary framework
- [[quantum-fourier-transform]] — The QFT output must be block-encoded before the logarithm can be applied via QSVT

## Open Questions

- What is the optimal ancilla count for block-encoding the frequency-domain diagonal in the Echo-Q pipeline?
- Can we avoid explicit block-encoding by interleaving QFT gates with QSVT rotations?
- How does the subnormalization factor $\alpha$ affect the overall success probability of the cepstral analysis circuit?
