/**
 * PROVIDER_CONFIGS — TS port of
 * C:\evolvingagents\skillos\agent_runtime.py lines 68-108.
 *
 * On mobile the OpenAI Python SDK is replaced by plain `fetch`. We target each
 * provider's OpenAI-compatible `/chat/completions` endpoint (OpenRouter,
 * Google's OpenAI-compat Gemini endpoint, Ollama's OpenAI compat API).
 *
 * `lanOnly` providers require cleartext access to an RFC-1918 host (typically
 * a laptop running `ollama serve`). Browsers block mixed content, so these
 * only work from the Capacitor-packaged app — the UI greys them out in the
 * pure-PWA case (M7).
 */

export type CloudProviderId = "openrouter-qwen" | "gemini" | "ollama" | "openrouter-gemma";
export type LocalProviderId = "wllama-local" | "litert-local" | "chrome-prompt-api";
export type ProviderId = CloudProviderId | LocalProviderId;

export interface ProviderConfig {
  id: ProviderId;
  label: string;
  defaultBaseUrl: string;
  defaultModel: string;
  defaultHeaders: Record<string, string>;
  defaultApiKey: string; // used when no key is configured (e.g. "ollama" for local)
  requiresKey: boolean;
  /** Requires cleartext LAN access — Capacitor native only. */
  lanOnly: boolean;
  /** Runs entirely on-device; pairs with a model chosen from `model_catalog.ts`. */
  localOnly: boolean;
  /** Native-only (requires a Capacitor plugin that isn't shimmed in pure-PWA). */
  nativeOnly?: boolean;
}

export function isLocalProvider(id: ProviderId): id is LocalProviderId {
  return (
    id === "wllama-local" || id === "litert-local" || id === "chrome-prompt-api"
  );
}

export const PROVIDER_CONFIGS: Record<ProviderId, ProviderConfig> = {
  "openrouter-qwen": {
    id: "openrouter-qwen",
    label: "OpenRouter · Qwen",
    defaultBaseUrl: "https://openrouter.ai/api/v1",
    defaultModel: "qwen/qwen3.6-plus:free",
    defaultHeaders: {
      "HTTP-Referer": "https://skillos.dev",
      "X-Title": "SkillOS",
    },
    defaultApiKey: "",
    requiresKey: true,
    lanOnly: false,
    localOnly: false,
  },
  gemini: {
    id: "gemini",
    label: "Google · Gemini",
    defaultBaseUrl: "https://generativelanguage.googleapis.com/v1beta/openai/",
    defaultModel: "gemini-2.5-flash",
    defaultHeaders: {},
    defaultApiKey: "",
    requiresKey: true,
    lanOnly: false,
    localOnly: false,
  },
  ollama: {
    id: "ollama",
    label: "Ollama (LAN)",
    defaultBaseUrl: "http://localhost:11434/v1",
    defaultModel: "gemma2:2b",
    defaultHeaders: { "Bypass-Tunnel-Reminder": "true" },
    defaultApiKey: "ollama",
    requiresKey: false,
    lanOnly: true,
    localOnly: false,
  },
  "openrouter-gemma": {
    id: "openrouter-gemma",
    label: "OpenRouter · Gemma",
    defaultBaseUrl: "https://openrouter.ai/api/v1",
    defaultModel: "google/gemma-4-26b-a4b-it",
    defaultHeaders: {
      "HTTP-Referer": "https://skillos.dev",
      "X-Title": "SkillOS",
    },
    defaultApiKey: "",
    requiresKey: true,
    lanOnly: false,
    localOnly: false,
  },
  // ── Local (on-device) providers — M9/M10 ─────────────────────────────
  "wllama-local": {
    id: "wllama-local",
    label: "On-device · wllama (WASM)",
    defaultBaseUrl: "",
    defaultModel: "qwen2.5-1.5b-instruct-q4_k_m",
    defaultHeaders: {},
    defaultApiKey: "",
    requiresKey: false,
    lanOnly: false,
    localOnly: true,
  },
  "litert-local": {
    id: "litert-local",
    label: "On-device · LiteRT (Android)",
    defaultBaseUrl: "",
    defaultModel: "gemma-2-2b-it-litertlm",
    defaultHeaders: {},
    defaultApiKey: "",
    requiresKey: false,
    lanOnly: false,
    localOnly: true,
    nativeOnly: true,
  },
  "chrome-prompt-api": {
    id: "chrome-prompt-api",
    label: "On-device · Chrome Prompt API",
    defaultBaseUrl: "",
    defaultModel: "",
    defaultHeaders: {},
    defaultApiKey: "",
    requiresKey: false,
    lanOnly: false,
    localOnly: true,
  },
};

export interface ResolvedProvider {
  id: ProviderId;
  baseUrl: string;
  model: string;
  apiKey: string;
  headers: Record<string, string>;
}

export interface ProviderOverrides {
  baseUrl?: string;
  model?: string;
  apiKey?: string;
  extraHeaders?: Record<string, string>;
}

export function resolveProvider(id: ProviderId, overrides: ProviderOverrides = {}): ResolvedProvider {
  const cfg = PROVIDER_CONFIGS[id];
  if (!cfg) throw new Error(`unknown provider: ${id}`);
  const baseUrl = (overrides.baseUrl ?? cfg.defaultBaseUrl).replace(/\/+$/, "");
  return {
    id,
    baseUrl,
    model: overrides.model ?? cfg.defaultModel,
    apiKey: overrides.apiKey ?? cfg.defaultApiKey,
    headers: { ...cfg.defaultHeaders, ...(overrides.extraHeaders ?? {}) },
  };
}

/** Pure-PWA (non-Capacitor) browsers block mixed content — LAN-only providers fail. */
export function isProviderAvailable(id: ProviderId, isNativeApp: boolean): boolean {
  const cfg = PROVIDER_CONFIGS[id];
  if (!cfg) return false;
  if (cfg.lanOnly && !isNativeApp) return false;
  if (cfg.nativeOnly && !isNativeApp) return false;
  return true;
}
