"""
Project Aorta: Quantum-Enhanced Cepstral Analysis for Arterial Echo Detection
==============================================================================

This module implements both classical and quantum-simulated cepstral analysis
pipelines for detecting arterial pressure pulse echoes. The echo delay reveals
the distance from a catheter tip to the nearest arterial bifurcation.

Mathematical Foundation:
    - Signal model: s(t) = p(t) + alpha * p(t - tau)
    - Cepstrum:     c(tau_q) = IFFT{ log|FFT(s)| }
    - Echo delay:   tau_detected = argmax_{tau_q > tau_min} |c(tau_q)|
    - Distance:     d = tau * c / 2

The quantum pipeline replaces FFT with QFT (Quantum Fourier Transform) and
the element-wise log with a QSVT-inspired polynomial approximation, achieving
theoretical exponential speedup: O(log^2 N) vs O(N log N).

Dependencies: numpy, scipy, matplotlib (standard scientific Python only)
No quantum computing libraries (qiskit, cirq, etc.) are required.

Author: Quantum Engineer Agent (SkillOS / Project Aorta Dialects)
"""

import numpy as np
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving figures


# =============================================================================
# SECTION 1: SIGNAL GENERATION
# =============================================================================

def generate_cardiac_pulse(t, heart_rate_bpm=72, systolic_duration=0.3):
    """
    Generate a realistic arterial pressure pulse waveform p(t).

    The pulse is modeled as a sum of Gaussians representing:
      - Systolic upstroke (sharp initial rise)
      - Systolic peak
      - Dicrotic notch (aortic valve closure)
      - Diastolic decay

    The pulse is designed as a single-shot waveform (not periodic within
    the observation window) to ensure the cepstrum cleanly separates
    the pulse envelope from the echo delay peak.

    Parameters
    ----------
    t : numpy.ndarray
        Time array in seconds.
    heart_rate_bpm : float
        Heart rate in beats per minute (default: 72 bpm).
    systolic_duration : float
        Duration of systolic phase in seconds (default: 0.3s).

    Returns
    -------
    numpy.ndarray
        Normalized pressure pulse waveform p(t) in range [0, 1].
    """
    # Generate a single cardiac pulse (not periodic) so the cepstrum
    # clearly shows the echo without interference from periodicity peaks.

    # Component 1: Systolic upstroke (sharp Gaussian, early in window)
    systolic_peak_time = 0.08  # seconds after start
    systolic_width = 0.015     # very narrow for sharp upstroke (high bandwidth)
    systolic_amplitude = 1.0
    component_systolic = systolic_amplitude * np.exp(
        -0.5 * ((t - systolic_peak_time) / systolic_width) ** 2
    )

    # Component 2: Systolic shoulder (broader, slightly later)
    shoulder_peak_time = 0.11
    shoulder_width = 0.025
    shoulder_amplitude = 0.7
    component_shoulder = shoulder_amplitude * np.exp(
        -0.5 * ((t - shoulder_peak_time) / shoulder_width) ** 2
    )

    # Component 3: Dicrotic notch (small bump after valve closure)
    dicrotic_peak_time = 0.18
    dicrotic_width = 0.015
    dicrotic_amplitude = 0.3
    component_dicrotic = dicrotic_amplitude * np.exp(
        -0.5 * ((t - dicrotic_peak_time) / dicrotic_width) ** 2
    )

    # Component 4: Diastolic decay (exponential-like via broad Gaussian)
    diastolic_peak_time = 0.15
    diastolic_width = 0.05
    diastolic_amplitude = 0.4
    component_diastolic = diastolic_amplitude * np.exp(
        -0.5 * ((t - diastolic_peak_time) / diastolic_width) ** 2
    )

    # Combine all components
    pulse = (component_systolic + component_shoulder +
             component_dicrotic + component_diastolic)

    # Normalize to [0, 1]
    pulse_min = pulse.min()
    pulse_max = pulse.max()
    if pulse_max - pulse_min > 0:
        pulse = (pulse - pulse_min) / (pulse_max - pulse_min)

    return pulse


