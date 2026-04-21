import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it } from "vitest";
import {
  clearCheckpoint,
  listAllCheckpoints,
  loadCheckpoint,
  saveCheckpoint,
} from "../src/lib/state/run_checkpoint";
import type { BlackboardSnapshot } from "../src/lib/cartridge/types";
import { _resetDBForTests } from "../src/lib/storage/db";

function fixtureBlackboard(): BlackboardSnapshot {
  return {
    user_goal: {
      value: "plan weekly menu",
      schema_ref: "",
      produced_by: "user",
      description: "",
      created_at: "2026-04-21T00:00:00Z",
    },
    weekly_menu: {
      value: { household_size: 2, days: [] },
      schema_ref: "weekly_menu.schema.json",
      produced_by: "menu-planner",
      description: "",
      created_at: "2026-04-21T00:01:00Z",
    },
  };
}

describe("run_checkpoint", () => {
  beforeEach(() => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
  });

  it("save + load round-trips the checkpoint shape", async () => {
    await saveCheckpoint({
      projectId: "prj1",
      cartridge: "cooking",
      flow: "plan-weekly-menu",
      goal: "plan weekly menu",
      blackboard: fixtureBlackboard(),
      completedSteps: ["menu-planner"],
      providerId: "wllama-local",
      providerModel: "qwen2.5-1.5b-instruct-q4_k_m",
    });
    const loaded = await loadCheckpoint("prj1");
    expect(loaded).toBeDefined();
    expect(loaded!.project_id).toBe("prj1");
    expect(loaded!.cartridge).toBe("cooking");
    expect(loaded!.flow).toBe("plan-weekly-menu");
    expect(loaded!.completed_steps).toEqual(["menu-planner"]);
    expect(loaded!.provider_id).toBe("wllama-local");
    expect(loaded!.provider_model).toBe("qwen2.5-1.5b-instruct-q4_k_m");
    expect(loaded!.created_at).toBeTruthy();
    expect(loaded!.updated_at).toBeTruthy();
  });

  it("preserves created_at on update but refreshes updated_at", async () => {
    await saveCheckpoint({
      projectId: "prj1",
      cartridge: "cooking",
      flow: "plan-weekly-menu",
      goal: "g",
      blackboard: {},
      completedSteps: [],
    });
    const firstLoad = (await loadCheckpoint("prj1"))!;
    await new Promise((r) => setTimeout(r, 10));
    await saveCheckpoint({
      projectId: "prj1",
      cartridge: "cooking",
      flow: "plan-weekly-menu",
      goal: "g",
      blackboard: {},
      completedSteps: ["menu-planner"],
    });
    const secondLoad = (await loadCheckpoint("prj1"))!;
    expect(secondLoad.created_at).toBe(firstLoad.created_at);
    expect(secondLoad.updated_at >= firstLoad.updated_at).toBe(true);
    expect(secondLoad.completed_steps).toEqual(["menu-planner"]);
  });

  it("clearCheckpoint removes the record", async () => {
    await saveCheckpoint({
      projectId: "prj1",
      cartridge: "c",
      flow: "f",
      goal: "g",
      blackboard: {},
      completedSteps: [],
    });
    await clearCheckpoint("prj1");
    expect(await loadCheckpoint("prj1")).toBeUndefined();
  });

  it("listAllCheckpoints returns every project's record", async () => {
    await saveCheckpoint({
      projectId: "a",
      cartridge: "c",
      flow: "f",
      goal: "g",
      blackboard: {},
      completedSteps: [],
    });
    await saveCheckpoint({
      projectId: "b",
      cartridge: "c",
      flow: "f",
      goal: "g",
      blackboard: {},
      completedSteps: [],
    });
    const all = await listAllCheckpoints();
    expect(all.map((c) => c.project_id).sort()).toEqual(["a", "b"]);
  });
});
