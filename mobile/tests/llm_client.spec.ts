import { afterEach, describe, expect, it, vi } from "vitest";
import { LLMClient } from "../src/lib/llm/client";
import { resolveProvider } from "../src/lib/llm/providers";

function mkClient() {
  const provider = resolveProvider("openrouter-qwen", { apiKey: "sk-test" });
  return new LLMClient(provider);
}

function sseBody(chunks: string[]): ReadableStream<Uint8Array> {
  const enc = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(enc.encode(chunk));
      }
      controller.close();
    },
  });
}

describe("LLMClient.chat (non-streaming)", () => {
  afterEach(() => vi.restoreAllMocks());

  it("POSTs to /chat/completions and returns the assistant content", async () => {
    const fetchMock = vi.fn(
      async (_url: string, _init: RequestInit) =>
        new Response(
          JSON.stringify({
            choices: [{ message: { content: "hello world" }, finish_reason: "stop" }],
            usage: { prompt_tokens: 5, completion_tokens: 2, total_tokens: 7 },
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        ),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = mkClient();
    const r = await client.chat([{ role: "user", content: "hi" }], { stream: false });

    expect(r.content).toBe("hello world");
    expect(r.finishReason).toBe("stop");
    expect(r.usage?.total_tokens).toBe(7);
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("https://openrouter.ai/api/v1/chat/completions");
    const headers = init.headers as Record<string, string>;
    expect(headers.authorization).toBe("Bearer sk-test");
    expect(headers["HTTP-Referer"]).toBe("https://skillos.dev");
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body as string);
    expect(body.model).toBe("qwen/qwen3.6-plus:free");
    expect(body.stream).toBe(false);
    expect(body.messages).toEqual([{ role: "user", content: "hi" }]);
  });

  it("throws on non-2xx", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response("boom", { status: 500 })),
    );
    const client = mkClient();
    await expect(client.chat([{ role: "user", content: "x" }], { stream: false })).rejects.toThrow(
      /LLM 500/,
    );
  });
});

describe("LLMClient.chat (streaming SSE)", () => {
  afterEach(() => vi.restoreAllMocks());

  it("assembles deltas and invokes onChunk for each piece", async () => {
    const chunks = [
      'data: {"choices":[{"delta":{"content":"hel"}}]}\n\n',
      'data: {"choices":[{"delta":{"content":"lo "}}]}\n\n',
      'data: {"choices":[{"delta":{"content":"world"},"finish_reason":"stop"}],"usage":{"prompt_tokens":1,"completion_tokens":3,"total_tokens":4}}\n\n',
      "data: [DONE]\n\n",
    ];
    const fetchMock = vi.fn(
      async () =>
        new Response(sseBody(chunks), {
          status: 200,
          headers: { "content-type": "text/event-stream" },
        }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const deltas: string[] = [];
    const client = mkClient();
    const r = await client.chat([{ role: "user", content: "hi" }], {
      stream: true,
      onChunk: (d) => deltas.push(d),
    });

    expect(r.content).toBe("hello world");
    expect(deltas).toEqual(["hel", "lo ", "world"]);
    expect(r.usage?.total_tokens).toBe(4);
    expect(r.finishReason).toBe("stop");
  });

  it("handles chunks split across multiple reads", async () => {
    // One SSE event, but split mid-frame over three reads.
    const chunks = [
      'data: {"choices":[{"delta":{"cont',
      'ent":"pie"}}]}\n',
      '\ndata: [DONE]\n\n',
    ];
    const fetchMock = vi.fn(
      async () =>
        new Response(sseBody(chunks), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const client = mkClient();
    const r = await client.chat([{ role: "user", content: "x" }]);
    expect(r.content).toBe("pie");
  });
});
