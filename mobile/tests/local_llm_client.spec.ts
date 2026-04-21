import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it } from "vitest";
import { _resetDBForTests, putModelBlob } from "../src/lib/storage/db";
import type {
  BackendGenerateOptions,
  BackendGenerateResult,
  BackendLoadOptions,
  LocalLLMBackend,
} from "../src/lib/llm/local/backend";
import { LocalLLMClient } from "../src/lib/llm/local/local_client";

/**
 * Minimal in-memory backend. Emits tokens by chunking the canned reply
 * through `onToken` so we exercise the streaming path end-to-end.
 */
class FakeBackend implements LocalLLMBackend {
  readonly id = "wllama" as const;
  readonly ready = Promise.resolve();
  loaded = false;
  lastPrompt = "";

  constructor(public cannedReply: string) {}

  async load(_opts: BackendLoadOptions): Promise<void> {
    this.loaded = true;
  }

  async generate(opts: BackendGenerateOptions): Promise<BackendGenerateResult> {
    this.lastPrompt =
      opts.messages
        .map((m) => `${m.role}:${m.content}`)
        .join("|");
    for (const tok of this.cannedReply.match(/.{1,3}/gs) ?? []) {
      opts.onToken?.(tok);
    }
    return { text: this.cannedReply, finishReason: "stop" };
  }

  async unload(): Promise<void> {
    this.loaded = false;
  }
}

describe("LocalLLMClient", () => {
  beforeEach(async () => {
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
    await putModelBlob({
      id: "qwen2.5-1.5b-instruct-q4_k_m",
      blob: new ArrayBuffer(4),
      size: 4,
      downloaded_at: "2026-04-21T00:00:00Z",
      backend: "wllama",
    });
  });

  it("chat() streams canned tokens via onChunk and returns final content", async () => {
    const fake = new FakeBackend("hello world from gemma");
    const client = new LocalLLMClient({
      modelId: "qwen2.5-1.5b-instruct-q4_k_m",
      backend: fake,
    });
    const deltas: string[] = [];
    const result = await client.chat(
      [
        { role: "system", content: "be helpful" },
        { role: "user", content: "hi" },
      ],
      { onChunk: (d) => deltas.push(d) },
    );
    expect(result.content).toBe("hello world from gemma");
    expect(result.finishReason).toBe("stop");
    expect(deltas.join("")).toBe("hello world from gemma");
    expect(fake.loaded).toBe(true);
    expect(fake.lastPrompt).toContain("user:hi");
  });

  it("testConnection reports ok after load succeeds", async () => {
    const fake = new FakeBackend("");
    const client = new LocalLLMClient({
      modelId: "qwen2.5-1.5b-instruct-q4_k_m",
      backend: fake,
    });
    const r = await client.testConnection();
    expect(r.ok).toBe(true);
    expect(r.message).toMatch(/loaded/);
  });

  it("throws a clear error when the model is not installed", async () => {
    // Reset DB to empty, then attempt to chat.
    (globalThis as unknown as { indexedDB: IDBFactory }).indexedDB = new IDBFactory();
    _resetDBForTests();
    const fake = new FakeBackend("ignored");
    const client = new LocalLLMClient({
      modelId: "qwen2.5-1.5b-instruct-q4_k_m",
      backend: fake,
    });
    await expect(client.chat([{ role: "user", content: "hi" }])).rejects.toThrow(
      /not installed/,
    );
  });
});
