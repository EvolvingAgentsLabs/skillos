/**
 * LiteRTBackend — uses the `@skillos/capacitor-litert-lm` plugin to run
 * `.litertlm` models through Google's on-device runtime.
 *
 * Selected by `pickBackendForModel` only on Android native builds; the web
 * / iOS plugin stubs throw "not implemented" on initModel, which is caught
 * and surfaced as a clear "install the app / use wllama" error upstream.
 *
 * Implementation is dynamically imported so pure-PWA builds don't pay the
 * cost of resolving `@capacitor/core` at startup.
 */

import { formatPrompt } from "./chat_templates";
import type {
  BackendGenerateOptions,
  BackendGenerateResult,
  BackendLoadOptions,
  LocalLLMBackend,
} from "./backend";

interface LiteRTPluginShape {
  isAvailable(): Promise<{ available: boolean }>;
  initModel(opts: { modelPath: string }): Promise<{ handle: string }>;
  generate(opts: {
    handle: string;
    prompt: string;
    maxTokens?: number;
    temperature?: number;
    stop?: string[];
  }): Promise<void>;
  cancel(opts: { handle: string }): Promise<void>;
  unloadModel(opts: { handle: string }): Promise<void>;
  addListener(
    eventName: "token" | "done" | "error",
    listener: (e: Record<string, unknown>) => void,
  ): Promise<{ remove: () => Promise<void> }>;
  removeAllListeners(): Promise<void>;
}

export class LiteRTBackend implements LocalLLMBackend {
  readonly id = "litert" as const;
  readonly ready: Promise<void>;

  private plugin: LiteRTPluginShape | null = null;
  private handle: string | null = null;
  private pluginReady: Promise<LiteRTPluginShape>;

  constructor() {
    this.pluginReady = this.loadPlugin();
    this.ready = this.pluginReady.then(() => undefined);
  }

  private async loadPlugin(): Promise<LiteRTPluginShape> {
    // Plugin is scaffolded under capacitor-plugins/; users install it via
    // `npm install file:./capacitor-plugins/litert-lm` after
    // `npx cap add android`. Route the specifier through a variable +
    // @vite-ignore so neither Vite nor Vitest tries to statically resolve
    // it at build time.
    const pkg = "@skillos/capacitor-litert-lm";
    const mod = await import(/* @vite-ignore */ pkg).catch(() => {
      throw new Error(
        "LiteRT plugin not installed. Install the native app or switch to wllama-local.",
      );
    });
    const plugin = (mod as { LiteRTLM?: LiteRTPluginShape }).LiteRTLM;
    if (!plugin) throw new Error("LiteRT plugin export missing");
    this.plugin = plugin;
    const { available } = await plugin.isAvailable();
    if (!available) {
      throw new Error(
        "LiteRT-LM unavailable on this platform (Android-only). Use wllama.",
      );
    }
    return plugin;
  }

  async load(opts: BackendLoadOptions): Promise<void> {
    const plugin = await this.pluginReady;
    if (!opts.nativePath) {
      throw new Error(
        "LiteRT requires a native file path. Did scripts/export-model-to-cache.ts run?",
      );
    }
    const result = await plugin.initModel({ modelPath: opts.nativePath });
    this.handle = result.handle;
  }

  async generate(opts: BackendGenerateOptions): Promise<BackendGenerateResult> {
    const plugin = await this.pluginReady;
    if (!this.handle) throw new Error("LiteRT: no model loaded");
    const handle = this.handle;
    const { prompt, stop } = formatPrompt(opts.template, opts.messages);
    const combinedStop = [...stop, ...(opts.stop ?? [])];

    let text = "";
    let finishReason = "stop";
    const tokenListener = await plugin.addListener("token", (e) => {
      if (e.handle !== handle) return;
      const delta = String(e.delta ?? "");
      if (!delta) return;
      text += delta;
      opts.onToken?.(delta);
    });

    const donePromise = new Promise<void>((resolve, reject) => {
      let resolved = false;
      const settle = (fn: () => void) => {
        if (resolved) return;
        resolved = true;
        fn();
      };
      plugin
        .addListener("done", (e) => {
          if (e.handle !== handle) return;
          if (typeof e.finishReason === "string") finishReason = e.finishReason;
          if (typeof e.text === "string" && e.text.length > text.length) {
            text = e.text;
          }
          settle(() => resolve());
        })
        .catch(reject);
      plugin
        .addListener("error", (e) => {
          if (e.handle !== handle) return;
          const msg = String(e.message ?? "litert error");
          settle(() => reject(new Error(msg)));
        })
        .catch(reject);
    });

    const abortHandler = async () => {
      await plugin.cancel({ handle }).catch(() => {});
    };
    opts.signal?.addEventListener("abort", abortHandler);

    try {
      await plugin.generate({
        handle,
        prompt,
        maxTokens: opts.maxTokens,
        temperature: opts.temperature,
        stop: combinedStop,
      });
      await donePromise;
    } finally {
      await tokenListener.remove().catch(() => {});
      opts.signal?.removeEventListener("abort", abortHandler);
    }
    return { text, finishReason };
  }

  async unload(): Promise<void> {
    if (!this.plugin || !this.handle) return;
    try {
      await this.plugin.unloadModel({ handle: this.handle });
    } catch {
      /* ignore */
    }
    this.handle = null;
    await this.plugin.removeAllListeners().catch(() => {});
  }
}

/**
 * Returns true when we're on Android native Capacitor with the LiteRT plugin
 * linked and reporting available. Cheap enough to call synchronously during
 * backend selection.
 */
export async function isLiteRTSupported(): Promise<boolean> {
  try {
    // Check Capacitor is native first to avoid loading the plugin on web.
    const cap = (globalThis as unknown as {
      Capacitor?: { isNativePlatform?: () => boolean; getPlatform?: () => string };
    }).Capacitor;
    if (!cap?.isNativePlatform?.()) return false;
    if (cap?.getPlatform?.() !== "android") return false;
    const pkg = "@skillos/capacitor-litert-lm";
    const mod = await import(/* @vite-ignore */ pkg).catch(() => null);
    if (!mod) return false;
    const plugin = (mod as { LiteRTLM?: LiteRTPluginShape }).LiteRTLM;
    if (!plugin) return false;
    const { available } = await plugin.isAvailable();
    return available;
  } catch {
    return false;
  }
}
