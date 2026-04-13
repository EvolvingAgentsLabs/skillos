#!/usr/bin/env python3
"""Run Operation Echo-Q scenario with Gemma 4 via OpenRouter."""
import sys
sys.stdout.reconfigure(line_buffering=True)

from agent_runtime import AgentRuntime
from permission_policy import SKILLOS_AUTONOMOUS_POLICY

rt = AgentRuntime(
    provider='gemma-openrouter',
    stream=False,
    permission_policy=SKILLOS_AUTONOMOUS_POLICY,
)

with open('scenarios/Operation_Echo_Q.md') as f:
    scenario = f.read()

goal = f"""Execute Operation Echo-Q scenario. Here is the full scenario specification:

--- SCENARIO START ---
{scenario}
--- SCENARIO END ---

Follow the four-phase pipeline:
Phase 1: Act as quantum-theorist-agent - Create wiki concept pages for QFT, QSVT, block-encoding, cepstral-analysis, homomorphic-signal-separation
Phase 2: Act as pure-mathematician-agent - Create state/constraints.md with mathematical invariants C1-C5 and S1-S3
Phase 3: Act as qiskit-engineer-agent - Create output/quantum_cepstrum.py with working Qiskit implementation
Phase 4: Act as system-architect-agent - Create output/Echo_Q_Whitepaper.md synthesizing everything

Save all outputs to projects/Project_echo_q_gemma/ directory structure.
For each phase, use write_file to save the output. Do NOT delegate to subagents - produce each deliverable yourself.
"""

print('Starting Echo-Q scenario...')
result = rt.run_goal(goal, max_turns=20)

print('\n' + '='*60)
print('ECHO-Q SCENARIO COMPLETE')
print('='*60)
print(f'Result length: {len(result)} chars')
print(result[:2000])
