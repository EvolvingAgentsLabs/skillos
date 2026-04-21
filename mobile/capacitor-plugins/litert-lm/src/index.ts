import { registerPlugin } from "@capacitor/core";

import type { LiteRTPlugin } from "./definitions";

/**
 * Registers the native plugin. On Android, Capacitor looks up
 * `com.skillos.litert.LiteRTLMPlugin`. On iOS / web, it returns a proxy
 * that throws "Not implemented" — `LiteRTBackend` detects this via
 * `isAvailable()` and falls through to the wllama backend.
 */
export const LiteRTLM = registerPlugin<LiteRTPlugin>("LiteRTLM", {
  web: () =>
    import("./web").then((m) => new m.LiteRTLMWeb()),
});

export * from "./definitions";
