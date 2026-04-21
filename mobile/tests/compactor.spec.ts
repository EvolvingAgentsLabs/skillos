import { describe, expect, it, vi } from "vitest";
import type { ChatMessage } from "../src/lib/llm/client";
import {
  compactMessages,
  compactMessagesAsync,
  configureForModel,
  defaultCompactionConfig,
  estimateTokens,
  shouldCompact,
} from "../src/lib/llm/compactor";
import type { LLMProvider } from "../src/lib/llm/provider";

function mkMsg(role: ChatMessage["role"], content: string): ChatMessage {
  return { role, content };
}

function longConversation(n: number, sizePer = 8000): ChatMessage[] {
  const out: ChatMessage[] = [mkMsg("user", "Original goal")];
  for (let i = 0; i < n; i++) {
    out.push(mkMsg("assistant", `turn ${i} ${"x".repeat(sizePer)}`));
    out.push(
      mkMsg("user", `Tool 'something' returned:\npayload ${"y".repeat(sizePer)}`),
    );
  }
  return out;
}

describe("estimateTokens", () => {
  it("uses the char/4 heuristic", () => {
    const ms = [mkMsg("user", "x".repeat(400))];
    const n = estimateTokens(ms);
    // 400/4 + 1 = 101
    expect(n).toBe(101);
  });
});

describe("shouldCompact", () => {
  it("requires both a preserve-count breach AND a token threshold breach", () => {
    const cfg = defaultCompactionConfig();
    const short = [mkMsg("user", "hi"), mkMsg("assistant", "hello")];
    expect(shouldCompact(short, cfg)).toBe(false);

    const manyShort = Array.from({ length: 20 }, (_, i) =>
      mkMsg(i % 2 === 0 ? "user" : "assistant", "a"),
    );
    expect(shouldCompact(manyShort, cfg)).toBe(false); // many but tiny

    const long = longConversation(6);
    expect(shouldCompact(long, cfg)).toBe(true);
  });
});

describe("configureForModel", () => {
  it("raises threshold for large-context models", () => {
    const cfg = configureForModel(defaultCompactionConfig(), "gemini-2.5-flash");
    // 1_048_576 * 0.7 = 734_003 (above the 8K floor)
    expect(cfg.maxEstimatedTokens).toBeGreaterThan(700_000);
  });
  it("floors at MIN_COMPACTION_THRESHOLD for tiny models", () => {
    const cfg = configureForModel(defaultCompactionConfig(), "gemma-2-2b-it-q4_k_m");
    // 8192 * 0.7 = 5734, below 8000 floor → clamped
    expect(cfg.maxEstimatedTokens).toBe(8_000);
  });
  it("no-ops for unknown models", () => {
    const base = defaultCompactionConfig();
    const cfg = configureForModel(base, "mystery-model");
    expect(cfg.maxEstimatedTokens).toBe(base.maxEstimatedTokens);
  });
});

describe("compactMessages (fifo textual)", () => {
  it("preserves the last N messages and folds the rest into a summary", () => {
    const cfg = { ...defaultCompactionConfig(), preserveRecentMessages: 3 };
    const long = longConversation(8);
    const res = compactMessages(long, cfg);
    expect(res.compacted).toBeGreaterThan(0);
    expect(res.messages.length).toBe(3 + 1); // preserved + 1 summary
    expect(res.messages[0].role).toBe("user");
    expect(res.messages[0].content).toContain("Session continues");
    expect(res.summary.length).toBeGreaterThan(0);
  });

  it("returns unchanged when under threshold", () => {
    const cfg = defaultCompactionConfig();
    const short = [mkMsg("user", "hi"), mkMsg("assistant", "there")];
    const res = compactMessages(short, cfg);
    expect(res.compacted).toBe(0);
    expect(res.messages).toBe(short);
  });
});

describe("compactMessagesAsync (llm path)", () => {
  it("calls the LLM for removed messages when above llmSummaryMinMessages", async () => {
    const chat = vi.fn(async () => ({
      content: "- point one\n- point two\n- point three",
    })) as unknown as LLMProvider["chat"];
    const llm = { chat, testConnection: async () => ({ ok: true, message: "fake" }) };
    const cfg = { ...defaultCompactionConfig(), preserveRecentMessages: 3 };
    const long = longConversation(8);
    const res = await compactMessagesAsync(long, cfg, llm);
    expect(res.summary).toContain("point one");
    expect(chat).toHaveBeenCalledTimes(1);
    const args = (chat as unknown as { mock: { calls: unknown[][] } }).mock.calls[0];
    // Arg 0 should be a messages array containing the transcript prompt.
    const messages = args[0] as ChatMessage[];
    expect(messages.some((m) => String(m.content).includes("Summarize this conversation"))).toBe(
      true,
    );
  });

  it("falls back to textual summary when llm throws", async () => {
    const llm: LLMProvider = {
      chat: async () => {
        throw new Error("provider down");
      },
      testConnection: async () => ({ ok: false, message: "down" }),
    };
    const cfg = { ...defaultCompactionConfig(), preserveRecentMessages: 3 };
    const long = longConversation(8);
    const res = await compactMessagesAsync(long, cfg, llm);
    // Textual summary contains at least one bullet and uses the role:content format
    expect(res.summary).toMatch(/^-\s\w+:/m);
  });

  it("skips llm summary when removed count is below llmSummaryMinMessages", async () => {
    const chat = vi.fn(async () => ({ content: "unused" }));
    const llm = {
      chat: chat as unknown as LLMProvider["chat"],
      testConnection: async () => ({ ok: true, message: "fake" }),
    };
    const cfg = {
      ...defaultCompactionConfig(),
      preserveRecentMessages: 10,
      llmSummaryMinMessages: 100, // never engages LLM
    };
    const res = await compactMessagesAsync(longConversation(8), cfg, llm);
    expect(chat).not.toHaveBeenCalled();
    // Textual summary still runs, producing a bulleted list.
    expect(res.compacted).toBeGreaterThan(0);
    expect(res.summary).toMatch(/^-\s/m);
  });
});
