---
skill_id: content/meta/claude-api
name: claude-api
type: tool
domain: content
family: meta
extends: content/base
version: 1.0.0
source: github:anthropics/skills/claude-api
description: Use the Anthropic Claude API / SDK to make sub-LLM calls for parallelism or specialization
capabilities: [sub-llm-calls, claude-api, anthropic-sdk, parallel-llm, streaming, batch-inference]
tools_required: [Bash]
token_cost: low
reliability: 95%
invoke_when: [call Claude API, sub-agent LLM call, Anthropic SDK, parallel inference, LLM pipeline]
full_spec: system/skills/content/meta/claude-api.md
---
