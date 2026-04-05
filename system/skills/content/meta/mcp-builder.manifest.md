---
skill_id: content/meta/mcp-builder
name: mcp-builder
type: tool
domain: content
family: meta
extends: content/base
version: 1.0.0
source: github:anthropics/skills/mcp-builder
description: Generate MCP (Model Context Protocol) servers from a spec — adds tools to Claude's runtime
capabilities: [mcp-server-generation, tool-spec-to-code, MCP-registration, server-scaffolding]
tools_required: [Read, Write, Bash]
token_cost: medium
reliability: 85%
invoke_when: [build MCP server, create MCP tool, expose API as MCP, generate MCP, extend Claude tools]
full_spec: system/skills/content/meta/mcp-builder.md
---
