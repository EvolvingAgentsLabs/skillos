---
name: mcp-builder
extends: content/base
domain: content
family: meta
source: github:anthropics/skills/mcp-builder
source_file: components/skills/mcp-builder/SKILL.md
version: 1.0.0
tools: [Read, Write, Bash]
---

# MCP Builder

Generate Model Context Protocol (MCP) servers from a spec — extends Claude's runtime toolset without code changes.

## Source

Wraps `components/skills/mcp-builder/SKILL.md` (sourced from `anthropics/skills`).

---

## What is MCP?

MCP (Model Context Protocol) is Anthropic's standard for adding tools to Claude at runtime.
An MCP server exposes tools as JSON-Schema-defined functions that Claude can call.
Building one means Claude gains new capabilities without modifying the core system.

---

## Capabilities

| Operation | Description |
|-----------|-------------|
| **Spec → server** | Generate a Python MCP server from a tool spec |
| **Register server** | Add MCP server to `.claude/settings.json` |
| **Test server** | Validate tool invocations locally |
| **Scaffold** | Boilerplate for new MCP projects |

---

## Protocol

### Step 1 — Define Tool Spec

Provide a plain-language description of the tool(s) to expose:
```
Tool name: weather-fetcher
Description: Get current weather for a city
Input: { "city": string }
Output: { "temperature": number, "conditions": string }
```

### Step 2 — Generate Server Code

```python
# Generated MCP server template
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types
import asyncio

server = Server("weather-fetcher")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_weather",
            description="Get current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name"}
                },
                "required": ["city"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "get_weather":
        city = arguments["city"]
        # TODO: implement actual weather fetch
        return [types.TextContent(type="text", text=f"Weather for {city}: 22°C, Sunny")]
    raise ValueError(f"Unknown tool: {name}")

async def main():
    async with stdio_server() as streams:
        await server.run(*streams, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3 — Write Server File

Save to `projects/[Project]/output/mcp_servers/{server_name}.py`

### Step 4 — Register in Settings

Add to `.claude/settings.json`:
```json
{
  "mcpServers": {
    "weather-fetcher": {
      "command": "python3",
      "args": ["projects/[Project]/output/mcp_servers/weather_fetcher.py"]
    }
  }
}
```

### Step 5 — Install Dependencies

```bash
pip install mcp
```

---

## Examples

**"Build an MCP tool that queries our internal database"**
→ Generates Python MCP server with `query_db` tool → registers in settings.json

**"Expose the web-research-agent as an MCP tool"**
→ Wraps web-research-agent invoke logic in MCP server → adds to Claude's toolset
