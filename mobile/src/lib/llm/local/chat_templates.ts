/**
 * Chat template formatters — turn OpenAI-style message arrays into the raw
 * prompt strings each model family expects. Wrong template ⇒ garbage output,
 * so we pin these per model entry in `model_catalog.ts`.
 *
 * Test fixtures in `tests/chat_templates.spec.ts` snapshot one turn per family
 * against a captured ground truth.
 */

import type { ChatMessage } from "../client";
import type { ChatTemplateFamily } from "./model_catalog";

export interface FormattedPrompt {
  prompt: string;
  /** Stop strings to pass to the backend's sampler. */
  stop: string[];
}

export function formatPrompt(family: ChatTemplateFamily, messages: ChatMessage[]): FormattedPrompt {
  switch (family) {
    case "gemma-v2":
    case "gemma-v3":
      return formatGemma(messages);
    case "qwen2":
      return formatChatML(messages, { imStart: "<|im_start|>", imEnd: "<|im_end|>" });
    case "chatml":
      return formatChatML(messages, { imStart: "<|im_start|>", imEnd: "<|im_end|>" });
    case "llama3":
      return formatLlama3(messages);
    case "tinyllama":
      return formatChatML(messages, { imStart: "<|system|>", imEnd: "</s>" });
  }
}

/**
 * Gemma 2/3: `<start_of_turn>user\n…\n<end_of_turn>\n<start_of_turn>model\n`
 * System messages are prepended to the first user turn — Gemma doesn't have a
 * dedicated system role.
 */
function formatGemma(messages: ChatMessage[]): FormattedPrompt {
  const parts: string[] = [];
  const systemPrefix = messages
    .filter((m) => m.role === "system")
    .map((m) => m.content.trim())
    .join("\n\n");

  let firstUser = true;
  for (const m of messages) {
    if (m.role === "system") continue;
    if (m.role === "user") {
      const body =
        firstUser && systemPrefix
          ? `${systemPrefix}\n\n${m.content.trim()}`
          : m.content.trim();
      parts.push(`<start_of_turn>user\n${body}<end_of_turn>`);
      firstUser = false;
    } else if (m.role === "assistant") {
      parts.push(`<start_of_turn>model\n${m.content.trim()}<end_of_turn>`);
    }
  }
  parts.push("<start_of_turn>model\n");
  return { prompt: parts.join("\n"), stop: ["<end_of_turn>", "<start_of_turn>"] };
}

function formatChatML(
  messages: ChatMessage[],
  { imStart, imEnd }: { imStart: string; imEnd: string },
): FormattedPrompt {
  const parts: string[] = [];
  for (const m of messages) {
    parts.push(`${imStart}${m.role}\n${m.content.trim()}${imEnd}`);
  }
  parts.push(`${imStart}assistant\n`);
  return { prompt: parts.join("\n"), stop: [imEnd] };
}

function formatLlama3(messages: ChatMessage[]): FormattedPrompt {
  const parts: string[] = ["<|begin_of_text|>"];
  for (const m of messages) {
    parts.push(
      `<|start_header_id|>${m.role}<|end_header_id|>\n\n${m.content.trim()}<|eot_id|>`,
    );
  }
  parts.push("<|start_header_id|>assistant<|end_header_id|>\n\n");
  return { prompt: parts.join(""), stop: ["<|eot_id|>"] };
}
