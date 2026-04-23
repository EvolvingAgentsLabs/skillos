/**
 * Done-card renderer registry.
 *
 * Rich typed output is one of the UI roadmap surfaces: a recipe output
 * should feel like "an app I built," not a JSON dump. This module picks
 * the best-fit renderer for a card's payload based on the schema_ref hint
 * plus structural detection on the data itself. Callers (Card.svelte)
 * route to the right Svelte component; the raw JSON pre view remains the
 * safe fallback for anything we can't classify.
 *
 * Kept deliberately small and additive — three renderers cover the
 * high-frequency scenarios from the idea storm (invoices → table, menus
 * and itineraries → schedule, articles and summaries → reader). Extend
 * by adding a detector here and a component that accepts `{ data }`.
 */

export type RendererKind = "table" | "schedule" | "reader" | "json";

export interface RendererChoice {
  kind: RendererKind;
  /** Tooltip/label for the UI — explains why this renderer was picked. */
  reason: string;
}

export function pickRenderer(
  schemaRef: string | undefined,
  data: unknown,
): RendererChoice {
  // Honest fallback first: no data means there's nothing to type-render.
  if (data === undefined || data === null) {
    return { kind: "json", reason: "no payload" };
  }

  const hint = (schemaRef ?? "").toLowerCase();

  // Skill-result shape: `{ result: "…" }` is the canonical output of
  // Gallery skills (see skill_result.ts). Text output is best rendered
  // as a reader view rather than JSON.
  if (isPlainObject(data) && typeof data.result === "string" && Object.keys(data).length <= 3) {
    return { kind: "reader", reason: "skill result text" };
  }

  // Explicit schema hint takes precedence over structural guessing when
  // available — schema_refs are authored, data shapes are inferred.
  if (hint) {
    if (/(invoice|receipt|ledger|items|line_items)/.test(hint)) {
      if (containsTableLike(data)) return { kind: "table", reason: `schema ${hint}` };
    }
    if (/(menu|schedule|itinerary|calendar|plan|week|day)/.test(hint)) {
      if (containsScheduleLike(data)) return { kind: "schedule", reason: `schema ${hint}` };
    }
    if (/(report|article|summary|doc|note|reader)/.test(hint)) {
      if (containsReaderLike(data)) return { kind: "reader", reason: `schema ${hint}` };
    }
  }

  // Structural detection — works regardless of schema_ref.
  if (containsScheduleLike(data)) return { kind: "schedule", reason: "detected dated items" };
  if (containsTableLike(data)) return { kind: "table", reason: "detected homogeneous rows" };
  if (containsReaderLike(data)) return { kind: "reader", reason: "detected text content" };

  return { kind: "json", reason: "no structural match" };
}

// ────────────────────────────────────────────────────────────────────────
// Detectors

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return !!v && typeof v === "object" && !Array.isArray(v);
}

/**
 * A table is an array of ≥2 objects whose keys overlap substantially.
 * Single-row arrays, mixed-shape arrays, and primitive arrays don't count.
 */
function containsTableLike(data: unknown): boolean {
  const rows = findArrayOfObjects(data);
  if (!rows || rows.length < 2) return false;
  const firstKeys = Object.keys(rows[0]);
  if (firstKeys.length === 0) return false;
  // At least half the rows must share ≥60% of the first row's keys.
  let conforming = 0;
  for (const r of rows) {
    const keys = Object.keys(r);
    const shared = keys.filter((k) => firstKeys.includes(k)).length;
    if (shared >= Math.ceil(firstKeys.length * 0.6)) conforming += 1;
  }
  return conforming >= Math.ceil(rows.length / 2);
}

/**
 * A schedule is a collection of items each carrying a date-like field
 * (date, day, when, at, timestamp, start, start_date). Covers weekly
 * menus, itineraries, calendars.
 */
function containsScheduleLike(data: unknown): boolean {
  const rows = findArrayOfObjects(data);
  if (!rows || rows.length === 0) return false;
  const DATE_KEYS = ["date", "day", "when", "at", "timestamp", "start", "start_date"];
  let withDate = 0;
  for (const r of rows) {
    const keys = Object.keys(r).map((k) => k.toLowerCase());
    if (keys.some((k) => DATE_KEYS.includes(k))) withDate += 1;
  }
  return withDate >= Math.ceil(rows.length * 0.6);
}

/**
 * Reader-worthy content: a string, or an object with a long text field
 * (body, content, text, markdown, summary, result).
 */
function containsReaderLike(data: unknown): boolean {
  if (typeof data === "string" && data.length > 40) return true;
  if (!isPlainObject(data)) return false;
  const TEXT_KEYS = ["body", "content", "text", "markdown", "summary", "result", "article"];
  for (const k of TEXT_KEYS) {
    const v = data[k];
    if (typeof v === "string" && v.length > 40) return true;
  }
  return false;
}

/** Find an array-of-objects either at the root or one level deep. */
function findArrayOfObjects(data: unknown): Record<string, unknown>[] | null {
  if (Array.isArray(data) && data.every(isPlainObject)) {
    return data as Record<string, unknown>[];
  }
  if (isPlainObject(data)) {
    for (const v of Object.values(data)) {
      if (Array.isArray(v) && v.length > 0 && v.every(isPlainObject)) {
        return v as Record<string, unknown>[];
      }
    }
  }
  return null;
}

// ────────────────────────────────────────────────────────────────────────
// Extractors — used by renderer components so the same heuristics apply
// when pulling the actual rows/text out for display.

export function extractRows(data: unknown): Record<string, unknown>[] {
  return findArrayOfObjects(data) ?? [];
}

export function extractReaderText(data: unknown): string {
  if (typeof data === "string") return data;
  if (!isPlainObject(data)) return "";
  const TEXT_KEYS = ["body", "content", "text", "markdown", "summary", "result", "article"];
  for (const k of TEXT_KEYS) {
    const v = data[k];
    if (typeof v === "string") return v;
  }
  return "";
}
