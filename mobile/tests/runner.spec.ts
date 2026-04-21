/**
 * Integration test for CartridgeRunner running the real cooking cartridge
 * against a fake LLM that returns canned `<produces>{…}</produces>` blocks.
 * Seeds real SkillOS cartridge files into IndexedDB from public/seed/.
 */

import { readFile } from "node:fs/promises";
import path from "node:path";
import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CartridgeRegistry } from "../src/lib/cartridge/registry";
import { CartridgeRunner, type RunEvent } from "../src/lib/cartridge/runner";
import { LLMClient } from "../src/lib/llm/client";
import { resolveProvider } from "../src/lib/llm/providers";
import { _resetDBForTests, putFile } from "../src/lib/storage/db";

const SEED_DIR = path.resolve(__dirname, "..", "public", "seed");

interface ManifestEntry {
  path: string;
  sha1: string;
}
interface Manifest {
  files: ManifestEntry[];
}

async function seedCooking(): Promise<void> {
  const mf = JSON.parse(
    await readFile(path.join(SEED_DIR, "manifest.json"), "utf-8"),
  ) as Manifest;
  for (const entry of mf.files) {
    if (!entry.path.startsWith("cartridges/cooking/")) continue;
    const buf = await readFile(path.join(SEED_DIR, entry.path));
    await putFile(entry.path, buf, { sha1: entry.sha1 });
  }
}

// ────────────────────────────────────────────────────────────────────────
// Canned agent outputs — shaped to pass the cooking schemas + validators.
// ────────────────────────────────────────────────────────────────────────

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const weeklyMenuJson = JSON.stringify({
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

const shoppingListJson = JSON.stringify({
  household_size: 2,
  aisles: {
    produce: [
      { item: "apples", quantity: "6 ea" },
      { item: "spinach", quantity: "2 bunches" },
    ],
    dairy: [{ item: "milk", quantity: "1 L" }],
    pantry: [
      { item: "rice", quantity: "1 kg" },
      { item: "oats", quantity: "500 g" },
    ],
    protein: [
      { item: "tofu", quantity: "400 g" },
      { item: "chicken", quantity: "600 g" },
    ],
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
    steps: ["wash ingredients", "heat oil in pan", "stir-fry until tender"],
  })),
);

function cannedTurn(key: string, payload: string): string {
  return `<final_answer>\n<produces>\n{"${key}": ${payload}}\n</produces>\n</final_answer>`;
}

// Route canned responses by the `Produce exactly these keys:` directive that
// composeTask injects into the request body — uniquely identifies the agent.
const ROUTES: Array<{ matcher: RegExp; reply: string }> = [
  {
    matcher: /Produce exactly these keys:[^\n]*weekly_menu/,
    reply: cannedTurn("weekly_menu", weeklyMenuJson),
  },
  {
    matcher: /Produce exactly these keys:[^\n]*shopping_list/,
    reply: cannedTurn("shopping_list", shoppingListJson),
  },
  {
    matcher: /Produce exactly these keys:[^\n]*recipes/,
    reply: cannedTurn("recipes", recipesJson),
  },
];

function pickReply(body: string): string {
  for (const r of ROUTES) {
    if (r.matcher.test(body)) return r.reply;
  }
  return "<final_answer>ok</final_answer>";
}

function sseResponse(content: string): Response {
  // LLMClient uses streaming by default; emit the content as a single SSE delta.
  const body = new ReadableStream<Uint8Array>({
    start(ctl) {
      const enc = new TextEncoder();
      ctl.enqueue(
        enc.encode(
          `data: ${JSON.stringify({
            choices: [{ delta: { content }, finish_reason: "stop" }],
            usage: { total_tokens: 100 },
          })}\n\n`,
        ),
      );
      ctl.enqueue(enc.encode("data: [DONE]\n\n"));
      ctl.close();
    },
  });
  return new Response(body, {
    status: 200,
    headers: { "content-type": "text/event-stream" },
  });
}

function mockFetch() {
  return vi.fn(async (_url: string, init: RequestInit) => {
    const body = String(init.body ?? "");
    const reply = pickReply(body);
    return sseResponse(reply);
  });
}

// ────────────────────────────────────────────────────────────────────────

describe("CartridgeRunner.run (cooking cartridge, fake LLM)", () => {
  beforeEach(async () => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
    await seedCooking();
  });

  it("runs plan-weekly-menu flow end-to-end with valid produces blocks", async () => {
    vi.stubGlobal("fetch", mockFetch());

    const registry = new CartridgeRegistry();
    await registry.init();
    const llm = new LLMClient(resolveProvider("openrouter-qwen", { apiKey: "sk-test" }));
    const runner = new CartridgeRunner(registry, llm);

    const events: RunEvent[] = [];
    const result = await runner.run("cooking", "plan weekly menu for my family", {
      onEvent: (e) => events.push(e),
    });

    // Three steps ran in order
    expect(result.steps.map((s) => s.agent)).toEqual([
      "menu-planner",
      "shopping-list-builder",
      "recipe-writer",
    ]);
    // All steps validated
    for (const s of result.steps) {
      expect(s.validated, `step ${s.agent}: ${s.message}`).toBe(true);
    }
    // Blackboard has the three produced keys
    expect(Object.keys(result.blackboard).sort()).toEqual(
      expect.arrayContaining(["recipes", "shopping_list", "user_goal", "weekly_menu"]),
    );
    // Validators ran and passed
    expect(result.validator_messages.length).toBe(2);
    for (const m of result.validator_messages) {
      expect(m.startsWith("ok")).toBe(true);
    }
    expect(result.ok).toBe(true);

    // Events include step-start x3 and run-start/run-end
    expect(events.some((e) => e.type === "run-start")).toBe(true);
    expect(events.filter((e) => e.type === "step-start").length).toBe(3);
    expect(events.filter((e) => e.type === "step-end").length).toBe(3);
    expect(events.some((e) => e.type === "run-end")).toBe(true);
  });

  it("selectFlow picks quick-shopping-list when goal mentions shopping", async () => {
    vi.stubGlobal("fetch", mockFetch());
    const registry = new CartridgeRegistry();
    await registry.init();
    const llm = new LLMClient(resolveProvider("openrouter-qwen", { apiKey: "x" }));
    const runner = new CartridgeRunner(registry, llm);

    const result = await runner.run("cooking", "make a quick shopping list for the week");
    // The shorter 2-step flow ran.
    expect(result.flow).toBe("quick-shopping-list");
    expect(result.steps.map((s) => s.agent)).toEqual([
      "menu-planner",
      "shopping-list-builder",
    ]);
  });

  it("reports a failing step when agent omits <produces>", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => sseResponse("<final_answer>nope</final_answer>")),
    );
    const registry = new CartridgeRegistry();
    await registry.init();
    const llm = new LLMClient(resolveProvider("openrouter-qwen", { apiKey: "x" }));
    const runner = new CartridgeRunner(registry, llm, );

    const result = await runner.run("cooking", "plan weekly menu");
    expect(result.ok).toBe(false);
    expect(result.steps[0].validated).toBe(false);
    expect(result.steps[0].message).toMatch(/produces/);
  });
});
