/**
 * Context compaction — TS port of
 * C:\evolvingagents\skillos\compactor.py.
 *
 * When a `runGoal` loop's conversation grows past a token-estimated
 * threshold, compact older messages into a single summary user-message and
 * preserve the recent N turns verbatim. Two modes:
 *   - "fifo": drop old tool-result turns (v0 behavior, kept as safety net)
 *   - "llm": semantic summary via the LLM (new in M16)
 *
 * The same char/4 token heuristic as the Python runtime.
 */

import type { ChatMessage } from "./client";
import type { LLMProvider } from "./provider";

export const MODEL_CONTEXT_WINDOWS: Record<string, number> = {
  "qwen/qwen3.6-plus:free": 32_000,
  "qwen/qwen3-plus": 32_000,
  "gemini-2.5-flash": 1_048_576,
  "gemini-2.5-pro": 1_048_576,
  "gemini-2.0-flash": 1_048_576,
  gemma4: 128_000,
  "gemma4:e2b": 128_000,
  "gemma4:e4b": 128_000,
  "gemma4:26b": 256_000,
  "gemma4:31b": 256_000,
  "google/gemma-4-26b-a4b-it": 131_072,
  // M9 local models
  "qwen2.5-1.5b-instruct-q4_k_m": 32_768,
  "gemma-2-2b-it-q4_k_m": 8_192,
  "gemma-2-2b-it-litertlm": 8_192,
};

export const DEFAULT_COMPACTION_RATIO = 0.7;
export const MIN_COMPACTION_THRESHOLD = 8_000;

export interface CompactionConfig {
  preserveRecentMessages: number;
  maxEstimatedTokens: number;
  /**
   * Minimum removed-message count for LLM summarization to engage. Below
   * this we fall through to the textual summary.
   */
  llmSummaryMinMessages: number;
}

export function defaultCompactionConfig(): CompactionConfig {
  return {
    preserveRecentMessages: 4,
    maxEstimatedTokens: 10_000,
    llmSummaryMinMessages: 4,
  };
}

export function configureForModel(
  config: CompactionConfig,
  modelName: string,
): CompactionConfig {
  const window = MODEL_CONTEXT_WINDOWS[modelName];
  if (window !== undefined) {
    return {
      ...config,
      maxEstimatedTokens: Math.max(
        MIN_COMPACTION_THRESHOLD,
        Math.floor(window * DEFAULT_COMPACTION_RATIO),
      ),
    };
  }
  return config;
}

export function estimateTokens(messages: ChatMessage[]): number {
  let total = 0;
  for (const m of messages) {
    const c = m.content ?? "";
    total += Math.floor(String(c).length / 4) + 1;
  }
  return total;
}

export function shouldCompact(
  messages: ChatMessage[],
  config: CompactionConfig,
): boolean {
  return (
    messages.length > config.preserveRecentMessages &&
    estimateTokens(messages) >= config.maxEstimatedTokens
  );
}

/** Textual fallback — just a bulleted list of short role:content previews. */
function summarizeTextual(messages: ChatMessage[]): string {
  return messages
    .map((m) => {
      const role = m.role ?? "unknown";
      const content = String(m.content ?? "");
      const short = content.length > 160 ? `${content.slice(0, 160)}…` : content;
      return `- ${role}: ${short}`;
    })
    .join("\n");
}

async function summarizeWithLLM(
  messages: ChatMessage[],
  llm: LLMProvider,
): Promise<string> {
  const transcript = messages
    .map((m) => `[${m.role}]: ${String(m.content ?? "").slice(0, 500)}`)
    .join("\n");
  const prompt =
    "Summarize this conversation into 3–5 bullet points. " +
    "Preserve concrete identifiers, numbers, file paths, tool results, errors encountered.\n\n" +
    `Conversation (${messages.length} messages):\n${transcript}`;
  try {
    const r = await llm.chat(
      [
        { role: "system", content: "Output only bullet points." },
        { role: "user", content: prompt },
      ],
      { stream: false, temperature: 0.1, maxTokens: 512 },
    );
    return r.content.trim() || summarizeTextual(messages);
  } catch {
    return summarizeTextual(messages);
  }
}

export interface CompactResult {
  messages: ChatMessage[];
  summary: string;
  /** How many messages were rolled into the summary. */
  compacted: number;
}

/**
 * Compact older messages into a summary user-message while preserving the
 * most recent N. Pure synchronous fallback (no LLM call).
 */
export function compactMessages(
  messages: ChatMessage[],
  config: CompactionConfig,
): CompactResult {
  if (!shouldCompact(messages, config)) {
    return { messages, summary: "", compacted: 0 };
  }
  const keepFrom = Math.max(0, messages.length - config.preserveRecentMessages);
  const removed = messages.slice(0, keepFrom);
  const preserved = messages.slice(keepFrom);
  const summary = summarizeTextual(removed);
  return {
    messages: [summaryMessage(summary), ...preserved],
    summary,
    compacted: removed.length,
  };
}

/** Async LLM-powered compaction. Fires through `llm.chat`. */
export async function compactMessagesAsync(
  messages: ChatMessage[],
  config: CompactionConfig,
  llm?: LLMProvider,
): Promise<CompactResult> {
  if (!shouldCompact(messages, config)) {
    return { messages, summary: "", compacted: 0 };
  }
  const keepFrom = Math.max(0, messages.length - config.preserveRecentMessages);
  const removed = messages.slice(0, keepFrom);
  const preserved = messages.slice(keepFrom);
  const summary =
    llm && removed.length >= config.llmSummaryMinMessages
      ? await summarizeWithLLM(removed, llm)
      : summarizeTextual(removed);
  return {
    messages: [summaryMessage(summary), ...preserved],
    summary,
    compacted: removed.length,
  };
}

function summaryMessage(summary: string): ChatMessage {
  return {
    role: "user",
    content:
      "Session continues. Prior context:\n\n" +
      `${summary}\n\n` +
      "Recent messages preserved verbatim. Continue without recapping.",
  };
}
