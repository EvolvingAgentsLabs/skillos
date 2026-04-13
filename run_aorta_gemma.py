#!/usr/bin/env python3
"""Run Project Aorta scenario with Gemma 4 via OpenRouter."""
import sys
sys.stdout.reconfigure(line_buffering=True)

from agent_runtime import AgentRuntime
from permission_policy import SKILLOS_AUTONOMOUS_POLICY

rt = AgentRuntime(
    provider='gemma-openrouter',
    stream=False,
    permission_policy=SKILLOS_AUTONOMOUS_POLICY,
)

with open('scenarios/ProjectAortaScenario.md') as f:
    scenario = f.read()

goal = f"""Execute the Project Aorta scenario. Here is the full scenario specification:

--- SCENARIO START ---
{scenario}
--- SCENARIO END ---

Follow the three-agent pipeline:
1. Act as visionary-agent: Create project_vision.md with comprehensive project description
2. Act as mathematician-agent: Create mathematical_framework.md with rigorous math
3. Act as quantum-engineer-agent: Create quantum_aorta_implementation.py with Qiskit code

Save all outputs to projects/Project_aorta_gemma/output/ directory.
For each stage, use write_file to save the output. Do NOT delegate to subagents - produce each deliverable yourself.
"""

print('Starting Project Aorta scenario...')
result = rt.run_goal(goal, max_turns=15)

print('\n' + '='*60)
print('AORTA SCENARIO COMPLETE')
print('='*60)
print(f'Result length: {len(result)} chars')
print(result[:2000])
