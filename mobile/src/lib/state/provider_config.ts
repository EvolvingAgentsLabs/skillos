/**
 * Per-project provider configuration — stored in IndexedDB `secrets` under
 * the key `provider:<projectId>`. v0 stored a flat `{providerId, …}` record;
 * M11 wraps that as `primary` and adds optional `fallback` for smart routing.
 *
 * Load is backward-compatible: a legacy record is auto-migrated by wrapping
 * it under `primary`.
 */

import { getDB } from "../storage/db";
import { PROVIDER_CONFIGS, type ProviderId } from "../llm/providers";

export interface ProviderConfigStored {
  providerId: ProviderId;
  baseUrl?: string;
  model?: string;
  apiKey?: string;
}

/**
 * M11: per-project routing config. `primary` is always used; `fallback` is
 * consulted for `tier: capable` agents and for tier-escalation on validation
 * failure. Callers that only care about the primary (e.g. evals harness) can
 * extract `cfg.primary` directly.
 */
export interface ProjectRouting {
  primary: ProviderConfigStored;
  fallback?: ProviderConfigStored;
}

const KEY_PREFIX = "provider:";

function isLegacyShape(x: unknown): x is ProviderConfigStored {
  return !!x && typeof x === "object" && "providerId" in (x as Record<string, unknown>);
}

function isRoutingShape(x: unknown): x is ProjectRouting {
  return (
    !!x &&
    typeof x === "object" &&
    "primary" in (x as Record<string, unknown>) &&
    isLegacyShape((x as Record<string, unknown>).primary)
  );
}

export async function loadProjectRouting(
  projectId: string,
): Promise<ProjectRouting | undefined> {
  const db = await getDB();
  const rec = await db.get("secrets", `${KEY_PREFIX}${projectId}`);
  if (!rec) return undefined;
  try {
    const parsed = JSON.parse(rec.value);
    if (isRoutingShape(parsed)) {
      if (!(parsed.primary.providerId in PROVIDER_CONFIGS)) return undefined;
      return parsed;
    }
    if (isLegacyShape(parsed)) {
      if (!(parsed.providerId in PROVIDER_CONFIGS)) return undefined;
      return { primary: parsed };
    }
    return undefined;
  } catch {
    return undefined;
  }
}

/** Back-compat shim for callers that only consume the primary. */
export async function loadProviderConfig(
  projectId: string,
): Promise<ProviderConfigStored | undefined> {
  const routing = await loadProjectRouting(projectId);
  return routing?.primary;
}

export async function saveProjectRouting(
  projectId: string,
  routing: ProjectRouting,
): Promise<void> {
  const db = await getDB();
  await db.put("secrets", {
    key: `${KEY_PREFIX}${projectId}`,
    value: JSON.stringify(routing),
    updated_at: new Date().toISOString(),
  });
}

/** Back-compat — treats `cfg` as `{primary: cfg}`. */
export async function saveProviderConfig(
  projectId: string,
  cfg: ProviderConfigStored,
): Promise<void> {
  const existing = await loadProjectRouting(projectId);
  await saveProjectRouting(projectId, { primary: cfg, fallback: existing?.fallback });
}

export async function saveFallbackConfig(
  projectId: string,
  fallback: ProviderConfigStored | undefined,
): Promise<void> {
  const existing = await loadProjectRouting(projectId);
  if (!existing) return;
  await saveProjectRouting(projectId, { primary: existing.primary, fallback });
}

export function isProviderNative(): boolean {
  const w = globalThis as unknown as { Capacitor?: { isNativePlatform?: () => boolean } };
  return Boolean(w.Capacitor?.isNativePlatform?.());
}
