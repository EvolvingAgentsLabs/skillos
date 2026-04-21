/**
 * run_goal — TS port of
 * C:\evolvingagents\skillos\agent_runtime.py lines 1088-1235.
 *
 * Multi-turn tool-call loop. The system prompt is passed in by the caller and
 * sent with every turn; compaction is simplified to FIFO truncation of older
 * tool-result user messages (per the plan — full LLM-powered compaction is
 * deferred post-M8).
 *
 * Permissions/sandbox are no-ops on mobile: the iframe sandbox is the security
 * boundary. Tool implementations are arbitrary JS functions supplied by the
 * caller (CartridgeRunner in M5, debug screens in M3).
 */

import type { ChatMessage } from "./client";
import {
  compactMessagesAsync,
  defaultCompactionConfig,
  type CompactionConfig,
} from "./compactor";
import type { LLMProvider } from "./provider";
import {
  TOOL_ALIASES,
  extractJsonObject,
  extractTagContent,
  parseToolCalls,
  repairJsonArgs,
} from "./tool_parser";

export type ToolFunction = (
  args: Record<string, unknown>,
) => Promise<unknown> | unknown;

export interface RunGoalEvent {
  type:
    | "turn-start"
    | "assistant-delta"
    | "assistant-done"
    | "tool-call"
    | "tool-result"
    | "final-answer"
    | "error";
  turn?: number;
  content?: string;
  tool?: string;
  args?: Record<string, unknown>;
  result?: unknown;
  error?: string;
}

export interface RunGoalOptions {
  systemPrompt: string;
  tools: Record<string, ToolFunction>;
  maxTurns?: number;
  temperature?: number;
  onEvent?: (e: RunGoalEvent) => void;
  signal?: AbortSignal;
  /** Safety cap on user/tool-result message count before FIFO truncation. */
  compactThreshold?: number;
  /**
   * Compaction strategy:
   *   "fifo" (default) — cheap: drop old Tool-returned user messages.
   *   "llm"            — spend one LLM call to summarize removed turns.
   *                      Pass `compactionConfig` to tune; pass `compactionLLM`
   *                      to route the summary to a specific (cheap) provider.
   */
  compactionStrategy?: "fifo" | "llm";
  compactionConfig?: Partial<CompactionConfig>;
  compactionLLM?: LLMProvider;
}

const DEFAULT_MAX_TURNS = 10;
const DEFAULT_COMPACT_THRESHOLD = 40;

