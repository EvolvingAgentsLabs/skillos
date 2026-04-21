import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it } from "vitest";
import { lookupDottedPath } from "../src/lib/evals/evals";
import type { BlackboardSnapshot } from "../src/lib/cartridge/types";
import { _resetDBForTests } from "../src/lib/storage/db";

const SNAP: BlackboardSnapshot = {
  weekly_menu: {
    value: {
      household_size: 2,
      days: [
        { day: "Mon", meals: [{ slot: "breakfast" }] },
        { day: "Tue", meals: [{ slot: "lunch" }] },
      ],
    },
    schema_ref: "",
    produced_by: "",
    description: "",
    created_at: "2026-04-21T00:00:00Z",
  },
  shopping_list: {
    value: { aisles: { produce: ["apples"] } },
    schema_ref: "",
    produced_by: "",
    description: "",
    created_at: "2026-04-21T00:00:00Z",
  },
};

describe("lookupDottedPath", () => {
  beforeEach(() => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
  });

  it("resolves top-level blackboard entry value", () => {
    expect(lookupDottedPath(SNAP, "weekly_menu.household_size")).toBe(2);
  });

  it("resolves nested object properties", () => {
    expect(lookupDottedPath(SNAP, "shopping_list.aisles.produce")).toEqual(["apples"]);
  });

  it("resolves array indices", () => {
    expect(lookupDottedPath(SNAP, "weekly_menu.days.0.day")).toBe("Mon");
    expect(lookupDottedPath(SNAP, "weekly_menu.days.1.meals.0.slot")).toBe("lunch");
  });

  it("returns undefined for missing paths", () => {
    expect(lookupDottedPath(SNAP, "missing.key")).toBeUndefined();
    expect(lookupDottedPath(SNAP, "weekly_menu.oops")).toBeUndefined();
  });
});
