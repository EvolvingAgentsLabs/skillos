import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  enqueue,
  flushQueue,
  invalidateProject,
  listQueue,
  loadPersistedQueueSummary,
} from "../src/lib/llm/offline_queue";
import { _resetDBForTests } from "../src/lib/storage/db";

describe("offline_queue", () => {
  beforeEach(async () => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
    // Drain any residual in-memory entries from previous tests.
    await invalidateProject("*");
    for (const e of listQueue()) await invalidateProject(e.projectId);
  });

  it("enqueue + list round-trips + persists summary to meta", async () => {
    const id = await enqueue("proj1", async () => undefined, {
      lastError: "network",
    });
    expect(id).toMatch(/^oq_/);
    const entries = listQueue();
    expect(entries.length).toBe(1);
    expect(entries[0].projectId).toBe("proj1");
    expect(entries[0].lastError).toBe("network");
    const persisted = await loadPersistedQueueSummary();
    expect(persisted.length).toBe(1);
  });

  it("flushQueue drains successful tasks", async () => {
    const seen: string[] = [];
    await enqueue("p1", async () => {
      seen.push("a");
    });
    await enqueue("p2", async () => {
      seen.push("b");
    });
    const r = await flushQueue();
    expect(r.drained).toBe(2);
    expect(r.remaining).toBe(0);
    expect(seen).toEqual(["a", "b"]);
    expect(listQueue()).toEqual([]);
  });

  it("flushQueue stops on first failure and preserves the failing entry", async () => {
    await enqueue("p1", async () => undefined);
    await enqueue("p2", async () => {
      throw new Error("still broken");
    });
    await enqueue("p3", vi.fn(async () => undefined));
    const r = await flushQueue();
    expect(r.drained).toBe(1);
    expect(r.remaining).toBe(2);
    const left = listQueue().map((e) => e.projectId);
    expect(left).toEqual(["p2", "p3"]);
    expect(listQueue().find((e) => e.projectId === "p2")?.lastError).toContain(
      "broken",
    );
  });

  it("invalidateProject removes only the matching project's entries", async () => {
    await enqueue("p1", async () => undefined);
    await enqueue("p2", async () => undefined);
    await enqueue("p1", async () => undefined);
    await invalidateProject("p1");
    const remaining = listQueue().map((e) => e.projectId);
    expect(remaining).toEqual(["p2"]);
  });
});
