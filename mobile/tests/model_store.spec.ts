import { IDBFactory } from "fake-indexeddb";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { _resetDBForTests } from "../src/lib/storage/db";
import type { ModelCatalogEntry } from "../src/lib/llm/local/model_catalog";
import {
  deleteInstalledModel,
  downloadModel,
  isModelInstalled,
  listInstalledModels,
} from "../src/lib/llm/local/model_store";

const ENTRY: ModelCatalogEntry = {
  id: "fake-model",
  name: "Fake · Tiny",
  description: "test model",
  url: "https://example.invalid/fake.gguf",
  backend: "wllama",
  sizeBytes: 1024,
  template: "qwen2",
  contextTokens: 1024,
  tier: "cheap",
  license: "test",
};

function streamBody(bytes: Uint8Array): ReadableStream<Uint8Array> {
  return new ReadableStream({
    start(c) {
      const CHUNK = 256;
      let i = 0;
      function push() {
        if (i >= bytes.byteLength) {
          c.close();
          return;
        }
        const slice = bytes.subarray(i, Math.min(i + CHUNK, bytes.byteLength));
        c.enqueue(slice);
        i += CHUNK;
        queueMicrotask(push);
      }
      push();
    },
  });
}

describe("model_store", () => {
  beforeEach(() => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
  });
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("downloads and commits a model to IndexedDB", async () => {
    const payload = new Uint8Array(ENTRY.sizeBytes);
    for (let i = 0; i < payload.length; i++) payload[i] = i % 256;
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(streamBody(payload), { status: 200 })),
    );
    const progress: string[] = [];
    const rec = await downloadModel(ENTRY, (p) => progress.push(p.phase));

    expect(rec.id).toBe("fake-model");
    expect(rec.size).toBe(ENTRY.sizeBytes);
    expect(rec.backend).toBe("wllama");
    expect(progress).toContain("preflight");
    expect(progress).toContain("fetching");
    expect(progress).toContain("done");

    expect(await isModelInstalled("fake-model")).toBe(true);
    const installed = await listInstalledModels();
    expect(installed.map((b) => b.id)).toEqual(["fake-model"]);
  });

  it("delete removes the blob", async () => {
    const payload = new Uint8Array(ENTRY.sizeBytes).fill(42);
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(streamBody(payload), { status: 200 })),
    );
    await downloadModel(ENTRY);
    await deleteInstalledModel(ENTRY.id);
    expect(await isModelInstalled(ENTRY.id)).toBe(false);
  });

  it("emits an error phase on fetch failure", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("boom", { status: 500 })),
    );
    const progress: string[] = [];
    await expect(downloadModel(ENTRY, (p) => progress.push(p.phase))).rejects.toThrow(/fetch 500/);
    expect(progress).toContain("error");
  });
});
