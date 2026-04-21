import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it } from "vitest";
import { buildProvider } from "../src/lib/llm/build_provider";
import { LLMClient } from "../src/lib/llm/client";
import { LocalLLMClient } from "../src/lib/llm/local/local_client";
import { _resetDBForTests } from "../src/lib/storage/db";

describe("buildProvider", () => {
  beforeEach(() => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
  });

  it("returns LLMClient for cloud provider ids", async () => {
    const p = await buildProvider({ providerId: "openrouter-qwen", apiKey: "sk-x" });
    expect(p).toBeInstanceOf(LLMClient);
  });

  it("returns LocalLLMClient for wllama-local", async () => {
    const p = await buildProvider({
      providerId: "wllama-local",
      model: "qwen2.5-1.5b-instruct-q4_k_m",
    });
    expect(p).toBeInstanceOf(LocalLLMClient);
  });

  it("defaults to a catalog model when local provider has no model field", async () => {
    const p = await buildProvider({ providerId: "wllama-local" });
    expect(p).toBeInstanceOf(LocalLLMClient);
  });

  it("throws on unknown local model id", async () => {
    await expect(
      buildProvider({ providerId: "wllama-local", model: "does-not-exist" }),
    ).rejects.toThrow(/unknown model/);
  });
});
