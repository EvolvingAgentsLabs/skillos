import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it } from "vitest";
import { _resetDBForTests } from "../src/lib/storage/db";
import {
  deleteProjectRecord,
  getProjectRecord,
  listProjectRecords,
  putProjectRecord,
  type StoredProject,
} from "../src/lib/storage/project_store";

function fixture(overrides: Partial<StoredProject> = {}): StoredProject {
  return {
    id: "prj_1",
    name: "Test project",
    cartridge: "cooking",
    created_at: "2026-04-21T10:00:00.000Z",
    updated_at: "2026-04-21T10:00:00.000Z",
    cards: [
      {
        id: "card_1",
        kind: "goal",
        lane: "planned",
        title: "Plan meals for the week",
        produced_by: "user",
        created_at: "2026-04-21T10:00:00.000Z",
      },
    ],
    ...overrides,
  };
}

describe("project_store", () => {
  beforeEach(() => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
  });

  it("put + get round-trips a project with cards", async () => {
    const p = fixture();
    await putProjectRecord(p);
    const back = await getProjectRecord("prj_1");
    expect(back).toBeDefined();
    expect(back!.name).toBe("Test project");
    expect(back!.cards).toHaveLength(1);
    expect(back!.cards[0].title).toBe("Plan meals for the week");
  });

  it("list returns all stored records", async () => {
    await putProjectRecord(fixture({ id: "a", updated_at: "2026-04-21T10:00:00.000Z" }));
    await putProjectRecord(fixture({ id: "b", updated_at: "2026-04-22T10:00:00.000Z" }));
    const all = await listProjectRecords();
    expect(all.map((p) => p.id).sort()).toEqual(["a", "b"]);
  });

  it("delete removes the record", async () => {
    await putProjectRecord(fixture());
    await deleteProjectRecord("prj_1");
    expect(await getProjectRecord("prj_1")).toBeUndefined();
    expect(await listProjectRecords()).toEqual([]);
  });

  it("put overwrites on same id", async () => {
    await putProjectRecord(fixture({ name: "v1" }));
    await putProjectRecord(fixture({ name: "v2", cards: [] }));
    const back = await getProjectRecord("prj_1");
    expect(back!.name).toBe("v2");
    expect(back!.cards).toEqual([]);
  });
});
