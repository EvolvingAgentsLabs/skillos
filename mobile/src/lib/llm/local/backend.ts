/**
 * LocalLLMBackend — abstraction over on-device inference runtimes.
 *
 * Implemented by `WllamaBackend` (M9) for WASM and `LiteRTBackend` (M10) for
 * Android native. A `LocalLLMClient` selects one via `pickBackend()` and
 * treats them interchangeably.
 */

import type { ChatMessage } from "../client";
import type { ChatTemplateFamily, LocalBackendId, ModelCatalogEntry } from "./model_catalog";

export interface BackendLoadOptions {
  entry: ModelCatalogEntry;
  modelBlob: ArrayBuffer;
  /** For LiteRT: the backend may need a native file path rather than a buffer. */
  nativePath?: string;
  signal?: AbortSignal;
}

export interface BackendGenerateOptions {
  messages: ChatMessage[];
  template: ChatTemplateFamily;
  maxTokens?: number;
  temperature?: number;
  stop?: string[];
  onToken?: (tok: string) => void;
  signal?: AbortSignal;
}

export interface BackendGenerateResult {
  text: string;
  /** `"stop"`, `"length"`, `"abort"`, `"error"`, or backend-specific. */
  finishReason: string;
}

export interface LocalLLMBackend {
  readonly id: LocalBackendId;
  readonly ready: Promise<void>;
  load(opts: BackendLoadOptions): Promise<void>;
  generate(opts: BackendGenerateOptions): Promise<BackendGenerateResult>;
  unload(): Promise<void>;
}
