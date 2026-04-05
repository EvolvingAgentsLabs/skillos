# pi-mono Bridge: TypeScript Implementation

Full source for `external/pi-mono/packages/pi-skillos/src/index.ts`.

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

  const systemAgentPath = path.join(
    skillOSRoot,
    "system/skills/orchestration/core/system-agent.md"
  );
  const systemPrompt = loadSkillOSManifest(systemAgentPath);

  const ai = createAI({ provider, model });

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

## Extending with New Tools

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
