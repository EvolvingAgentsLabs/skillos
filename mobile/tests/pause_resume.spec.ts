/**
 * Integration: runner checkpoints after each step and resumes cleanly.
 *
 * Scenario:
 *   1. Start a cooking-cartridge run with a fake LLM that produces valid
 *      menu + shopping_list + recipes.
 *   2. After the first step-end, trigger an abort to simulate app death.
 *   3. The runner's onStepCommitted hook has already persisted a checkpoint.
 *   4. A second run() with resumeFrom skips menu-planner and executes only
 *      shopping-list-builder + recipe-writer.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CartridgeRegistry } from "../src/lib/cartridge/registry";
import { CartridgeRunner } from "../src/lib/cartridge/runner";
import type { LLMProvider } from "../src/lib/llm/provider";
import { _resetDBForTests, putFile } from "../src/lib/storage/db";
import { loadCheckpoint, saveCheckpoint } from "../src/lib/state/run_checkpoint";

const SEED_DIR = path.resolve(__dirname, "..", "public", "seed");

async function seedCooking(): Promise<void> {
  const mf = JSON.parse(
    await readFile(path.join(SEED_DIR, "manifest.json"), "utf-8"),
  ) as { files: Array<{ path: string; sha1: string }> };
  for (const entry of mf.files) {
    if (!entry.path.startsWith("cartridges/cooking/")) continue;
    const buf = await readFile(path.join(SEED_DIR, entry.path));
    await putFile(entry.path, buf, { sha1: entry.sha1 });
  }
}

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const menuJson = JSON.stringify({
  household_size: 2,
  days: DAYS.map((day) => ({
    day,
    meals: [
      { slot: "breakfast", name: `${day} oats`, prep_minutes: 10 },
      { slot: "lunch", name: `${day} salad`, prep_minutes: 15 },
      { slot: "dinner", name: `${day} stir-fry`, prep_minutes: 30 },
    ],
  })),
});
const shoppingJson = JSON.stringify({
  household_size: 2,
  aisles: {
    produce: [{ item: "apples", quantity: "6 ea" }],
    dairy: [{ item: "milk", quantity: "1 L" }],
    pantry: [{ item: "rice", quantity: "1 kg" }],
    protein: [{ item: "tofu", quantity: "400 g" }],
    other: [{ item: "olive oil", quantity: "1 bottle" }],
  },
});
const recipesJson = JSON.stringify(
  DAYS.map((day) => ({
    name: `${day} stir-fry`,
    day,
    servings: 2,
    total_minutes: 30,
    ingredients: [
      { item: "tofu", quantity: "200g" },
      { item: "rice", quantity: "150g" },
    ],
    steps: ["wash ingredients", "heat oil", "stir-fry until tender"],
  })),
);

function dispatch(body: string): string {
  // `composeTask` emits "Produce exactly these keys: [\"<key>\"]" — unique.
  const m = /Produce exactly these keys:[^\n]*"([\w_]+)"/.exec(body);
  const key = m?.[1];
  if (key === "weekly_menu") {
    return `<final_answer><produces>\n${JSON.stringify({ weekly_menu: JSON.parse(menuJson) })}\n</produces></final_answer>`;
  }
  if (key === "shopping_list") {
    return `<final_answer><produces>\n${JSON.stringify({ shopping_list: JSON.parse(shoppingJson) })}\n</produces></final_answer>`;
  }
  if (key === "recipes") {
    return `<final_answer><produces>\n${JSON.stringify({ recipes: JSON.parse(recipesJson) })}\n</produces></final_answer>`;
  }
  return "<final_answer>ok</final_answer>";
}

function agentKeyOf(body: string): string | undefined {
  return /Produce exactly these keys:[^\n]*"([\w_]+)"/.exec(body)?.[1];
}

function cannedProvider(name: string): {
  llm: LLMProvider;
  calls: Array<{ body: string }>;
} {
  const calls: Array<{ body: string }> = [];
  const llm: LLMProvider = {
    chat: async (messages, opts) => {
      const body = messages.map((m) => m.content).join("\n");
      calls.push({ body });
      const content = dispatch(body);
      opts?.onChunk?.(content);
      return { content, finishReason: "stop" };
    },
    testConnection: async () => ({ ok: true, message: name }),
  };
  return { llm, calls };
}

describe("CartridgeRunner checkpoint + resume", () => {
  beforeEach(async () => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
    await seedCooking();
  });

  it("saves a checkpoint via onStepCommitted after each successful step", async () => {
    const { llm } = cannedProvider("primary");
    const registry = new CartridgeRegistry();
    await registry.init();
    const runner = new CartridgeRunner(registry, llm);

    const commits: Array<{ stepName: string; completed: string[] }> = [];
    await runner.run("cooking", "plan weekly menu", {
      projectId: "prj1",
      onStepCommitted: async ({ stepName, completedSteps, blackboard }) => {
        commits.push({ stepName, completed: [...completedSteps] });
        await saveCheckpoint({
          projectId: "prj1",
          cartridge: "cooking",
          flow: "plan-weekly-menu",
          goal: "plan weekly menu",
          blackboard,
          completedSteps,
        });
      },
    });

    expect(commits.map((c) => c.stepName)).toEqual([
      "menu-planner",
      "shopping-list-builder",
      "recipe-writer",
    ]);
    // Checkpoint landed on disk after the final step as well.
    const ckpt = await loadCheckpoint("prj1");
    expect(ckpt?.completed_steps).toEqual([
      "menu-planner",
      "shopping-list-builder",
      "recipe-writer",
    ]);
  });

  it("resumeFrom skips completed steps and rehydrates the blackboard", async () => {
    // First run — capture the checkpoint after the first step only.
    const { llm: llm1 } = cannedProvider("p1");
    const registry = new CartridgeRegistry();
    await registry.init();
    const runner1 = new CartridgeRunner(registry, llm1);
    let pauseAbort: AbortController | null = null;

    await runner1
      .run("cooking", "plan weekly menu", {
        projectId: "prj1",
        signal: (pauseAbort = new AbortController()).signal,
        onStepCommitted: async ({ stepName, completedSteps, blackboard }) => {
          await saveCheckpoint({
            projectId: "prj1",
            cartridge: "cooking",
            flow: "plan-weekly-menu",
            goal: "plan weekly menu",
            blackboard,
            completedSteps,
          });
          if (stepName === "menu-planner") {
            pauseAbort?.abort();
          }
        },
      })
      .catch(() => {
        /* first run may throw AbortError; that's the point */
      });

    const mid = await loadCheckpoint("prj1");
    expect(mid?.completed_steps).toContain("menu-planner");

    // Second run — resume from the saved checkpoint.
    const { llm: llm2, calls } = cannedProvider("p2");
    const runner2 = new CartridgeRunner(registry, llm2);
    const result = await runner2.run("cooking", "plan weekly menu", {
      projectId: "prj1",
      resumeFrom: {
        completed_steps: mid!.completed_steps,
        blackboard: mid!.blackboard as never,
      },
    });

    // The resumed run should NOT have called the LLM for menu-planner —
    // identify by the unique `produces` directive that composeTask emits.
    const calledForMenuPlanner = calls.some(
      (c) => agentKeyOf(c.body) === "weekly_menu",
    );
    expect(calledForMenuPlanner).toBe(false);

    // It ran shopping-list-builder and recipe-writer.
    const stepNames = result.steps.map((s) => s.agent);
    expect(stepNames).toContain("shopping-list-builder");
    expect(stepNames).toContain("recipe-writer");
    expect(stepNames).not.toContain("menu-planner");

    // Final blackboard carries the menu from the prior run.
    expect(result.blackboard.weekly_menu).toBeDefined();
    const v = result.blackboard.weekly_menu.value as { household_size: number };
    expect(v.household_size).toBe(2);
  });
});
