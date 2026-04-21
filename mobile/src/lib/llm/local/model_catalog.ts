/**
 * Curated catalog of on-device models.
 *
 * Each entry pins a quantized model weight hosted on Hugging Face and the
 * backend that consumes it. The chat template is captured per entry so the
 * backend's `chat()` wrapper can format OpenAI-style messages correctly —
 * wrong template ⇒ garbage output.
 */

export type LocalBackendId = "wllama" | "litert" | "chrome-prompt-api";

export type ChatTemplateFamily =
  | "gemma-v2"
  | "gemma-v3"
  | "qwen2"
  | "llama3"
  | "chatml"
  | "tinyllama";

export interface ModelCatalogEntry {
  /** Stable id used as the IndexedDB key. Must be URL-safe. */
  id: string;
  /** Display name in the Model Manager UI. */
  name: string;
  /** Short one-liner shown under the name. */
  description: string;
  /** HTTPS URL to the model weights. Must serve CORS / range requests. */
  url: string;
  /** Backend that can consume this file format. */
  backend: LocalBackendId;
  /** Expected file size in bytes (used for progress and quota preflight). */
  sizeBytes: number;
  /** Optional integrity check. SHA-256 hex. */
  sha256?: string;
  /** Chat template family — picks the right prompt wrapping in the backend. */
  template: ChatTemplateFamily;
  /** Context window in tokens. Fed into ProviderCapabilities.contextWindow. */
  contextTokens: number;
  /** Capability tier used by the M11 smart router. */
  tier: "cheap" | "capable";
  /** License string for the About / catalog UI. */
  license: string;
}

/**
 * Keep the catalog conservative — three entries covering fast-and-tiny,
 * balanced, and quality-at-cost. More can be authored as user-curated JSON
 * in a later milestone without changing this schema.
 */
export const MODEL_CATALOG: ModelCatalogEntry[] = [
  {
    id: "qwen2.5-1.5b-instruct-q4_k_m",
    name: "Qwen 2.5 · 1.5B · Q4_K_M",
    description: "Tiny, multilingual. Fits in ~1 GB. Best for phones with < 4 GB RAM.",
    url: "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
    backend: "wllama",
    sizeBytes: 986_000_000,
    template: "qwen2",
    contextTokens: 32_768,
    tier: "cheap",
    license: "Apache-2.0",
  },
  {
    id: "gemma-2-2b-it-q4_k_m",
    name: "Gemma 2 · 2B · Q4_K_M",
    description: "Google's balanced small model. ~1.3 GB. Strong tool-use on simple tasks.",
    url: "https://huggingface.co/bartowski/gemma-2-2b-it-GGUF/resolve/main/gemma-2-2b-it-Q4_K_M.gguf",
    backend: "wllama",
    sizeBytes: 1_630_000_000,
    template: "gemma-v2",
    contextTokens: 8_192,
    tier: "cheap",
    license: "Gemma Terms of Use",
  },
  {
    id: "gemma-2-2b-it-litertlm",
    name: "Gemma 2 · 2B · LiteRT (Android only)",
    description: "Native-accelerated LiteRT build. 5–15× faster on Android than WASM.",
    url: "https://huggingface.co/litert-community/gemma-2-2b-it/resolve/main/gemma-2-2b-it.litertlm",
    backend: "litert",
    sizeBytes: 1_640_000_000,
    template: "gemma-v2",
    contextTokens: 8_192,
    tier: "cheap",
    license: "Gemma Terms of Use",
  },
];

export function getModelEntry(id: string): ModelCatalogEntry | undefined {
  return MODEL_CATALOG.find((m) => m.id === id);
}

export function catalogFor(backend: LocalBackendId): ModelCatalogEntry[] {
  return MODEL_CATALOG.filter((m) => m.backend === backend);
}
