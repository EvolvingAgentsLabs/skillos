#!/usr/bin/env python3
"""
Project Aorta: Quantum Homomorphic Signal Processing for Arterial Echo Detection
=================================================================================

Complete implementation of a hybrid classical-quantum cepstral analysis pipeline
for detecting arterial echo reflections from aortic arch bifurcations.

Mathematical Foundation
-----------------------
The measured arterial pressure signal is modeled as:

    s(t) = p(t) + sum_i alpha_i * p(t - tau_i)

where p(t) is the cardiac pulse, alpha_i are reflection coefficients, and tau_i
are round-trip delays to impedance discontinuities (vessel bifurcations).

The homomorphic (cepstral) analysis pipeline decomposes this convolution:

    s[n] -> FFT -> log|.| -> IFFT -> cepstrum c[n]

yielding peaks at quefrency indices m_i = round(tau_i * fs) with amplitudes
alpha_i / 2 (Theorem 4.2 from the mathematical framework).

The quantum pipeline replaces FFT/IFFT with QFT/IQFT, using the hybrid
Approach C (Section 5.6): QFT -> Measure -> Classical log -> Re-encode -> IQFT.

References
----------
- Project Aorta Mathematical Framework (MathematicianAgent, 2026)
- Oppenheim & Schafer, "Discrete-Time Signal Processing" (cepstral analysis)
- Nielsen & Chuang, "Quantum Computation" (QFT circuits)

Author: QuantumEngineerAgent (SkillOS)
Date: 2026-04-12
"""

import warnings
import sys
from typing import Tuple, List, Dict, Optional, NamedTuple
from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks, hamming
from scipy.fft import fft, ifft

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for file output
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# ---------------------------------------------------------------------------
# Qiskit import with graceful fallback
# ---------------------------------------------------------------------------
QISKIT_AVAILABLE = False
QISKIT_VERSION = "N/A"

try:
    from qiskit import QuantumCircuit, transpile
    QISKIT_AVAILABLE = True

    # Detect Qiskit version and import appropriate simulator
    try:
        from qiskit import __version__ as _qk_ver
        QISKIT_VERSION = _qk_ver
    except ImportError:
        QISKIT_VERSION = "unknown"

    # Try qiskit-aer (standalone package, Qiskit >= 1.0)
    try:
        from qiskit_aer import AerSimulator
        _SIMULATOR = AerSimulator()
    except ImportError:
        try:
            # Fallback for older Qiskit (< 1.0)
            from qiskit import Aer  # type: ignore[attr-defined]
            _SIMULATOR = Aer.get_backend("aer_simulator")
        except Exception:
            try:
                # Last resort: BasicProvider / BasicSimulator
                from qiskit.providers.basic_provider import BasicSimulator
                _SIMULATOR = BasicSimulator()
            except ImportError:
                warnings.warn(
                    "Qiskit found but no simulator backend available. "
                    "Quantum simulation will be skipped.",
                    RuntimeWarning,
                )
                QISKIT_AVAILABLE = False

except ImportError:
    warnings.warn(
        "Qiskit not installed. Running in classical-only mode. "
        "Install with: pip install qiskit qiskit-aer",
        RuntimeWarning,
    )

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------

# Signal parameters
N_SAMPLES: int = 1024           # Number of samples in the analysis window
FS: int = 2000                  # Sampling rate (Hz)
T_WINDOW: float = N_SAMPLES / FS  # Window duration (seconds)

# Quantum parameters
N_QUBITS_FULL: int = 10        # Qubits for full-resolution pipeline (2^10 = 1024)
N_QUBITS_SIM: int = 6          # Qubits for practical Aer simulation (2^6 = 64)
N_SHOTS: int = 8192             # Measurement shots for quantum simulation

# Echo detection parameters
PEAK_THRESHOLD_RATIO: float = 0.15   # Peak detection threshold (fraction of max)
MIN_QUEFRENCY_SAMPLES: int = 2       # Minimum quefrency index (exclude DC / pulse)
MAX_QUEFRENCY_SAMPLES: int = 80      # Maximum quefrency index (tau_max ~ 40 ms)

# Physical constants
PWV_DEFAULT: float = 7.5        # Pulse wave velocity (m/s), typical aortic value


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class EchoParameters:
    """Parameters for a single arterial echo reflection."""
    name: str           # Anatomical label (e.g. "Brachiocephalic")
    alpha: float        # Effective reflection coefficient
    tau_ms: float       # Round-trip delay in milliseconds
    distance_mm: float  # Estimated distance in millimetres (= tau * PWV / 2)

    @property
    def tau_s(self) -> float:
        """Delay in seconds."""
        return self.tau_ms / 1000.0

    @property
    def sample_index(self) -> int:
        """Delay in samples at the global sampling rate FS."""
        return round(self.tau_ms / 1000.0 * FS)


class DetectedEcho(NamedTuple):
    """An echo detected from cepstral peak analysis."""
    tau_ms: float
    alpha: float
    sample_index: int


# ---------------------------------------------------------------------------
# Default aortic arch echo model
# ---------------------------------------------------------------------------

DEFAULT_ECHOES: List[EchoParameters] = [
    EchoParameters(
        name="Brachiocephalic trunk",
        alpha=0.12,
        tau_ms=1.2,
        distance_mm=1.2e-3 * PWV_DEFAULT / 2 * 1000,
    ),
    EchoParameters(
        name="Left common carotid",
        alpha=0.08,
        tau_ms=2.0,
        distance_mm=2.0e-3 * PWV_DEFAULT / 2 * 1000,
    ),
    EchoParameters(
        name="Left subclavian",
        alpha=0.06,
        tau_ms=2.8,
        distance_mm=2.8e-3 * PWV_DEFAULT / 2 * 1000,
    ),
]


# ===================================================================
# 1. Signal Generation
# ===================================================================

