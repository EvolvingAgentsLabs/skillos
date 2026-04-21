/**
 * Smart router — per-agent provider selection for `CartridgeRunner`.
 *
 * Given:
 *   - the agent being run (its tier, its cartridge's preferred_tier),
 *   - the project's provider config ({primary, fallback?}),
 *   - the current attempt context ({attempt, previousFailure}),
 *
 * returns which `LLMProvider` to use *this turn*.
 *
 * Rules (in order — first match wins):
 *   1. If the caller asks for `capable` and a fallback exists, use fallback.
 *   2. If the manifest says `preferred_tier: cloud` and a cloud fallback
 *      exists, use fallback even for `cheap` agents.
 *   3. If this is a retry-after-validation-failure and we have a fallback
 *      that we haven't tried yet, escalate to it.
 *   4. Otherwise use primary.
 *
 * Escalation is capped at one switch per step so a persistently-broken run
 * can't bounce between primary and fallback forever.
 */

import type { LLMProvider } from "../llm/provider";
import type { AgentSpec, CartridgeManifest } from "./types";

export interface ProviderBundle {
  primary: LLMProvider;
  fallback?: LLMProvider;
}

export interface RouteContext {
  /** 1-indexed turn count for the current step. */
  attempt: number;
  /** Last failure reason that triggered the retry, if any. */
  previousFailure?: "validation" | "error";
  /** Which provider we used on the prior attempt (for escalation). */
  previousTarget?: "primary" | "fallback";
}

export interface RouteDecision {
  provider: LLMProvider;
  target: "primary" | "fallback";
  reason: string;
}

export function resolveProvider(
  agent: AgentSpec,
  manifest: CartridgeManifest,
  providers: ProviderBundle,
  ctx: RouteContext = { attempt: 1 },
): RouteDecision {
  const hasFallback = providers.fallback !== undefined;

  // Rule 1: capable agents prefer fallback when available.
  if (agent.tier === "capable" && hasFallback) {
    return {
      provider: providers.fallback!,
      target: "fallback",
      reason: `agent tier=capable`,
    };
  }

  // Rule 2: cartridge-level cloud preference wins for every agent.
  if (manifest.preferred_tier === "cloud" && hasFallback) {
    return {
      provider: providers.fallback!,
      target: "fallback",
      reason: "cartridge preferred_tier=cloud",
    };
  }

  // Rule 3: escalate on validation failure once.
  if (
    ctx.previousFailure === "validation" &&
    ctx.previousTarget !== "fallback" &&
    hasFallback
  ) {
    return {
      provider: providers.fallback!,
      target: "fallback",
      reason: "tier-escalated after validation failure",
    };
  }

  return {
    provider: providers.primary,
    target: "primary",
    reason: "default",
  };
}

export function sameProvider(a: RouteDecision, b: RouteDecision): boolean {
  return a.target === b.target;
}
