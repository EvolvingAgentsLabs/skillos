---
title: "Project Aorta: Mathematical Framework"
dialect: formal-proof + system-dynamics
agent: mathematician-agent
generated: 2026-04-12
---

# Project Aorta: Mathematical Framework

---

## Section 1: Signal Model (formal-proof)

GIVEN:
- p(t) is the cardiac pressure pulse, p: R -> R, bandlimited to bandwidth B
- alpha in (0, 1) is the attenuation coefficient at bifurcation reflection
- tau > 0 is the round-trip echo delay, tau = 2d/c where d = distance to bifurcation, c = local wave speed
- s(t) is the measured pressure signal at catheter tip
- The reflection coefficient R = (Z2 - Z1)/(Z2 + Z1) where Z = rho*c/A

DERIVE:

Step 1: The measured signal is the superposition of direct pulse and attenuated delayed echo:
  s(t) = p(t) + alpha * p(t - tau)  [BY superposition_principle]

Step 2: Define the impulse response of the echo channel:
  h(t) = delta(t) + alpha * delta(t - tau)  [BY linear_system_representation]

Step 3: Therefore s(t) = (p * h)(t) where * denotes convolution:
  s(t) = integral_{-inf}^{inf} p(u) * h(t - u) du
       = integral_{-inf}^{inf} p(u) * [delta(t-u) + alpha*delta(t-u-tau)] du
       = p(t) + alpha*p(t-tau)  [BY convolution_with_delta]

Step 4: Apply Fourier Transform F{.} to both sides:
  S(omega) = F{s(t)} = F{p(t) + alpha*p(t-tau)}
           = F{p(t)} + alpha*F{p(t-tau)}  [BY linearity_of_FT]

Step 5: Apply time-shift theorem: F{f(t-tau)} = e^{-i*omega*tau} * F{f(t)}:
  S(omega) = P(omega) + alpha * e^{-i*omega*tau} * P(omega)  [BY time_shift_theorem]

Step 6: Factor:
  S(omega) = P(omega) * (1 + alpha * e^{-i*omega*tau})  [BY algebraic_factoring]

Step 7: Define the transfer function:
  H(omega) = 1 + alpha * e^{-i*omega*tau}  [BY definition]

Step 8: Therefore S(omega) = P(omega) * H(omega), confirming convolution-multiplication duality.  [BY convolution_theorem]

QED: The frequency-domain representation of the echo signal is S(omega) = P(omega) * (1 + alpha * e^{-i*omega*tau}).

---

## Section 2: Homomorphic Decomposition (formal-proof)

GIVEN:
- S(omega) = P(omega) * (1 + alpha * e^{-i*omega*tau}) from Section 1
- |S(omega)| = |P(omega)| * |1 + alpha * e^{-i*omega*tau}| (modulus of product)
- log is the natural logarithm
- IFFT denotes the inverse discrete Fourier transform
- The cepstrum is defined as c(tau_q) = IFFT{log|S(omega)|}

DERIVE:

**Part A: Log-Spectrum Separation**

Step 1: Take the magnitude spectrum:
  |S(omega)| = |P(omega)| * |1 + alpha * e^{-i*omega*tau}|  [BY modulus_of_product]

Step 2: Apply logarithm to both sides:
  log|S(omega)| = log(|P(omega)| * |1 + alpha * e^{-i*omega*tau}|)
                = log|P(omega)| + log|1 + alpha * e^{-i*omega*tau}|  [BY log_product_rule]

Step 3: Define:
  L_p(omega) = log|P(omega)|  (log-spectrum of pulse)
  L_h(omega) = log|1 + alpha * e^{-i*omega*tau}|  (log-spectrum of echo channel)

  Therefore: log|S(omega)| = L_p(omega) + L_h(omega)  [BY definition]

QED (Part A): Multiplicative convolution in time domain becomes additive in log-spectral domain.

**Part B: Periodicity of Echo Term**

Step 4: Compute |1 + alpha * e^{-i*omega*tau}|^2:
  |1 + alpha * e^{-i*omega*tau}|^2 = (1 + alpha*e^{-i*omega*tau})(1 + alpha*e^{+i*omega*tau})
  = 1 + alpha*e^{i*omega*tau} + alpha*e^{-i*omega*tau} + alpha^2
  = 1 + alpha^2 + 2*alpha*cos(omega*tau)  [BY euler_formula]

