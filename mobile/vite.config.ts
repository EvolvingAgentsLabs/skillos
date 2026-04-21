/// <reference types="vitest" />
import { defineConfig } from "vitest/config";
import { svelte } from "@sveltejs/vite-plugin-svelte";

export default defineConfig({
  plugins: [svelte()],
  resolve: {
    alias: {
      $lib: "/src/lib",
      $components: "/src/components",
    },
  },
  server: {
    host: true,
    port: 5173,
  },
  worker: {
    // ES-module workers so Vite can code-split dynamic imports (e.g. wllama
    // is dynamically imported inside wllama_worker.ts).
    format: "es",
  },
  build: {
    rollupOptions: {
      // The LiteRT Capacitor plugin (M10) is only installed under
      // capacitor-plugins/ and lands in node_modules after users run
      // `npm install file:./capacitor-plugins/litert-lm`. Externalize so the
      // dynamic import falls through to the runtime "plugin not installed"
      // error path with graceful degradation.
      external: [/^@skillos\/capacitor-litert-lm(\/.*)?$/],
    },
  },
  test: {
    environment: "happy-dom",
    include: ["tests/**/*.spec.ts"],
    setupFiles: ["./tests/setup.ts"],
  },
});
