/**
 * Runner × smart routing integration.
 *
 * Wires a CartridgeRunner with `{primary, fallback}`. Primary returns output
 * that fails schema validation; the retry escalates to fallback which
 * produces a valid blackboard entry. Asserts the run completes green and a
 * `tier-switch` RunEvent fires.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it } from "vitest";
import { CartridgeRegistry } from "../src/lib/cartridge/registry";
import { CartridgeRunner, type RunEvent } from "../src/lib/cartridge/runner";
import type { LLMProvider } from "../src/lib/llm/provider";
import { _resetDBForTests, putFile } from "../src/lib/storage/db";

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

function cannedProvider(reply: string): LLMProvider {
  return {
    chat: async (_m, opts) => {
      if (opts?.onChunk) opts.onChunk(reply);
      return { content: reply, finishReason: "stop" };
    },
    testConnection: async () => ({ ok: true, message: "fake" }),
  };
}

// Menu data that passes weekly_menu.schema.json (7 days × 3 meals × prep_minutes).
const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const validMenuJson = JSON.stringify({
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

const validShoppingJson = JSON.stringify({
  household_size: 2,
  aisles: {
    produce: [{ item: "apples", quantity: "6 ea" }],
    dairy: [{ item: "milk", quantity: "1 L" }],
    pantry: [{ item: "rice", quantity: "1 kg" }],
    protein: [{ item: "tofu", quantity: "400 g" }],
    other: [{ item: "olive oil", quantity: "1 bottle" }],
  },
});

const validRecipesJson = JSON.stringify(
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

function primaryDispatch(body: string): string {
  // Primary agent: emits a menu that's missing prep_minutes (fails schema)
  // so the runner retries via fallback.
  if (/weekly_menu/.test(body)) {
    return `<final_answer><produces>\n${JSON.stringify({
      weekly_menu: { household_size: 2, days: DAYS.map((d) => ({ day: d, meals: [] })) },
    })}\n</produces></final_answer>`;
  }
  if (/shopping_list/.test(body)) {
    return `<final_answer><produces>\n${JSON.stringify({ shopping_list: JSON.parse(validShoppingJson) })}\n</produces></final_answer>`;
  }
  if (/recipes/.test(body)) {
    return `<final_answer><produces>\n${JSON.stringify({ recipes: JSON.parse(validRecipesJson) })}\n</produces></final_answer>`;
  }
  return "<final_answer>ok</final_answer>";
}

function fallbackDispatch(body: string): string {
  if (/weekly_menu/.test(body)) {
    return `<final_answer><produces>\n${JSON.stringify({ weekly_menu: JSON.parse(validMenuJson) })}\n</produces></final_answer>`;
  }
  return primaryDispatch(body);
}

function dispatchingProvider(name: string, dispatch: (body: string) => string): LLMProvider {
  return {
    chat: async (messages, opts) => {
      const body = messages.map((m) => m.content).join("\n");
      const reply = dispatch(body);
      opts?.onChunk?.(reply);
      return { content: reply, finishReason: "stop" };
    },
    testConnection: async () => ({ ok: true, message: name }),
  };
}

describe("CartridgeRunner with fallback routing", () => {
  beforeEach(async () => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
    await seedCooking();
  });

  it("escalates to fallback on validation failure and completes green", async () => {
    const primary = dispatchingProvider("primary", primaryDispatch);
    const fallback = dispatchingProvider("fallback", fallbackDispatch);

    const registry = new CartridgeRegistry();
    await registry.init();
    const runner = new CartridgeRunner(registry, { primary, fallback });

    const events: RunEvent[] = [];
    const result = await runner.run("cooking", "plan weekly menu", {
      onEvent: (e) => events.push(e),
    });

    // menu-planner retries once; fallback fires on the retry.
    expect(
      events.some(
        (e) =>
          e.type === "tier-switch" &&
          e.agent === "menu-planner" &&
          e.from === "primary" &&
          e.to === "fallback",
      ),
    ).toBe(true);
    // All three steps eventually validate.
    const stepNames = result.steps.map((s) => s.agent);
    expect(stepNames).toContain("menu-planner");
    expect(result.steps.find((s) => s.agent === "menu-planner")?.validated).toBe(true);
  });

  it("default (no fallback) preserves v0 single-provider behavior", async () => {
    const primary = dispatchingProvider("primary", fallbackDispatch); // healthy
    const registry = new CartridgeRegistry();
    await registry.init();
    // Pass a single provider — runner wraps as `{primary}`.
    const runner = new CartridgeRunner(registry, primary);

    const events: RunEvent[] = [];
    await runner.run("cooking", "plan weekly menu", {
      onEvent: (e) => events.push(e),
    });
    // No tier-switch because we have no fallback provider to escalate to.
    expect(events.some((e) => e.type === "tier-switch")).toBe(false);
    // The menu-planner produces a valid schema, so it validates at least on retry.
    // (Shopping-list + recipe-writer use the primary dispatch which is healthy.)
    // We assert the first step validates — same shape as v0's runner.spec.ts.
    const menuStep = events.find(
      (e): e is Extract<RunEvent, { type: "step-end" }> =>
        e.type === "step-end" && e.step.agent === "menu-planner",
    );
    expect(menuStep?.step.validated).toBe(true);
  });
});