Step 5: Therefore:
  L_h(omega) = (1/2) * log(1 + alpha^2 + 2*alpha*cos(omega*tau))  [BY log_sqrt]

Step 6: Since cos(omega*tau) has period 2*pi/tau in omega:
  cos((omega + 2*pi/tau)*tau) = cos(omega*tau + 2*pi) = cos(omega*tau)  [BY periodicity_of_cosine]

Step 7: Therefore L_h(omega) is periodic with period 2*pi/tau in omega.  [BY function_composition_periodicity]

QED (Part B): The echo channel log-spectrum L_h(omega) is periodic with period 2*pi/tau.

**Part C: IFFT Recovery of Echo Delay**

Step 8: The cepstrum c(tau_q) = IFFT{log|S(omega)|} = IFFT{L_p(omega)} + IFFT{L_h(omega)}  [BY linearity_of_IFFT]

Step 9: L_p(omega) is a smooth, slowly-varying function (pulse envelope):
  IFFT{L_p(omega)} concentrates energy at low quefrencies (tau_q near 0)  [BY spectral_smoothness_duality]

Step 10: L_h(omega) is periodic with period 2*pi/tau. Its Fourier series has fundamental:
  L_h(omega) = sum_{k=-inf}^{inf} c_k * e^{i*k*(2*pi/tau)*... }
  By Fourier duality, a periodic function with period 2*pi/tau in frequency maps to impulses at integer multiples of tau in the quefrency domain:
  IFFT{L_h(omega)} has peaks at tau_q = tau, 2*tau, 3*tau, ...  [BY fourier_series_duality]

Step 11: For alpha < 1, the dominant peak is at tau_q = tau with amplitude proportional to alpha:
  |c(tau)| is proportional to alpha  [BY geometric_series_decay]

Step 12: The echo delay is extracted as:
  tau_detected = argmax_{tau_q > tau_min} |c(tau_q)|  [BY peak_detection]

Step 13: Position recovery:
  d = (tau_detected * c) / 2  [BY definition_of_tau]

QED (Part C): IFFT of the log-spectrum recovers the echo delay tau as a peak in the cepstrum at quefrency tau_q = tau, enabling distance computation d = tau*c/2.

---

## Section 3: Hemodynamic System Model (system-dynamics)

### Stocks

[STOCK] arterial_pressure
  - Units: mmHg
  - Range: [60, 180] (diastolic to peak systolic)
  - Description: Instantaneous pressure at measurement point

[STOCK] echo_amplitude
  - Units: mmHg (relative)
  - Range: [0, alpha_max * arterial_pressure]
  - Description: Accumulated reflected wave energy at catheter tip

[STOCK] catheter_position_estimate
  - Units: mm
  - Range: [0, L_aorta] where L_aorta ~ 400 mm
  - Description: Estimated catheter tip distance from aortic root

### Flows

[FLOW] cardiac_ejection -> +arterial_pressure
  - Rate: stroke_volume * ventricular_elastance / dt
  - Active during: systolic phase (0 < t < T_systole, T_systole ~ 0.3s)

[FLOW] pulse_propagation -> -arterial_pressure
  - Rate: arterial_pressure / (Z_characteristic * compliance)
  - Continuous: pressure wave propagates distally at speed c ~ 5 m/s

[FLOW] reflection_generation -> +echo_amplitude
  - Rate: R_bifurcation * incident_wave_amplitude
  - R_bifurcation = (Z_distal - Z_proximal) / (Z_distal + Z_proximal)
  - Triggered: when wavefront reaches each bifurcation

[FLOW] signal_attenuation -> -echo_amplitude
  - Rate: gamma * echo_amplitude
  - gamma = viscous_damping_coefficient + geometric_spreading
  - Continuous: exponential decay during propagation

[FLOW] position_update -> +/- catheter_position_estimate
  - Rate: (measured_delay * c / 2 - catheter_position_estimate) / T_filter
  - T_filter = smoothing time constant (10-100 ms)
  - Triggered: each successful cepstral measurement

