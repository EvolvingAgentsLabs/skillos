import numpy as np
from qiskit import QuantumCircuit, Aer, execute
from qiskit.circuit.library import QFT
import matplotlib.pyplot as plt

"""
Project Aorta: Quantum Homomorphic Signal Processing Simulation

This script simulates the quantum-inspired approach to detecting echo delays 
in an arterial pressure signal using QFT-based spectral analysis.
"""

def generate_synthetic_arterial_signal(n_samples=64, delay=8, alpha=0.5):
    """Generates a synthetic pulse and its echo."""
    t = np.linspace(0, 1, n_samples)
    # Simple low-frequency pulse (sine wave approximation)
    pulse = np.sin(2 * np.pi * 1 * t)
    
    # Create the signal with echo
    signal = np.zeros(n_samples)
    for i in range(n_samples):
        echo_idx = i - delay
        if echo_idx >= 0:
            signal[i] = pulse[i] + alpha * pulse[echo_idx]
        else:
            signal[i] = pulse[i]
            
    # Ensure signal is real and positive for amplitude encoding simulation
    signal = (signal - np.min(signal)) / (np.max(signal) - np.min(signal))
    return signal, pulse

def simulate_quantum_cepstrum(signal):
    """
    Simulates the quantum pipeline:
    1. Amplitude encoding (conceptual)
    2. QFT (Frequency domain)
    3. Log-magnitude (Homomorphic step)
    4. IQFT (Cepstral domain)
    """
    n = len(signal)
    num_qubits = int(np.ceil(np.log2(n)))
    
    # 1. Simulate Frequency Domain via QFT
    # In a real quantum computer, we would use amplitude encoding.
    # Here we simulate the result of the QFT operation on the signal.
    signal_fft = np.fft.fft(signal)
    magnitude_spectrum = np.abs(signal_fft)
    
    # 2. Homomorphic Step: Logarithm
    # We add a small epsilon to avoid log(0)
    log_magnitude = np.log(magnitude_spectrum + 1e-10)
    
    # 3. Inverse QFT (Cepstrum)
    # Mapping back to the quefrency domain
    cepstrum = np.real(np.fft.ifft(log_magnitude))
    
    return cepstrum

def run_experiment():
    print("--- Initializing Project Aorta Quantum Simulation ---")
    
    # Parameters
    N = 64
    DELAY = 8
    ALPHA = 0.6
    
    # Step 1: Generate Signal
    signal, pulse = generate_synthetic_arterial_signal(n_samples=N, delay=DELAY, alpha=ALPHA)
    print(f"[INFO] Signal generated. Expected Echo Delay: {DELAY} samples.")

    # Step 2: Run Simulated Quantum Pipeline
    cepstrum = simulate_quantum_cepstrum(signal)
    print("[INFO] Quantum Homomorphic Pipeline execution complete.")

    # Step 3: Analyze Results
    detected_delay = np.argmax(cepstrum)
    print(f"[RESULT] Detected Quefrency Peak at: {detected_delay}")
    
    if detected_delay == DELAY:
        print("[SUCCESS] Echo delay matched clinical expectation.")
    else:
        print("[FAILURE] Echo delay mismatch.")

    # Visualization
    fig, axs = plt.subplots(3, 1, figsize=(10, 12))

    axs[0].plot(signal, color='blue')
    axs[0].set_title("Time Domain: Arterial Pressure Signal $s(t)$ (Pulse + Echo)")
    axs[0].set_xlabel("Samples")
    axs[0].set_ylabel("Amplitude")

    axs[1].plot(np.abs(np.fft.fft(signal)), color='green')
    axs[1].set_title("Frequency Domain: Magnitude Spectrum $|S(\omega)|$")
    axs[1].set_xlabel("Frequency Bin")
    axs[1].set_ylabel("Magnitude")

    axs[2].plot(cepstrum, color='red')
    axs[2].set_title("Cepstral Domain: Homomorphic Result $c(t_q)$")
    axs[2].set_xlabel("Quefrency (Delay)")
    axs[2].set_ylabel("Amplitude")
    axs[2].axvline(x=DELAY, color='black', linestyle='--', label=f'Target Delay ({DELAY})')
    axs[2].legend()

    plt.tight_layout()
    plt.savefig("projects/Project_aorta_gemma/output/validation_results.png")
    print("[INFO] Plots saved to projects/Project_aorta_gemma/output/validation_results.png")

if __name__ == "__main__":
    run_experiment()