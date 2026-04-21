import { defineConfig } from "vite";
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
  test: {
    environment: "happy-dom",
    include: ["tests/**/*.spec.ts"],
    setupFiles: ["tests/setup.ts"],
  },
});