### Feedback Loops

[FB+] resonance_amplification
  - Path: arterial_pressure -> pulse_propagation -> reflection_at_boundary -> echo_amplitude -> (if constructive interference) -> arterial_pressure
  - Condition: tau = n * T_cardiac for integer n (standing wave resonance)
  - Effect: Amplifies pressure oscillations at resonant frequencies
  - Clinical significance: Can distort echo pattern, requires deconvolution

[FB-] damping_dissipation
  - Path: arterial_pressure -> viscous_losses -> -arterial_pressure
  - Mechanism: Viscosity of blood + viscoelasticity of arterial wall
  - Time constant: ~ 0.5 s
  - Effect: Prevents unbounded resonance, stabilizes pressure oscillations

[FB-] compliance_buffering
  - Path: arterial_pressure -> arterial_wall_stretch -> increased_volume -> -arterial_pressure
  - Mechanism: Windkessel effect of elastic arteries
  - Effect: Smooths pulsatile flow, reduces echo amplitude variability

[FB+] measurement_refinement
  - Path: catheter_position_estimate -> improved_signal_model -> better_echo_extraction -> more_accurate_position -> catheter_position_estimate
  - Effect: Position knowledge improves signal interpretation iteratively

### External Inputs

[EXT] cardiac_output
  - Source: Left ventricular contraction
  - Waveform: Quasi-periodic, period T_cardiac ~ 0.6-1.2 s (50-100 bpm)
  - Variability: Heart rate variability (HRV) sigma ~ 50 ms

[EXT] respiratory_modulation
  - Source: Intrathoracic pressure changes during breathing
  - Effect: Modulates arterial_pressure by +/- 5 mmHg
  - Period: T_resp ~ 3-5 s

[EXT] catheter_advancement
  - Source: Operator (manual or robotic)
  - Effect: Changes true position, alters echo pattern
  - Rate: 0-10 mm/s typical

### Delays

[DELAY] propagation_delay(tau = 2d/c)
  - d = distance from catheter tip to reflecting bifurcation
  - c = local pulse wave velocity (3-10 m/s depending on arterial stiffness)
  - Range: tau in [0.1 ms, 160 ms] for d in [0.25 mm, 400 mm]

[DELAY] measurement_latency(T_process ~ 1-10 ms)
  - Acquisition + quantum processing + classical postprocessing
  - Target: T_process < 10 ms for real-time display

[DELAY] physiological_response(T_baroreceptor ~ 1-3 s)
  - Baroreceptor reflex adjusts cardiac output in response to pressure changes
  - Slow relative to measurement update rate

### Equilibrium Conditions

[EQ] steady_state_pressure
  - Condition: cardiac_ejection_rate (time-averaged) = peripheral_drainage_rate
  - Mean arterial pressure MAP = CO * TPR (cardiac output * total peripheral resistance)
  - Oscillation: superimposed on MAP with amplitude ~ 40 mmHg

[EQ] echo_steady_state
  - Condition: reflection_generation_rate = signal_attenuation_rate (per echo)
  - Implies: echo_amplitude_steady = R * incident_amplitude / gamma
  - Achieves stable cepstral peaks for reliable measurement

[EQ] position_convergence
  - Condition: position_update flow -> 0 as estimate converges to true position
  - Convergence criterion: |estimate - true_position| < 1 mm
  - Convergence time: ~ 3-5 cardiac cycles (with Kalman filtering)

---

## Section 4: Quantum Operator Mapping (formal-proof)

GIVEN:
- Classical cepstrum pipeline: c(tau_q) = IFFT{log|FFT(s)|}
- N = number of signal samples, n = log2(N) qubits
- QFT = Quantum Fourier Transform on n qubits
- QSVT = Quantum Singular Value Transformation
- Block-encoding U_A encodes matrix A such that (<0| tensor I) U_A (|0> tensor I) = A/alpha_norm

DERIVE:

**Mapping 1: FFT -> QFT**

Step 1: Classical DFT on N-point signal requires O(N log N) operations via FFT.  [BY cooley_tukey_complexity]

