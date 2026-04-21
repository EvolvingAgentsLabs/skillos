/**
 * WllamaBackend — llama.cpp-in-WASM backend via `@wllama/wllama`.
 *
 * Runs in a dedicated Web Worker so tokenization + inference don't block the
 * Svelte main thread. The backend here is the main-thread façade: it spins up
 * the worker on first `load()`, serializes requests through a simple
 * request-id scheme, and bridges `onToken` streaming via postMessage.
 *
 * The worker script lives at `wllama_worker.ts` and imports the actual
 * `@wllama/wllama` package. We ship the worker via `new URL(..., import.meta.url)`
 * so Vite bundles it as a separate chunk alongside the wllama WASM assets.
 */

import { formatPrompt } from "./chat_templates";
import type {
  BackendGenerateOptions,
  BackendGenerateResult,
  BackendLoadOptions,
  LocalLLMBackend,
} from "./backend";

type WorkerInbound =
  | { type: "ready" }
  | { type: "loaded"; id: string }
  | { type: "error"; id?: string; message: string }
  | { type: "token"; id: string; delta: string }
  | { type: "done"; id: string; text: string; finishReason: string };

type WorkerOutbound =
  | {
      type: "load";
      id: string;
      modelBlob: ArrayBuffer;
      singleThread: boolean;
    }
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

export class WllamaBackend implements LocalLLMBackend {
  readonly id = "wllama" as const;
  readonly ready: Promise<void>;

  private worker: Worker | null = null;
  private workerReady: Promise<void>;
  private workerReadyResolve: (() => void) | null = null;
  private pending = new Map<
    string,
    {
      resolve: (result: BackendGenerateResult) => void;
      reject: (err: Error) => void;
      text: string;
      onToken?: (t: string) => void;
    }
  >();
  private loaded = false;

  constructor() {
    this.workerReady = new Promise<void>((r) => {
      this.workerReadyResolve = r;
    });
    this.ready = this.workerReady;
  }

  private ensureWorker(): Worker {
    if (this.worker) return this.worker;
    // Vite resolves the URL at build time; in tests a shim replaces Worker.
    const w = new Worker(new URL("./wllama_worker.ts", import.meta.url), {
      type: "module",
    });
    w.addEventListener("message", (ev) => this.onMessage(ev));
    w.addEventListener("error", (ev) => {
      for (const p of this.pending.values()) p.reject(new Error(ev.message));
      this.pending.clear();
    });
    this.worker = w;
    return w;
  }

  private onMessage(ev: MessageEvent<WorkerInbound>): void {
    const msg = ev.data;
    if (!msg || typeof msg !== "object") return;
    switch (msg.type) {
      case "ready":
        this.workerReadyResolve?.();
        break;
      case "loaded": {
        const p = this.pending.get(msg.id);
        if (p) {
          this.pending.delete(msg.id);
          p.resolve({ text: "", finishReason: "loaded" });
        }
        this.loaded = true;
        break;
      }
      case "token": {
        const p = this.pending.get(msg.id);
        if (!p) return;
        p.text += msg.delta;
        p.onToken?.(msg.delta);
        break;
      }
      case "done": {
        const p = this.pending.get(msg.id);
        if (!p) return;
        this.pending.delete(msg.id);
        p.resolve({ text: msg.text, finishReason: msg.finishReason });
        break;
      }
      case "error": {
        if (msg.id && this.pending.has(msg.id)) {
          const p = this.pending.get(msg.id)!;
          this.pending.delete(msg.id);
          p.reject(new Error(msg.message));
        }
        break;
      }
    }
  }

  private post(msg: WorkerOutbound, transfer: Transferable[] = []): void {
    const w = this.ensureWorker();
    w.postMessage(msg, transfer);
  }

  async load(opts: BackendLoadOptions): Promise<void> {
    await this.workerReady;
    const id = newId();
    const singleThread = !hasSharedArrayBuffer();
    return new Promise<void>((resolve, reject) => {
      this.pending.set(id, {
        resolve: () => resolve(),
        reject,
        text: "",
      });
      // Pass the model buffer as a transferable to avoid a 1+ GB copy.
      const clone = opts.modelBlob.slice(0);
      this.post({ type: "load", id, modelBlob: clone, singleThread }, [clone]);
      opts.signal?.addEventListener("abort", () => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new Error("load aborted"));
        }
      });
    });
  }

  async generate(opts: BackendGenerateOptions): Promise<BackendGenerateResult> {
    if (!this.loaded) throw new Error("wllama backend: no model loaded");
    await this.workerReady;
    const id = newId();
    const { prompt, stop: tplStop } = formatPrompt(opts.template, opts.messages);
    const stop = [...tplStop, ...(opts.stop ?? [])];
    return new Promise<BackendGenerateResult>((resolve, reject) => {
      this.pending.set(id, {
        resolve,
        reject,
        text: "",
        onToken: opts.onToken,
      });
      this.post({
        type: "generate",
        id,
        prompt,
        stop,
        maxTokens: opts.maxTokens ?? 512,
        temperature: opts.temperature ?? 0.7,
      });
      opts.signal?.addEventListener("abort", () => {
        this.post({ type: "cancel", id });
      });
    });
  }

  async unload(): Promise<void> {
    if (!this.worker) return;
    this.post({ type: "unload" });
    this.worker.terminate();
    this.worker = null;
    this.loaded = false;
    // Reset ready promise for potential reuse.
    this.workerReady = new Promise<void>((r) => {
      this.workerReadyResolve = r;
    });
  }
}

function newId(): string {
  return `w_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function hasSharedArrayBuffer(): boolean {
  return typeof SharedArrayBuffer !== "undefined" && typeof crossOriginIsolated !== "undefined"
    ? crossOriginIsolated
    : typeof SharedArrayBuffer !== "undefined";
}
