/**
 * SkillResult — TS port of
 * C:\evolvingagents\skillos\experiments\gemma4-skills\js_executor.py lines 30-64.
 *
 * Normalized output shape for Gallery skills. Matches the schema at
 * cartridges/demo/schemas/skill_result.schema.json so the iframe's response
 * can be validated with the same ajv instance used by the cartridge blackboard.
 */

export interface SkillWebview {
  url: string;
  iframe?: boolean;
  aspectRatio?: number;
}

export interface SkillImage {
  base64: string;
  mimeType?: string;
}

/**
 * Provenance — how a skill run was actually executed. Populated by
 * `SkillHostBridge.runSkill` and used by the UI to render a clear
 * cloud/local badge. The bridge cannot know a skill's logic; it reports
 * what it observed (wall-clock time + how many times the skill asked for
 * an LLM completion) and which provider was installed at the time.
 */
export interface SkillResultProvenance {
  /** Wall-clock duration of the iframe round-trip for this run. */
  durationMs: number;
  /** Number of `__skillos.llm.chat` / `chatJSON` calls the skill made. */
  llmCalls: number;
  /** Human-readable provider label if one was installed (e.g. "openrouter-qwen · qwen/qwen-2.5-72b"). */
  llmProvider?: string;
  /** Where that provider runs — used to color the badge cloud vs local. */
  llmLocation?: "cloud" | "on-device";
  /**
   * Estimated USD cost of this run. `0` means the run was fully local (no
   * billable LLM calls). `undefined` means cost could not be determined
   * (cloud run without a pricing entry for the active provider). The badge
   * renders "$0.00" for 0 and hides the field for undefined so we never
   * claim zero cost for a cloud run whose pricing we don't know.
   */
  costUsd?: number;
}

export interface SkillResult {
  ok: boolean;
  result?: string;
  error?: string;
  webview?: SkillWebview;
  image?: SkillImage;
  raw?: unknown;
  provenance?: SkillResultProvenance;
}

export function skillResultFromJson(payload: unknown): SkillResult {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return { ok: false, error: "invalid skill payload" };
  }
  const obj = payload as Record<string, unknown>;

  // The skill may have returned a bare string (serialized JSON or not).
  if (typeof obj.error === "string" && obj.error.length > 0) {
    return { ok: false, error: obj.error, raw: obj };
  }
  return {
    ok: true,
    result: typeof obj.result === "string" ? obj.result : undefined,
    webview: toWebview(obj.webview),
    image: toImage(obj.image),
    raw: obj,
  };
}

function toWebview(v: unknown): SkillWebview | undefined {
  if (!isObject(v)) return undefined;
  const url = typeof v.url === "string" ? v.url : undefined;
  if (!url) return undefined;
  return {
    url,
    iframe: typeof v.iframe === "boolean" ? v.iframe : undefined,
    aspectRatio: typeof v.aspectRatio === "number" ? v.aspectRatio : undefined,
  };
}

function toImage(v: unknown): SkillImage | undefined {
  if (!isObject(v)) return undefined;
  const base64 = typeof v.base64 === "string" ? v.base64 : undefined;
  if (!base64) return undefined;
  return {
    base64,
    mimeType: typeof v.mimeType === "string" ? v.mimeType : undefined,
  };
}

export function skillResultFromError(err: unknown): SkillResult {
  const msg = err instanceof Error ? err.message : String(err);
  return { ok: false, error: msg };
}

/** String projection of a SkillResult suitable for feeding back into an LLM turn. */
export function skillResultToLlmString(r: SkillResult): string {
  if (!r.ok) return `Skill failed: ${r.error ?? "unknown"}`;
  const parts: string[] = [];
  if (r.result) parts.push(r.result);
  if (r.image?.base64) parts.push(`[image attached (${r.image.mimeType ?? "image/png"})]`);
  if (r.webview?.url) parts.push(`[webview: ${r.webview.url}]`);
  return parts.length > 0 ? parts.join("\n") : "(skill returned empty result)";
}

function isObject(v: unknown): v is Record<string, unknown> {
  return !!v && typeof v === "object" && !Array.isArray(v);
}
