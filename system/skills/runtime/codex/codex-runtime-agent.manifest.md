---
skill_id: runtime/codex/codex-runtime-agent
name: codex-runtime-agent
type: agent
domain: runtime
family: codex
extends: runtime/base
version: 1.0.0
description: Runs SkillOS agents on top of OpenAI Codex CLI — adapts SkillOS tool-call XML to Codex's function-calling interface with OpenAI / Azure OpenAI provider support
capabilities: [openai-function-calling, azure-openai, codex-cli, tool-call-translation, process-lifecycle]
tools_required: [Read, Write, Bash, Glob, Grep]
subagent_type: codex-runtime-agent
token_cost: medium
reliability: 88%
invoke_when: [run SkillOS on Codex, OpenAI Codex CLI, Azure OpenAI, codex runtime, openai function calling]
source_repo: https://github.com/openai/codex
full_spec: system/skills/runtime/codex/codex-runtime-agent.md
---
