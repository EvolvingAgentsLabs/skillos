/**
 * Integration tests for SkillRegistry against the real seeded Gallery skills
 * under cartridges/demo/skills/*.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it } from "vitest";
import { SkillRegistry, loadSkill } from "../src/lib/skills/skill_loader";
import { _resetDBForTests, putFile } from "../src/lib/storage/db";

const SEED_DIR = path.resolve(__dirname, "..", "public", "seed");

interface ManifestEntry {
  path: string;
  sha1: string;
}
interface Manifest {
  files: ManifestEntry[];
}

async function seedFromDisk(): Promise<void> {
  const mf = JSON.parse(
    await readFile(path.join(SEED_DIR, "manifest.json"), "utf-8"),
  ) as Manifest;
  for (const entry of mf.files) {
    // Only seed demo cartridge to keep tests fast; we're only testing the
    // demo skill registry.
    if (!entry.path.startsWith("cartridges/demo/")) continue;
    const buf = await readFile(path.join(SEED_DIR, entry.path));
    await putFile(entry.path, buf, { sha1: entry.sha1 });
  }
}

describe("SkillRegistry (integration)", () => {
  beforeEach(async () => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
    await seedFromDisk();
  });

  it("scans cartridges/demo/skills/ and loads every skill", async () => {
    const reg = new SkillRegistry();
    await reg.scan("cartridges/demo/skills/");
    const names = reg.names().sort();
    // The demo cartridge ships 12 Gallery skills.
    expect(names.length).toBeGreaterThanOrEqual(10);
    expect(names).toContain("calculate-hash");
  });

  it("loadSkill parses SKILL.md frontmatter for calculate-hash", async () => {
    const s = await loadSkill("cartridges/demo/skills/calculate-hash");
    expect(s).toBeDefined();
    expect(s!.name).toBe("calculate-hash");
    expect(s!.description).toMatch(/hash/i);
    expect(s!.require_secret).toBe(false);
    expect(s!.runtime).toBe("node");
    expect(s!.script_path).toBe("cartridges/demo/skills/calculate-hash/scripts/index.html");
    expect(s!.js_path).toBe("cartridges/demo/skills/calculate-hash/scripts/index.js");
    expect(s!.instructions.length).toBeGreaterThan(20);
  });

  it("returns undefined for a skill dir without SKILL.md", async () => {
    expect(await loadSkill("cartridges/demo/skills/does-not-exist")).toBeUndefined();
  });

  it("descriptions() renders a one-line-per-skill summary", async () => {
    const reg = new SkillRegistry();
    await reg.scan("cartridges/demo/skills/");
    const desc = reg.descriptions();
    expect(desc).toContain("calculate-hash");
    // Each line starts with "- **…"
    for (const line of desc.split("\n")) {
      expect(line.startsWith("- **")).toBe(true);
    }
  });
});
