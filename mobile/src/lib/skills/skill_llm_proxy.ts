/**
 * Adapter that turns a stored `ProviderConfigStored` into an `LLMProxy` suitable
 * for `skillHostBridge.setLLMProxy`. Mirrors the inline adapter in
 * `CartridgeRunner.makeLLMProxy` so that runs triggered from the Skills tab
 * behave identically to skills invoked through a cartridge flow.
 *
 * Also exposes a "global" (non-project) provider config slot — SkillCard reads
 * and writes `_skills` via the same per-project provider_config helpers, which
 * avoids introducing a second provider-store surface.
 */

import { buildProvider } from "../llm/build_provider";
import { isLocalProvider } from "../llm/providers";
import {
  loadProviderConfig,
  saveProviderConfig,
  type ProviderConfigStored,
} from "../state/provider_config";
import { skillHostBridge } from "./skill_host_bridge";
import type { LLMProxy } from "./skill_host_bridge";

const GLOBAL_SKILLS_KEY = "_skills";

export async function loadSkillsProviderConfig(): Promise<ProviderConfigStored | undefined> {
  return loadProviderConfig(GLOBAL_SKILLS_KEY);
}

export async function saveSkillsProviderConfig(cfg: ProviderConfigStored): Promise<void> {
  await saveProviderConfig(GLOBAL_SKILLS_KEY, cfg);
}

export const SKILLS_PROVIDER_PROJECT_ID = GLOBAL_SKILLS_KEY;

/**
 * Build an `LLMProxy` from a stored provider config. Throws if the provider
 * cannot be constructed (e.g. local model not downloaded). Callers should
 * surface the error to the user — skills that don't call __skillos.llm will
 * still run successfully if the proxy is never installed.
 */
export async function buildSkillLLMProxy(cfg: ProviderConfigStored): Promise<LLMProxy> {
  const llm = await buildProvider(cfg);
  return {
    async chat(prompt, options) {
      const messages = options?.system
        ? [
            { role: "system" as const, content: options.system },
            { role: "user" as const, content: prompt },
          ]
        : [{ role: "user" as const, content: prompt }];
      const r = await llm.chat(messages, {
        stream: false,
        temperature: options?.temperature,
        maxTokens: options?.max_tokens,
      });
      return r.content;
    },
    async chatJSON(prompt, schema, options) {
      const suffix = schema
        ? `\n\nRespond with valid JSON matching this schema:\n${JSON.stringify(schema, null, 2)}`
        : "\n\nRespond with valid JSON only. No markdown, no explanation.";
      const messages = options?.system
        ? [
            { role: "system" as const, content: options.system },
            { role: "user" as const, content: prompt + suffix },
          ]
        : [{ role: "user" as const, content: prompt + suffix }];
      const r = await llm.chat(messages, {
        stream: false,
        temperature: 0.1,
        maxTokens: options?.max_tokens,
      });
      const m = /```(?:json)?\s*([\s\S]*?)```/.exec(r.content);
      const cleaned = (m ? m[1] : r.content).trim();
      return JSON.parse(cleaned);
    },
  };
}

function providerLabel(cfg: ProviderConfigStored): string {
  return cfg.model ? `${cfg.providerId} · ${cfg.model}` : cfg.providerId;
}

/**
 * Best-effort: load the global skills provider config and install it on the
 * bridge. Returns true on success. On any failure (no config, build error)
 * clears the proxy and returns false — the skill can still run its pure-JS
 * logic; any __skillos.llm call will surface an error inside the iframe.
 *
 * Also sets a human-readable provider label on the bridge so the provenance
 * badge in SkillCard can show "cloud · openrouter-qwen · qwen-2.5-72b" vs
 * "on-device · gemma-2-2b" without re-deriving the label from config shape.
 */
export async function ensureSkillsProxyInstalled(): Promise<boolean> {
  try {
    const cfg = await loadSkillsProviderConfig();
    if (!cfg) {
      skillHostBridge.setLLMProxy(null);
      skillHostBridge.setProviderLabel(null, null);
      return false;
    }
    const proxy = await buildSkillLLMProxy(cfg);
    skillHostBridge.setLLMProxy(proxy);
    skillHostBridge.setProviderLabel(
      providerLabel(cfg),
      isLocalProvider(cfg.providerId) ? "on-device" : "cloud",
    );
    return true;
  } catch {
    skillHostBridge.setLLMProxy(null);
    skillHostBridge.setProviderLabel(null, null);
    return false;
  }
}
