/**
 * LocalLLMClient — on-device `LLMProvider` implementation.
 *
 * Wraps a pluggable `LocalLLMBackend` (wllama today, LiteRT in M10, Chrome
 * Prompt API later) and presents the same `chat()` surface as the cloud
 * `LLMClient`. Any place that holds an `LLMProvider` reference — `runGoal`,
 * `CartridgeRunner`, `skillHostBridge`'s LLM proxy — works unchanged.
 */

import type { ChatMessage, ChatOptions, ChatResult } from "../client";
import type { LLMProvider } from "../provider";
import { getModelBlob } from "../../storage/db";
import type { LocalLLMBackend } from "./backend";
import { LiteRTBackend } from "./litert_backend";
import { getModelEntry, type ModelCatalogEntry } from "./model_catalog";
import { WllamaBackend } from "./wllama_backend";

export interface LocalLLMClientOptions {
  modelId: string;
  backend?: LocalLLMBackend;
}

/**
 * Pick a backend for the given model entry. Defaults to wllama — M10 replaces
 * this with a capability-aware picker that prefers LiteRT on Android native.
 */
export function pickBackendForModel(entry: ModelCatalogEntry): LocalLLMBackend {
  switch (entry.backend) {
    case "wllama":
      return new WllamaBackend();
    case "litert":
      return new LiteRTBackend();
    case "chrome-prompt-api":
      throw new Error(
        "chrome-prompt-api backend is not yet available in this build",
      );
  }
}

export class LocalLLMClient implements LLMProvider {
  private readonly entry: ModelCatalogEntry;
  private readonly backend: LocalLLMBackend;
  private initPromise: Promise<void> | null = null;

  constructor(opts: LocalLLMClientOptions) {
    const entry = getModelEntry(opts.modelId);
    if (!entry) throw new Error(`unknown model id: ${opts.modelId}`);
    this.entry = entry;
    this.backend = opts.backend ?? pickBackendForModel(entry);
  }

  private async ensureLoaded(signal?: AbortSignal): Promise<void> {
    if (this.initPromise) return this.initPromise;
    this.initPromise = (async () => {
      const rec = await getModelBlob(this.entry.id);
      if (!rec) {
        throw new Error(
          `model "${this.entry.id}" not installed — open the Model Manager and download it first`,
        );
      }
      await this.backend.load({
        entry: this.entry,
        modelBlob: rec.blob,
        nativePath: rec.native_path,
        signal,
      });
    })();
    return this.initPromise;
  }

  async chat(messages: ChatMessage[], opts: ChatOptions = {}): Promise<ChatResult> {
    await this.ensureLoaded(opts.signal);
    const result = await this.backend.generate({
      messages,
      template: this.entry.template,
      maxTokens: opts.maxTokens,
      temperature: opts.temperature,
      onToken: opts.onChunk,
      signal: opts.signal,
    });
    return {
      content: result.text,
      finishReason: result.finishReason,
    };
  }

  async testConnection(): Promise<{ ok: boolean; message: string }> {
    try {
      await this.ensureLoaded();
      return { ok: true, message: `loaded ${this.entry.name}` };
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return { ok: false, message: msg };
    }
  }

  /** Release worker / native resources. */
  async dispose(): Promise<void> {
    if (!this.initPromise) return;
    try {
      await this.initPromise;
    } catch {
      /* init may have failed */
    }
    await this.backend.unload();
    this.initPromise = null;
  }
}
