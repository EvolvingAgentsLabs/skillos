---
name: mcp-builder
version: 1.0.0
source_repo: anthropics/skills
source_path: skills/mcp-builder/
license: MIT
installed_by: SkillOS
description: Generate MCP servers from a tool spec — adds tools to Claude's runtime
tools: [Read, Write, Bash]
dependencies:
  - mcp>=1.0.0
---

# MCP Builder (Source)

Raw skill source from `anthropics/skills`.
SkillOS-integrated version: `system/skills/content/meta/mcp-builder.md`

## What This Skill Does

Generates Python MCP (Model Context Protocol) server code from a plain-language
tool specification. The generated server can be registered in `.claude/settings.json`
to extend Claude Code's available tools at runtime.

## Quick Start

1. Describe your tool: name, description, input schema, output format
2. MCP Builder generates a Python server using the `mcp` SDK
3. Register the server in `.claude/settings.json`
4. Claude Code discovers the new tool on next startup

## Install Dependencies

```bash
pip install mcp
```