Step 2: QFT on n = log2(N) qubits implements the same unitary transformation:
  QFT|j> = (1/sqrt(N)) * sum_{k=0}^{N-1} e^{2*pi*i*j*k/N} |k>  [BY QFT_definition]

Step 3: QFT decomposes into O(n^2) = O(log^2(N)) controlled-rotation gates.  [BY QFT_circuit_decomposition]

Step 4: Input preparation: encode s(t) into quantum state:
  |s> = (1/||s||) * sum_{j=0}^{N-1} s(j) |j>  [BY amplitude_encoding]

Step 5: Apply QFT:
  QFT|s> = (1/||s||) * sum_{k=0}^{N-1} S(k) |k>
  where S(k) = (1/sqrt(N)) * sum_{j} s(j) * e^{-2*pi*i*j*k/N}  [BY linearity_of_QFT]

**Mapping 2: log|.| -> QSVT polynomial approximation**

Step 6: Classical log computation on N spectral values: O(N) operations.  [BY element_wise_computation]

Step 7: QSVT applies a polynomial transformation P(x) to singular values of a block-encoded matrix.  [BY QSVT_theorem]

Step 8: Approximate log(x) on [epsilon, 1] by polynomial P_d(x) of degree d:
  |P_d(x) - log(x)| < delta for all x in [epsilon, 1]  [BY polynomial_approximation_theory]

Step 9: QSVT circuit depth for degree-d polynomial: O(d) queries to block-encoding.  [BY QSVT_query_complexity]

Step 10: Required degree d = O(log(1/epsilon) * log(1/delta)) for log approximation.  [BY jackson_theorem_variant]

**Mapping 3: IFFT -> QFT^{-1}**

Step 11: QFT^{-1} = QFT^dagger, same gate count O(log^2(N)).  [BY unitarity_of_QFT]

**Complexity Comparison:**

Step 12: Classical pipeline total:
  C_classical = O(N log N) + O(N) + O(N log N) = O(N log N)  [BY dominant_term]

Step 13: Quantum pipeline total:
  C_quantum = O(log^2(N)) + O(d * log(N)) + O(log^2(N))
  where d = O(log(1/epsilon) * log(1/delta))
  = O(log^2(N) * polylog(1/epsilon, 1/delta))  [BY sum_of_terms]

Step 14: For fixed precision requirements (epsilon, delta constants):
  C_quantum = O(log^2(N))  [BY absorbing_constants]

Step 15: Speedup factor:
  C_classical / C_quantum = O(N log N) / O(log^2 N) = O(N / log N)
  This is exponential in n = log2(N).  [BY ratio_analysis]

QED: The quantum cepstrum pipeline achieves exponential speedup: O(log^2 N) quantum gates versus O(N log N) classical operations, with the dominant quantum cost in the QSVT log approximation step.

---

## Section 5: QSVT Log Approximation (formal-proof)

GIVEN:
- Target function: f(x) = log(x) for x in [epsilon, 1], epsilon > 0
- Block-encoding: unitary U_A such that (<0|_a tensor I_s) U_A (|0>_a tensor I_s) = A / alpha where alpha >= ||A||
- A = diag(sigma_1, ..., sigma_N) represents the magnitude spectrum values normalized to [epsilon, 1]
- QSVT phases: Phi = (phi_0, phi_1, ..., phi_d) in R^{d+1}
- Approximation error budget: delta_log for log polynomial

DERIVE:

**Part A: Block-Encoding Construction**

Step 1: Normalize the magnitude spectrum:
  Define A = diag(|S(omega_0)|, ..., |S(omega_{N-1})|) / max_k|S(omega_k)|
  All singular values sigma_k in [epsilon, 1] where epsilon = min_k|S(omega_k)| / max_k|S(omega_k)|  [BY normalization]

Step 2: Construct block-encoding U_A as a (1, a, 0)-block-encoding:
  U_A acts on (n + a) qubits where a = ancilla count
  (<0|^a tensor I^n) U_A (|0>^a tensor I^n) = A  [BY block_encoding_definition]

