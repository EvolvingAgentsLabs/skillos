/**
 * Library rune store — reactive view of installed cartridges + skills, used
 * by `LibraryScreen.svelte` (M12) and the editors (M13+).
 *
 * Keeps a single `CartridgeRegistry` + per-cartridge `SkillRegistry` cached
 * in-memory. Mutations (clone, delete, save) call through to
 * registry_mutations.ts and then refresh the rune.
 */

import { CartridgeRegistry } from "../cartridge/registry";
import {
  cloneCartridge as cloneCartridgeImpl,
  deleteCartridge as deleteCartridgeImpl,
  deleteSkill as deleteSkillImpl,
  saveAgent as saveAgentImpl,
  saveCartridge as saveCartridgeImpl,
  saveSchema as saveSchemaImpl,
  saveSkill as saveSkillImpl,
  type CartridgeFiles,
  type SkillFiles,
} from "../cartridge/registry_mutations";
import type {
  AgentSpec,
  CartridgeManifest,
} from "../cartridge/types";
import { SkillRegistry, type SkillDefinition } from "../skills/skill_loader";

export interface LibraryCartridge {
  name: string;
  manifest: CartridgeManifest;
  agents: AgentSpec[];
  skills: SkillDefinition[];
}

interface LibraryStore {
  loaded: boolean;
  cartridges: LibraryCartridge[];
  error: string | null;
}

export const library = $state<LibraryStore>({
  loaded: false,
  cartridges: [],
  error: null,
});

let registry: CartridgeRegistry | null = null;
const skillRegs = new Map<string, SkillRegistry>();

async function ensureRegistry(): Promise<CartridgeRegistry> {
  if (registry) return registry;
  const r = new CartridgeRegistry();
  await r.init();
  registry = r;
  return r;
}

async function skillRegistryFor(m: CartridgeManifest): Promise<SkillRegistry> {
  const cached = skillRegs.get(m.name);
  if (cached) return cached;
  const reg = new SkillRegistry();
  const dirs: string[] = [];
  if (m.skills_source) dirs.push(m.skills_source);
  dirs.push(`${m.path}/skills`);
  await reg.scan(...dirs);
  skillRegs.set(m.name, reg);
  return reg;
}

async function hydrate(): Promise<void> {
  const reg = await ensureRegistry();
  const cartridges: LibraryCartridge[] = [];
  for (const m of reg.list()) {
    const agents: AgentSpec[] = [];
    // Best-effort: list every `agents/*.md` and load each spec.
    const { listFiles } = await import("../storage/db");
    const agentPaths = await listFiles(`${m.path}/agents/`);
    const agentNames = agentPaths
      .filter((p) => p.endsWith(".md"))
      .map((p) => p.slice(`${m.path}/agents/`.length, -3));
    for (const an of agentNames) {
      const a = await reg.loadAgent(m.name, an);
      if (a) agents.push(a);
    }
    const skillReg = await skillRegistryFor(m);
    cartridges.push({
      name: m.name,
      manifest: m,
      agents,
      skills: skillReg.list(),
    });
  }
  library.cartridges = cartridges.sort((a, b) => a.name.localeCompare(b.name));
  library.loaded = true;
  library.error = null;
}

export async function loadLibrary(): Promise<void> {
  try {
    await hydrate();
  } catch (err) {
    library.error = err instanceof Error ? err.message : String(err);
    library.loaded = true;
  }
}

export async function refreshLibrary(): Promise<void> {
  await hydrate();
}

// ─── Cartridge mutations ───────────────────────────────────────────────

export async function cloneCartridge(src: string, dst: string): Promise<void> {
  const reg = await ensureRegistry();
  await cloneCartridgeImpl(reg, src, dst);
  skillRegs.delete(dst);
  await hydrate();
}

export async function deleteCartridge(name: string): Promise<void> {
  const reg = await ensureRegistry();
  await deleteCartridgeImpl(reg, name);
  skillRegs.delete(name);
  await hydrate();
}

export async function saveCartridge(
  name: string,
  files: CartridgeFiles,
): Promise<void> {
  const reg = await ensureRegistry();
  await saveCartridgeImpl(reg, name, files);
  skillRegs.delete(name);
  await hydrate();
}

export async function saveAgent(
  cartridge: string,
  agentName: string,
  frontmatter: Record<string, unknown>,
  body: string,
): Promise<void> {
  const reg = await ensureRegistry();
  await saveAgentImpl(reg, cartridge, agentName, frontmatter, body);
  await hydrate();
}

export async function saveSchema(
  cartridge: string,
  ref: string,
  schema: object,
): Promise<void> {
  const reg = await ensureRegistry();
  await saveSchemaImpl(reg, cartridge, ref, schema);
  await hydrate();
}

// ─── Skill mutations ───────────────────────────────────────────────────

export async function saveSkill(
  cartridge: string,
  skillName: string,
  files: SkillFiles,
): Promise<void> {
  const reg = await ensureRegistry();
  const manifest = reg.get(cartridge);
  if (!manifest) throw new Error(`unknown cartridge: ${cartridge}`);
  const dir = manifest.skills_source || `${manifest.path}/skills`;
  const skillReg = await skillRegistryFor(manifest);
  await saveSkillImpl(skillReg, dir, skillName, files);
  await hydrate();
}

export async function deleteSkill(
  cartridge: string,
  skillName: string,
): Promise<void> {
  const reg = await ensureRegistry();
  const manifest = reg.get(cartridge);
  if (!manifest) throw new Error(`unknown cartridge: ${cartridge}`);
  const dir = manifest.skills_source || `${manifest.path}/skills`;
  const skillReg = await skillRegistryFor(manifest);
  await deleteSkillImpl(skillReg, dir, skillName);
  await hydrate();
}

// Expose the registry for the M13 editors to lint against live schemas.
export async function getRegistry(): Promise<CartridgeRegistry> {
  return ensureRegistry();
}