export async function runGoal(
  client: LLMProvider,
  goal: string,
  opts: RunGoalOptions,
): Promise<string> {
  const maxTurns = opts.maxTurns ?? DEFAULT_MAX_TURNS;
  const messages: ChatMessage[] = [
    { role: "user", content: `My goal is: ${goal}` },
  ];

  const compactionCfg: CompactionConfig = {
    ...defaultCompactionConfig(),
    ...(opts.compactionConfig ?? {}),
  };
  const strategy = opts.compactionStrategy ?? "fifo";

  for (let i = 0; i < maxTurns; i++) {
    if (opts.signal?.aborted) throw new Error("aborted");
    opts.onEvent?.({ type: "turn-start", turn: i + 1 });

    if (strategy === "llm") {
      const res = await compactMessagesAsync(
        messages,
        compactionCfg,
        opts.compactionLLM ?? client,
      );
      if (res.compacted > 0) {
        messages.splice(0, messages.length, ...res.messages);
      }
    } else {
      maybeCompact(messages, opts.compactThreshold ?? DEFAULT_COMPACT_THRESHOLD);
    }

    let assistantText = "";
    try {
      const result = await client.chat(
        buildMessages(messages, opts.systemPrompt),
        {
          stream: true,
          temperature: opts.temperature,
          signal: opts.signal,
          onChunk: (delta) =>
            opts.onEvent?.({ type: "assistant-delta", turn: i + 1, content: delta }),
        },
      );
      assistantText = result.content ?? "";
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      opts.onEvent?.({ type: "error", turn: i + 1, error: msg });
      return `Failed to get response from LLM: ${msg}`;
    }

    if (!assistantText.trim()) {
      messages.push({
        role: "user",
        content: "Please provide a response with tool calls or a final_answer.",
      });
      continue;
    }

    messages.push({ role: "assistant", content: assistantText });
    opts.onEvent?.({ type: "assistant-done", turn: i + 1, content: assistantText });

    const toolCalls = parseToolCalls(assistantText);
    if (toolCalls.length > 0) {
      for (const call of toolCalls) {
        const name = TOOL_ALIASES[call.name] ?? call.name;
        let args: Record<string, unknown> = {};
        try {
          const clean = extractJsonObject(call.args.trim());
          try {
            args = JSON.parse(clean);
          } catch {
            const repaired = repairJsonArgs(clean);
            if (!repaired) throw new Error("JSON repair failed");
            args = repaired;
          }
        } catch (err) {
          const msg = err instanceof Error ? err.message : String(err);
          messages.push({
            role: "user",
            content: `Error parsing arguments for tool '${name}': ${msg}. Args: ${call.args}`,
          });
          opts.onEvent?.({ type: "error", turn: i + 1, tool: name, error: msg });
          continue;
        }

        opts.onEvent?.({ type: "tool-call", turn: i + 1, tool: name, args });
        const handler = opts.tools[name];
        let toolResult: unknown;
        if (!handler) {
          const available = Object.keys(opts.tools).join(", ") || "(none)";
          toolResult = `Error: Tool '${name}' not found. Available tools: ${available}`;
        } else {
          try {
            toolResult = await handler(args);
          } catch (err) {
            toolResult = `Error executing tool '${name}': ${err instanceof Error ? err.message : String(err)}`;
          }
        }
        opts.onEvent?.({ type: "tool-result", turn: i + 1, tool: name, result: toolResult });
        messages.push({
          role: "user",
          content: `Tool '${name}' returned:\n${stringifyResult(toolResult)}`,
        });
      }
    }

    // Check for final answer after tool execution (matches Python ordering).
    const finalAnswer = extractTagContent("final_answer", assistantText);
    if (finalAnswer) {
      opts.onEvent?.({ type: "final-answer", turn: i + 1, content: finalAnswer });
      return finalAnswer;
    }

    // No tool calls, no final_answer — nudge once, then accept the raw reply.
    if (toolCalls.length === 0 && !/final_answer/i.test(assistantText)) {
      const prev = messages[messages.length - 2];
      const prevContent = prev?.content ?? "";
      if (prev?.role === "user" && prevContent.includes("provide a final_answer")) {
        opts.onEvent?.({ type: "final-answer", turn: i + 1, content: assistantText });
        return assistantText;
      }
      messages.push({
        role: "user",
        content: "Please either make a tool call or provide a final_answer.",
      });
    }
  }

  return "Agent reached maximum turns without providing a final answer.";
}

// ────────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────────

function buildMessages(conversation: ChatMessage[], systemPrompt: string): ChatMessage[] {
  if (!systemPrompt) return conversation;
  return [{ role: "system", content: systemPrompt }, ...conversation];
}

function stringifyResult(v: unknown): string {
  if (typeof v === "string") return v;
  try {
    return JSON.stringify(v, null, 2);
  } catch {
    return String(v);
  }
}

/**
 * Very-simple FIFO compaction: when the conversation grows past `threshold`
 * messages, drop the oldest tool-result user messages until we're under. We
 * never drop the first user message (the goal) or the last two messages.
 */
function maybeCompact(messages: ChatMessage[], threshold: number): void {
  if (messages.length <= threshold) return;
  const keepLast = 2;
  let i = 1; // skip goal
  while (messages.length > threshold && i < messages.length - keepLast) {
    const m = messages[i];
    if (m.role === "user" && m.content.startsWith("Tool '")) {
      messages.splice(i, 1);
      continue;
    }
    i++;
  }
}
