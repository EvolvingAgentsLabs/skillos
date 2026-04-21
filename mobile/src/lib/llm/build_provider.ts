/**
 * buildProvider — factory that turns a `ProviderConfigStored` into a concrete
 * `LLMProvider`. Branches on `providerId` to pick between the cloud HTTP
 * client and `LocalLLMClient`.
 *
 * Used by `runProject()` (and by the LLM proxy installed on the skill iframe)
 * so every caller interacts with `LLMProvider` only and no one hand-rolls
 * provider selection.
 */

import { LLMClient } from "./client";
import { LocalLLMClient } from "./local/local_client";
import type { LLMProvider } from "./provider";
import { isLocalProvider, resolveProvider, type ProviderId } from "./providers";

/**
 * Structural shape for any caller that stores provider settings. Matches
 * `ProviderConfigStored` in `state/provider_config.ts` without creating a
 * circular dependency through the `state/` module.
 */
export interface BuildProviderConfig {
  providerId: ProviderId;
  baseUrl?: string;
  model?: string;
  apiKey?: string;
}

export async function buildProvider(cfg: BuildProviderConfig): Promise<LLMProvider> {
  if (isLocalProvider(cfg.providerId)) {
    // For local providers, `cfg.model` is the catalog `modelId` (required).
    const modelId = cfg.model?.trim() || defaultModelForLocal(cfg.providerId);
    if (!modelId) {
      throw new Error(
        `local provider ${cfg.providerId} requires a model id — open Model Manager`,
      );
    }
    return new LocalLLMClient({ modelId });
  }
  // Cloud path: behave exactly like v0.
  const provider = resolveProvider(cfg.providerId, {
    baseUrl: cfg.baseUrl,
    model: cfg.model,
    apiKey: cfg.apiKey,
  });
  return new LLMClient(provider);
}

function defaultModelForLocal(providerId: string): string {
  switch (providerId) {
    case "wllama-local":
      return "qwen2.5-1.5b-instruct-q4_k_m";
    case "litert-local":
      return "gemma-2-2b-it-litertlm";
    default:
      return "";
  }
}