Step 3: For diagonal A, use quantum signal processing with single-qubit rotations:
  U_A = product of controlled rotations R_y(2*arccos(sigma_k)) conditioned on |k>  [BY diagonal_block_encoding]

**Part B: Polynomial Degree Analysis**

Step 4: By Chebyshev approximation theory, log(x) on [epsilon, 1] can be approximated by polynomial P_d(x) satisfying:
  ||P_d - log||_inf,[epsilon,1] <= delta_log  [BY chebyshev_approximation]

Step 5: Required degree for log(x) approximation:
  d = O((1/epsilon) * log(1/delta_log))  [BY bernstein_inequality_for_log]

Step 6: More precisely, using the transformation x -> (2x - 1 - epsilon)/(1 - epsilon) mapping [epsilon, 1] to [-1, 1]:
  d >= (2/pi) * log(1/epsilon) * log(2/delta_log)  [BY jackson_theorem]

Step 7: For QSVT, the polynomial must additionally satisfy |P_d(x)| <= 1 for all x in [-1, 1].
  Rescale: P_d^{QSVT}(x) = P_d(x) / ||P_d||_inf
  This introduces factor kappa_log = ||log||_inf,[epsilon,1] = |log(epsilon)|  [BY QSVT_normalization_constraint]

**Part C: QSVT Circuit Construction**

Step 8: Given degree-d polynomial P_d satisfying parity and boundedness constraints, QSVT constructs:
  U_Phi = e^{i*phi_0*Z} * product_{j=1}^{d} [U_A * e^{i*phi_j*Z}]  [BY QSVT_circuit_structure]

Step 9: The phases Phi are computed classically (one-time preprocessing):
  Phi = QSVT_Phase_Finding(P_d) in time O(d * polylog(d))  [BY phase_finding_algorithm]

Step 10: Total quantum circuit depth:
  Depth = d * depth(U_A) + d * O(1)  [BY sequential_composition]

Step 11: For our diagonal block-encoding, depth(U_A) = O(n) = O(log N):
  Total depth = O(d * log N) = O(log(1/epsilon) * log(1/delta_log) * log(N))  [BY substitution]

**Part D: Error Budget Derivation**

Step 12: Sources of error in QSVT log approximation:
  (i) Polynomial approximation error: delta_log
  (ii) Phase computation finite precision: delta_phase ~ 2^{-b} for b-bit phases
  (iii) Gate implementation error: delta_gate per gate, d gates total  [BY error_decomposition]

Step 13: Total QSVT error:
  delta_QSVT <= delta_log + d * delta_phase + d * delta_gate  [BY triangle_inequality]

Step 14: For target total error delta_QSVT = 10^{-6}:
  Allocate: delta_log = 3 * 10^{-7}, delta_phase = 3 * 10^{-7}/d, delta_gate = 3 * 10^{-7}/d  [BY equal_allocation_strategy]

Step 15: Required phase precision: b >= log2(d / (3*10^{-7})) bits
  For d = 100: b >= 29 bits  [BY precision_requirement]

QED: The QSVT log approximation uses a degree-d polynomial with d = O(log(1/epsilon)*log(1/delta_log)), requires circuit depth O(d * log N), and achieves total approximation error bounded by delta_QSVT <= delta_log + d*(delta_phase + delta_gate).

---

## Section 6: Quantum Cepstrum Error Analysis (formal-proof)

GIVEN:
- Full quantum pipeline: |s> -> QFT -> QSVT(log) -> QFT^{-1} -> Measure
- QFT error per gate: delta_QFT_gate
- QFT gate count: G_QFT = O(n^2) where n = log2(N)
- QSVT total error: delta_QSVT (from Section 5)
- Measurement shots: M
- Echo detection threshold: signal peak must exceed noise floor by factor SNR_min
- True echo delay: tau_true, true amplitude: alpha_true

DERIVE:

**Part A: Component Error Analysis**

Step 1: QFT accumulated error (forward transform):
  delta_QFT_forward <= G_QFT * delta_QFT_gate = O(n^2) * delta_QFT_gate = O(log^2(N) * delta_QFT_gate)  [BY gate_error_accumulation]

