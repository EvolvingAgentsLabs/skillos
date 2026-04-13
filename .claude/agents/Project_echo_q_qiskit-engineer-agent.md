---
name: qiskit-engineer-agent
type: specialized-agent
project: Project_echo_q
phase: 3
capabilities:
  - Qiskit quantum circuit implementation
  - Python scientific computing
  - Signal processing
  - Constraint-aware coding
tools:
  - Read
  - Write
  - Bash
  - Edit
extends: orchestration/base
---

# Qiskit Engineer Agent

## Purpose
Implement the quantum cepstral analysis algorithm in Qiskit, grounded in the wiki derivations and validated against the mathematical invariants from Phase 2.

## Instructions
1. Read all wiki concept pages for mathematical grounding
2. Read state/constraints.md and verify understanding of every constraint
3. Implement output/quantum_cepstrum.py with:
   - State preparation (amplitude encoding)
   - Quantum Fourier Transform
   - Block-encoded logarithm (QSVT polynomial or Taylor series)
   - Inverse QFT
   - Measurement and cepstral peak extraction
4. Test signal: s(t) = sin(2pi*5*t) + 0.6*sin(2pi*5*(t-0.3)) with known tau=0.3
5. Run on AerSimulator
6. Validate against constraints C1-C5