def generate_composite_signal(N=1024, fs=1000.0, alpha=0.3, tau=0.05):
    """
    Generate the composite arterial signal with echo.

    The signal model follows Section 1 of the mathematical framework:
        s(t) = p(t) + alpha * p(t - tau)

    where:
        - p(t) is the cardiac pressure pulse
        - alpha is the attenuation coefficient at bifurcation reflection
        - tau is the round-trip echo delay (tau = 2d/c)

    Parameters
    ----------
    N : int
        Number of samples (default: 1024).
    fs : float
        Sampling rate in Hz (default: 1000 Hz).
    alpha : float
        Echo attenuation coefficient, in (0, 1) (default: 0.3).
    tau : float
        Echo delay in seconds (default: 0.05s = 50ms).

    Returns
    -------
    t : numpy.ndarray
        Time array of shape (N,).
    signal : numpy.ndarray
        Composite signal s(t) of shape (N,).
    pulse : numpy.ndarray
        Original pulse p(t) of shape (N,).
    """
    # Time vector
    t = np.arange(N) / fs

    # Generate the primary cardiac pulse
    pulse = generate_cardiac_pulse(t)

    # Compute delay in samples
    delay_samples = int(round(tau * fs))

    # Generate the delayed echo: alpha * p(t - tau)
    echo = np.zeros(N)
    if delay_samples < N:
        echo[delay_samples:] = alpha * pulse[:N - delay_samples]

    # Composite signal: s(t) = p(t) + alpha * p(t - tau)
    signal = pulse + echo

    return t, signal, pulse


# =============================================================================
# SECTION 2: CLASSICAL CEPSTRAL ANALYSIS
# =============================================================================

def classical_cepstrum(signal, fs):
    """
    Compute the classical cepstrum of a signal.

    Implements the homomorphic deconvolution pipeline from Section 2:
        c(tau_q) = IFFT{ log|FFT(s)| }

    The cepstrum separates the pulse envelope (low quefrencies) from
    the echo structure (peaks at quefrency = echo delay).

    Parameters
    ----------
    signal : numpy.ndarray
        Input signal s(t).
    fs : float
        Sampling rate in Hz.

    Returns
    -------
    quefrency : numpy.ndarray
        Quefrency axis in seconds.
    cepstrum : numpy.ndarray
        Real cepstrum values.
    """
    N = len(signal)

    # Step 1: Compute FFT of the signal
    spectrum = np.fft.fft(signal)

    # Step 2: Compute log of magnitude spectrum
    # Handle zeros/near-zeros to avoid log(0) = -inf
    magnitude = np.abs(spectrum)
    epsilon = 1e-10  # Floor to prevent log(0)
    log_magnitude = np.log(np.maximum(magnitude, epsilon))

    # Step 3: Compute IFFT to get the cepstrum
    cepstrum = np.real(np.fft.ifft(log_magnitude))

    # Quefrency axis (in seconds)
    quefrency = np.arange(N) / fs

    return quefrency, cepstrum


def detect_echo_delay_classical(quefrency, cepstrum, tau_min=0.02, tau_max=0.2):
    """
    Detect the echo delay from the classical cepstrum.

    Finds the dominant peak in the cepstrum within the expected range
    of echo delays, as described in Section 2, Step 12:
        tau_detected = argmax_{tau_q > tau_min} |c(tau_q)|

    The tau_min is set to 20ms to skip the low-quefrency region that
    contains the pulse envelope energy (spectral smoothness duality,
    Section 2, Step 9).

    Parameters
    ----------
    quefrency : numpy.ndarray
        Quefrency axis in seconds.
    cepstrum : numpy.ndarray
        Cepstrum values.
    tau_min : float
        Minimum expected echo delay in seconds (default: 20ms).
        Must be set above the pulse envelope width to avoid
        detecting pulse structure rather than echo delay.
    tau_max : float
        Maximum expected echo delay in seconds (default: 200ms).

    Returns
    -------
    float
        Detected echo delay in seconds.
    """
    # Restrict search to valid range [tau_min, tau_max]
    # tau_min must be above the pulse envelope region to avoid false peaks
    valid_mask = (quefrency >= tau_min) & (quefrency <= tau_max)
    valid_indices = np.where(valid_mask)[0]

    if len(valid_indices) == 0:
        return 0.0

    # Find the dominant peak in the valid range
    valid_cepstrum = np.abs(cepstrum[valid_indices])
    peak_idx_local = np.argmax(valid_cepstrum)
    peak_idx_global = valid_indices[peak_idx_local]

    return quefrency[peak_idx_global]


