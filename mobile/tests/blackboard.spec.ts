import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it } from "vitest";
import { Blackboard } from "../src/lib/cartridge/blackboard";
import { makeValidatorForCartridge } from "../src/lib/cartridge/validators";
import { _resetDBForTests } from "../src/lib/storage/db";

const weeklyMenuSchema = {
  type: "object",
  required: ["week_start", "days"],
  properties: {
    week_start: { type: "string", format: "date" },
    days: {
      type: "array",
      minItems: 1,
      items: { type: "object", required: ["day"], properties: { day: { type: "string" } } },
    },
  },
};

describe("Blackboard", () => {
  beforeEach(() => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
  });

  it("stores and retrieves entries with metadata", () => {
    const bb = new Blackboard();
    const res = bb.put("x", { v: 1 }, { produced_by: "agent-a", description: "thing" });
    expect(res.ok).toBe(true);
    const e = bb.get("x")!;
    expect(e.value).toEqual({ v: 1 });
    expect(e.produced_by).toBe("agent-a");
    expect(e.description).toBe("thing");
    expect(e.created_at).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    expect(bb.has("x")).toBe(true);
    expect(bb.keys()).toEqual(["x"]);
  });

  it("bundle and describe return selected keys only", () => {
    const bb = new Blackboard();
    bb.put("a", 1, { produced_by: "alice", description: "first" });
    bb.put("b", 2, { produced_by: "bob", description: "second" });
    bb.put("c", 3);
    expect(bb.bundle(["a", "c"])).toEqual({ a: 1, c: 3 });
    expect(bb.describe(["a", "b"])).toBe(
      "- `a` (from alice): first\n- `b` (from bob): second",
    );
    expect(bb.describe([])).toBe("(no inputs)");
  });

  it("snapshot serializes entries round-trippably", () => {
    const bb = new Blackboard();
    bb.put("k", "v", { schema_ref: "foo.json", produced_by: "a", description: "d" });
    const snap = bb.snapshot();
    expect(snap.k.value).toBe("v");
    expect(snap.k.schema_ref).toBe("foo.json");
    expect(snap.k.produced_by).toBe("a");
    expect(snap.k.description).toBe("d");
    expect(typeof snap.k.created_at).toBe("string");
    expect(JSON.parse(JSON.stringify(snap))).toEqual(snap);
  });

  it("returns ok:false on schema violations but still stores the value", () => {
    const validator = makeValidatorForCartridge("t", [
      { ref: "weekly_menu.schema.json", schema: weeklyMenuSchema },
    ]);
    const bb = new Blackboard(validator);
    const bad = bb.put("weekly_menu", { days: [] }, {
      schema_ref: "weekly_menu.schema.json",
      produced_by: "menu-planner",
    });
    expect(bad.ok).toBe(false);
    expect(bad.message).toMatch(/schema violation/);
    // Still stored — caller decides whether to retry.
    expect(bb.has("weekly_menu")).toBe(true);

    const good = bb.put(
      "weekly_menu",
      { week_start: "2026-04-20", days: [{ day: "mon" }] },
      { schema_ref: "weekly_menu.schema.json" },
    );
    expect(good.ok).toBe(true);
  });

  it("validate=false skips schema check even when validator is set", () => {
    const validator = makeValidatorForCartridge("t", [
      { ref: "x.schema.json", schema: { type: "object", required: ["a"] } },
    ]);
    const bb = new Blackboard(validator);
    const res = bb.put("k", {}, { schema_ref: "x.schema.json", validate: false });
    expect(res.ok).toBe(true);
  });

  it("returns undefined fallback when key missing", () => {
    const bb = new Blackboard();
    expect(bb.value("missing")).toBeUndefined();
    expect(bb.value("missing", 42)).toBe(42);
    expect(bb.get("missing")).toBeUndefined();
  });
});
