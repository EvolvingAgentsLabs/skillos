/**
 * GoalRouter — maps a free-text user goal to an execution plan.
 *
 * This is the piece that makes the mobile app "autonomous": rather than
 * forcing the user to pick a cartridge, the router inspects the library of
 * installed cartridges + skills, decides which one fits the goal, and
 * returns either:
 *
 *   - a **cartridge** decision (run this flow), or
 *   - an **ad-hoc** skill-chain (use these Gallery skills directly, no
 *     cartridge flow), or
 *   - a **synthesize** decision (no fit — describe what's missing), or
 *   - a **none** fallback (router could not classify; UI should ask).
 *
 * The router uses the installed LLM provider (if one is configured). On no
 * provider / LLM failure, it falls back to a keyword-overlap heuristic so
 * the user is never completely stuck.
 */

import type { LLMProvider } from "../llm/provider";
import type { CartridgeManifest } from "../cartridge/types";
import {
  deriveCapabilities,
  type SkillDefinition,
} from "../skills/skill_loader";

export interface RouterCartridgeDecision {
  mode: "cartridge";
  cartridge: string;
  flow?: string;
  reason: string;
  confidence: number;
}

export interface RouterAdHocDecision {
  mode: "ad-hoc";
  cartridge: string;
  skills: string[];
  reason: string;
  confidence: number;
}

export interface RouterSynthesizeDecision {
  mode: "synthesize";
  /** What the user seems to want that nothing currently covers. */
  description: string;
  /** Best-effort suggested skill name (slug-like). */
  suggestedName: string;
  /** Nearest existing skill if any — used as a seed for synthesis. */
  nearestSkill?: string;
  reason: string;
}

export interface RouterNoneDecision {
  mode: "none";
  reason: string;
}

export type RouterDecision =
  | RouterCartridgeDecision
  | RouterAdHocDecision
  | RouterSynthesizeDecision
  | RouterNoneDecision;

export interface RouterCatalog {
  cartridges: CartridgeManifest[];
  skills: Array<{ cartridge: string; skill: SkillDefinition }>;
}

export interface RouterOptions {
  /** If false, skips the LLM round-trip and uses only heuristic matching. */
  useLlm?: boolean;
  /** Max cartridges / skills to include in the prompt catalog. */
  maxCatalogEntries?: number;
}

// ────────────────────────────────────────────────────────────────────────
// Public API
// ────────────────────────────────────────────────────────────────────────

export async function routeGoal(
  goal: string,
  catalog: RouterCatalog,
  llm: LLMProvider | null,
  opts: RouterOptions = {},
): Promise<RouterDecision> {
  const trimmed = goal.trim();
  if (!trimmed) {
    return { mode: "none", reason: "goal is empty" };
  }

  // 1) Cheap heuristic first — catches exact cartridge-name matches, known
  //    entry intents, single-skill hits. If confident, skip the LLM.
  const heuristic = heuristicRoute(trimmed, catalog);
  if (heuristic && heuristic.confidence >= 0.8) return heuristic;

  // 2) LLM routing when available.
  if (llm && opts.useLlm !== false) {
    try {
      const llmDecision = await llmRoute(trimmed, catalog, llm, opts);
      if (llmDecision) return llmDecision;
    } catch {
      // Fall through to the heuristic decision.
    }
  }

  // 3) Heuristic best-effort fallback, or a "synthesize" hint when nothing matched.
  if (heuristic) return heuristic;
  return synthesizeDecisionFrom(trimmed, catalog);
}

// ────────────────────────────────────────────────────────────────────────
// Heuristic router
// ────────────────────────────────────────────────────────────────────────

type RouterConfidentDecision = RouterCartridgeDecision | RouterAdHocDecision;

