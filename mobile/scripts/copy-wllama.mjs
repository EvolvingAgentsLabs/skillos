#!/usr/bin/env node
/**
 * Copy wllama WASM artifacts from node_modules into mobile/public/wllama/
 * so the worker's `new Wllama({…})` config can reference `/wllama/*` at
 * runtime. Skips silently when @wllama/wllama isn't installed — lets the
 * app build in environments where on-device is a no-op.
 */

import { promises as fs } from "node:fs";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const MOBILE_ROOT = path.resolve(__dirname, "..");
const WLLAMA_SRC = path.join(MOBILE_ROOT, "node_modules", "@wllama", "wllama", "esm");
const DEST = path.join(MOBILE_ROOT, "public", "wllama");

const TARGETS = [
  ["single-thread/wllama.wasm", "single-thread/wllama.wasm"],
  ["multi-thread/wllama.wasm", "multi-thread/wllama.wasm"],
];

async function main() {
  if (!existsSync(WLLAMA_SRC)) {
    console.log("[wllama-copy] @wllama/wllama not installed — skipping");
    return;
  }
  let copied = 0;
  for (const [src, dst] of TARGETS) {
    const srcAbs = path.join(WLLAMA_SRC, src);
    const dstAbs = path.join(DEST, dst);
    if (!existsSync(srcAbs)) continue;
    await fs.mkdir(path.dirname(dstAbs), { recursive: true });
    await fs.copyFile(srcAbs, dstAbs);
    copied++;
  }
  console.log(`[wllama-copy] copied ${copied} wasm files → public/wllama/`);
}

main().catch((err) => {
  console.error("[wllama-copy] failed:", err);
  process.exit(1);
});
