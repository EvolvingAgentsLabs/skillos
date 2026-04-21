/**
 * TS ports of the Python validators shipped under
 * C:\evolvingagents\skillos\cartridges\cooking\validators\.
 *
 * The mobile runner cannot exec `.py` files; it looks up validators by
 * filename in this registry instead. Cartridges that declare validators not
 * listed here get a "validator missing" message — parity with the Python
 * behaviour when a .py file cannot be imported.
 */

import type { BlackboardSnapshot, ValidationResult } from "./types";

export type BuiltinValidator = (bb: BlackboardSnapshot) => ValidationResult;

// ────────────────────────────────────────────────────────────────────────
// cooking/validators/menu_complete.py
// ────────────────────────────────────────────────────────────────────────

const REQUIRED_DAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
];

const menuComplete: BuiltinValidator = (bb) => {
  const menuEntry = bb.weekly_menu;
  if (!menuEntry) return { ok: false, message: "weekly_menu missing from blackboard" };
  const menu = menuEntry.value;
  if (!isObject(menu)) return { ok: false, message: "weekly_menu is not an object" };

  const days = Array.isArray(menu.days) ? (menu.days as unknown[]) : [];
  if (days.length !== 7) {
    return { ok: false, message: `weekly_menu must have 7 days, got ${days.length}` };
  }
  const seen = new Set<string>();
  for (const d of days) if (isObject(d)) seen.add(String(d.day ?? ""));
  const missing = REQUIRED_DAYS.filter((d) => !seen.has(d));
  if (missing.length) {
    return { ok: false, message: `missing days: ${JSON.stringify(missing)}` };
  }
  for (const d of days) {
    if (!isObject(d)) continue;
    const meals = Array.isArray(d.meals) ? (d.meals as unknown[]) : [];
    const slots = new Set<string>();
    for (const m of meals) if (isObject(m) && typeof m.slot === "string") slots.add(m.slot);
    const required = new Set(["breakfast", "lunch", "dinner"]);
    const diff = [...required].filter((s) => !slots.has(s));
    if (diff.length) {
      return {
        ok: false,
        message: `day '${String(d.day)}' missing slots: ${JSON.stringify(diff)}`,
      };
    }
  }

  const recipesEntry = bb.recipes;
  if (recipesEntry) {
    const recipes = recipesEntry.value;
    if (!Array.isArray(recipes) || recipes.length !== 7) {
      return {
        ok: false,
        message: `recipes must be a list of 7, got ${Array.isArray(recipes) ? recipes.length : "non-list"}`,
      };
    }
    const recipeDays = new Set<string>();
    for (const r of recipes) if (isObject(r)) recipeDays.add(String(r.day ?? ""));
    const menuDays = seen;
    const notIn = [...recipeDays].filter((d) => !menuDays.has(d));
    if (notIn.length) {
      return {
        ok: false,
        message: `recipes reference days not in weekly_menu: ${JSON.stringify(notIn)}`,
      };
    }
  }

  return { ok: true, message: "weekly_menu has all 7 days × 3 slots" };
};

// ────────────────────────────────────────────────────────────────────────
// cooking/validators/shopping_list_sane.py
// ────────────────────────────────────────────────────────────────────────

const REQUIRED_AISLES = ["produce", "dairy", "pantry", "protein", "other"];

const shoppingListSane: BuiltinValidator = (bb) => {
  const entry = bb.shopping_list;
  if (!entry) {
    return {
      ok: true,
      message: "skipped (no shopping_list on blackboard — flow may omit it)",
    };
  }
  const sl = entry.value;
  if (!isObject(sl)) return { ok: false, message: "shopping_list is not an object" };
  const aisles = sl.aisles;
  if (!isObject(aisles)) {
    return { ok: false, message: "shopping_list.aisles must be an object" };
  }
  const missing = REQUIRED_AISLES.filter((a) => !(a in aisles));
  if (missing.length) {
    return { ok: false, message: `missing aisles: ${JSON.stringify(missing)}` };
  }
  let total = 0;
  for (const a of REQUIRED_AISLES) {
    const list = aisles[a];
    if (Array.isArray(list)) total += list.length;
  }
  if (total < 5) {
    return {
      ok: true,
      message: `warning: only ${total} items across all aisles — suspiciously thin list`,
    };
  }
  return {
    ok: true,
    message: `shopping_list ok (${total} items across ${REQUIRED_AISLES.length} aisles)`,
  };
};

// ────────────────────────────────────────────────────────────────────────

export const BUILTIN_VALIDATORS: Record<string, BuiltinValidator> = {
  "menu_complete.py": menuComplete,
  "menu_complete.ts": menuComplete,
  "shopping_list_sane.py": shoppingListSane,
  "shopping_list_sane.ts": shoppingListSane,
};

function isObject(v: unknown): v is Record<string, unknown> {
  return !!v && typeof v === "object" && !Array.isArray(v);
}
