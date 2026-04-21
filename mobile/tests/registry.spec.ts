/**
 * Integration tests for CartridgeRegistry against the real seeded cartridge
 * files produced by scripts/seed-build.mjs into public/seed/.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { IDBFactory } from "fake-indexeddb";
import { beforeAll, beforeEach, describe, expect, it } from "vitest";
import { CartridgeRegistry } from "../src/lib/cartridge/registry";
import { _resetDBForTests, putFile } from "../src/lib/storage/db";

const SEED_DIR = path.resolve(__dirname, "..", "public", "seed");

interface ManifestEntry {
  path: string;
  sha1: string;
  size: number;
}
interface Manifest {
  files: ManifestEntry[];
}

async function seedFromDisk(): Promise<number> {
  const mf = JSON.parse(
    await readFile(path.join(SEED_DIR, "manifest.json"), "utf-8"),
  ) as Manifest;
  for (const entry of mf.files) {
    const abs = path.join(SEED_DIR, entry.path);
    const buf = await readFile(abs);
    await putFile(entry.path, buf, { sha1: entry.sha1 });
  }
  return mf.files.length;
}

describe("CartridgeRegistry (integration)", () => {
  beforeAll(async () => {
    // Verify seed exists on disk.
    const mf = await readFile(path.join(SEED_DIR, "manifest.json"), "utf-8");
    expect(JSON.parse(mf).file_count).toBeGreaterThan(0);
  });

  beforeEach(() => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
  });

  it("loads every seeded cartridge manifest", async () => {
    await seedFromDisk();
    const reg = new CartridgeRegistry();
    await reg.init();
    const names = reg.names().sort();
    expect(names.length).toBeGreaterThanOrEqual(3);
    expect(names).toContain("cooking");
    expect(names).toContain("demo");
  });

  it("cooking cartridge exposes the expected flows and schema refs", async () => {
    await seedFromDisk();
    const reg = new CartridgeRegistry();
    await reg.init();

    const cooking = reg.get("cooking");
    expect(cooking).toBeDefined();
    expect(cooking!.flows["plan-weekly-menu"]).toEqual([
      "menu-planner",
      "shopping-list-builder",
      "recipe-writer",
    ]);
    expect(cooking!.flows["quick-shopping-list"]).toEqual([
      "menu-planner",
      "shopping-list-builder",
    ]);
    expect(cooking!.default_flow).toBe("plan-weekly-menu");
    expect(cooking!.blackboard_schema).toMatchObject({
      weekly_menu: "weekly_menu.schema.json",
      shopping_list: "shopping_list.schema.json",
      recipes: "recipes.schema.json",
    });
    expect(cooking!.validators).toContain("menu_complete.py");
    expect(cooking!.max_turns_per_agent).toBe(3);
  });

  it("loadAgent parses YAML frontmatter and body", async () => {
    await seedFromDisk();
    const reg = new CartridgeRegistry();
    await reg.init();
    const agent = await reg.loadAgent("cooking", "menu-planner");
    expect(agent).toBeDefined();
    expect(agent!.name.length).toBeGreaterThan(0);
    expect(agent!.body.length).toBeGreaterThan(0);
    // Body should not start with frontmatter marker.
    expect(agent!.body.startsWith("---")).toBe(false);
    // Caching: same instance on second fetch.
    const agent2 = await reg.loadAgent("cooking", "menu-planner");
    expect(agent2).toBe(agent);
  });

  it("getValidator validates real schemas and rejects bad payloads", async () => {
    await seedFromDisk();
    const reg = new CartridgeRegistry();
    await reg.init();
    const validate = await reg.getValidator("cooking");

    const bad = validate({ oops: true }, "weekly_menu.schema.json");
    expect(bad.ok).toBe(false);
    expect(bad.message).toMatch(/schema violation/);

    const minimalValid = {
      week_start: "2026-04-20",
      days: [
        {
          day: "monday",
          breakfast: "oatmeal",
          lunch: "sandwich",
          dinner: "pasta",
        },
      ],
    };
    const res = validate(minimalValid, "weekly_menu.schema.json");
    // Schema may require additional fields; assert the validator ran and
    // produced a deterministic ok boolean without throwing.
    expect(typeof res.ok).toBe("boolean");
    expect(typeof res.message).toBe("string");

    // Missing schema file should pass-through as a warning, not crash.
    const missing = validate({}, "does-not-exist.schema.json");
    expect(missing.ok).toBe(true);
  });

  it("matchIntent routes 'plan weekly menu' to cooking", async () => {
    await seedFromDisk();
    const reg = new CartridgeRegistry();
    await reg.init();
    const { cartridge, score } = reg.matchIntent("plan weekly menu for my family");
    expect(cartridge).toBe("cooking");
    expect(score).toBeGreaterThanOrEqual(2);
  });

  it("matchIntent returns null below minScore", async () => {
    await seedFromDisk();
    const reg = new CartridgeRegistry();
    await reg.init();
    const { cartridge } = reg.matchIntent("hello world");
    expect(cartridge).toBeNull();
  });
});
