import { describe, expect, it } from "vitest";
import { formatPrompt } from "../src/lib/llm/local/chat_templates";

describe("formatPrompt — gemma-v2", () => {
  it("wraps a single user turn with model generation tags", () => {
    const { prompt, stop } = formatPrompt("gemma-v2", [
      { role: "user", content: "What is 2+2?" },
    ]);
    expect(prompt).toBe(
      "<start_of_turn>user\nWhat is 2+2?<end_of_turn>\n<start_of_turn>model\n",
    );
    expect(stop).toContain("<end_of_turn>");
  });

  it("fuses system messages into the first user turn", () => {
    const { prompt } = formatPrompt("gemma-v2", [
      { role: "system", content: "You are helpful." },
      { role: "user", content: "Hi" },
    ]);
    expect(prompt).toContain("You are helpful.");
    expect(prompt).toContain("Hi");
    expect(prompt).not.toContain("<start_of_turn>system");
  });

  it("interleaves user/assistant turns", () => {
    const { prompt } = formatPrompt("gemma-v2", [
      { role: "user", content: "hi" },
      { role: "assistant", content: "hello" },
      { role: "user", content: "how are you?" },
    ]);
    expect(prompt).toContain("<start_of_turn>user\nhi<end_of_turn>");
    expect(prompt).toContain("<start_of_turn>model\nhello<end_of_turn>");
    expect(prompt).toContain("<start_of_turn>user\nhow are you?<end_of_turn>");
    expect(prompt.endsWith("<start_of_turn>model\n")).toBe(true);
  });
});

describe("formatPrompt — chatml / qwen2", () => {
  it("formats chatml with system role", () => {
    const { prompt, stop } = formatPrompt("qwen2", [
      { role: "system", content: "Be brief." },
      { role: "user", content: "Hi" },
    ]);
    expect(prompt).toContain("<|im_start|>system\nBe brief.<|im_end|>");
    expect(prompt).toContain("<|im_start|>user\nHi<|im_end|>");
    expect(prompt.endsWith("<|im_start|>assistant\n")).toBe(true);
    expect(stop).toContain("<|im_end|>");
  });
});

describe("formatPrompt — llama3", () => {
  it("emits the llama3 header tokens", () => {
    const { prompt, stop } = formatPrompt("llama3", [
      { role: "system", content: "s" },
      { role: "user", content: "u" },
    ]);
    expect(prompt.startsWith("<|begin_of_text|>")).toBe(true);
    expect(prompt).toContain("<|start_header_id|>system<|end_header_id|>");
    expect(prompt).toContain("<|start_header_id|>user<|end_header_id|>");
    expect(prompt).toContain("<|eot_id|>");
    expect(stop).toContain("<|eot_id|>");
  });
});