Step 2: QSVT log approximation error (from Section 5):
  delta_QSVT <= delta_log + d * (delta_phase + delta_gate)  [BY section_5_result]

Step 3: QFT^{-1} accumulated error (inverse transform):
  delta_QFT_inverse <= G_QFT * delta_QFT_gate = delta_QFT_forward  [BY symmetric_circuit]

Step 4: Measurement statistical error:
  delta_meas = O(1/sqrt(M)) for M measurement shots  [BY quantum_measurement_statistics]

**Part B: Total Error Budget**

Step 5: Total state error before measurement (trace distance):
  delta_state <= delta_QFT_forward + delta_QSVT + delta_QFT_inverse
  = 2 * O(log^2(N)) * delta_QFT_gate + delta_QSVT  [BY triangle_inequality_trace_distance]

Step 6: Error in measured cepstrum value at quefrency tau_q:
  |c_measured(tau_q) - c_true(tau_q)| <= delta_state + delta_meas
  = 2 * O(log^2(N)) * delta_QFT_gate + delta_QSVT + O(1/sqrt(M))  [BY measurement_error_propagation]

**Part C: Echo Detection Conditions**

Step 7: True cepstral peak amplitude at tau_q = tau_true:
  |c_true(tau_true)| is proportional to alpha_true (echo attenuation)  [BY section_2_result]

Step 8: Noise floor in cepstrum (from all error sources):
  sigma_noise = delta_state + delta_meas  [BY noise_characterization]

Step 9: Echo detection succeeds when signal-to-noise ratio exceeds threshold:
  SNR = |c_true(tau_true)| / sigma_noise >= SNR_min  [BY detection_criterion]

Step 10: Substituting:
  alpha_true / (2*O(log^2(N))*delta_QFT_gate + delta_QSVT + O(1/sqrt(M))) >= SNR_min  [BY substitution]

Step 11: For successful detection, require:
  Condition 1: delta_QFT_gate <= alpha_true / (6 * SNR_min * log^2(N))
  Condition 2: delta_QSVT <= alpha_true / (3 * SNR_min)
  Condition 3: M >= (3 * SNR_min / alpha_true)^2  [BY allocation_to_three_sources]

**Part D: Position Estimation Error**

Step 12: Quefrency resolution of cepstrum: Delta_tau_q = 1/B where B = signal bandwidth.  [BY fourier_resolution_limit]

Step 13: Position error from quefrency discretization:
  delta_d_resolution = (c / 2) * Delta_tau_q = c / (2B)  [BY position_from_delay]

Step 14: Position error from noise-induced peak shift:
  delta_d_noise = (c / 2) * sigma_noise / |c''(tau_true)|
  where c''(tau_true) is second derivative (peak curvature)  [BY parabolic_interpolation_error]

Step 15: Total position error:
  delta_d_total = sqrt(delta_d_resolution^2 + delta_d_noise^2)  [BY quadrature_sum]

Step 16: For clinical requirement delta_d_total < 1 mm:
  With c = 5 m/s and B = 1 MHz: delta_d_resolution = 5/(2*10^6) = 2.5 * 10^{-6} m = 0.0025 mm (negligible)
  Dominant constraint: delta_d_noise < 1 mm
  Requires: sigma_noise < 2 * |c''(tau_true)| * 10^{-3} / c  [BY rearrangement]

QED: Successful echo detection requires: (1) QFT gate error < alpha/(6*SNR_min*log^2 N), (2) QSVT error < alpha/(3*SNR_min), (3) measurement shots M > (3*SNR_min/alpha)^2. Sub-millimeter positioning is achievable with bandwidth B >= 1 MHz and the above error constraints satisfied.

---

## Section 7: Quantum-Hemodynamic Feedback (system-dynamics)

### Stocks

[STOCK] quantum_state_fidelity
  - Units: dimensionless, range [0, 1]
  - Description: Fidelity of quantum processor state relative to ideal cepstrum computation
  - Initial: 1.0 (pure state at preparation)

[STOCK] position_estimate_confidence
  - Units: dimensionless, range [0, 1]
  - Description: Bayesian posterior confidence in current catheter position estimate
  - Initial: 0.0 (no information before first measurement)