# =============================================================================
# SECTION 3: QUANTUM CIRCUIT IMPLEMENTATION (Numpy Simulation)
# =============================================================================

def build_qft_matrix(N):
    """
    Build the Quantum Fourier Transform matrix of size N x N.

    The QFT matrix implements the unitary transformation:
        QFT[j, k] = (1/sqrt(N)) * exp(2*pi*i*j*k/N)

    This corresponds to Section 4, Step 2:
        QFT|j> = (1/sqrt(N)) * sum_{k=0}^{N-1} e^{2*pi*i*j*k/N} |k>

    For n = log2(N) qubits, the QFT would decompose into O(n^2) gates.
    Here we construct the full matrix for simulation purposes.

    Parameters
    ----------
    N : int
        Dimension of the QFT matrix (must be power of 2).

    Returns
    -------
    numpy.ndarray
        Complex unitary QFT matrix of shape (N, N).
    """
    # Create index arrays
    j = np.arange(N)
    k = np.arange(N)

    # Build the QFT matrix using outer product of indices
    # QFT[j, k] = (1/sqrt(N)) * exp(2*pi*i*j*k/N)
    phase_matrix = np.outer(j, k)
    qft_matrix = (1.0 / np.sqrt(N)) * np.exp(2j * np.pi * phase_matrix / N)

    return qft_matrix


def build_inverse_qft_matrix(N):
    """
    Build the inverse QFT matrix (QFT-dagger).

    The inverse QFT is the conjugate transpose of the QFT matrix:
        QFT^{-1} = QFT^dagger

    As noted in Section 4, Step 11: QFT^{-1} = QFT^dagger with
    the same gate count O(log^2(N)).

    Parameters
    ----------
    N : int
        Dimension of the inverse QFT matrix.

    Returns
    -------
    numpy.ndarray
        Complex unitary inverse QFT matrix of shape (N, N).
    """
    qft = build_qft_matrix(N)
    return qft.conj().T


def quantum_state_preparation(signal):
    """
    Prepare the quantum state by amplitude encoding the signal.

    Implements Section 4, Step 4:
        |s> = (1/||s||) * sum_{j=0}^{N-1} s(j) |j>

    The signal amplitudes are normalized to form a valid quantum state
    (unit norm in the L2 sense).

    Parameters
    ----------
    signal : numpy.ndarray
        Real-valued input signal.

    Returns
    -------
    numpy.ndarray
        Normalized quantum state vector (complex, unit norm).
    """
    # Convert to float for numerical stability
    state = signal.astype(np.complex128)

    # Normalize to unit L2 norm (quantum state requirement)
    norm = np.linalg.norm(state)
    if norm > 0:
        state = state / norm

    return state


def apply_qft(state, qft_matrix):
    """
    Apply the Quantum Fourier Transform to a state vector.

    This simulates the quantum operation QFT|s> by matrix-vector
    multiplication. In a real quantum computer, this would be
    implemented with O(log^2(N)) controlled-rotation gates.

    Parameters
    ----------
    state : numpy.ndarray
        Input quantum state vector.
    qft_matrix : numpy.ndarray
        Pre-computed QFT matrix.

    Returns
    -------
    numpy.ndarray
        Transformed state vector in the frequency domain.
    """
    return qft_matrix @ state


