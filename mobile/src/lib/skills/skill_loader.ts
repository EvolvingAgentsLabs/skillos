/**
 * SkillRegistry — TS port of
 * C:\evolvingagents\skillos\experiments\gemma4-skills\skill_loader.py.
 *
 * Scans the seeded IndexedDB `files` store for Gallery-format skills at the
 * paths configured by each cartridge's `skills_source`. Parses SKILL.md
 * frontmatter into a typed SkillDefinition and stores the resolved paths of
 * scripts/index.html and scripts/index.js.
 */

import yaml from "js-yaml";
import { getFileText, listFiles } from "../storage/db";

export interface SkillDefinition {
  name: string;
  description: string;
  instructions: string;
  require_secret: boolean;
  require_secret_description: string;
  homepage: string;
  /** posix-style IndexedDB path key to the skill folder. */
  skill_dir: string;
  /** scripts/index.html path (may be empty). */
  script_path: string;
  /** scripts/index.js path, or the html path if no dedicated .js file. */
  js_path: string;
  /** "node" (default) or "browser" — mobile only supports "node". */
  runtime: "node" | "browser";
}

function parseSkillMd(content: string): { frontmatter: Record<string, unknown>; body: string } {
  // SKILL.md files shipped from the repo use CRLF on Windows; match both.
  const m = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/.exec(content);
  if (!m) return { frontmatter: {}, body: content };
  const fm = yaml.load(m[1]);
  return {
    frontmatter:
      fm && typeof fm === "object" && !Array.isArray(fm) ? (fm as Record<string, unknown>) : {},
    body: m[2].trim(),
  };
}

function getMetadata(fm: Record<string, unknown>): Record<string, unknown> {
  const md = fm.metadata;
  if (md && typeof md === "object" && !Array.isArray(md)) return md as Record<string, unknown>;
  return {};
}

export async function loadSkill(skillDir: string): Promise<SkillDefinition | undefined> {
  const normalized = skillDir.replace(/\/+$/, "");
  const skillMdPath = `${normalized}/SKILL.md`;
  const content = await getFileText(skillMdPath);
  if (content === undefined) return undefined;
  const { frontmatter, body } = parseSkillMd(content);
  const metadata = getMetadata(frontmatter);

  const scriptsPrefix = `${normalized}/scripts/`;
  const scriptPaths = await listFiles(scriptsPrefix);
  const indexHtml = scriptPaths.find((p) => p === `${scriptsPrefix}index.html`) ?? "";
  const indexJs = scriptPaths.find((p) => p === `${scriptsPrefix}index.js`) ?? "";
  const scriptPath = indexHtml;
  const jsPath = indexJs || indexHtml;

  const folderName = normalized.split("/").pop() ?? "skill";
  const runtime = metadata.runtime === "browser" ? "browser" : "node";

  return {
    name: String(frontmatter.name ?? folderName),
    description: String(frontmatter.description ?? ""),
    instructions: body,
    require_secret: Boolean(metadata["require-secret"]),
    require_secret_description: String(metadata["require-secret-description"] ?? ""),
    homepage: String(metadata.homepage ?? ""),
    skill_dir: normalized,
    script_path: scriptPath,
    js_path: jsPath,
    runtime,
  };
}

export class SkillRegistry {
  private _skills = new Map<string, SkillDefinition>();

  /**
   * Scan a list of directories (posix path prefixes in the files store).
   * Typically called with each cartridge's `skills_source`.
   */
  async scan(...dirs: string[]): Promise<void> {
    for (const d of dirs) {
      const prefix = d.endsWith("/") ? d : `${d}/`;
      const all = await listFiles(prefix);
      const skillDirs = new Set<string>();
      for (const p of all) {
        // A skill dir is any <prefix><skillName>/ containing SKILL.md.
        // Candidate: top-level child of prefix.
        const rel = p.slice(prefix.length);
        const firstSlash = rel.indexOf("/");
        if (firstSlash <= 0) continue;
        const skillDir = `${prefix}${rel.slice(0, firstSlash)}`;
        skillDirs.add(skillDir);
      }
      for (const sd of Array.from(skillDirs).sort()) {
        const skill = await loadSkill(sd);
        if (skill) this._skills.set(skill.name, skill);
      }
    }
  }

  list(): SkillDefinition[] {
    return Array.from(this._skills.values());
  }
  names(): string[] {
    return Array.from(this._skills.keys());
  }
  get(name: string): SkillDefinition | undefined {
    return this._skills.get(name);
  }
  has(name: string): boolean {
    return this._skills.has(name);
  }
  size(): number {
    return this._skills.size;
  }

  descriptions(): string {
    const lines: string[] = [];
    for (const s of this._skills.values()) {
      const tag = s.require_secret ? " [requires API key]" : "";
      lines.push(`- **${s.name}**: ${s.description}${tag}`);
    }
    return lines.join("\n");
  }

  /** M12 — reload a single skill after a save. */
  async reloadSkill(skillDir: string): Promise<void> {
    const s = await loadSkill(skillDir);
    if (s) this._skills.set(s.name, s);
  }

  /** M12 — drop a skill from the registry (after deleteSkill). */
  forget(skillName: string): void {
    this._skills.delete(skillName);
  }
}