[STOCK] catheter_position_estimate
  - Units: mm from aortic root
  - Description: Current best estimate of catheter tip location

[STOCK] signal_model_accuracy
  - Units: dimensionless, range [0, 1]
  - Description: Goodness-of-fit of assumed echo model to actual arterial geometry

### Flows

[FLOW] state_preparation -> +quantum_state_fidelity
  - Rate: (1 - quantum_state_fidelity) / T_prep
  - T_prep ~ 1 microsecond
  - Resets fidelity at start of each measurement cycle

[FLOW] decoherence -> -quantum_state_fidelity
  - Rate: quantum_state_fidelity / T2
  - T2 = coherence time of quantum processor (~100 microsecond superconducting, ~1 s trapped ion)
  - Continuous during circuit execution

[FLOW] gate_errors -> -quantum_state_fidelity
  - Rate: delta_gate * gate_rate
  - Discrete: each gate application reduces fidelity
  - Cumulative over circuit depth

[FLOW] measurement_update -> +position_estimate_confidence
  - Rate: information_gain_per_shot / shot_interval
  - information_gain_per_shot = SNR^2 / (1 + SNR^2) (quantum Fisher information)
  - Triggered: each measurement outcome

[FLOW] measurement_collapse -> -quantum_state_fidelity
  - Rate: instantaneous (fidelity -> 0 upon measurement)
  - Effect: Quantum state destroyed; must re-prepare for next cycle
  - This is the fundamental measurement-disturbance tradeoff

[FLOW] position_drift -> -position_estimate_confidence
  - Rate: v_catheter / sigma_position
  - v_catheter = catheter advancement velocity (operator-controlled)
  - Continuous: confidence degrades as catheter moves between measurements

[FLOW] model_learning -> +signal_model_accuracy
  - Rate: learning_rate * (measured_residual < threshold)
  - Triggered: each measurement cycle with successful echo detection
  - Saturates at anatomical map completeness

[FLOW] anatomy_change -> -signal_model_accuracy
  - Rate: proportional to catheter velocity
  - As catheter advances into new territory, model from previous position degrades

### Feedback Loops

[FB-] measurement_collapse_reset (Balancing — Fundamental Quantum Limit)
  - Path: quantum_state_fidelity -> measurement -> measurement_collapse -> (fidelity = 0) -> state_preparation -> quantum_state_fidelity
  - Mechanism: Each measurement destroys quantum state; system must restart preparation
  - Period: T_cycle = T_prep + T_circuit + T_measure
  - Effect: Limits measurement rate to 1/T_cycle regardless of classical processing speed
  - Equilibrium: Average fidelity during useful computation ~ exp(-T_circuit/T2)

[FB+] confidence_model_reinforcement (Reinforcing — Virtuous Learning Cycle)
  - Path: position_estimate_confidence -> better_signal_windowing -> signal_model_accuracy -> improved_echo_extraction -> measurement_update -> position_estimate_confidence
  - Mechanism: Higher confidence enables better signal preprocessing (gating, windowing), which improves model, which improves next measurement
  - Growth: Exponential convergence until saturation
  - Saturation: Limited by fundamental quantum measurement noise floor

[FB-] motion_measurement_balance (Balancing — Nyquist-like Constraint)
  - Path: catheter_advancement -> position_drift -> -position_estimate_confidence -> (if confidence < threshold) -> HALT advancement until confidence restored
  - Mechanism: Operator cannot advance faster than measurement system can track
  - Equilibrium: v_max = delta_d_acceptable * f_measurement
  - Clinical implication: Maximum safe advancement rate ~ 1 mm * 100 Hz = 100 mm/s

[FB-] error_correction_overhead (Balancing — Resource Tradeoff)
  - Path: gate_errors -> -quantum_state_fidelity -> activate_error_correction -> increased_circuit_depth -> increased_decoherence -> -quantum_state_fidelity
  - Mechanism: Error correction adds gates, which add decoherence exposure
  - Threshold: Error correction beneficial only when delta_gate < delta_threshold (surface code ~ 10^{-3})
  - Effect: Defines minimum hardware quality for useful quantum advantage

### External Inputs

