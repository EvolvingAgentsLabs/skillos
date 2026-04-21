import { describe, expect, it } from "vitest";
import { BUILTIN_VALIDATORS } from "../src/lib/cartridge/validators_builtin";
import type { BlackboardSnapshot } from "../src/lib/cartridge/types";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const SLOTS = ["breakfast", "lunch", "dinner"];

function weeklyMenuBB(): BlackboardSnapshot {
  return {
    weekly_menu: {
      value: {
        days: DAYS.map((day) => ({
          day,
          meals: SLOTS.map((slot) => ({ slot, name: `${slot} on ${day}` })),
        })),
      },
      schema_ref: "weekly_menu.schema.json",
      produced_by: "menu-planner",
      description: "",
      created_at: "2026-04-21T00:00:00.000Z",
    },
  };
}

describe("menu_complete validator", () => {
  const menuComplete = BUILTIN_VALIDATORS["menu_complete.py"];

  it("passes a well-formed 7-day × 3-slot menu", () => {
    const r = menuComplete(weeklyMenuBB());
    expect(r.ok).toBe(true);
    expect(r.message).toMatch(/7 days/);
  });

  it("fails when weekly_menu is missing", () => {
    const r = menuComplete({});
    expect(r.ok).toBe(false);
    expect(r.message).toMatch(/missing/);
  });

  it("fails when a day is missing", () => {
    const bb = weeklyMenuBB();
    const menu = bb.weekly_menu.value as { days: unknown[] };
    menu.days = menu.days.slice(0, 6);
    const r = menuComplete(bb);
    expect(r.ok).toBe(false);
    expect(r.message).toMatch(/7 days/);
  });

  it("fails when a slot is missing on a day", () => {
    const bb = weeklyMenuBB();
    const menu = bb.weekly_menu.value as { days: Array<{ meals: Array<{ slot: string }> }> };
    menu.days[0].meals = menu.days[0].meals.filter((m) => m.slot !== "lunch");
    const r = menuComplete(bb);
    expect(r.ok).toBe(false);
    expect(r.message).toMatch(/missing slots/);
  });

  it("validates recipes coverage when present", () => {
    const bb = weeklyMenuBB();
    bb.recipes = {
      value: DAYS.map((day) => ({ day, title: `${day} dinner` })),
      schema_ref: "",
      produced_by: "recipe-writer",
      description: "",
      created_at: "2026-04-21T00:00:00.000Z",
    };
    const r = menuComplete(bb);
    expect(r.ok).toBe(true);
  });
});

describe("shopping_list_sane validator", () => {
  const shoppingList = BUILTIN_VALIDATORS["shopping_list_sane.py"];

  it("skips quietly when shopping_list is absent", () => {
    const r = shoppingList({});
    expect(r.ok).toBe(true);
    expect(r.message).toMatch(/skipped/);
  });

  it("fails when aisles are missing", () => {
    const r = shoppingList({
      shopping_list: {
        value: { aisles: { produce: ["apples"] } },
        schema_ref: "",
        produced_by: "",
        description: "",
        created_at: "x",
      },
    });
    expect(r.ok).toBe(false);
    expect(r.message).toMatch(/missing aisles/);
  });

  it("warns when list is thin but still passes", () => {
    const r = shoppingList({
      shopping_list: {
        value: {
          aisles: { produce: ["a"], dairy: [], pantry: [], protein: [], other: [] },
        },
        schema_ref: "",
        produced_by: "",
        description: "",
        created_at: "x",
      },
    });
    expect(r.ok).toBe(true);
    expect(r.message).toMatch(/warning/);
  });

  it("passes when list is sufficient", () => {
    const r = shoppingList({
      shopping_list: {
        value: {
          aisles: {
            produce: ["a", "b"],
            dairy: ["c"],
            pantry: ["d", "e"],
            protein: ["f", "g"],
            other: ["h"],
          },
        },
        schema_ref: "",
        produced_by: "",
        description: "",
        created_at: "x",
      },
    });
    expect(r.ok).toBe(true);
    expect(r.message).toMatch(/items across/);
  });
});
