import numpy as np
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit, Aer, execute
from qiskit.circuit.library import QFT
from scipy.fft import fft, ifft

"""
Project Aorta: Quantum Homomorphic Cepstral Analysis Implementation

This implementation translates the mathematical framework for arterial echo detection
into a simulation comparing classical cepstral analysis with a quantum-inspired
approach using Quantum Fourier Transform (QFT).

Mathematical Context:
Signal: s(t) = p(t) + alpha * p(t - tau)
In the frequency domain (via Fourier Transform):
S(f) = P(f) * (1 + alpha * exp(-i * 2 * pi * f * tau))
In the log-spectral domain:
log|S(f)| = log|P(f)| + log|1 + alpha * exp(-i * 2 * pi * f * tau)|

The cepstrum (IFFT of the log-spectrum) reveals a peak at the 'quefrency' corresponding
to the delay tau.
"""

class QuantumAortaSimulator:
    def __init__(self, n_qubits=8, sample_rate=1000, signal_duration=1.0):
        self.n_qubits = n_qubits
        self.n_samples = 2**n_qubits
        self.fs = sample_rate
        self.duration = signal_duration
        self.t = np.linspace(0, self.duration, self.n_samples, endpoint=False)
        
    def generate_arterial_signal(self, alpha=0.6, tau_seconds=0.15):
        """
        Generates a synthetic arterial pressure pulse with an echo component.
        s(t) = p(t) + alpha * p(t - tau)
        """
        # Primary pulse: A dampened sinusoid representing a systolic surge
        p_t = np.exp(-5 * self.t) * np.sin(2 * np.pi * 2 * self.t)
        
        # Delay tau in samples
        tau_samples = int(tau_seconds * self.fs)
        
        # Create signal with echo
        s_t = np.zeros(self.n_samples)
        s_t[:len(p_t)] += p_t
        
        # Add the delayed echo component
        if tau_samples < self.n_samples:
            s_t[tau_samples:] += alpha * p_t[:-tau_samples]
            
        # Add some realistic measurement noise
        noise = np.random.normal(0, 0.05, self.n_samples)
        s_t += noise
        
        return s_t, p_t, tau_samples

    def classical_cepstral_analysis(self, signal):
        """
        Implements the classical homomorphic pipeline:
        1. FFT -> 2. Log Magnitude -> 3. IFFT (Cepstrum)
        """
        # Step 1: Fourier Transform
        spec = fft(signal)
        
        # Step 2: Log Magnitude (Homomorphic transformation)
        # We use log(abs(spec) + epsilon) to avoid log(0)
        log_spec = np.log(np.abs(spec) + 1e-10)
        
        # Step 3: Inverse Fourier Transform to find the cepstrum
        cepstrum = np.real(ifft(log_spec))
        return cepstrum

    def build_quantum_circuit(self, signal_amplitude_data):
        """
        Constructs a Qiskit circuit to perform QFT-based analysis.
        Note: In a true quantum computer, we would use Amplitude Encoding.
        This simulation demonstrates the structure of the QFT-based decomposition.
        """
        qc = QuantumCircuit(self.n_qubits)
        
        # 1. State Preparation (Simulated via Amplitude Encoding)
        # In practice, this involves mapping signal values to quantum amplitudes.
        # For simulation, we represent the 'quantum' state via the input vector.
        
        # 2. Apply Quantum Fourier Transform (QFT)
        # The QFT is the quantum analogue of the Discrete Fourier Transform.
        qft_circuit = QFT(num_qubits=self.n_qubits)
        qc.append(qft_circuit, range(self.n_qubits))
        
        return qc

    def run_quantum_simulation(self, signal):
        """
        Simulates the quantum signal processing pipeline.
        Quantum approach: Signal -> Amplitude Encoding -> QFT -> Measurement
        """
        # Normalize signal for amplitude encoding
        norm_signal = np.abs(signal) / np.linalg.norm(signal)
        
        # In a real quantum device, the 'log' operation is the hardest part.
        # We approximate the homomorphic step by performing the QFT on the
        # magnitude-encoded state.
        
        # 1. Compute the DFT (simulating the QFT effect on the state amplitudes)
        quantum_spec = fft(norm_signal)
        
        # 2. Simulate Quantum Logarithmic Operator U_log
        # This represents the non-linear step in homomorphic processing
        log_quantum_spec = np.log(np.abs(quantum_spec) + 1e-10)
        
        # 3. Inverse QFT (Simulated)
        quantum_cepstrum = np.real(ifft(log_quantum_spec))
        
        return quantum_cepstrum

    def execute_full_study(self, alpha=0.5, tau_sec=0.12):
        print(f"--- Project Aorta: Quantum Signal Processing Study ---")
        print(f"Parameters: alpha={alpha}, target_tau={tau_sec}s, fs={self.fs}Hz")
        
        # 1. Signal Generation
        s_t, p_t, true_tau_samples = self.generate_arterial_signal(alpha=alpha, tau_seconds=tau_sec)
        
        # 2. Classical Path
        c_cepstrum = self.classical_cepstral_analysis(s_t)
        
        # 3. Quantum Path
        q_cepstrum = self.run_quantum_simulation(s_t)
        
        # 4. Peak Detection (Finding the delay)
        # We look for the maximum peak in the cepstrum (excluding the zero-lag peak)
        c_peak_idx = np.argmax(c_cepstrum[1:]) + 1
        q_peak_idx = np.argmax(q_cepstrum[1:]) + 1
        
        c_tau_est = c_peak_idx / self.fs
        q_tau_est = q_peak_idx / self.fs
        
        print(f"\nResults:")
        print(f"True Delay:       {tau_sec:.4f} s")
        print(f"Classical Delay:  {c_tau_est:.4f} s (Error: {abs(c_tau_est-tau_sec):.4f}s)")
        print(f"Quantum Delay:    {q_tau_est:.4f} s (Error: {abs(q_tau_est-tau_sec):.4f}s)")

        # 5. Visualization
        self.plot_results(s_t, p_t, c_cepstrum, q_cepstrum, true_tau_samples)

    def plot_results(self, signal, pulse, c_cep, q_cep, true_tau):
        fig, axs = plt.subplots(3, 1, figsize=(12, 15))
        
        # Plot 1: Time Domain Signal
        axs[0].plot(self.t, signal, label='Arterial Signal (with Echo)', color='tab:red', alpha=0.7)
        axs[0].plot(self.t, pulse, label='Primary Pulse', color='black', linestyle='--')
        axs[0].set_title("Time Domain: Arterial Pressure Pulse & Echo")
        axs[0].set_xlabel("Time (s)")
        axs[0].set_ylabel("Amplitude")
        axs[0].legend()
        axs[0].grid(True)

        # Plot 2: Classical Cepstrum
        axs[1].plot(c_cep, label='Classical Cepstrum', color='tab:blue')
        axs[1].axvline(x=true_tau, color='red', linestyle='--', label='True Delay')
        axs[1].set_title("Classical Cepstral Domain (Homomorphic Analysis)")
        axs[1].set_xlabel("Quefrency (s)")
        axs[1].set_ylabel("Magnitude")
        axs[1].set_xlim(0, 0.5) # Focus on relevant delay window
        axs[1].legend()
        axs[1].grid(True)

        # Plot 3: Quantum Cepstrum (Simulated)
        axs[2].plot(q_cep, label='Quantum-Inspired Cepstrum', color='tab:green')
        axs[2].axvline(x=true_tau, color='red', linestyle='--', label='True Delay')
        axs[2].set_title("Quantum-Inspired Cepstral Domain (QFT-based Simulation)")
        axs[2].set_xlabel("Quefrency (s)")
        axs[2].set_ylabel("Magnitude")
        axs[2].set_xlim(0, 0.5)
        axs[2].legend()
        axs[2].grid(True)

        plt.tight_layout()
        plt.savefig('quantum_aorta_analysis_results.png')
        print("\nVisualization saved to 'quantum_aorta_analysis_results.png'")
        plt.show()

if __name__ == '__main__':
    # Initialize simulator
    # Using 10 qubits provides 1024 samples for high resolution
    simulator = QuantumAortaSimulator(n_qubits=10, sample_rate=1000, signal_duration=1.0)
    
    # Execute analysis with a specific echo delay of 0.18 seconds
    simulator.execute_full_study(alpha=0.5, tau_sec=0.18)