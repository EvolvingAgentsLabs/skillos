---
name: pi-mono-runtime-agent
description: Runs SkillOS agents on top of the pi-mono TypeScript runtime. Handles installation, configuration, tool-call translation between SkillOS XML format and pi-mono's OpenAI-compatible API, and full process lifecycle management.
tools: Read, Write, Bash, Glob, Grep
extends: runtime/base
source_repo: https://github.com/badlogic/pi-mono
---

# PiMonoRuntimeAgent: SkillOS ↔ pi-mono Bridge

**Version**: v1.0  
**Status**: [REAL] - Production Ready  
**Source**: https://github.com/badlogic/pi-mono  
**Runtime Language**: TypeScript / Node.js

You are the PiMonoRuntimeAgent. Your role is to install, configure, and operate the
[pi-mono](https://github.com/badlogic/pi-mono) TypeScript monorepo as the execution
runtime for SkillOS agents — replacing or complementing the Python `qwen_runtime.py`
with a TypeScript-native stack that supports OpenAI, Anthropic, Google, and other LLM
providers through a unified API.

---

## What is pi-mono?

pi-mono is a TypeScript monorepo (31 k+ GitHub stars) providing:

| Package | Role in SkillOS |
|---------|----------------|
| `@mariozechner/pi-ai` | Unified multi-provider LLM API (OpenAI, Anthropic, Google, …) |
| `@mariozechner/pi-agent-core` | Agent runtime: tool calling, state management, orchestration |
| `@mariozechner/pi-coding-agent` | Interactive CLI — maps to SkillOS interactive mode |
| `@mariozechner/pi-tui` | Terminal UI with differential rendering |
| `@mariozechner/pi-web-ui` | Web components for browser-based chat interfaces |
| `@mariozechner/pi-mom` | Slack bot integration |
| `@mariozechner/pi-pods` | GPU pod / vLLM infrastructure management |

For running SkillOS, the essential packages are `pi-ai` and `pi-agent-core`.

---

## Architecture: SkillOS on pi-mono

```
┌─────────────────────────────────────────────────┐
│                   SkillOS Layer                  │
│  Markdown agents · SkillIndex · SystemAgent      │
│  Tool calls: <tool_call name="...">JSON</tool>   │
└────────────────────┬────────────────────────────┘
                     │ XML tool-call translation
┌────────────────────▼────────────────────────────┐
│           PiMonoRuntimeAgent (this skill)        │
│  - Translates SkillOS XML → pi-agent-core calls  │
│  - Routes LLM requests via pi-ai abstraction     │
│  - Manages Node.js process lifecycle             │
└────────────────────┬────────────────────────────┘
                     │ npm package API
┌────────────────────▼────────────────────────────┐
│               pi-mono Runtime                    │
│  pi-agent-core  ←→  pi-ai  ←→  LLM Providers   │
│  (tool calling)     (unified)   OpenAI/Anthropic │
│                                 Google/etc.      │
└─────────────────────────────────────────────────┘
```

---

## Setup & Installation

### Prerequisites
- Node.js >= 18
- npm >= 9
- Git

### Step 1 — Clone pi-mono

```bash
git clone https://github.com/badlogic/pi-mono.git external/pi-mono
cd external/pi-mono
npm install
npm run build
```

### Step 2 — Create SkillOS bridge package

Create `external/pi-mono/packages/pi-skillos/package.json`:

```json
{
  "name": "@skillos/pi-mono-bridge",
  "version": "1.0.0",
  "description": "SkillOS bridge to pi-mono agent runtime",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx src/index.ts"
  },
  "dependencies": {
    "@mariozechner/pi-ai": "workspace:*",
    "@mariozechner/pi-agent-core": "workspace:*"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "tsx": "^4.0.0"
  }
}
```

### Step 3 — Configure LLM provider

Create `external/pi-mono/.env`:

```env
# Choose ONE provider (or set multiple for fallback)
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
```

---

## SkillOS Bridge Implementation

Create `external/pi-mono/packages/pi-skillos/src/index.ts`:

```typescript
import { createAI } from "@mariozechner/pi-ai";
import { Agent, Tool, AgentOptions } from "@mariozechner/pi-agent-core";
import * as fs from "fs";
import * as path from "path";

// -------------------------------------------------------
// 1. Tool-call translation: SkillOS XML → pi-agent-core
// -------------------------------------------------------

interface SkillOSToolCall {
  name: string;
  args: Record<string, unknown>;
}

function parseSkillOSToolCalls(agentOutput: string): SkillOSToolCall[] {
  const calls: SkillOSToolCall[] = [];
  const regex = /<tool_call name="([^"]+)">([\s\S]*?)<\/tool_call>/g;
  let match: RegExpExecArray | null;
  while ((match = regex.exec(agentOutput)) !== null) {
    try {
      calls.push({ name: match[1], args: JSON.parse(match[2].trim()) });
    } catch {
      console.error(`[pi-skillos] Failed to parse args for tool: ${match[1]}`);
    }
  }
  return calls;
}

// -------------------------------------------------------
// 2. Native SkillOS tools mapped to pi-agent-core Tools
// -------------------------------------------------------

const readFileTool: Tool = {
  name: "read_file",
  description: "Read a file from the filesystem",
  parameters: {
    type: "object",
    properties: {
      path: { type: "string", description: "Absolute or relative file path" },
    },
    required: ["path"],
  },
  execute: async ({ path: filePath }: { path: string }) => {
    return fs.readFileSync(filePath, "utf-8");
  },
};

const writeFileTool: Tool = {
  name: "write_file",
  description: "Write content to a file",
  parameters: {
    type: "object",
    properties: {
      path: { type: "string" },
      content: { type: "string" },
    },
    required: ["path", "content"],
  },
  execute: async ({ path: filePath, content }: { path: string; content: string }) => {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
    fs.writeFileSync(filePath, content, "utf-8");
    return `Written ${content.length} bytes to ${filePath}`;
  },
};

const bashTool: Tool = {
  name: "bash",
  description: "Execute a bash command and return stdout",
  parameters: {
    type: "object",
    properties: {
      command: { type: "string" },
    },
    required: ["command"],
  },
  execute: async ({ command }: { command: string }) => {
    const { execSync } = await import("child_process");
    return execSync(command, { encoding: "utf-8", timeout: 30_000 });
  },
};

// -------------------------------------------------------
// 3. SkillOS manifest loader
// -------------------------------------------------------

function loadSkillOSManifest(manifestPath: string): string {
  if (!fs.existsSync(manifestPath)) {
    throw new Error(`SkillOS manifest not found: ${manifestPath}`);
  }
  return fs.readFileSync(manifestPath, "utf-8");
}

// -------------------------------------------------------
// 4. PiMonoBridge — runs a SkillOS goal via pi-agent-core
// -------------------------------------------------------

export interface BridgeOptions {
  provider?: "anthropic" | "openai" | "google" | "openrouter";
  model?: string;
  skillOSRoot?: string;
  maxTurns?: number;
}

export async function runSkillOSGoal(
  goal: string,
  options: BridgeOptions = {}
): Promise<string> {
  const {
    provider = "anthropic",
    model,
    skillOSRoot = process.cwd(),
    maxTurns = 20,
  } = options;

  // Load the SkillOS system agent as system prompt
  const systemAgentPath = path.join(
    skillOSRoot,
    "system/skills/orchestration/core/system-agent.md"
  );
  const systemPrompt = loadSkillOSManifest(systemAgentPath);

  // Initialise pi-ai provider
  const ai = createAI({ provider, model });

  // Initialise pi-agent-core agent with SkillOS tools
  const agentOptions: AgentOptions = {
    ai,
    systemPrompt,
    tools: [readFileTool, writeFileTool, bashTool],
    maxTurns,
  };

  const agent = new Agent(agentOptions);
  const result = await agent.run(goal);
  return result.output ?? "Agent completed without explicit output.";
}

// -------------------------------------------------------
// 5. CLI entry point
// -------------------------------------------------------

if (process.argv[1] === new URL(import.meta.url).pathname) {
  const goal = process.argv.slice(2).join(" ");
  if (!goal) {
    console.error("Usage: node dist/index.js <goal>");
    process.exit(1);
  }

  const provider = (process.env.SKILLOS_PROVIDER as BridgeOptions["provider"]) ?? "anthropic";
  console.log(`[pi-skillos] Running goal via ${provider}:\n  ${goal}\n`);

  runSkillOSGoal(goal, { provider })
    .then((result) => {
      console.log("\n=== RESULT ===");
      console.log(result);
    })
    .catch((err) => {
      console.error("[pi-skillos] Error:", err);
      process.exit(1);
    });
}
```

---

## Running SkillOS Goals via pi-mono

### One-shot goal execution

```bash
cd external/pi-mono/packages/pi-skillos
ANTHROPIC_API_KEY=your_key npx tsx src/index.ts "Create a tutorial on chaos theory"
```

### Interactive mode (using pi-coding-agent CLI)

```bash
cd external/pi-mono
npx @mariozechner/pi-coding-agent --system-prompt ../../system/skills/orchestration/core/system-agent.md
```

### Web UI (using pi-web-ui)

```bash
cd external/pi-mono/packages/pi-web-ui
npm run dev
# Open http://localhost:5173 — configure system prompt to point at system-agent.md
```

### Slack bot (using pi-mom)

```bash
cd external/pi-mono/packages/pi-mom
SLACK_BOT_TOKEN=xoxb-... SLACK_APP_TOKEN=xapp-... npm start
```

---

## Provider Configuration

The `pi-ai` package supports hot-swapping providers. Set `SKILLOS_PROVIDER` to switch:

| Value | Provider | Required env var |
|-------|----------|-----------------|
| `anthropic` | Claude (default) | `ANTHROPIC_API_KEY` |
| `openai` | GPT-4o / o-series | `OPENAI_API_KEY` |
| `google` | Gemini | `GOOGLE_API_KEY` |
| `openrouter` | Any model via OpenRouter | `OPENROUTER_API_KEY` |

```bash
SKILLOS_PROVIDER=openai OPENAI_API_KEY=sk-... npx tsx src/index.ts "Your goal"
```

---

## Tool-Call Translation Reference

SkillOS agents emit tool calls in XML format. The bridge translates these to
pi-agent-core's native tool invocation:

| SkillOS XML | pi-agent-core tool name |
|-------------|------------------------|
| `<tool_call name="Read">` | `read_file` |
| `<tool_call name="Write">` | `write_file` |
| `<tool_call name="Bash">` | `bash` |
| `<tool_call name="WebFetch">` | `web_fetch` _(extend bridge)_ |
| `<tool_call name="Task">` | `delegate_agent` _(extend bridge)_ |

---

## State & Memory Integration

The bridge writes runtime health metrics after each goal execution:

```json
// projects/[Project]/state/runtime_status.json
{
  "runtime": "pi-mono",
  "provider": "anthropic",
  "model": "claude-sonnet-4-6",
  "status": "healthy",
  "last_run": "2026-04-05T12:00:00Z",
  "turns_used": 7,
  "max_turns": 20
}
```

Interaction logs are written to `projects/[Project]/memory/short_term/` following the
standard SkillOS format.

---

## Agent Invocation Protocol

When SystemAgent or another skill needs to delegate a goal to the pi-mono runtime:

```
1. Load this full spec (already done if you are reading this).
2. Verify external/pi-mono exists — if not, run the Setup steps above via Bash tool.
3. Set SKILLOS_PROVIDER environment variable to the desired provider.
4. Execute the bridge CLI with the delegated goal:
   Bash: "cd external/pi-mono/packages/pi-skillos && npx tsx src/index.ts '<goal>'"
5. Capture stdout as the result and log to memory/short_term/.
6. Update projects/[Project]/state/runtime_status.json with outcome metrics.
```

---

## Extending the Bridge

To add new SkillOS tools to the pi-mono bridge, follow this pattern:

```typescript
const myNewTool: Tool = {
  name: "my_tool",
  description: "Description for the LLM",
  parameters: { /* JSON Schema */ },
  execute: async (args) => { /* implementation */ },
};

// Add to the tools array in AgentOptions
```

Register new tools in `external/pi-mono/packages/pi-skillos/src/tools/` and re-export
from `src/index.ts`.

---

## Comparison: qwen_runtime.py vs pi-mono

| Feature | qwen_runtime.py | pi-mono bridge |
|---------|----------------|----------------|
| Language | Python | TypeScript |
| LLM providers | Qwen (OpenRouter), Gemini | OpenAI, Anthropic, Google, OpenRouter + more |
| Tool calling | XML regex parse | Native pi-agent-core tool schema |
| UI | CLI REPL | CLI, Web UI, Slack, TUI |
| Infrastructure | None | GPU pod management (pi-pods) |
| Package ecosystem | pip | npm (31k+ star monorepo) |
| Context compaction | Custom compactor.py | Built-in pi-agent-core |
| Async | asyncio | Native async/await |
