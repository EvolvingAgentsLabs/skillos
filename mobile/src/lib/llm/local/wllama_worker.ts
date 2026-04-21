/// <reference lib="webworker" />
/**
 * wllama_worker — Web Worker that hosts the actual `@wllama/wllama` engine.
 *
 * Loaded by `WllamaBackend.ensureWorker()`. Receives `load`, `generate`,
 * `cancel`, `unload` messages; posts `ready`, `loaded`, `token`, `done`,
 * `error`.
 *
 * The wllama package is imported dynamically so Vite emits the WASM alongside
 * this chunk. If the package isn't installed, the worker fails gracefully
 * with a clear error message on the first `load` attempt.
 */

type Inbound =
  | { type: "load"; id: string; modelBlob: ArrayBuffer; singleThread: boolean }
  | {
      type: "generate";
      id: string;
      prompt: string;
      stop: string[];
      maxTokens: number;
      temperature: number;
    }
  | { type: "cancel"; id: string }
  | { type: "unload" };

type Outbound =
  | { type: "ready" }
  | { type: "loaded"; id: string }
  | { type: "error"; id?: string; message: string }
  | { type: "token"; id: string; delta: string }
  | { type: "done"; id: string; text: string; finishReason: string };

import type { Wllama as WllamaClass } from "@wllama/wllama";

let wllama: WllamaClass | null = null;
const activeAborts = new Map<string, AbortController>();

async function ensureWllama(singleThread: boolean): Promise<WllamaClass> {
  if (wllama) return wllama;
  // Dynamic import — keeps the main-thread bundle free of the WASM deps.
  // If `@wllama/wllama` isn't installed, this throws and we surface it via
  // the `error` postMessage to the host.
  const mod = await import("@wllama/wllama");
  // Config paths served from the bundle. Vite copies these via a build rule
  // added to vite.config.ts so `/wllama/...` resolves at runtime.
  const CONFIG = singleThread
    ? ({
        "single-thread/wllama.wasm": "/wllama/single-thread/wllama.wasm",
      } as const)
    : ({
        "single-thread/wllama.wasm": "/wllama/single-thread/wllama.wasm",
        "multi-thread/wllama.wasm": "/wllama/multi-thread/wllama.wasm",
      } as const);
  wllama = new mod.Wllama(CONFIG);
  return wllama;
}

async function handleLoad(msg: Extract<Inbound, { type: "load" }>): Promise<void> {
  try {
    const w = await ensureWllama(msg.singleThread);
    const blob = new Blob([msg.modelBlob]);
    await w.loadModel([blob]);
    post({ type: "loaded", id: msg.id });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    post({ type: "error", id: msg.id, message });
  }
}

async function handleGenerate(msg: Extract<Inbound, { type: "generate" }>): Promise<void> {
  if (!wllama) {
    post({ type: "error", id: msg.id, message: "no model loaded" });
    return;
  }
  const controller = new AbortController();
  activeAborts.set(msg.id, controller);
  try {
    // Tokenize stop strings → numeric token IDs wllama expects.
    let stopTokens: number[] = [];
    if (msg.stop.length > 0) {
      try {
        for (const s of msg.stop) {
          const ids = await wllama.tokenize(s, false);
          stopTokens.push(...ids);
        }
      } catch {
        stopTokens = [];
      }
    }
    const text = await wllama.createCompletion(msg.prompt, {
      nPredict: msg.maxTokens,
      stopTokens,
      sampling: { temp: msg.temperature },
      onNewToken: (_tok, piece, _currentText) => {
        try {
          const delta = new TextDecoder().decode(piece);
          if (delta) post({ type: "token", id: msg.id, delta });
        } catch {
          /* ignore decode errors on stream */
        }
      },
      abortSignal: controller.signal,
    });
    activeAborts.delete(msg.id);
    post({
      type: "done",
      id: msg.id,
      text,
      finishReason: controller.signal.aborted ? "abort" : "stop",
    });
  } catch (err) {
    activeAborts.delete(msg.id);
    const message = err instanceof Error ? err.message : String(err);
    post({ type: "error", id: msg.id, message });
  }
}

function handleCancel(msg: Extract<Inbound, { type: "cancel" }>): void {
  const ctl = activeAborts.get(msg.id);
  if (ctl) ctl.abort();
}

async function handleUnload(): Promise<void> {
  if (wllama) {
    try {
      await wllama.exit();
    } catch {
      /* ignore */
    }
    wllama = null;
  }
  for (const ctl of activeAborts.values()) ctl.abort();
  activeAborts.clear();
}

function post(msg: Outbound): void {
  (self as unknown as { postMessage(data: Outbound): void }).postMessage(msg);
}

self.addEventListener("message", (ev: MessageEvent<Inbound>) => {
  const msg = ev.data;
  if (!msg || typeof msg !== "object") return;
  switch (msg.type) {
    case "load":
      void handleLoad(msg);
      break;
    case "generate":
      void handleGenerate(msg);
      break;
    case "cancel":
      handleCancel(msg);
      break;
    case "unload":
      void handleUnload();
      break;
  }
});

post({ type: "ready" });