function heuristicRoute(goal: string, catalog: RouterCatalog): RouterConfidentDecision | null {
  const tokens = tokenize(goal);
  if (tokens.size === 0) return null;

  // Cartridge scores: overlap between goal tokens and (name + description +
  // tags + category + entry_intents).
  let bestCartridge: { m: CartridgeManifest; score: number } | null = null;
  for (const m of catalog.cartridges) {
    const hay = [
      m.name,
      m.description,
      m.category ?? "",
      ...(m.tags ?? []),
      ...m.entry_intents,
    ]
      .join(" ")
      .toLowerCase();
    const hayTokens = tokenize(hay);
    const overlap = countOverlap(tokens, hayTokens);
    if (overlap === 0) continue;
    const score = overlap / Math.max(3, tokens.size);
    if (!bestCartridge || score > bestCartridge.score) {
      bestCartridge = { m, score };
    }
  }

  // Skill scores: overlap with name + description + capabilities.
  let bestSkill: { cartridge: string; skill: SkillDefinition; score: number } | null = null;
  for (const entry of catalog.skills) {
    const caps = deriveCapabilities(entry.skill);
    const hay = [
      entry.skill.name,
      entry.skill.description,
      entry.skill.category ?? "",
      ...caps,
    ]
      .join(" ")
      .toLowerCase();
    const hayTokens = tokenize(hay);
    const overlap = countOverlap(tokens, hayTokens);
    if (overlap === 0) continue;
    const score = overlap / Math.max(2, tokens.size);
    if (!bestSkill || score > bestSkill.score) {
      bestSkill = { ...entry, score };
    }
  }

  // Prefer a strong skill match over a weak cartridge match, since skills are
  // more specific. When both are similar, prefer the cartridge (it carries a
  // validated flow).
  if (bestSkill && (!bestCartridge || bestSkill.score > bestCartridge.score + 0.1)) {
    return {
      mode: "ad-hoc",
      cartridge: bestSkill.cartridge,
      skills: [bestSkill.skill.name],
      reason: `Keyword match on skill "${bestSkill.skill.name}"`,
      confidence: Math.min(0.95, bestSkill.score),
    };
  }
  if (bestCartridge) {
    return {
      mode: "cartridge",
      cartridge: bestCartridge.m.name,
      flow: bestCartridge.m.default_flow || undefined,
      reason: `Keyword match on cartridge "${bestCartridge.m.name}"`,
      confidence: Math.min(0.95, bestCartridge.score),
    };
  }
  return null;
}

// ────────────────────────────────────────────────────────────────────────
// LLM router
// ────────────────────────────────────────────────────────────────────────

const SYSTEM_PROMPT = `You are SkillOS's goal router. The user states a goal; you decide how to run it using only the installed library.

Return a single JSON object. No prose, no markdown fences. Exactly one of these shapes:

{"mode":"cartridge","cartridge":"<name>","flow":"<flow-name-or-empty>","reason":"<one-line>"}
{"mode":"ad-hoc","cartridge":"<host-cartridge>","skills":["<skill1>","<skill2>"],"reason":"<one-line>"}
{"mode":"synthesize","description":"<what's missing, phrased as a new skill>","suggestedName":"<slug>","nearestSkill":"<existing-skill-or-empty>","reason":"<one-line>"}

Rules:
- Prefer a cartridge when the goal maps to an entire workflow (planning, research, multi-step).
- Prefer ad-hoc when one or two skills cover it end-to-end (hashing, formatting, calculation).
- Choose synthesize ONLY when no installed cartridge or skill fits. Describe the new skill concretely.
- Always pick a cartridge that exists in the provided list. Never invent names.`;

async function llmRoute(
  goal: string,
  catalog: RouterCatalog,
  llm: LLMProvider,
  opts: RouterOptions,
): Promise<RouterDecision | null> {
  const max = opts.maxCatalogEntries ?? 60;
  const cartridgeLines = catalog.cartridges
    .slice(0, max)
    .map(
      (m) =>
        `- ${m.name}${m.category ? ` [${m.category}]` : ""} — ${truncate(m.description, 120)}${
          m.entry_intents.length ? ` · intents: ${m.entry_intents.slice(0, 3).join(", ")}` : ""
        }`,
    );
  const skillLines = catalog.skills
    .slice(0, max)
    .map(
      ({ cartridge, skill }) =>
        `- ${skill.name} (in ${cartridge})${
          skill.category ? ` [${skill.category}]` : ""
        } — ${truncate(skill.description, 120)}`,
    );

  const user = `Goal: ${goal}

Cartridges:
${cartridgeLines.join("\n") || "(none)"}

Skills:
${skillLines.join("\n") || "(none)"}

Return one JSON object as specified. Do not wrap in code fences.`;

  const r = await llm.chat(
    [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: user },
    ],
    { stream: false, temperature: 0.1, maxTokens: 400 },
  );
  return parseLlmDecision(r.content, catalog);
}

