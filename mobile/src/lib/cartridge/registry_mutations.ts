/**
 * CartridgeRegistry mutations — CRUD helpers that let the Library UI
 * (M12+) create, fork, edit, and delete cartridges / agents / skills.
 *
 * All writes funnel through `putFile` (from storage/db.ts) so Export-to-Files
 * (M7) automatically persists user edits out to `Documents/SkillOS/` on
 * Capacitor builds.
 *
 * Each mutation invalidates the relevant registry cache entry so the next
 * `registry.list()` or `registry.loadAgent()` reflects the change without
 * a full re-init.
 */

import yaml from "js-yaml";
import {
  deleteFile,
  getDB,
  getFileText,
  listFiles,
  putFile,
} from "../storage/db";
import type { CartridgeRegistry } from "./registry";
import type { SkillRegistry } from "../skills/skill_loader";

// ────────────────────────────────────────────────────────────────────────
// Cartridge / agent / schema writes
// ────────────────────────────────────────────────────────────────────────

export interface CartridgeFiles {
  /** `cartridges/<name>/cartridge.yaml` body. */
  manifestYaml: string;
  /** Optional `router.md` body. */
  routerMd?: string;
  /** Agents — key = `<agentName>.md` (no path prefix). */
  agents: Record<string, string>;
  /** Schemas — key = `<ref>.schema.json` (no path prefix). */
  schemas?: Record<string, string>;
  /** Validator source — key = `<name>.ts|.py`. Usually optional on mobile. */
  validators?: Record<string, string>;
  /** Optional extra files under `cartridges/<name>/<rel>`. */
  extras?: Record<string, string>;
}

function cartridgePrefix(name: string): string {
  return `cartridges/${name}/`;
}

async function writeCartridgeFiles(
  name: string,
  files: CartridgeFiles,
): Promise<string[]> {
  const base = cartridgePrefix(name);
  const written: string[] = [];
  await putFile(`${base}cartridge.yaml`, files.manifestYaml, {
    user_edited: true,
  });
  written.push(`${base}cartridge.yaml`);
  if (files.routerMd) {
    await putFile(`${base}router.md`, files.routerMd, { user_edited: true });
    written.push(`${base}router.md`);
  }
  for (const [agentName, body] of Object.entries(files.agents)) {
    const fname = agentName.endsWith(".md") ? agentName : `${agentName}.md`;
    await putFile(`${base}agents/${fname}`, body, { user_edited: true });
    written.push(`${base}agents/${fname}`);
  }
  for (const [ref, body] of Object.entries(files.schemas ?? {})) {
    const fname = ref.endsWith(".json") ? ref : `${ref}.schema.json`;
    await putFile(`${base}schemas/${fname}`, body, { user_edited: true });
    written.push(`${base}schemas/${fname}`);
  }
  for (const [v, body] of Object.entries(files.validators ?? {})) {
    await putFile(`${base}validators/${v}`, body, { user_edited: true });
    written.push(`${base}validators/${v}`);
  }
  for (const [rel, body] of Object.entries(files.extras ?? {})) {
    await putFile(`${base}${rel}`, body, { user_edited: true });
    written.push(`${base}${rel}`);
  }
  return written;
}

export async function saveCartridge(
  registry: CartridgeRegistry,
  name: string,
  files: CartridgeFiles,
): Promise<{ written: string[] }> {
  const written = await writeCartridgeFiles(name, files);
  await registry.reloadCartridge(name);
  return { written };
}

export async function saveAgent(
  registry: CartridgeRegistry,
  cartridge: string,
  agentName: string,
  frontmatter: Record<string, unknown>,
  body: string,
): Promise<void> {
  const fm = yaml.dump(frontmatter, { sortKeys: false, noRefs: true });
  const md = `---\n${fm.trimEnd()}\n---\n\n${body.replace(/^\s+/, "")}`;
  const path = `cartridges/${cartridge}/agents/${agentName.endsWith(".md") ? agentName : agentName + ".md"}`;
  await putFile(path, md, { user_edited: true });
  registry.invalidateAgent(cartridge, agentName.replace(/\.md$/, ""));
}

export async function saveSchema(
  registry: CartridgeRegistry,
  cartridge: string,
  ref: string,
  schema: object,
): Promise<void> {
  const body = JSON.stringify(schema, null, 2);
  const fname = ref.endsWith(".json") ? ref : `${ref}.schema.json`;
  const path = `cartridges/${cartridge}/schemas/${fname}`;
  await putFile(path, body, { user_edited: true });
  registry.invalidateValidator(cartridge);
}

