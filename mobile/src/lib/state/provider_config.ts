/**
 * Per-project provider configuration — stored in IndexedDB `secrets` under
 * the key `provider:<projectId>`. Includes provider id + optional base URL
 * override + model + API key.
 */

import { getDB } from "../storage/db";
import { PROVIDER_CONFIGS, type ProviderId } from "../llm/providers";

export interface ProviderConfigStored {
  providerId: ProviderId;
  baseUrl?: string;
  model?: string;
  apiKey?: string;
}

const KEY_PREFIX = "provider:";

export async function loadProviderConfig(
  projectId: string,
): Promise<ProviderConfigStored | undefined> {
  const db = await getDB();
  const rec = await db.get("secrets", `${KEY_PREFIX}${projectId}`);
  if (!rec) return undefined;
  try {
    const parsed = JSON.parse(rec.value) as ProviderConfigStored;
    if (!parsed.providerId || !(parsed.providerId in PROVIDER_CONFIGS)) return undefined;
    return parsed;
  } catch {
    return undefined;
  }
}

export async function saveProviderConfig(
  projectId: string,
  cfg: ProviderConfigStored,
): Promise<void> {
  const db = await getDB();
  await db.put("secrets", {
    key: `${KEY_PREFIX}${projectId}`,
    value: JSON.stringify(cfg),
    updated_at: new Date().toISOString(),
  });
}

export function isProviderNative(): boolean {
  const w = globalThis as unknown as { Capacitor?: { isNativePlatform?: () => boolean } };
  return Boolean(w.Capacitor?.isNativePlatform?.());
}
