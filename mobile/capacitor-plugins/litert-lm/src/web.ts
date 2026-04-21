import { WebPlugin } from "@capacitor/core";

import type {
  InitModelOptions,
  InitModelResult,
  GenerateOptions,
  LiteRTPlugin,
} from "./definitions";

/**
 * Web fallback — honest "not available" responses. Code paths that care
 * check `isAvailable()` before calling `initModel` so the app can gracefully
 * route to wllama instead.
 */
export class LiteRTLMWeb extends WebPlugin implements LiteRTPlugin {
  async isAvailable(): Promise<{ available: boolean }> {
    return { available: false };
  }

  async initModel(_: InitModelOptions): Promise<InitModelResult> {
    throw this.unimplemented("LiteRT-LM is native-only (Android).");
  }

  async generate(_: GenerateOptions): Promise<void> {
    throw this.unimplemented("LiteRT-LM is native-only (Android).");
  }

  async cancel(_: { handle: string }): Promise<void> {
    /* noop */
  }

  async unloadModel(_: { handle: string }): Promise<void> {
    /* noop */
  }
}
