import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  _resetDBForTests,
  fileCount,
  getFile,
  getMeta,
  listFiles,
} from "../src/lib/storage/db";
import { seedIfNeeded } from "../src/lib/storage/seed";

function makeManifest() {
  return {
    seed_version: "test-1",
    source_root: "skillos",
    file_count: 3,
    files: [
      { path: "cartridges/cooking/cartridge.yaml", sha1: "a1", size: 5 },
      { path: "cartridges/cooking/agents/menu-planner.md", sha1: "a2", size: 8 },
      { path: "system/SmartMemory.md", sha1: "a3", size: 4 },
    ],
  };
}

const content: Record<string, string> = {
  "cartridges/cooking/cartridge.yaml": "name: cooking\n",
  "cartridges/cooking/agents/menu-planner.md": "---\nname: menu\n---\nbody",
  "system/SmartMemory.md": "# mem",
};

describe("seedIfNeeded", () => {
  beforeEach(() => {
    // Fresh fake-indexeddb per test + drop cached db handle.
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
    vi.unstubAllGlobals();
  });

  it("fetches manifest and writes every listed file to IndexedDB", async () => {
    const manifest = makeManifest();
    const fetchMock = vi.fn(async (url: string) => {
      if (url.endsWith("/seed/manifest.json")) {
        return new Response(JSON.stringify(manifest), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      }
      const rel = url.replace(/^.*\/seed\//, "");
      const body = content[rel];
      if (body === undefined) {
        return new Response("not found", { status: 404 });
      }
      return new Response(body, { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    const progress: string[] = [];
    const result = await seedIfNeeded((p) => progress.push(p.phase));

    expect(result.phase).toBe("done");
    expect(result.completed).toBe(3);
    expect(await fileCount()).toBe(3);
    for (const entry of manifest.files) {
      const rec = await getFile(entry.path);
      expect(rec, `file ${entry.path} should be present`).toBeDefined();
      expect(rec!.sha1).toBe(entry.sha1);
      expect(new TextDecoder().decode(rec!.content)).toBe(content[entry.path]);
    }
    expect(await getMeta("seed_version")).toBe("test-1");
    expect(progress).toContain("seeding");
    expect(progress).toContain("done");
  });

  it("is idempotent when seed_version matches", async () => {
    const manifest = makeManifest();
    const fetchMock = vi.fn(async (url: string) => {
      if (url.endsWith("/seed/manifest.json")) {
        return new Response(JSON.stringify(manifest), { status: 200 });
      }
      const rel = url.replace(/^.*\/seed\//, "");
      return new Response(content[rel] ?? "", { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    await seedIfNeeded();
    fetchMock.mockClear();

    const second = await seedIfNeeded();
    expect(second.phase).toBe("skipped");
    // Only the manifest should have been refetched on the second pass.
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toMatch(/manifest\.json$/);
  });

  it("listFiles returns seeded paths by prefix", async () => {
    const manifest = makeManifest();
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.endsWith("/seed/manifest.json")) {
          return new Response(JSON.stringify(manifest), { status: 200 });
        }
        const rel = url.replace(/^.*\/seed\//, "");
        return new Response(content[rel] ?? "", { status: 200 });
      }),
    );

    await seedIfNeeded();
    const cartridgeFiles = await listFiles("cartridges/");
    expect(cartridgeFiles.sort()).toEqual([
      "cartridges/cooking/agents/menu-planner.md",
      "cartridges/cooking/cartridge.yaml",
    ]);
    const systemFiles = await listFiles("system/");
    expect(systemFiles).toEqual(["system/SmartMemory.md"]);
  });
});
