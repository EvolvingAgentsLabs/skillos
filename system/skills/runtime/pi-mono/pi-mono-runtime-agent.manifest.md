---
skill_id: runtime/pi-mono/pi-mono-runtime-agent
name: pi-mono-runtime-agent
type: agent
domain: runtime
family: pi-mono
extends: runtime/base
version: 1.0.0
description: Runs SkillOS agents on top of the pi-mono TypeScript runtime — handles setup, tool-call translation, multi-provider LLM routing, and process lifecycle
capabilities: [runtime-setup, tool-call-translation, multi-provider-llm, process-lifecycle, skillos-bridge]
tools_required: [Read, Write, Bash, Glob, Grep]
subagent_type: pi-mono-runtime-agent
token_cost: medium
reliability: 90%
invoke_when: [run SkillOS on pi-mono, TypeScript agent runtime, Node.js deployment, pi-mono integration, multi-provider LLM via pi-ai]
source_repo: https://github.com/badlogic/pi-mono
full_spec: system/skills/runtime/pi-mono/pi-mono-runtime-agent.md
---