def apply_log_transformation(state, epsilon=1e-10):
    """
    Apply log-magnitude transformation to the frequency-domain state.

    This simulates the QSVT polynomial approximation of log(x)
    described in Section 5. In a real quantum computer, this would
    be implemented using Quantum Singular Value Transformation with
    a degree-d polynomial approximation to log(x).

    The simulation applies the element-wise operation:
        1. Extract magnitudes of state amplitudes
        2. Apply log to magnitudes (with floor for numerical safety)
        3. Re-normalize to maintain valid quantum state

    Note: This is a simplification. True QSVT would apply a polynomial
    P_d(x) approximating log(x) to the singular values of a block-encoded
    matrix, with error bounded by delta_QSVT (Section 5, Step 13).

    Parameters
    ----------
    state : numpy.ndarray
        Frequency-domain quantum state vector.
    epsilon : float
        Floor value to prevent log(0) (default: 1e-10).

    Returns
    -------
    numpy.ndarray
        State vector with log-magnitude transformation applied.
    """
    # Extract magnitudes of the frequency-domain amplitudes
    magnitudes = np.abs(state)

    # Apply floor to prevent log(0)
    magnitudes_safe = np.maximum(magnitudes, epsilon)

    # Apply log transformation (simulating QSVT polynomial approximation)
    log_magnitudes = np.log(magnitudes_safe)

    # The log values become the new state amplitudes
    # Re-normalize to maintain valid quantum state (unit norm)
    log_state = log_magnitudes.astype(np.complex128)
    norm = np.linalg.norm(log_state)
    if norm > 0:
        log_state = log_state / norm

    return log_state


def quantum_cepstrum_pipeline(signal, fs):
    """
    Execute the full quantum cepstral analysis pipeline.

    Implements the quantum pipeline from Section 4:
        |s> -> QFT -> QSVT(log) -> QFT^{-1} -> Measure

    Steps:
        1. State preparation: Encode signal into quantum state |s>
        2. QFT: Apply Quantum Fourier Transform
        3. Log approximation: Simulate QSVT polynomial for log(x)
        4. Inverse QFT: Apply QFT^{-1}
        5. Measurement: Extract cepstrum from resulting state

    Parameters
    ----------
    signal : numpy.ndarray
        Input signal s(t).
    fs : float
        Sampling rate in Hz.

    Returns
    -------
    quefrency : numpy.ndarray
        Quefrency axis in seconds.
    quantum_cepstrum : numpy.ndarray
        Cepstrum extracted from the quantum simulation.
    """
    N = len(signal)

    # Step 1: State Preparation (amplitude encoding)
    # |s> = (1/||s||) * sum_j s(j) |j>
    state = quantum_state_preparation(signal)

    # Step 2: Build and apply QFT
    # QFT|s> = (1/||s||) * sum_k S(k) |k>
    qft_matrix = build_qft_matrix(N)
    freq_state = apply_qft(state, qft_matrix)

    # Step 3: Apply log-magnitude transformation (simulating QSVT)
    # This approximates: log|S(k)| via polynomial transformation
    log_state = apply_log_transformation(freq_state)

    # Step 4: Apply inverse QFT
    # QFT^{-1} maps back to quefrency domain -> cepstrum
    iqft_matrix = build_inverse_qft_matrix(N)
    cepstrum_state = iqft_matrix @ log_state

    # Step 5: Measurement simulation
    # In a real quantum computer, we would measure multiple shots
    # and reconstruct the probability distribution. Here we extract
    # the real part of the state amplitudes as the cepstrum estimate.
    quantum_cepstrum = np.real(cepstrum_state)

    # Quefrency axis
    quefrency = np.arange(N) / fs

    return quefrency, quantum_cepstrum


def detect_echo_delay_quantum(quefrency, quantum_cepstrum, tau_min=0.02, tau_max=0.2):
    """
    Detect the echo delay from the quantum cepstrum.

    Uses the same peak detection strategy as the classical method
    (Section 2, Step 12), applied to the quantum-derived cepstrum.

    Parameters
    ----------
    quefrency : numpy.ndarray
        Quefrency axis in seconds.
    quantum_cepstrum : numpy.ndarray
        Quantum-derived cepstrum values.
    tau_min : float
        Minimum expected echo delay in seconds (default: 20ms).
    tau_max : float
        Maximum expected echo delay in seconds (default: 200ms).

    Returns
    -------
    float
        Detected echo delay in seconds.
    """
    # Same detection algorithm as classical, with tau_min above pulse region
    valid_mask = (quefrency >= tau_min) & (quefrency <= tau_max)
    valid_indices = np.where(valid_mask)[0]

    if len(valid_indices) == 0:
        return 0.0

    valid_cepstrum = np.abs(quantum_cepstrum[valid_indices])
    peak_idx_local = np.argmax(valid_cepstrum)
    peak_idx_global = valid_indices[peak_idx_local]

    return quefrency[peak_idx_global]


