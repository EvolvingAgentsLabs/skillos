#!/usr/bin/env node
/**
 * seed-build.mjs
 *
 * Walks the SkillOS repo and copies cartridges + selected projects + SmartMemory.md
 * into mobile/public/seed/, writing mobile/public/seed/manifest.json so that
 * storage/seed.ts can fetch each asset on first boot and populate IndexedDB.
 *
 * Usage:
 *   node scripts/seed-build.mjs
 *   node scripts/seed-build.mjs --projects=Project_aorta,Project_echo_q
 *   node scripts/seed-build.mjs --all-projects
 */

import { createHash } from "node:crypto";
import { promises as fs } from "node:fs";
import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const MOBILE_ROOT = path.resolve(__dirname, "..");
const SKILLOS_ROOT = path.resolve(MOBILE_ROOT, "..");
const SEED_OUT = path.join(MOBILE_ROOT, "public", "seed");

const IGNORE_DIRS = new Set([
  "__pycache__",
  ".pytest_cache",
  ".mypy_cache",
  "node_modules",
  ".git",
  ".venv",
  "venv",
  "dist",
]);
const IGNORE_FILES = new Set([".DS_Store", "Thumbs.db"]);

function parseArgs(argv) {
  const out = { projects: ["Project_aorta"], allProjects: false };
  for (const a of argv.slice(2)) {
    if (a === "--all-projects") out.allProjects = true;
    else if (a.startsWith("--projects=")) out.projects = a.slice("--projects=".length).split(",").filter(Boolean);
  }
  return out;
}

async function* walk(dir, rel = "") {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const ent of entries) {
    if (ent.isDirectory()) {
      if (IGNORE_DIRS.has(ent.name)) continue;
      yield* walk(path.join(dir, ent.name), path.posix.join(rel, ent.name));
    } else if (ent.isFile()) {
      if (IGNORE_FILES.has(ent.name)) continue;
      yield { abs: path.join(dir, ent.name), rel: path.posix.join(rel, ent.name) };
    }
  }
}

async function copyFile(src, destRel, manifest) {
  const buf = await fs.readFile(src);
  const dest = path.join(SEED_OUT, destRel);
  await fs.mkdir(path.dirname(dest), { recursive: true });
  await fs.writeFile(dest, buf);
  const sha1 = createHash("sha1").update(buf).digest("hex");
  manifest.push({ path: destRel.replaceAll("\\", "/"), sha1, size: buf.length });
}

async function seedTree(srcAbs, destRelRoot, manifest) {
  if (!existsSync(srcAbs)) return 0;
  let n = 0;
  for await (const { abs, rel } of walk(srcAbs)) {
    const destRel = path.posix.join(destRelRoot, rel);
    await copyFile(abs, destRel, manifest);
    n++;
  }
  return n;
}

async function main() {
  const args = parseArgs(process.argv);

  if (existsSync(SEED_OUT)) {
    await fs.rm(SEED_OUT, { recursive: true, force: true });
  }
  await fs.mkdir(SEED_OUT, { recursive: true });

  const manifest = [];
  const stats = { cartridges: 0, projects: 0, system: 0 };

  // 1. All cartridges
  const cartridgesRoot = path.join(SKILLOS_ROOT, "cartridges");
  stats.cartridges = await seedTree(cartridgesRoot, "cartridges", manifest);

  // 2. Projects (default: Project_aorta only; --all-projects copies everything)
  const projectsRoot = path.join(SKILLOS_ROOT, "projects");
  if (existsSync(projectsRoot)) {
    const projectNames = args.allProjects
      ? (await fs.readdir(projectsRoot, { withFileTypes: true }))
          .filter((d) => d.isDirectory() && !IGNORE_DIRS.has(d.name))
          .map((d) => d.name)
      : args.projects;
    for (const name of projectNames) {
      const abs = path.join(projectsRoot, name);
      if (!existsSync(abs)) {
        console.warn(`[seed] project not found, skipping: ${name}`);
        continue;
      }
      stats.projects += await seedTree(abs, path.posix.join("projects", name), manifest);
    }
  }

  // 3. SmartMemory.md
  const smartMemoryPath = path.join(SKILLOS_ROOT, "system", "SmartMemory.md");
  if (existsSync(smartMemoryPath)) {
    await copyFile(smartMemoryPath, "system/SmartMemory.md", manifest);
    stats.system++;
  }

  // 4. Write manifest
  const manifestPayload = {
    seed_version: new Date().toISOString(),
    source_root: "skillos",
    file_count: manifest.length,
    files: manifest.sort((a, b) => a.path.localeCompare(b.path)),
  };
  await fs.writeFile(
    path.join(SEED_OUT, "manifest.json"),
    JSON.stringify(manifestPayload, null, 2),
    "utf-8",
  );

  const totalBytes = manifest.reduce((s, f) => s + f.size, 0);
  console.log(
    `[seed] wrote ${manifest.length} files (${(totalBytes / 1024 / 1024).toFixed(2)} MB) → public/seed/\n` +
      `       cartridges=${stats.cartridges}  projects=${stats.projects}  system=${stats.system}`,
  );
}

main().catch((err) => {
  console.error("[seed] failed:", err);
  process.exit(1);
});
