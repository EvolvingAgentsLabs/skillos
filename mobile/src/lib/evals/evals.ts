/**
 * Cartridge evals harness.
 *
 * Walks every cartridge that ships an `evals/cases.yaml`, runs each case
 * through the CartridgeRunner with the project's provider, and evaluates the
 * assertions in the YAML against the resulting blackboard snapshot.
 */

import yaml from "js-yaml";
import { CartridgeRegistry } from "../cartridge/registry";
import { CartridgeRunner } from "../cartridge/runner";
import type { BlackboardSnapshot } from "../cartridge/types";
import { LLMClient } from "../llm/client";
import { resolveProvider } from "../llm/providers";
import type { ProviderConfigStored } from "../state/provider_config";
import { getFileText, listFiles } from "../storage/db";

export interface Assertion {
  key: string;
  equals?: unknown;
  length?: number;
  min_length?: number;
  present?: boolean;
}

export interface EvalCase {
  id: string;
  goal: string;
  flow?: string;
  assertions: Assertion[];
}

export interface CartridgeEvalFile {
  cartridge: string;
  cases: EvalCase[];
}

export interface AssertionResult {
  assertion: Assertion;
  ok: boolean;
  actual?: unknown;
  message?: string;
}

export interface CaseResult {
  case_id: string;
  cartridge: string;
  ok: boolean;
  run_ok: boolean;
  assertions: AssertionResult[];
  error?: string;
  duration_seconds: number;
}

export async function discoverEvalFiles(): Promise<CartridgeEvalFile[]> {
  const all = await listFiles("cartridges/");
  const evalPaths = all.filter((p) => /^cartridges\/[^/]+\/evals\/cases\.ya?ml$/.test(p));
  const out: CartridgeEvalFile[] = [];
  for (const p of evalPaths) {
    const text = await getFileText(p);
    if (!text) continue;
    try {
      const raw = yaml.load(text) as { cases?: unknown[] };
      const cartridge = p.split("/")[1];
      const cases = Array.isArray(raw?.cases) ? (raw.cases as EvalCase[]) : [];
      out.push({ cartridge, cases });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.warn(`[evals] failed to parse ${p}: ${msg}`);
    }
  }
  return out;
}

export async function runEvalCase(
  registry: CartridgeRegistry,
  provider: ProviderConfigStored,
  cartridge: string,
  ec: EvalCase,
): Promise<CaseResult> {
  const startedAt = Date.now();
  const llm = new LLMClient(
    resolveProvider(provider.providerId, {
      baseUrl: provider.baseUrl,
      model: provider.model,
      apiKey: provider.apiKey,
    }),
  );
  const runner = new CartridgeRunner(registry, llm);

  let run_ok = false;
  let error: string | undefined;
  let snapshot: BlackboardSnapshot = {};
  try {
    const res = await runner.run(cartridge, ec.goal, { flow: ec.flow });
    run_ok = res.ok;
    snapshot = res.blackboard;
  } catch (err) {
    error = err instanceof Error ? err.message : String(err);
  }

  const results: AssertionResult[] = ec.assertions.map((a) => evalAssertion(a, snapshot));
  const ok = run_ok && results.every((r) => r.ok);
  return {
    case_id: ec.id,
    cartridge,
    ok,
    run_ok,
    assertions: results,
    error,
    duration_seconds: Math.round((Date.now() - startedAt) / 1000),
  };
}

function evalAssertion(a: Assertion, snap: BlackboardSnapshot): AssertionResult {
  const actual = lookupDottedPath(snap, a.key);
  if (a.present !== undefined) {
    const got = actual !== undefined;
    return {
      assertion: a,
      ok: got === a.present,
      actual,
      message: got === a.present ? "ok" : `expected present=${a.present}, got ${got}`,
    };
  }
  if (a.equals !== undefined) {
    const ok = deepEqual(actual, a.equals);
    return {
      assertion: a,
      ok,
      actual,
      message: ok ? "ok" : `expected ${JSON.stringify(a.equals)}, got ${JSON.stringify(actual)}`,
    };
  }
  if (a.length !== undefined) {
    const len = (actual as unknown[] | string | undefined)?.length;
    return {
      assertion: a,
      ok: len === a.length,
      actual: len,
      message: len === a.length ? "ok" : `expected length ${a.length}, got ${len}`,
    };
  }
  if (a.min_length !== undefined) {
    const len = (actual as unknown[] | string | undefined)?.length ?? 0;
    return {
      assertion: a,
      ok: len >= a.min_length,
      actual: len,
      message: len >= a.min_length ? "ok" : `expected length >= ${a.min_length}, got ${len}`,
    };
  }
  return { assertion: a, ok: true, actual, message: "unsupported predicate (skipped)" };
}

/**
 * Dotted-path lookup against a blackboard snapshot. Top-level keys address
 * the blackboard entry, then `.value.<rest>` descends into the stored JSON.
 * Arrays accept numeric indices.
 */
export function lookupDottedPath(snap: BlackboardSnapshot, path: string): unknown {
  const parts = path.split(".");
  if (parts.length === 0) return undefined;
  const top = snap[parts[0]];
  if (!top) return undefined;
  let cur: unknown = top.value;
  for (let i = 1; i < parts.length; i++) {
    if (cur === undefined || cur === null) return undefined;
    const p = parts[i];
    if (Array.isArray(cur) && /^\d+$/.test(p)) {
      cur = cur[Number(p)];
    } else if (typeof cur === "object") {
      cur = (cur as Record<string, unknown>)[p];
    } else {
      return undefined;
    }
  }
  return cur;
}

function deepEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (a === null || b === null) return a === b;
  if (typeof a !== typeof b) return false;
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) if (!deepEqual(a[i], b[i])) return false;
    return true;
  }
  if (typeof a === "object" && typeof b === "object") {
    const ak = Object.keys(a as object);
    const bk = Object.keys(b as object);
    if (ak.length !== bk.length) return false;
    for (const k of ak) {
      if (!deepEqual((a as Record<string, unknown>)[k], (b as Record<string, unknown>)[k])) {
        return false;
      }
    }
    return true;
  }
  return false;
}
