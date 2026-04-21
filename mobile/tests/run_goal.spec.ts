import { describe, expect, it, vi } from "vitest";
import type { LLMClient } from "../src/lib/llm/client";
import { runGoal, type RunGoalEvent } from "../src/lib/llm/run_goal";

/**
 * Fake LLMClient that returns canned assistant turns in order. Ignores
 * messages; each chat() call pops one response and simulates streaming.
 */
function fakeClient(turns: string[]): LLMClient {
  let i = 0;
  const chat = async (
    _messages: Array<{ role: string; content: string }>,
    opts: { onChunk?: (s: string) => void } = {},
  ) => {
    const content = turns[i++] ?? "";
    // Simulate per-character streaming so onChunk observers see activity.
    if (opts.onChunk && content.length > 0) {
      for (const ch of content.match(/.{1,8}/gs) ?? []) opts.onChunk(ch);
    }
    return { content };
  };
  return { chat } as unknown as LLMClient;
}

describe("runGoal", () => {
  it("stops when the model returns <final_answer>", async () => {
    const client = fakeClient([
      "<final_answer>hello world</final_answer>",
    ]);
    const events: RunGoalEvent[] = [];
    const result = await runGoal(client, "say hello", {
      systemPrompt: "you are helpful",
      tools: {},
      onEvent: (e) => events.push(e),
    });
    expect(result).toBe("hello world");
    expect(events.some((e) => e.type === "final-answer")).toBe(true);
    expect(events.some((e) => e.type === "assistant-delta")).toBe(true);
  });

  it("executes a tool call then accepts the subsequent final_answer", async () => {
    const client = fakeClient([
      '<tool_call name="write_file">{"path":"a.md","content":"x"}</tool_call>',
      "<final_answer>wrote it</final_answer>",
    ]);
    const tool = vi.fn(async (_args: Record<string, unknown>) => "ok");
    const events: RunGoalEvent[] = [];
    const out = await runGoal(client, "write a file", {
      systemPrompt: "",
      tools: { write_file: tool },
      onEvent: (e) => events.push(e),
    });
    expect(out).toBe("wrote it");
    expect(tool).toHaveBeenCalledTimes(1);
    expect(tool.mock.calls[0][0]).toEqual({ path: "a.md", content: "x" });
    expect(events.filter((e) => e.type === "tool-call").length).toBe(1);
    expect(events.filter((e) => e.type === "tool-result").length).toBe(1);
  });

  it("maps run_agent to delegate_to_agent via TOOL_ALIASES", async () => {
    const client = fakeClient([
      '<tool_call name="run_agent">{"agent_name":"mathematician","task":"go"}</tool_call>',
      "<final_answer>done</final_answer>",
    ]);
    const delegate = vi.fn(async () => "delegated");
    await runGoal(client, "delegate", {
      systemPrompt: "",
      tools: { delegate_to_agent: delegate },
    });
    expect(delegate).toHaveBeenCalledTimes(1);
  });

  it("reports tool-not-found error without crashing", async () => {
    const client = fakeClient([
      '<tool_call name="missing">{"a":1}</tool_call>',
      "<final_answer>ok</final_answer>",
    ]);
    const events: RunGoalEvent[] = [];
    const result = await runGoal(client, "test", {
      systemPrompt: "",
      tools: {},
      onEvent: (e) => events.push(e),
    });
    expect(result).toBe("ok");
    const toolResult = events.find((e) => e.type === "tool-result");
    expect(String(toolResult?.result)).toContain("not found");
  });

  it("falls back to accepting raw response after two prompts without tags", async () => {
    const client = fakeClient(["plain text answer", "still plain text"]);
    const result = await runGoal(client, "q", {
      systemPrompt: "",
      tools: {},
      maxTurns: 5,
    });
    expect(result).toBe("still plain text");
  });

  it("stops at maxTurns", async () => {
    const client = fakeClient(Array(20).fill(""));
    const result = await runGoal(client, "q", {
      systemPrompt: "",
      tools: {},
      maxTurns: 3,
    });
    expect(result).toMatch(/maximum turns/);
  });

  it("recovers from malformed JSON args by injecting an error turn", async () => {
    const client = fakeClient([
      '<tool_call name="write_file">not json</tool_call>',
      "<final_answer>ok</final_answer>",
    ]);
    const events: RunGoalEvent[] = [];
    const result = await runGoal(client, "x", {
      systemPrompt: "",
      tools: { write_file: () => "ok" },
      onEvent: (e) => events.push(e),
    });
    expect(result).toBe("ok");
    expect(events.some((e) => e.type === "error")).toBe(true);
  });
});
