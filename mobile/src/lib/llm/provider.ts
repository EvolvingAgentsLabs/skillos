/**
 * LLMProvider — unifying interface for cloud and on-device language models.
 *
 * The cloud `LLMClient` (src/lib/llm/client.ts) already has this shape; v1
 * extracts the contract here so `LocalLLMClient` (M9) can implement it
 * identically. `runGoal` and `CartridgeRunner` consume providers through this
 * interface so swapping backends requires no orchestration changes.
 */

import type { ChatMessage, ChatOptions, ChatResult } from "./client";

export interface LLMProvider {
  /** Multi-turn chat completion. Streams when `opts.stream !== false`. */
  chat(messages: ChatMessage[], opts?: ChatOptions): Promise<ChatResult>;
  /** Lightweight health check; returns `{ok: true}` on 2xx / successful init. */
  testConnection(): Promise<{ ok: boolean; message: string }>;
}

/**
 * Static description of what a provider can do. Used by M11's smart router to
 * pick a provider per-agent (e.g. skip local models for a `tier: capable`
 * agent if their context window is too small).
 */
export interface ProviderCapabilities {
  /** Human-readable label for the Provider Settings UI. */
  label: string;
  /** Does the underlying endpoint / runtime support SSE-style streaming? */
  supportsStreaming: boolean;
  /** Does the provider honor an OpenAI-style `response_format: json_object`? */
  supportsJsonMode: boolean;
  /** Max tokens the model can attend to (prompt + completion). */
  contextWindow: number;
  /** Very rough throughput used by the router to estimate budget. */
  avgTokensPerSec: number;
  /** Tier bucket for routing decisions. Cheap = small/fast; capable = larger/slower. */
  tier: "cheap" | "capable";
  /**
   * `native-only`: requires Capacitor native wrapper (e.g. mixed content over
   *    LAN for Ollama, or Kotlin-only plugins).
   * `local`: runs entirely on-device, no network.
   * `cloud`: remote HTTP endpoint.
   */
  surface: "cloud" | "local" | "native-only";
}

export type { ChatMessage, ChatOptions, ChatResult } from "./client";