def generate_cardiac_pulse(t: np.ndarray, heart_rate_hz: float = 1.2) -> np.ndarray:
    """
    Generate a synthetic cardiac pressure pulse p(t).

    Uses a sum of Gaussian-modulated sinusoidal components to approximate
    the systolic upstroke, peak, dicrotic notch, and diastolic runoff.

    Parameters
    ----------
    t : ndarray
        Time axis in seconds.
    heart_rate_hz : float
        Fundamental heart rate frequency.

    Returns
    -------
    p : ndarray
        Normalised cardiac pressure pulse.
    """
    T0 = 1.0 / heart_rate_hz
    # Phase within each cardiac cycle
    phase = np.mod(t, T0) / T0

    # Systolic upstroke: sharp Gaussian near phase = 0.1
    systolic = 1.0 * np.exp(-((phase - 0.10) ** 2) / (2 * 0.015 ** 2))

    # Systolic peak / ejection plateau: broader Gaussian
    plateau = 0.7 * np.exp(-((phase - 0.18) ** 2) / (2 * 0.04 ** 2))

    # Dicrotic notch: small negative dip
    notch = -0.15 * np.exp(-((phase - 0.35) ** 2) / (2 * 0.01 ** 2))

    # Diastolic runoff: slow exponential-like decay modelled as broad Gaussian
    diastolic = 0.25 * np.exp(-((phase - 0.40) ** 2) / (2 * 0.10 ** 2))

    # Harmonic components for spectral richness (up to 10th harmonic)
    harmonics = np.zeros_like(t)
    for k in range(1, 11):
        amplitude = 0.15 / k  # 1/k roll-off
        harmonics += amplitude * np.sin(2 * np.pi * k * heart_rate_hz * t + k * 0.3)

    pulse = systolic + plateau + notch + diastolic + harmonics

    # Normalise to unit peak
    pulse = pulse / np.max(np.abs(pulse))
    return pulse


def generate_arterial_signal(
    n_samples: int = N_SAMPLES,
    fs: int = FS,
    echoes: Optional[List[EchoParameters]] = None,
    noise_level: float = 0.005,
    heart_rate_hz: float = 1.2,
) -> Tuple[np.ndarray, np.ndarray, List[EchoParameters]]:
    """
    Generate a synthetic arterial pressure signal with echoes.

    Implements Definition 1.2 from the mathematical framework:
        s(t) = p(t) + sum_i alpha_i * p(t - tau_i)

    Parameters
    ----------
    n_samples : int
        Number of time-domain samples.
    fs : int
        Sampling rate in Hz.
    echoes : list of EchoParameters, optional
        Echo specifications. Defaults to aortic arch bifurcations.
    noise_level : float
        Additive white Gaussian noise standard deviation.
    heart_rate_hz : float
        Fundamental heart rate (Hz).

    Returns
    -------
    signal : ndarray of shape (n_samples,)
        Composite arterial pressure signal s[n].
    time_axis : ndarray of shape (n_samples,)
        Time axis in seconds.
    echoes : list of EchoParameters
        Ground-truth echo parameters used.
    """
    if echoes is None:
        echoes = DEFAULT_ECHOES

    t = np.arange(n_samples) / fs
    pulse = generate_cardiac_pulse(t, heart_rate_hz=heart_rate_hz)

    # Build composite signal: s[n] = p[n] + sum_i alpha_i * p[n - m_i]
    signal = pulse.copy()
    for echo in echoes:
        m_i = echo.sample_index
        if m_i > 0 and m_i < n_samples:
            delayed_pulse = np.zeros(n_samples)
            delayed_pulse[m_i:] = pulse[: n_samples - m_i]
            signal += echo.alpha * delayed_pulse

    # Add measurement noise
    if noise_level > 0:
        rng = np.random.default_rng(seed=42)
        signal += noise_level * rng.standard_normal(n_samples)

    return signal, t, echoes


# ===================================================================
# 2. Classical Cepstral Analysis
# ===================================================================