function parseLlmDecision(raw: string, catalog: RouterCatalog): RouterDecision | null {
  const cleaned = stripFences(raw).trim();
  const start = cleaned.indexOf("{");
  const end = cleaned.lastIndexOf("}");
  if (start < 0 || end <= start) return null;
  let obj: Record<string, unknown>;
  try {
    obj = JSON.parse(cleaned.slice(start, end + 1));
  } catch {
    return null;
  }

  const mode = String(obj.mode ?? "");
  const reason = String(obj.reason ?? "").slice(0, 200);

  if (mode === "cartridge") {
    const name = String(obj.cartridge ?? "");
    const m = catalog.cartridges.find((c) => c.name === name);
    if (!m) return null;
    const flow =
      typeof obj.flow === "string" && obj.flow && m.flows[obj.flow] ? obj.flow : undefined;
    return {
      mode: "cartridge",
      cartridge: m.name,
      flow: flow ?? (m.default_flow || undefined),
      reason: reason || `LLM picked cartridge ${m.name}`,
      confidence: 0.85,
    };
  }
  if (mode === "ad-hoc") {
    const hostName = String(obj.cartridge ?? "");
    const skillNames = Array.isArray(obj.skills)
      ? obj.skills.filter((s): s is string => typeof s === "string")
      : [];
    const host = catalog.cartridges.find((c) => c.name === hostName);
    const validSkills = skillNames.filter((sn) =>
      catalog.skills.some((e) => e.skill.name === sn),
    );
    if (!host || validSkills.length === 0) return null;
    return {
      mode: "ad-hoc",
      cartridge: host.name,
      skills: validSkills,
      reason: reason || `LLM picked skills: ${validSkills.join(", ")}`,
      confidence: 0.85,
    };
  }
  if (mode === "synthesize") {
    return {
      mode: "synthesize",
      description: String(obj.description ?? "").slice(0, 400) || "(no description)",
      suggestedName: String(obj.suggestedName ?? "user-skill")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "")
        .slice(0, 60) || "user-skill",
      nearestSkill:
        typeof obj.nearestSkill === "string" && obj.nearestSkill
          ? obj.nearestSkill
          : undefined,
      reason: reason || "LLM judged nothing fits — synthesize a new skill",
    };
  }
  return null;
}

// ────────────────────────────────────────────────────────────────────────
// Fallback "synthesize" decision (no LLM, no match)
// ────────────────────────────────────────────────────────────────────────

function synthesizeDecisionFrom(goal: string, catalog: RouterCatalog): RouterDecision {
  const tokens = Array.from(tokenize(goal));
  const nearest = pickNearestSkill(tokens, catalog);
  const suggested = tokens.slice(0, 3).join("-").slice(0, 40) || "user-skill";
  return {
    mode: "synthesize",
    description: `Nothing in the library matched "${truncate(goal, 100)}". Create a skill that handles this.`,
    suggestedName: suggested,
    nearestSkill: nearest ?? undefined,
    reason: "No keyword match against installed cartridges or skills",
  };
}

function pickNearestSkill(
  tokens: string[],
  catalog: RouterCatalog,
): string | undefined {
  if (tokens.length === 0) return undefined;
  const tokenSet = new Set(tokens);
  let best: { name: string; score: number } | null = null;
  for (const { skill } of catalog.skills) {
    const caps = deriveCapabilities(skill);
    const overlap = caps.reduce((n, c) => (tokenSet.has(c) ? n + 1 : n), 0);
    if (overlap === 0) continue;
    if (!best || overlap > best.score) best = { name: skill.name, score: overlap };
  }
  return best?.name;
}

// ────────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────────

const STOP = new Set([
  "a", "an", "the", "and", "or", "of", "for", "to", "from", "with", "in",
  "on", "at", "by", "as", "is", "are", "be", "this", "that", "it",
  "my", "your", "me", "i", "we", "can", "could", "should", "would",
  "please", "do", "does", "need", "want",
]);

function tokenize(s: string): Set<string> {
  const toks = s
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((t) => t.length >= 3 && !STOP.has(t));
  return new Set(toks);
}

function countOverlap(a: Set<string>, b: Set<string>): number {
  let n = 0;
  for (const t of a) if (b.has(t)) n += 1;
  return n;
}

function truncate(s: string, n: number): string {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function stripFences(s: string): string {
  const m = /```(?:json)?\s*([\s\S]*?)```/.exec(s);
  return m ? m[1] : s;
}