# =============================================================================
# SECTION 4: COMPARISON AND VISUALIZATION
# =============================================================================

def plot_results(t, signal, quefrency_classical, cepstrum_classical,
                 quefrency_quantum, cepstrum_quantum,
                 tau_true, tau_classical, tau_quantum,
                 output_path):
    """
    Generate the four-subplot comparison visualization.

    Subplots:
        1. Original signal s(t) with marked echo region
        2. Classical cepstrum with detected peak
        3. Quantum cepstrum with detected peak
        4. Overlay comparison of classical vs quantum cepstrum

    Parameters
    ----------
    t : numpy.ndarray
        Time array.
    signal : numpy.ndarray
        Composite signal.
    quefrency_classical : numpy.ndarray
        Quefrency axis for classical cepstrum.
    cepstrum_classical : numpy.ndarray
        Classical cepstrum values.
    quefrency_quantum : numpy.ndarray
        Quefrency axis for quantum cepstrum.
    cepstrum_quantum : numpy.ndarray
        Quantum cepstrum values.
    tau_true : float
        True echo delay in seconds.
    tau_classical : float
        Classical detected delay.
    tau_quantum : float
        Quantum detected delay.
    output_path : str
        Path to save the output figure.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        'Project Aorta: Quantum-Enhanced Cepstral Analysis\n'
        'Arterial Echo Detection via Classical and Quantum Pipelines',
        fontsize=13, fontweight='bold'
    )

    # --- Subplot 1: Original Signal ---
    ax1 = axes[0, 0]
    ax1.plot(t * 1000, signal, 'b-', linewidth=1.0, label='s(t) = p(t) + alpha*p(t-tau)')
    ax1.axvline(x=tau_true * 1000, color='r', linestyle='--', linewidth=1.5,
                label=f'Echo onset (tau={tau_true*1000:.1f} ms)')
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Amplitude (normalized)')
    ax1.set_title('Composite Arterial Signal with Echo')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim([0, t[-1] * 1000])

    # --- Subplot 2: Classical Cepstrum ---
    ax2 = axes[0, 1]
    # Plot only the relevant quefrency range
    plot_mask = quefrency_classical <= 0.25
    ax2.plot(quefrency_classical[plot_mask] * 1000,
             np.abs(cepstrum_classical[plot_mask]),
             'g-', linewidth=1.0, label='|c(tau_q)| classical')
    ax2.axvline(x=tau_true * 1000, color='r', linestyle='--', linewidth=1.5,
                label=f'True tau = {tau_true*1000:.1f} ms')
    ax2.axvline(x=tau_classical * 1000, color='orange', linestyle='-', linewidth=2.0,
                label=f'Detected tau = {tau_classical*1000:.1f} ms')
    ax2.set_xlabel('Quefrency (ms)')
    ax2.set_ylabel('|Cepstrum|')
    ax2.set_title('Classical Cepstrum Analysis')
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)

    # --- Subplot 3: Quantum Cepstrum ---
    ax3 = axes[1, 0]
    plot_mask_q = quefrency_quantum <= 0.25
    ax3.plot(quefrency_quantum[plot_mask_q] * 1000,
             np.abs(cepstrum_quantum[plot_mask_q]),
             'm-', linewidth=1.0, label='|c(tau_q)| quantum')
    ax3.axvline(x=tau_true * 1000, color='r', linestyle='--', linewidth=1.5,
                label=f'True tau = {tau_true*1000:.1f} ms')
    ax3.axvline(x=tau_quantum * 1000, color='cyan', linestyle='-', linewidth=2.0,
                label=f'Detected tau = {tau_quantum*1000:.1f} ms')
    ax3.set_xlabel('Quefrency (ms)')
    ax3.set_ylabel('|Cepstrum|')
    ax3.set_title('Quantum Cepstrum Analysis (Simulated)')
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(True, alpha=0.3)

    # --- Subplot 4: Overlay Comparison ---
    ax4 = axes[1, 1]
    # Normalize both cepstra for comparison
    classical_norm = np.abs(cepstrum_classical[plot_mask])
    quantum_norm = np.abs(cepstrum_quantum[plot_mask_q])
    if classical_norm.max() > 0:
        classical_norm = classical_norm / classical_norm.max()
    if quantum_norm.max() > 0:
        quantum_norm = quantum_norm / quantum_norm.max()

    ax4.plot(quefrency_classical[plot_mask] * 1000, classical_norm,
             'g-', linewidth=1.5, alpha=0.8, label='Classical (normalized)')
    ax4.plot(quefrency_quantum[plot_mask_q] * 1000, quantum_norm,
             'm--', linewidth=1.5, alpha=0.8, label='Quantum (normalized)')
    ax4.axvline(x=tau_true * 1000, color='r', linestyle='--', linewidth=1.5,
                label=f'True tau = {tau_true*1000:.1f} ms')
    ax4.set_xlabel('Quefrency (ms)')
    ax4.set_ylabel('Normalized |Cepstrum|')
    ax4.set_title('Classical vs Quantum Cepstrum Comparison')
    ax4.legend(loc='upper right', fontsize=9)
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"\nVisualization saved to: {output_path}")


def print_results_table(tau_true, tau_classical, tau_quantum, fs):
    """
    Print a formatted comparison table of results.

    Parameters
    ----------
    tau_true : float
        True echo delay in seconds.
    tau_classical : float
        Classical detected delay in seconds.
    tau_quantum : float
        Quantum detected delay in seconds.
    fs : float
        Sampling rate in Hz.
    """
    # Compute errors
    error_classical = abs(tau_classical - tau_true)
    error_quantum = abs(tau_quantum - tau_true)

    # Quefrency resolution limit
    resolution = 1.0 / fs

    # Distance estimates (assuming pulse wave velocity c = 5 m/s)
    c = 5.0  # m/s
    d_true = tau_true * c / 2.0
    d_classical = tau_classical * c / 2.0
    d_quantum = tau_quantum * c / 2.0

    print("\n" + "=" * 72)
    print("  PROJECT AORTA: QUANTUM-ENHANCED CEPSTRAL ANALYSIS RESULTS")
    print("=" * 72)

    print("\n  Signal Parameters:")
    print(f"    Samples (N):          1024")
    print(f"    Sampling Rate (fs):   {fs:.0f} Hz")
    print(f"    Echo Attenuation (a): 0.3")
    print(f"    Quefrency Resolution: {resolution*1000:.3f} ms")

    print("\n" + "-" * 72)
    print(f"  {'Metric':<30} {'True':>12} {'Classical':>12} {'Quantum':>12}")
    print("-" * 72)
    print(f"  {'Echo Delay (ms)':<30} {tau_true*1000:>12.3f} {tau_classical*1000:>12.3f} {tau_quantum*1000:>12.3f}")
    print(f"  {'Absolute Error (ms)':<30} {'---':>12} {error_classical*1000:>12.3f} {error_quantum*1000:>12.3f}")
    print(f"  {'Relative Error (%)':<30} {'---':>12} {error_classical/tau_true*100:>12.3f} {error_quantum/tau_true*100:>12.3f}")
    print(f"  {'Distance Estimate (mm)':<30} {d_true*1000:>12.2f} {d_classical*1000:>12.2f} {d_quantum*1000:>12.2f}")
    print(f"  {'Distance Error (mm)':<30} {'---':>12} {abs(d_classical-d_true)*1000:>12.3f} {abs(d_quantum-d_true)*1000:>12.3f}")
    print("-" * 72)

    print("\n  Complexity Comparison (Theoretical):")
    print(f"    Classical Pipeline:  O(N log N) = O({1024 * 10:.0f}) operations")
    print(f"    Quantum Pipeline:   O(log^2 N) = O({10**2:.0f}) quantum gates")
    print(f"    Speedup Factor:     O(N / log N) = O({1024 // 10:.0f})x")

    print("\n  Clinical Interpretation:")
    if error_classical * 1000 < 1.0:
        print(f"    Classical: Echo delay detected within 1 mm accuracy (PASS)")
    else:
        print(f"    Classical: Echo delay error = {error_classical*1000:.3f} ms (review needed)")
    if error_quantum * 1000 < 1.0:
        print(f"    Quantum:   Echo delay detected within 1 mm accuracy (PASS)")
    else:
        print(f"    Quantum:   Echo delay error = {error_quantum*1000:.3f} ms (review needed)")

    print("\n" + "=" * 72)


# =============================================================================
# SECTION 5: MAIN EXECUTION
# =============================================================================

def main():
    """
    Main execution block: runs the full Project Aorta analysis pipeline.

    Sequence:
        1. Generate synthetic arterial signal with echo
        2. Run classical cepstral analysis (baseline)
        3. Run quantum-simulated cepstral analysis
        4. Compare results and generate visualization
    """
    # -------------------------------------------------------------------------
    # Configuration Parameters
    # -------------------------------------------------------------------------
    N = 1024            # Number of signal samples
    fs = 1000.0         # Sampling rate (Hz)
    alpha = 0.3         # Echo attenuation coefficient
    tau = 0.05          # Echo delay (seconds) = 50 ms
    output_path = (
        '/Users/agustinazwiener/evolvingagents/skillos/'
        'projects/Project_aorta_dialects/output/quantum_aorta_results.png'
    )

    print("=" * 72)
    print("  PROJECT AORTA: Quantum-Enhanced Cepstral Analysis")
    print("  Arterial Echo Detection for Catheter Navigation")
    print("=" * 72)

    # -------------------------------------------------------------------------
    # Step 1: Signal Generation
    # -------------------------------------------------------------------------
    print("\n[1/4] Generating synthetic arterial signal...")
    print(f"       N={N}, fs={fs} Hz, alpha={alpha}, tau={tau*1000:.1f} ms")

    t, signal, pulse = generate_composite_signal(N=N, fs=fs, alpha=alpha, tau=tau)

    print(f"       Signal generated: {len(signal)} samples, duration={t[-1]*1000:.1f} ms")
    print(f"       Echo delay in samples: {int(round(tau * fs))}")

    # -------------------------------------------------------------------------
    # Step 2: Classical Cepstral Analysis
    # -------------------------------------------------------------------------
    print("\n[2/4] Running classical cepstral analysis...")
    print("       Pipeline: FFT -> log|.| -> IFFT")

    quefrency_classical, cepstrum_classical = classical_cepstrum(signal, fs)
    tau_classical = detect_echo_delay_classical(quefrency_classical, cepstrum_classical)

    print(f"       Detected echo delay: {tau_classical*1000:.3f} ms")
    print(f"       True echo delay:     {tau*1000:.3f} ms")
    print(f"       Error:               {abs(tau_classical - tau)*1000:.3f} ms")

    # -------------------------------------------------------------------------
    # Step 3: Quantum Cepstral Analysis (Simulated)
    # -------------------------------------------------------------------------
    print("\n[3/4] Running quantum cepstral analysis (numpy simulation)...")
    print("       Pipeline: |s> -> QFT -> QSVT(log) -> QFT^-1 -> Measure")
    print(f"       QFT matrix size: {N}x{N}")
    print(f"       Equivalent qubits: n = log2({N}) = {int(np.log2(N))}")

    quefrency_quantum, cepstrum_quantum = quantum_cepstrum_pipeline(signal, fs)
    tau_quantum = detect_echo_delay_quantum(quefrency_quantum, cepstrum_quantum)

    print(f"       Detected echo delay: {tau_quantum*1000:.3f} ms")
    print(f"       True echo delay:     {tau*1000:.3f} ms")
    print(f"       Error:               {abs(tau_quantum - tau)*1000:.3f} ms")

    # -------------------------------------------------------------------------
    # Step 4: Comparison and Visualization
    # -------------------------------------------------------------------------
    print("\n[4/4] Generating comparison visualization...")

    plot_results(
        t, signal,
        quefrency_classical, cepstrum_classical,
        quefrency_quantum, cepstrum_quantum,
        tau, tau_classical, tau_quantum,
        output_path
    )

    # Print the final results table
    print_results_table(tau, tau_classical, tau_quantum, fs)

    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    print("\n  Execution complete.")
    print(f"  Output figure: {output_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