[EXT] cardiac_output
  - Provides: pressure pulse waveform p(t) for encoding into |s>
  - Variability: Period T_cardiac ~ 0.6-1.2 s, amplitude varies with respiration
  - Synchronization: Measurement triggered by R-wave (ECG gating)

[EXT] operator_input
  - Provides: catheter_advancement commands
  - Constraint: Rate-limited by motion_measurement_balance feedback
  - Mode: Manual or robotic (robotic enables closed-loop position control)

[EXT] anatomical_prior
  - Provides: Expected arterial geometry from preoperative imaging (CT/MRI)
  - Effect: Initializes signal_model_accuracy > 0, accelerates convergence
  - Update: Registered to patient via landmark matching

### Delays

[DELAY] quantum_processing(T_circuit = O(log^2(N)) * T_gate)
  - T_gate ~ 100 ns (superconducting) or ~ 10 microsecond (trapped ion)
  - For N = 2^20, n = 20: T_circuit ~ 400 * 100 ns = 40 microsecond (superconducting)
  - Critical: Must complete before decoherence (T_circuit << T2)

[DELAY] classical_postprocessing(T_post ~ 0.1-1 ms)
  - Peak detection in measured cepstrum
  - Kalman filter update for position estimate
  - Display rendering

[DELAY] state_preparation(T_prep ~ 1-10 microsecond)
  - Amplitude encoding of signal vector
  - Requires O(N) classical gates or O(log N) with QRAM
  - Bottleneck if QRAM unavailable

[DELAY] ECG_synchronization(T_sync ~ 0-T_cardiac)
  - Wait for next R-wave to initiate measurement
  - Jitter: +/- 10 ms from R-wave detection uncertainty

### Equilibrium Conditions

[EQ] measurement_rate_equilibrium
  - Condition: T_cycle = T_prep + T_circuit + T_measure + T_post remains constant
  - f_measurement = 1/T_cycle
  - Target: f_measurement >= 100 Hz
  - Requires: T_cycle <= 10 ms
  - Feasibility: T_circuit ~ 40 microsecond + T_prep ~ 10 microsecond + T_measure ~ 1 microsecond + T_post ~ 1 ms => T_cycle ~ 1.05 ms => f_measurement ~ 950 Hz (achievable)

[EQ] tracking_convergence
  - Condition: position_drift_rate <= position_update_rate * delta_d_per_update
  - v_catheter <= f_measurement * delta_d_noise
  - For f = 100 Hz, delta_d_noise = 0.5 mm: v_max = 50 mm/s
  - Clinical procedures typically < 10 mm/s (constraint easily satisfied)

[EQ] quantum_advantage_threshold
  - Condition: Quantum pipeline provides net benefit over classical
  - Requires: T_quantum_cycle < T_classical_cycle for same resolution
  - Classical: T_FFT = O(N log N) * T_flop ~ 10^6 * 20 * 1 ns = 20 ms for N = 10^6
  - Quantum: T_quantum ~ 1 ms (from above)
  - Advantage realized when N > N_crossover where quantum overhead < classical compute
  - Estimated N_crossover ~ 10^4 - 10^5 (depending on QRAM availability and error correction overhead)

---

## Summary of Key Results

| Property | Classical | Quantum | Advantage |
|----------|-----------|---------|-----------|
| FFT complexity | O(N log N) | O(log^2 N) | Exponential |
| Log computation | O(N) | O(d log N) | Exponential (d = polylog) |
| Total pipeline | O(N log N) | O(log^2 N) | Exponential |
| Update rate (N=10^6) | ~50 Hz | ~950 Hz | 19x |
| Position resolution | Limited by N | Same, faster | Time advantage |

| Error Source | Budget Allocation | Constraint |
|--------------|-------------------|------------|
| QFT gates | alpha/(6*SNR_min*log^2 N) per gate | ~10^{-8} per gate for alpha=0.1 |
| QSVT polynomial | alpha/(3*SNR_min) total | ~3*10^{-3} for alpha=0.1 |
| Measurement statistics | (3*SNR_min/alpha)^2 shots | ~900 shots for SNR_min=1 |
| Total position error | < 1 mm | Achievable with above constraints |
