# Quantum Fourier Transform (QFT)

## Definition
The Quantum Fourier Transform (QFT) is a linear transformation on quantum bits that is the quantum analogue of the discrete Fourier transform (DFT). It maps a state $|j\rangle$ to a superposition of states representing the frequency components of $j$.

## Mathematical Derivation
Given a state $|j\rangle = |j_1 j_2 \dots j_n\rangle$, where $j = \sum_{k=1}^n j_k 2^{n-k}$, the QFT is defined as:

$$\text{QFT}|j\rangle = \frac{1}{\sqrt{N}} \sum_{k=0}^{N-1} e^{2\pi i j k / N} |k\rangle$$

Where $N = 2^n$. Using product notation, this can be expressed as:

$$\text{QFT}|j_1\dots j_n\rangle = \frac{1}{\sqrt{2^n}} \bigotimes_{l=1}^n \left( |0\rangle + e^{2\pi i [0.j_l j_{l+1} \dots j_n]} |1\rangle \right)$$

In the context of [[concepts/cepstral-analysis]], the QFT is the engine used to transform pressure wave signals from the time domain to the frequency domain, allowing for the logarithmic operations required for cepstral computation.

## Key Properties
1. **Complexity:** $O(n^2)$ gates, providing an exponential speedup over the classical FFT ($O(n 2^n)$).
2. **Unitary:** The QFT is a unitary transformation, preserving the $L^2$ norm of the quantum state.
3. **Periodicity Detection:** Essential for finding periodicities in arterial waveforms.

## How It Works
The QFT is implemented via a sequence of Hadamard gates ($H$) and controlled phase rotation gates ($R_k$). The rotation gate is defined as:

$$R_k = \begin{pmatrix} 1 & 0 \\ 0 & e^{2\pi i / 2^k} \end{pmatrix}$$

## Open Questions
- How can we mitigate noise-induced phase errors in the $R_k$ gates during the deconvolution of low-amplitude arterial echoes?
- Integration with [[concepts/block-encoding]] for non-unitary signal operations.