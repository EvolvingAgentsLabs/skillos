# Error Diagnosis — Operation Echo-Q

## Cycle 1 Errors

### Error 1: AerError — unknown instruction: IQFT
**Traceback**: `qiskit_aer.aererror.AerError: 'unknown instruction: IQFT'`
**Root cause**: `QFT(n, inverse=True)` from `qiskit.circuit.library` creates a high-level gate labeled `IQFT` that AerSimulator does not recognize natively. The deprecated `QFT` class does not auto-decompose.
**Constraint violated**: None (implementation bug, not a physics constraint violation)
**Wiki ref**: [[quantum-fourier-transform]] — QFT is built from Hadamard + controlled-R_k gates; need to synthesize to native gates.
**Fix strategy**: Use `qiskit.synthesis.qft.synth_qft_full` or decompose the QFT circuit manually, or call `qc.decompose()` to break down the high-level gate.

### Error 2: Classical cepstrum echo detection FAIL (error=0.1125s)
**Root cause**: With N=16 samples at 16 Hz sample rate, the quefrency resolution is 1/16=0.0625s. The nearest quefrency bin to tau=0.3s is index 5 (0.3125s) with error 0.0125s. However, the peak was detected at index 3 (0.1875s) — the signal's spectral structure at such low resolution places the dominant cepstral energy at a different bin.
**Constraint violated**: S4 (Test Signal Fidelity)
**Wiki ref**: [[cepstral-analysis]] — echo detection requires sufficient quefrency resolution
**Fix strategy**: Increase N_QUBITS to 6 (N=64) for finer quefrency bins (resolution 1/64=0.015625s). Also increase SAMPLE_RATE to match.

## Cycle 2 Fixes Applied
1. Replace `QFT(n, inverse=True)` with manual IQFT decomposition using H, CP, SWAP gates
2. Increase N_QUBITS from 4 to 6 (N=64) for adequate quefrency resolution
3. Increase SAMPLE_RATE to 64 to match N
4. Added `transpile()` before AerSimulator execution
5. Increased polynomial degree from 8 to 12

## Cycle 2 Results
- **SUCCESS**: Quantum statevector echo detection PASS (error=0.0344s < 0.05s)
- All hard constraints C1-C6: PASS
- Polynomial approximation error: 5.4e-4 (well within S1 budget)
- QASM measurement noisy at 6 qubits — expected behavior, would improve with amplitude estimation (S3)
