---
skill_id: forge/compile/forge-compile-cartridge-tool
name: forge-compile-cartridge-tool
type: tool
domain: forge
family: compile
extends: forge/base
version: 1.0.0
description: Promotes a validated candidate to the hot path — writes to system/skills/ or cartridges/, updates packages.lock, and optionally precomputes a cartridge bundle.
capabilities: [artifact-promotion, cartridge-packaging, registry-update, rollback-support]
tools_required: [Read, Write, Bash, Grep, Glob]
backend: deterministic
target_model: gemma4:e2b
token_cost: low
reliability: 99%
invoke_when: [forge-validate emits pass, artifact ready for hot path, mass promotion after model upgrade]
full_spec: system/skills/forge/compile/forge-compile-cartridge-tool.md
---