def classical_cepstral_analysis(
    signal: np.ndarray,
    fs: int = FS,
    threshold_ratio: float = PEAK_THRESHOLD_RATIO,
    min_quefrency: int = MIN_QUEFRENCY_SAMPLES,
    max_quefrency: int = MAX_QUEFRENCY_SAMPLES,
) -> Tuple[np.ndarray, np.ndarray, List[DetectedEcho], np.ndarray]:
    """
    Full classical homomorphic (cepstral) analysis pipeline.

    Pipeline (Theorem 3.1, Definition 4.1):
        1. Window signal with Hamming window
        2. Compute FFT -> S[k]
        3. Compute log|S[k]|  (homomorphic separation)
        4. Compute IFFT -> real cepstrum c[n]
        5. Detect peaks in the cepstral domain (Algorithm 4.1)

    Parameters
    ----------
    signal : ndarray
        Time-domain signal s[n].
    fs : int
        Sampling rate (Hz).
    threshold_ratio : float
        Peak detection threshold as fraction of max cepstral amplitude.
    min_quefrency : int
        Minimum quefrency index for peak search (excludes pulse component).
    max_quefrency : int
        Maximum quefrency index for peak search.

    Returns
    -------
    cepstrum : ndarray
        Real cepstrum c[n].
    quefrency : ndarray
        Quefrency axis in milliseconds.
    detected : list of DetectedEcho
        Detected echo parameters.
    spectrum_mag : ndarray
        Magnitude spectrum |S[k]| (for plotting).
    """
    n = len(signal)

    # Step 1: Apply Hamming window (reduces spectral leakage)
    window = hamming(n)
    windowed = signal * window

    # Step 2: FFT
    spectrum = fft(windowed, n=n)
    spectrum_mag = np.abs(spectrum)

    # Step 3: Log-magnitude (with floor to avoid log(0))
    log_spectrum = np.log(np.maximum(spectrum_mag, 1e-12))

    # Step 4: Inverse FFT to get real cepstrum
    cepstrum = np.real(ifft(log_spectrum))

    # Step 5: Peak detection (Algorithm 4.1)
    # Liftering: restrict search to the echo quefrency range
    search_region = cepstrum[min_quefrency: min(max_quefrency, n // 2)]
    threshold = threshold_ratio * np.max(np.abs(search_region))

    peaks, properties = find_peaks(
        search_region,
        height=threshold,
        distance=1,  # Minimum 1-sample separation
    )

    # Adjust peak indices to global cepstrum indexing
    peaks_global = peaks + min_quefrency

    # Extract echo parameters (Theorem 4.2: alpha_i = 2 * c[m_i])
    detected: List[DetectedEcho] = []
    for idx in peaks_global:
        tau_ms = (idx / fs) * 1000.0
        alpha_est = 2.0 * cepstrum[idx]  # Theorem 4.2
        detected.append(DetectedEcho(tau_ms=tau_ms, alpha=alpha_est, sample_index=idx))

    # Sort by delay
    detected.sort(key=lambda e: e.tau_ms)

    # Quefrency axis in milliseconds
    quefrency = np.arange(n) / fs * 1000.0

    return cepstrum, quefrency, detected, spectrum_mag


# ===================================================================
# 3. Quantum Circuit Construction
# ===================================================================

def _normalize_for_amplitude_encoding(data: np.ndarray) -> np.ndarray:
    """
    Normalise a real-valued array for amplitude encoding into a quantum state.

    Shifts all values to be non-negative (offset encoding from Section 5.3),
    then normalises to unit L2 norm. Returns the normalised array of length
    2^ceil(log2(len(data))), zero-padded if necessary.
    """
    # Offset to make non-negative (Section 5.3: offset encoding)
    offset = np.min(data)
    shifted = data - offset if offset < 0 else data.copy()

    # Ensure at least a small positive baseline to avoid all-zero
    if np.max(shifted) < 1e-15:
        shifted += 1e-10

    norm = np.linalg.norm(shifted)
    if norm > 0:
        shifted = shifted / norm

    return shifted


def build_qft_circuit(n_qubits: int) -> QuantumCircuit:
    """
    Construct the Quantum Fourier Transform circuit on n qubits.

    Implements Algorithm 5.1 from the mathematical framework:
        For each qubit q_j (j = 0 .. n-1):
            1. Apply Hadamard to q_j
            2. Apply controlled-R_k rotations with controls q_{j+1} .. q_{n-1}
        Finish with SWAP gates for bit reversal.

    Gate count (Section 6.1):
        Hadamard:    n
        Controlled:  n*(n-1)/2
        SWAP:        floor(n/2)

    Parameters
    ----------
    n_qubits : int
        Number of qubits.

    Returns
    -------
    qc : QuantumCircuit
        QFT circuit (without measurements).
    """
    qc = QuantumCircuit(n_qubits, name="QFT")

    for j in range(n_qubits):
        qc.h(j)
        for k in range(j + 1, n_qubits):
            # Controlled phase rotation R_{k-j+1}: angle = 2*pi / 2^{k-j+1}
            angle = 2 * np.pi / (2 ** (k - j + 1))
            qc.cp(angle, k, j)

    # Bit-reversal SWAP network
    for j in range(n_qubits // 2):
        qc.swap(j, n_qubits - j - 1)

    return qc


def build_inverse_qft_circuit(n_qubits: int) -> QuantumCircuit:
    """
    Construct the inverse QFT circuit (QFT-dagger).

    The inverse QFT is the QFT circuit run in reverse with negated
    rotation angles (Definition 5.4).

    Parameters
    ----------
    n_qubits : int
        Number of qubits.

    Returns
    -------
    qc : QuantumCircuit
        Inverse QFT circuit.
    """
    qc = build_qft_circuit(n_qubits)
    qc = qc.inverse()
    qc.name = "QFT_dagger"
    return qc


def build_quantum_cepstral_circuit(
    signal_amplitudes: np.ndarray,
    n_qubits: int = N_QUBITS_SIM,
    label: str = "QCepstral",
) -> QuantumCircuit:
    """
    Build a quantum circuit for one stage of the hybrid cepstral pipeline.

    For the hybrid approach (Section 5.6, Approach C), this circuit performs:
        |0>^n  --[Amplitude Encode]--> |psi>  --[QFT]--> |Psi>  --[Measure]-->

    The circuit amplitude-encodes the (downsampled, normalised) input data
    and applies the QFT. Measurements in the computational basis yield
    samples from |S[k]|^2 (the power spectrum).

    Parameters
    ----------
    signal_amplitudes : ndarray
        Normalised amplitude vector of length 2^n_qubits. Must have unit L2 norm.
    n_qubits : int
        Number of qubits (determines state dimension 2^n_qubits).
    label : str
        Circuit label for display.

    Returns
    -------
    qc : QuantumCircuit
        Complete circuit with amplitude encoding + QFT + measurement.
    """
    N = 2 ** n_qubits

    if len(signal_amplitudes) != N:
        raise ValueError(
            f"Signal length {len(signal_amplitudes)} != 2^{n_qubits} = {N}"
        )

    # Ensure unit-norm for valid quantum state
    norm = np.linalg.norm(signal_amplitudes)
    if abs(norm - 1.0) > 1e-6:
        signal_amplitudes = signal_amplitudes / norm

    qc = QuantumCircuit(n_qubits, n_qubits, name=label)

    # --- Stage 1: Amplitude encoding ---
    # Qiskit's initialize() prepares an arbitrary quantum state from amplitudes.
    # Complexity is O(2^n) gates for generic state (Section 5.3).
    qc.initialize(signal_amplitudes.tolist(), range(n_qubits))

    qc.barrier(label="Encode|QFT")

    # --- Stage 2: QFT ---
    qft = build_qft_circuit(n_qubits)
    qc.compose(qft, range(n_qubits), inplace=True)

    qc.barrier(label="QFT|Meas")

    # --- Stage 3: Measurement ---
    qc.measure(range(n_qubits), range(n_qubits))

    return qc


# ===================================================================
# 4. Quantum Simulation
# ===================================================================

def _downsample_signal(signal: np.ndarray, target_length: int) -> np.ndarray:
    """
    Downsample a signal to target_length using linear interpolation.

    For going from N_SAMPLES (1024) down to 2^N_QUBITS_SIM (e.g. 64).
    """
    n_orig = len(signal)
    if n_orig == target_length:
        return signal.copy()

    x_orig = np.linspace(0, 1, n_orig)
    x_new = np.linspace(0, 1, target_length)
    return np.interp(x_new, x_orig, signal)


def _counts_to_probability_vector(
    counts: dict, n_qubits: int
) -> np.ndarray:
    """
    Convert Qiskit measurement counts to a probability distribution vector.

    Parameters
    ----------
    counts : dict
        Measurement counts {bitstring: count}.
    n_qubits : int
        Number of qubits.

    Returns
    -------
    prob : ndarray of shape (2^n_qubits,)
        Probability for each computational basis state.
    """
    N = 2 ** n_qubits
    prob = np.zeros(N)
    total = sum(counts.values())

    for bitstring, count in counts.items():
        # Qiskit returns bitstrings with qubit 0 as rightmost
        idx = int(bitstring, 2)
        prob[idx] = count / total

    return prob


def run_quantum_cepstral_analysis(
    signal: np.ndarray,
    fs: int = FS,
    n_qubits: int = N_QUBITS_SIM,
    n_shots: int = N_SHOTS,
    threshold_ratio: float = PEAK_THRESHOLD_RATIO,
    min_quefrency: int = MIN_QUEFRENCY_SAMPLES,
    max_quefrency: int = MAX_QUEFRENCY_SAMPLES,
) -> Tuple[np.ndarray, np.ndarray, List[DetectedEcho], dict]:
    """
    Hybrid classical-quantum cepstral analysis (Approach C, Section 5.6).

    Pipeline:
        Round 1:  Encode s[n] -> QFT -> Measure -> estimate |S[k]|^2
        Classical: Compute log|S[k]| from measurement probabilities
        Round 2:  Encode log|S[k]| -> IQFT -> Measure -> approximate cepstrum
        Detect:   Find peaks in the quantum cepstrum

    Parameters
    ----------
    signal : ndarray
        Time-domain signal s[n].
    fs : int
        Sampling rate (Hz).
    n_qubits : int
        Number of qubits for quantum simulation.
    n_shots : int
        Number of measurement shots per circuit execution.
    threshold_ratio : float
        Peak detection threshold.
    min_quefrency : int
        Minimum quefrency sample index for peak search.
    max_quefrency : int
        Maximum quefrency sample index for peak search.

    Returns
    -------
    quantum_cepstrum : ndarray
        Approximate cepstrum from quantum pipeline.
    quefrency : ndarray
        Quefrency axis in milliseconds (at the downsampled rate).
    detected : list of DetectedEcho
        Detected echo parameters.
    metadata : dict
        Diagnostic information (circuit depth, gate count, etc.).
    """
    if not QISKIT_AVAILABLE:
        raise RuntimeError(
            "Qiskit is not available. Cannot run quantum simulation."
        )

    N_q = 2 ** n_qubits
    # Effective sampling rate for the downsampled signal
    fs_q = fs * N_q / N_SAMPLES  # preserves time scaling

    # ------------------------------------------------------------------
    # Round 1: QFT to estimate the power spectrum
    # ------------------------------------------------------------------

    # Downsample and normalise for amplitude encoding
    signal_ds = _downsample_signal(signal, N_q)
    signal_norm = _normalize_for_amplitude_encoding(signal_ds)

    # Build and simulate the QFT circuit
    qc_fft = build_quantum_cepstral_circuit(signal_norm, n_qubits, label="QFT_round")

    # Transpile for the simulator
    qc_fft_t = transpile(qc_fft, _SIMULATOR)

    result_fft = _SIMULATOR.run(qc_fft_t, shots=n_shots).result()
    counts_fft = result_fft.get_counts()

    # Convert counts to approximate |S[k]|^2 (probability ~ |amplitude|^2)
    power_spectrum_q = _counts_to_probability_vector(counts_fft, n_qubits)

    # ------------------------------------------------------------------
    # Classical interlude: compute log|S[k]|
    # ------------------------------------------------------------------

    # |S[k]| ~ sqrt(probability * N_q) -- approximate amplitude recovery
    # (probability = |<k|Psi>|^2, so amplitude ~ sqrt(prob))
    mag_spectrum_q = np.sqrt(np.maximum(power_spectrum_q, 1e-15))
    log_spectrum_q = np.log(np.maximum(mag_spectrum_q, 1e-12))

    # ------------------------------------------------------------------
    # Round 2: IQFT to compute the cepstrum
    # ------------------------------------------------------------------

    log_norm = _normalize_for_amplitude_encoding(log_spectrum_q)

    # Build IQFT circuit: Encode log|S[k]| -> IQFT -> Measure
    qc_ifft = QuantumCircuit(n_qubits, n_qubits, name="IQFT_round")
    qc_ifft.initialize(log_norm.tolist(), range(n_qubits))
    qc_ifft.barrier()

    iqft = build_inverse_qft_circuit(n_qubits)
    qc_ifft.compose(iqft, range(n_qubits), inplace=True)
    qc_ifft.barrier()
    qc_ifft.measure(range(n_qubits), range(n_qubits))

    qc_ifft_t = transpile(qc_ifft, _SIMULATOR)
    result_ifft = _SIMULATOR.run(qc_ifft_t, shots=n_shots).result()
    counts_ifft = result_ifft.get_counts()

    # Convert to approximate cepstrum
    cepstrum_prob = _counts_to_probability_vector(counts_ifft, n_qubits)

    # The cepstrum amplitudes are approximated from the measurement distribution.
    # Higher probability at index n => larger cepstral coefficient magnitude.
    # We use sqrt(prob) as a proxy for the coefficient magnitude.
    quantum_cepstrum = np.sqrt(np.maximum(cepstrum_prob, 0))

    # Subtract baseline (mean of cepstrum beyond the pulse region)
    baseline_region = quantum_cepstrum[max(4, min_quefrency):]
    if len(baseline_region) > 0:
        baseline = np.median(baseline_region)
        quantum_cepstrum_detrended = quantum_cepstrum - baseline
    else:
        quantum_cepstrum_detrended = quantum_cepstrum.copy()

    # ------------------------------------------------------------------
    # Peak detection in the quantum cepstrum
    # ------------------------------------------------------------------

    # Scale quefrency indices from quantum resolution back to original time
    # The downsampled signal has effective fs_q, so quefrency index i corresponds
    # to delay i / fs_q seconds. But since we preserved the time window,
    # index i in the quantum cepstrum maps to t = i * T_WINDOW / N_q.
    quefrency_s = np.arange(N_q) * T_WINDOW / N_q  # seconds
    quefrency_ms = quefrency_s * 1000.0

    # Search within the echo quefrency range
    # Map physical quefrency bounds to quantum sample indices
    min_q_idx = max(2, int(np.ceil(min_quefrency * N_q / N_SAMPLES)))
    max_q_idx = min(N_q // 2, int(np.floor(max_quefrency * N_q / N_SAMPLES)))

    if max_q_idx <= min_q_idx:
        max_q_idx = N_q // 2

    search_region = quantum_cepstrum_detrended[min_q_idx:max_q_idx]

    if len(search_region) > 0 and np.max(search_region) > 0:
        threshold = threshold_ratio * np.max(np.abs(search_region))
        peaks, _ = find_peaks(search_region, height=threshold, distance=1)
        peaks_global = peaks + min_q_idx
    else:
        peaks_global = np.array([], dtype=int)

    detected: List[DetectedEcho] = []
    for idx in peaks_global:
        tau_ms = quefrency_ms[idx]
        # Rough alpha estimate from quantum measurement statistics
        alpha_est = 2.0 * quantum_cepstrum[idx]
        detected.append(DetectedEcho(tau_ms=tau_ms, alpha=alpha_est, sample_index=idx))

    detected.sort(key=lambda e: e.tau_ms)

    # ------------------------------------------------------------------
    # Collect metadata
    # ------------------------------------------------------------------
    # Get gate counts from transpiled circuit
    try:
        gate_count_fft = qc_fft_t.count_ops()
        depth_fft = qc_fft_t.depth()
    except Exception:
        gate_count_fft = {}
        depth_fft = 0

    metadata = {
        "n_qubits": n_qubits,
        "n_shots": n_shots,
        "quantum_N": N_q,
        "effective_fs": fs_q,
        "quefrency_resolution_ms": T_WINDOW / N_q * 1000.0,
        "qft_gate_count": dict(gate_count_fft),
        "qft_circuit_depth": depth_fft,
        "qiskit_version": QISKIT_VERSION,
    }

    return quantum_cepstrum, quefrency_ms, detected, metadata


# ===================================================================
# 5. Visualisation
# ===================================================================

def plot_results(
    signal: np.ndarray,
    time_axis: np.ndarray,
    ground_truth: List[EchoParameters],
    spectrum_mag: np.ndarray,
    cepstrum_classical: np.ndarray,
    quefrency_classical: np.ndarray,
    detected_classical: List[DetectedEcho],
    quantum_cepstrum: Optional[np.ndarray] = None,
    quefrency_quantum: Optional[np.ndarray] = None,
    detected_quantum: Optional[List[DetectedEcho]] = None,
    quantum_metadata: Optional[dict] = None,
    output_path: str = "/Users/agustinazwiener/evolvingagents/skillos/projects/Project_aorta/output/quantum_aorta_results.png",
) -> None:
    """
    Create a multi-panel figure comparing classical and quantum cepstral analysis.

    Panels:
        (a) Time-domain signal with echo positions annotated
        (b) Magnitude spectrum |S[k]|
        (c) Classical real cepstrum with detected peaks
        (d) Quantum cepstrum approximation (or placeholder if unavailable)

    Parameters
    ----------
    signal : ndarray
        Time-domain signal.
    time_axis : ndarray
        Time axis (seconds).
    ground_truth : list of EchoParameters
        True echo parameters.
    spectrum_mag : ndarray
        Magnitude spectrum from classical FFT.
    cepstrum_classical : ndarray
        Classical real cepstrum.
    quefrency_classical : ndarray
        Classical quefrency axis (ms).
    detected_classical : list of DetectedEcho
        Classically detected echoes.
    quantum_cepstrum : ndarray, optional
        Quantum cepstrum approximation.
    quefrency_quantum : ndarray, optional
        Quantum quefrency axis (ms).
    detected_quantum : list of DetectedEcho, optional
        Quantum-detected echoes.
    quantum_metadata : dict, optional
        Quantum simulation metadata.
    output_path : str
        Path for the output PNG file.
    """
    fig = plt.figure(figsize=(16, 14))
    gs = GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.30)

    # Colour palette
    COL_SIGNAL = "#1f77b4"
    COL_ECHO_TRUE = "#d62728"
    COL_PEAK_CLASSICAL = "#2ca02c"
    COL_PEAK_QUANTUM = "#9467bd"
    COL_SPECTRUM = "#ff7f0e"
    COL_CEPSTRUM = "#17becf"
    COL_QUANTUM = "#9467bd"

    # ------------------------------------------------------------------
    # (a) Time-domain signal — top left
    # ------------------------------------------------------------------
    ax_time = fig.add_subplot(gs[0, 0])
    ax_time.plot(time_axis * 1000, signal, color=COL_SIGNAL, linewidth=0.8, alpha=0.9)
    for echo in ground_truth:
        ax_time.axvline(
            echo.tau_ms, color=COL_ECHO_TRUE, linestyle="--", linewidth=1.2,
            alpha=0.7, label=f"{echo.name} ({echo.tau_ms:.1f} ms)"
        )
    ax_time.set_xlabel("Time (ms)")
    ax_time.set_ylabel("Pressure (normalised)")
    ax_time.set_title("(a) Arterial Pressure Signal with Echo Positions")
    ax_time.set_xlim(0, 30)  # Zoom in to show echo region
    ax_time.legend(fontsize=7, loc="upper right")
    ax_time.grid(True, alpha=0.3)

    # ------------------------------------------------------------------
    # (b) Magnitude spectrum — top right
    # ------------------------------------------------------------------
    ax_spec = fig.add_subplot(gs[0, 1])
    n = len(spectrum_mag)
    freq_axis = np.arange(n // 2) * FS / n
    ax_spec.plot(freq_axis, 20 * np.log10(spectrum_mag[: n // 2] + 1e-12),
                 color=COL_SPECTRUM, linewidth=0.6)
    ax_spec.set_xlabel("Frequency (Hz)")
    ax_spec.set_ylabel("Magnitude (dB)")
    ax_spec.set_title("(b) Magnitude Spectrum |S[k]|")
    ax_spec.set_xlim(0, 200)  # Show up to 200 Hz
    ax_spec.grid(True, alpha=0.3)

    # ------------------------------------------------------------------
    # (c) Classical cepstrum — middle, full width
    # ------------------------------------------------------------------
    ax_ceps = fig.add_subplot(gs[1, :])

    # Plot cepstrum in the echo quefrency range
    q_max_plot = 10.0  # ms
    mask = quefrency_classical <= q_max_plot
    ax_ceps.plot(
        quefrency_classical[mask], cepstrum_classical[mask],
        color=COL_CEPSTRUM, linewidth=1.0, label="Classical cepstrum"
    )

    # Mark ground truth echo positions
    for echo in ground_truth:
        ax_ceps.axvline(
            echo.tau_ms, color=COL_ECHO_TRUE, linestyle=":", linewidth=1.0, alpha=0.6
        )
        ax_ceps.annotate(
            f"GT: {echo.tau_ms:.1f} ms\n(a={echo.alpha:.2f})",
            xy=(echo.tau_ms, 0), xytext=(echo.tau_ms + 0.2, np.max(cepstrum_classical[mask]) * 0.7),
            fontsize=7, color=COL_ECHO_TRUE,
            arrowprops=dict(arrowstyle="->", color=COL_ECHO_TRUE, lw=0.8),
        )

    # Mark classical detected peaks
    for det in detected_classical:
        if det.tau_ms <= q_max_plot:
            ax_ceps.plot(
                det.tau_ms, cepstrum_classical[det.sample_index],
                "v", color=COL_PEAK_CLASSICAL, markersize=10,
                label=f"Classical: {det.tau_ms:.2f} ms (a={det.alpha:.3f})"
            )

    ax_ceps.set_xlabel("Quefrency (ms)")
    ax_ceps.set_ylabel("Cepstral Amplitude")
    ax_ceps.set_title(
        "(c) Classical Real Cepstrum with Echo Detection"
    )
    ax_ceps.legend(fontsize=7, loc="upper right")
    ax_ceps.grid(True, alpha=0.3)

    # ------------------------------------------------------------------
    # (d) Quantum cepstrum — bottom, full width
    # ------------------------------------------------------------------
    ax_quant = fig.add_subplot(gs[2, :])

    if quantum_cepstrum is not None and quefrency_quantum is not None:
        q_max_q = 10.0  # ms
        mask_q = quefrency_quantum <= q_max_q

        ax_quant.plot(
            quefrency_quantum[mask_q], quantum_cepstrum[mask_q],
            color=COL_QUANTUM, linewidth=1.0, label="Quantum cepstrum (hybrid)"
        )

        # Mark ground truth
        for echo in ground_truth:
            ax_quant.axvline(
                echo.tau_ms, color=COL_ECHO_TRUE, linestyle=":", linewidth=1.0, alpha=0.6
            )

        # Mark quantum detected peaks
        if detected_quantum:
            for det in detected_quantum:
                if det.tau_ms <= q_max_q:
                    ax_quant.plot(
                        det.tau_ms, quantum_cepstrum[det.sample_index],
                        "^", color=COL_PEAK_QUANTUM, markersize=10,
                        label=f"Quantum: {det.tau_ms:.2f} ms (a~{det.alpha:.3f})"
                    )

        # Add metadata annotation
        if quantum_metadata:
            meta_text = (
                f"Qubits: {quantum_metadata['n_qubits']}  |  "
                f"N = {quantum_metadata['quantum_N']}  |  "
                f"Shots: {quantum_metadata['n_shots']}  |  "
                f"Quefrency res: {quantum_metadata['quefrency_resolution_ms']:.2f} ms"
            )
            ax_quant.text(
                0.02, 0.95, meta_text, transform=ax_quant.transAxes,
                fontsize=7, verticalalignment="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.8),
            )

        ax_quant.legend(fontsize=7, loc="upper right")
    else:
        ax_quant.text(
            0.5, 0.5,
            "Quantum simulation unavailable\n(Qiskit not installed)",
            transform=ax_quant.transAxes, fontsize=14,
            ha="center", va="center", color="gray",
        )

    ax_quant.set_xlabel("Quefrency (ms)")
    ax_quant.set_ylabel("Cepstral Amplitude (approx.)")
    ax_quant.set_title("(d) Quantum Cepstrum (Hybrid Approach C: QFT + Classical Log + IQFT)")
    ax_quant.grid(True, alpha=0.3)

    # ------------------------------------------------------------------
    # Suptitle and save
    # ------------------------------------------------------------------
    fig.suptitle(
        "Project Aorta: Quantum Homomorphic Signal Processing\n"
        "Arterial Echo Detection via Classical & Quantum Cepstral Analysis",
        fontsize=14, fontweight="bold", y=0.98,
    )

    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"\n[Plot saved to {output_path}]")


# ===================================================================
# 6. Results Comparison and Reporting
# ===================================================================

def compare_results(
    ground_truth: List[EchoParameters],
    detected_classical: List[DetectedEcho],
    detected_quantum: Optional[List[DetectedEcho]],
    quantum_metadata: Optional[dict],
) -> None:
    """
    Print a formatted comparison of ground truth vs. detected echoes.

    Parameters
    ----------
    ground_truth : list of EchoParameters
        True echo parameters.
    detected_classical : list of DetectedEcho
        Classical cepstral detections.
    detected_quantum : list of DetectedEcho or None
        Quantum cepstral detections.
    quantum_metadata : dict or None
        Quantum simulation metadata.
    """
    sep = "=" * 78
    thin_sep = "-" * 78

    print(f"\n{sep}")
    print("  PROJECT AORTA: ECHO DETECTION RESULTS")
    print(f"  Quantum Homomorphic Signal Processing for Arterial Echo Detection")
    print(sep)

    # --- Ground Truth ---
    print(f"\n{'GROUND TRUTH ECHOES':^78}")
    print(thin_sep)
    print(f"  {'Reflector':<28} {'alpha':>8} {'tau (ms)':>10} {'m (samples)':>12} {'d (mm)':>10}")
    print(thin_sep)
    for echo in ground_truth:
        print(
            f"  {echo.name:<28} {echo.alpha:>8.4f} {echo.tau_ms:>10.2f} "
            f"{echo.sample_index:>12d} {echo.distance_mm:>10.2f}"
        )

    # --- Classical Results ---
    print(f"\n{'CLASSICAL CEPSTRAL DETECTION':^78}")
    print(thin_sep)
    if detected_classical:
        print(f"  {'#':>3} {'tau_det (ms)':>12} {'alpha_det':>10} {'m_det':>8} {'Nearest GT':>16} {'Error (ms)':>12}")
        print(thin_sep)
        for i, det in enumerate(detected_classical):
            # Find nearest ground truth echo
            if ground_truth:
                errors = [abs(det.tau_ms - gt.tau_ms) for gt in ground_truth]
                best_idx = int(np.argmin(errors))
                nearest_name = ground_truth[best_idx].name.split()[0]
                error_ms = det.tau_ms - ground_truth[best_idx].tau_ms
            else:
                nearest_name = "N/A"
                error_ms = float("nan")
            print(
                f"  {i+1:>3} {det.tau_ms:>12.3f} {det.alpha:>10.4f} "
                f"{det.sample_index:>8d} {nearest_name:>16} {error_ms:>+12.3f}"
            )
    else:
        print("  No echoes detected by classical cepstral analysis.")

    # --- Quantum Results ---
    print(f"\n{'QUANTUM CEPSTRAL DETECTION (HYBRID APPROACH C)':^78}")
    print(thin_sep)

    if quantum_metadata:
        print(f"  Qiskit version:      {quantum_metadata.get('qiskit_version', 'N/A')}")
        print(f"  Qubits:              {quantum_metadata.get('n_qubits', 'N/A')}")
        print(f"  Quantum state dim:   {quantum_metadata.get('quantum_N', 'N/A')}")
        print(f"  Measurement shots:   {quantum_metadata.get('n_shots', 'N/A')}")
        print(f"  Quefrency resolution:{quantum_metadata.get('quefrency_resolution_ms', 0):.3f} ms")
        print(f"  QFT circuit depth:   {quantum_metadata.get('qft_circuit_depth', 'N/A')}")
        print(f"  QFT gate breakdown:  {quantum_metadata.get('qft_gate_count', {})}")
        print(thin_sep)

    if detected_quantum:
        print(f"  {'#':>3} {'tau_det (ms)':>12} {'alpha_est':>10} {'Nearest GT':>16} {'Error (ms)':>12}")
        print(thin_sep)
        for i, det in enumerate(detected_quantum):
            if ground_truth:
                errors = [abs(det.tau_ms - gt.tau_ms) for gt in ground_truth]
                best_idx = int(np.argmin(errors))
                nearest_name = ground_truth[best_idx].name.split()[0]
                error_ms = det.tau_ms - ground_truth[best_idx].tau_ms
            else:
                nearest_name = "N/A"
                error_ms = float("nan")
            print(
                f"  {i+1:>3} {det.tau_ms:>12.3f} {det.alpha:>10.4f} "
                f"{nearest_name:>16} {error_ms:>+12.3f}"
            )
    elif not QISKIT_AVAILABLE:
        print("  Qiskit not installed -- quantum analysis skipped.")
    else:
        print("  No echoes detected by quantum cepstral analysis.")

    # --- Resolution Comparison ---
    print(f"\n{'RESOLUTION COMPARISON (Theorem 7.2 vs 7.1)':^78}")
    print(thin_sep)

    B_eff = 20.0  # Hz, effective bandwidth of cardiac signal
    delta_q_classical_ms = (1.0 / B_eff) * 1000.0

    print(f"  Classical quefrency resolution:  {delta_q_classical_ms:.1f} ms  (1/B = 1/{B_eff:.0f} Hz)")
    print(f"  Classical distance resolution:   {delta_q_classical_ms * 1e-3 * PWV_DEFAULT / 2 * 1000:.1f} mm  (at PWV = {PWV_DEFAULT} m/s)")
    print()

    if quantum_metadata:
        n_q = quantum_metadata["n_qubits"]
        N_q = quantum_metadata["quantum_N"]
        delta_q_quantum_ms = T_WINDOW / N_q * 1000.0
        enhancement = delta_q_classical_ms / delta_q_quantum_ms if delta_q_quantum_ms > 0 else 0
        print(f"  Quantum quefrency resolution:   {delta_q_quantum_ms:.2f} ms  (T_window / 2^n = {T_WINDOW*1000:.0f} ms / {N_q})")
        print(f"  Quantum distance resolution:    {delta_q_quantum_ms * 1e-3 * PWV_DEFAULT / 2 * 1000:.2f} mm")
        print(f"  Enhancement factor:             {enhancement:.1f}x")
        print()
        print(f"  Full-scale (n=10, N=1024):")
        delta_full = T_WINDOW / 1024 * 1000.0
        enh_full = delta_q_classical_ms / delta_full
        print(f"    Quefrency resolution:         {delta_full:.2f} ms")
        print(f"    Distance resolution:           {delta_full * 1e-3 * PWV_DEFAULT / 2 * 1000:.2f} mm")
        print(f"    Enhancement factor:            {enh_full:.0f}x")
    else:
        print("  Quantum resolution data unavailable (Qiskit not installed).")

    print(f"\n{sep}")
    print("  Pipeline: s[n] -> FFT/QFT -> log|.| -> IFFT/IQFT -> Cepstrum -> Peaks")
    print(f"  Reference: Project Aorta Mathematical Framework, Sections 3-8")
    print(sep)


# ===================================================================
# 7. Main Execution
# ===================================================================

def main() -> None:
    """
    Execute the complete Project Aorta analysis pipeline.

    Steps:
        1. Generate synthetic arterial signal with known echoes
        2. Run classical cepstral analysis
        3. Run quantum cepstral analysis (if Qiskit available)
        4. Compare results and generate visualisation
    """
    print("=" * 78)
    print("  Project Aorta: Quantum Homomorphic Signal Processing")
    print("  Arterial Echo Detection Pipeline")
    print("=" * 78)

    # ------------------------------------------------------------------
    # Step 1: Generate arterial signal with known echoes
    # ------------------------------------------------------------------
    print("\n[1/4] Generating synthetic arterial signal...")
    print(f"      N = {N_SAMPLES}, fs = {FS} Hz, T_window = {T_WINDOW*1000:.0f} ms")

    signal, time_axis, ground_truth = generate_arterial_signal()

    echo_summary = ", ".join(
        f"{e.name} (a={e.alpha}, tau={e.tau_ms} ms)" for e in ground_truth
    )
    print(f"      Echoes: {echo_summary}")
    print(f"      Signal range: [{signal.min():.4f}, {signal.max():.4f}]")

    # ------------------------------------------------------------------
    # Step 2: Classical cepstral analysis
    # ------------------------------------------------------------------
    print("\n[2/4] Running classical cepstral analysis...")

    cepstrum_cl, quefrency_cl, detected_cl, spectrum_mag = classical_cepstral_analysis(signal)

    print(f"      Detected {len(detected_cl)} echoes:")
    for det in detected_cl:
        print(f"        tau = {det.tau_ms:.3f} ms, alpha = {det.alpha:.4f} (sample {det.sample_index})")

    # ------------------------------------------------------------------
    # Step 3: Quantum cepstral analysis
    # ------------------------------------------------------------------
    quantum_cepstrum = None
    quefrency_quantum = None
    detected_quantum = None
    quantum_metadata = None

    if QISKIT_AVAILABLE:
        print(f"\n[3/4] Running quantum cepstral analysis (hybrid Approach C)...")
        print(f"      Qiskit version: {QISKIT_VERSION}")
        print(f"      Qubits: {N_QUBITS_SIM}, N_quantum = {2**N_QUBITS_SIM}")
        print(f"      Shots: {N_SHOTS}")

        try:
            quantum_cepstrum, quefrency_quantum, detected_quantum, quantum_metadata = \
                run_quantum_cepstral_analysis(signal)

            print(f"      QFT circuit depth: {quantum_metadata.get('qft_circuit_depth', 'N/A')}")
            print(f"      Quefrency resolution: {quantum_metadata.get('quefrency_resolution_ms', 0):.2f} ms")
            print(f"      Detected {len(detected_quantum)} echoes:")
            for det in detected_quantum:
                print(f"        tau = {det.tau_ms:.3f} ms, alpha ~ {det.alpha:.4f}")
        except Exception as exc:
            print(f"      [WARNING] Quantum simulation failed: {exc}")
            print("      Falling back to classical-only results.")
    else:
        print(f"\n[3/4] Quantum analysis SKIPPED (Qiskit not installed).")
        print("      Install with: pip install qiskit qiskit-aer")

    # ------------------------------------------------------------------
    # Step 4: Visualisation and comparison
    # ------------------------------------------------------------------
    print("\n[4/4] Generating visualisation and comparison report...")

    plot_results(
        signal=signal,
        time_axis=time_axis,
        ground_truth=ground_truth,
        spectrum_mag=spectrum_mag,
        cepstrum_classical=cepstrum_cl,
        quefrency_classical=quefrency_cl,
        detected_classical=detected_cl,
        quantum_cepstrum=quantum_cepstrum,
        quefrency_quantum=quefrency_quantum,
        detected_quantum=detected_quantum,
        quantum_metadata=quantum_metadata,
    )

    compare_results(ground_truth, detected_cl, detected_quantum, quantum_metadata)

    print("\nPipeline complete.")


if __name__ == "__main__":
    main()
