---
skill_id: forge/validate/forge-validate-agent
name: forge-validate-agent
type: agent
domain: forge
family: validate
extends: forge/base
version: 1.0.0
description: Runs candidate artifacts against the Gemma 4 runtime via Ollama, executes the test suite, and writes the gemma_compat attestation on pass.
capabilities: [artifact-validation, gemma-compat-attestation, regression-testing, ab-testing]
tools_required: [Read, Write, Bash, Grep]
subagent_type: forge-validate-agent
backend: gemma-local
target_model: gemma4:e2b
token_cost: medium
reliability: 95%
invoke_when: [after forge-generate, after forge-evolve, before cartridge compile, after gemma model upgrade]
full_spec: system/skills/forge/validate/forge-validate-agent.md
---