/**
 * Clone every file under `cartridges/<src>/` into `cartridges/<dst>/`, then
 * reload the destination manifest so it appears in `registry.list()` with
 * its new name.
 */
export async function cloneCartridge(
  registry: CartridgeRegistry,
  src: string,
  dst: string,
): Promise<{ copied: number }> {
  if (!registry.get(src)) throw new Error(`source cartridge not found: ${src}`);
  if (registry.get(dst)) throw new Error(`destination exists: ${dst}`);
  const srcBase = cartridgePrefix(src);
  const dstBase = cartridgePrefix(dst);
  const paths = await listFiles(srcBase);
  let copied = 0;
  for (const path of paths) {
    const body = await getFileText(path);
    if (body === undefined) continue;
    const relative = path.slice(srcBase.length);
    const dstPath = `${dstBase}${relative}`;
    let content = body;
    // Rewrite the manifest's `name:` field so the cloned cartridge has the
    // new id when loaded.
    if (relative === "cartridge.yaml") {
      content = body.replace(/^name:\s*.+$/m, `name: ${dst}`);
    }
    await putFile(dstPath, content, { user_edited: true });
    copied++;
  }
  await registry.reloadCartridge(dst);
  return { copied };
}

export async function deleteCartridge(
  registry: CartridgeRegistry,
  name: string,
): Promise<{ removed: number }> {
  const base = cartridgePrefix(name);
  const paths = await listFiles(base);
  const db = await getDB();
  const tx = db.transaction("files", "readwrite");
  for (const p of paths) {
    await tx.store.delete(p);
  }
  await tx.done;
  registry.forget(name);
  return { removed: paths.length };
}

// ────────────────────────────────────────────────────────────────────────
// Gallery skill writes
// ────────────────────────────────────────────────────────────────────────

export interface SkillFiles {
  /** `SKILL.md` body including YAML frontmatter. */
  skillMd: string;
  /** `scripts/index.js` body. Optional for text-only skills. */
  indexJs?: string;
  /** `scripts/index.html` body. Optional; defaults to a minimal shell. */
  indexHtml?: string;
  /** Additional assets — key is relative to the skill dir. */
  extras?: Record<string, string>;
}

const DEFAULT_INDEX_HTML = `<!doctype html><html><body><script src="index.js"></script></body></html>`;

export async function saveSkill(
  skillRegistry: SkillRegistry,
  skillsSourceDir: string,
  skillName: string,
  files: SkillFiles,
): Promise<string[]> {
  const dir = skillsSourceDir.endsWith("/")
    ? `${skillsSourceDir}${skillName}`
    : `${skillsSourceDir}/${skillName}`;
  const written: string[] = [];
  await putFile(`${dir}/SKILL.md`, files.skillMd, { user_edited: true });
  written.push(`${dir}/SKILL.md`);
  if (files.indexJs !== undefined) {
    await putFile(`${dir}/scripts/index.js`, files.indexJs, { user_edited: true });
    written.push(`${dir}/scripts/index.js`);
  }
  const html = files.indexHtml ?? DEFAULT_INDEX_HTML;
  await putFile(`${dir}/scripts/index.html`, html, { user_edited: true });
  written.push(`${dir}/scripts/index.html`);
  for (const [rel, body] of Object.entries(files.extras ?? {})) {
    await putFile(`${dir}/${rel}`, body, { user_edited: true });
    written.push(`${dir}/${rel}`);
  }
  await skillRegistry.reloadSkill(dir);
  return written;
}

export async function deleteSkill(
  skillRegistry: SkillRegistry,
  skillsSourceDir: string,
  skillName: string,
): Promise<{ removed: number }> {
  const dir = skillsSourceDir.endsWith("/")
    ? `${skillsSourceDir}${skillName}`
    : `${skillsSourceDir}/${skillName}`;
  const paths = await listFiles(`${dir}/`);
  const db = await getDB();
  const tx = db.transaction("files", "readwrite");
  for (const p of paths) await tx.store.delete(p);
  await tx.done;
  skillRegistry.forget(skillName);
  return { removed: paths.length };
}

// Re-export for test convenience
export { deleteFile };
