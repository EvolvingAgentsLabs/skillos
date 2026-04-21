/**
 * CartridgeRegistry — TS port of
 * C:\evolvingagents\skillos\cartridge_runtime.py lines 280-425.
 *
 * On mobile we do not have a filesystem iterator. Instead we read the seeded
 * IndexedDB `files` store. Paths are posix-style strings rooted at
 * `cartridges/<name>/…` just as they were on disk.
 */

import yaml from "js-yaml";
import { getFileText, listFiles } from "../storage/db";
import { makeValidatorForCartridge, type SchemaFile } from "./validators";
import type {
  AgentSpec,
  CartridgeManifest,
  FlowDef,
  FlowStep,
  SchemaValidator,
  SkillStep,
} from "./types";

// ────────────────────────────────────────────────────────────────────────
// Stopwords + tokenizer — lines 428-436.
// ────────────────────────────────────────────────────────────────────────

const STOPWORDS: ReadonlySet<string> = new Set([
  "the", "a", "an", "and", "or", "for", "to", "of", "in", "on", "with",
  "my", "your", "our", "is", "are", "be", "do", "make", "create",
]);

export function tokenize(text: string): Set<string> {
  const out = new Set<string>();
  const re = /[a-zA-Z]{3,}/g;
  for (const m of text.toLowerCase().matchAll(re)) {
    const tok = m[0];
    if (!STOPWORDS.has(tok)) out.add(tok);
  }
  return out;
}

// ────────────────────────────────────────────────────────────────────────
// Frontmatter splitter — lines 439-452.
// ────────────────────────────────────────────────────────────────────────

export function splitFrontmatter(text: string): { frontmatter: Record<string, unknown>; body: string } {
  if (!text.startsWith("---")) return { frontmatter: {}, body: text };
  const end = text.indexOf("\n---", 3);
  if (end === -1) return { frontmatter: {}, body: text };
  const block = text.slice(3, end).trim();
  const body = text.slice(end + 4).replace(/^\s+/, "");
  const data = yaml.load(block);
  const fm =
    data && typeof data === "object" && !Array.isArray(data)
      ? (data as Record<string, unknown>)
      : {};
  return { frontmatter: fm, body };
}

// ────────────────────────────────────────────────────────────────────────
// Flow-step parser — lines 251-273.
// ────────────────────────────────────────────────────────────────────────

function parseFlowSteps(raw: unknown[]): FlowStep[] {
  const steps: FlowStep[] = [];
  for (const item of raw) {
    if (typeof item === "string") {
      steps.push(item);
    } else if (item && typeof item === "object") {
      const obj = item as Record<string, unknown>;
      const step: SkillStep = {
        skill: String(obj.skill ?? obj.name ?? ""),
        needs: asStringArray(obj.needs),
        produces: asStringArray(obj.produces),
        produces_schema: String(obj.produces_schema ?? ""),
        data_map: asStringMap(obj.data_map),
        defaults: asRecord(obj.defaults),
      };
      steps.push(step);
    } else {
      steps.push(String(item));
    }
  }
  return steps;
}

function asStringArray(v: unknown): string[] {
  if (!Array.isArray(v)) return [];
  return v.map((x) => String(x));
}

function asStringMap(v: unknown): Record<string, string> {
  if (!v || typeof v !== "object") return {};
  const out: Record<string, string> = {};
  for (const [k, val] of Object.entries(v as Record<string, unknown>)) out[k] = String(val);
  return out;
}

function asRecord(v: unknown): Record<string, unknown> {
  if (!v || typeof v !== "object") return {};
  return { ...(v as Record<string, unknown>) };
}

// ────────────────────────────────────────────────────────────────────────
// Registry
// ────────────────────────────────────────────────────────────────────────

export class CartridgeRegistry {
  private _manifests = new Map<string, CartridgeManifest>();
  private _agentsCache = new Map<string, AgentSpec>();
  private _validatorCache = new Map<string, SchemaValidator>();
  private _initialized = false;

  constructor(private readonly filesRoot = "cartridges/") {}

  async init(): Promise<void> {
    if (this._initialized) return;
    const all = await listFiles(this.filesRoot);
    // Find every cartridges/<name>/cartridge.yaml
    const manifestPaths = all.filter((p) => {
      const parts = p.split("/");
      return parts.length === 3 && parts[0] === "cartridges" && parts[2] === "cartridge.yaml";
    });
    for (const path of manifestPaths.sort()) {
      try {
        const manifest = await this.loadManifest(path);
        this._manifests.set(manifest.name, manifest);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        console.warn(`[cartridge-registry] skipped ${path}: ${msg}`);
      }
    }
    this._initialized = true;
  }

  // ── M12 mutation hooks ──────────────────────────────────────────────

  /** Re-parse a single cartridge's manifest from IndexedDB. */
  async reloadCartridge(name: string): Promise<void> {
    const yamlPath = `cartridges/${name}/cartridge.yaml`;
    try {
      const manifest = await this.loadManifest(yamlPath);
      this._manifests.set(manifest.name, manifest);
      // Drop any cached agents + validator for this cartridge.
      for (const key of [...this._agentsCache.keys()]) {
        if (key.startsWith(`${name}/`)) this._agentsCache.delete(key);
      }
      this._validatorCache.delete(name);
    } catch (err) {
      console.warn(`[cartridge-registry] reloadCartridge ${name}:`, err);
    }
  }

  /** Drop a single agent's cached AgentSpec; next `loadAgent` re-reads. */
  invalidateAgent(cartridge: string, agentName: string): void {
    this._agentsCache.delete(`${cartridge}/${agentName}`);
  }

  /** Drop the cached ajv validator so a schema edit takes effect. */
  invalidateValidator(cartridge: string): void {
    this._validatorCache.delete(cartridge);
  }

  /** Remove a cartridge from the registry entirely (after deleteCartridge). */
  forget(name: string): void {
    this._manifests.delete(name);
    this._validatorCache.delete(name);
    for (const key of [...this._agentsCache.keys()]) {
      if (key.startsWith(`${name}/`)) this._agentsCache.delete(key);
    }
  }

  private async loadManifest(yamlPath: string): Promise<CartridgeManifest> {
    const text = await getFileText(yamlPath);
    if (!text) throw new Error(`manifest not found: ${yamlPath}`);
    const raw = yaml.load(text) ?? {};
    if (typeof raw !== "object" || Array.isArray(raw)) {
      throw new Error(`manifest is not a mapping: ${yamlPath}`);
    }
    const data = raw as Record<string, unknown>;
    const cartridgeDir = yamlPath.slice(0, yamlPath.lastIndexOf("/")); // cartridges/<name>

    // Parse flows into both legacy list[str] and rich FlowDef form.
    const flows: Record<string, string[]> = {};
    const flow_defs: Record<string, FlowDef> = {};
    const flowsRaw = normalizeFlowsRaw(data.flows);
    for (const [fname, fval] of Object.entries(flowsRaw)) {
      if (fval && typeof fval === "object" && !Array.isArray(fval)) {
        const rich = fval as Record<string, unknown>;
        const mode = String(rich.mode ?? "standard") === "agentic" ? "agentic" : "standard";
        const stepsRaw = (rich.steps ?? rich.tools ?? []) as unknown[];
        const steps = parseFlowSteps(stepsRaw);
        flow_defs[fname] = { steps, mode };
        flows[fname] = steps.map((s) => (typeof s === "string" ? s : s.skill));
      } else if (Array.isArray(fval)) {
        const steps = parseFlowSteps(fval);
        flow_defs[fname] = { steps, mode: "standard" };
        flows[fname] = steps.map((s) => (typeof s === "string" ? s : s.skill));
      } else {
        flows[fname] = [String(fval)];
        flow_defs[fname] = { steps: [String(fval)], mode: "standard" };
      }
    }

    // Resolve skills_source relative to cartridge dir.
    let skills_source = String(data.skills_source ?? "");
    if (skills_source) {
      skills_source = resolveRelPath(cartridgeDir, skills_source);
    }

    const fallbackName = cartridgeDir.split("/").pop() ?? "unknown";
    const preferredTierRaw = String(data.preferred_tier ?? "auto");
    const preferred_tier: CartridgeManifest["preferred_tier"] =
      preferredTierRaw === "local" || preferredTierRaw === "cloud"
        ? preferredTierRaw
        : "auto";
    const manifest: CartridgeManifest = {
      name: String(data.name ?? fallbackName),
      path: cartridgeDir,
      description: String(data.description ?? ""),
      entry_intents: asStringArray(data.entry_intents),
      flows,
      flow_defs,
      blackboard_schema: asStringMap(data.blackboard_schema),
      validators: asStringArray(data.validators),
      max_turns_per_agent: Number(data.max_turns_per_agent ?? 3) | 0,
      default_flow: String(data.default_flow ?? ""),
      variables: asRecord(data.variables),
      type: data.type === "js-skills" ? "js-skills" : "standard",
      skills_source,
      preferred_tier,
    };
    if (!manifest.default_flow) {
      const firstFlow = Object.keys(manifest.flows)[0];
      if (firstFlow) manifest.default_flow = firstFlow;
    }
    return manifest;
  }

  // --- accessors ---------------------------------------------------------

  list(): CartridgeManifest[] {
    return Array.from(this._manifests.values());
  }

  names(): string[] {
    return Array.from(this._manifests.keys());
  }

  get(name: string): CartridgeManifest | undefined {
    return this._manifests.get(name);
  }

  async loadAgent(cartridge: string, agentName: string): Promise<AgentSpec | undefined> {
    const key = `${cartridge}/${agentName}`;
    const cached = this._agentsCache.get(key);
    if (cached) return cached;

    const manifest = this.get(cartridge);
    if (!manifest) return undefined;

    const agentPath = `${manifest.path}/agents/${agentName}.md`;
    const content = await getFileText(agentPath);
    if (content === undefined) return undefined;

    const { frontmatter, body } = splitFrontmatter(content);
    const tierRaw = String(frontmatter.tier ?? "cheap");
    const tier: AgentSpec["tier"] = tierRaw === "capable" ? "capable" : "cheap";
    const spec: AgentSpec = {
      name: String(frontmatter.name ?? agentName),
      path: agentPath,
      body,
      needs: asStringArray(frontmatter.needs),
      produces: asStringArray(frontmatter.produces),
      produces_schema: String(frontmatter.produces_schema ?? ""),
      produces_description: String(frontmatter.produces_description ?? ""),
      tools: asStringArray(frontmatter.tools),
      max_turns:
        (Number(frontmatter.max_turns ?? manifest.max_turns_per_agent) | 0) ||
        manifest.max_turns_per_agent,
      description: String(frontmatter.description ?? ""),
      tier,
    };
    this._agentsCache.set(key, spec);
    return spec;
  }

  async getValidator(cartridge: string): Promise<SchemaValidator> {
    const cached = this._validatorCache.get(cartridge);
    if (cached) return cached;
    const manifest = this.get(cartridge);
    if (!manifest) {
      return () => ({ ok: true, message: "no cartridge" });
    }
    const prefix = `${manifest.path}/schemas/`;
    const schemaPaths = (await listFiles(prefix)).filter((p) => p.endsWith(".schema.json"));
    const files: SchemaFile[] = [];
    for (const p of schemaPaths) {
      const text = await getFileText(p);
      if (!text) continue;
      try {
        const schema = JSON.parse(text) as Record<string, unknown>;
        files.push({ ref: p.slice(prefix.length), schema });
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        console.warn(`[cartridge-registry] bad schema ${p}: ${msg}`);
      }
    }
    const v = makeValidatorForCartridge(cartridge, files);
    this._validatorCache.set(cartridge, v);
    return v;
  }

  // --- intent matching — lines 407-425 -----------------------------------

  matchIntent(goal: string, minScore = 2): { cartridge: string | null; score: number } {
    let best: string | null = null;
    let bestScore = 0;
    const goalTokens = tokenize(goal);
    for (const m of this._manifests.values()) {
      for (const intent of m.entry_intents) {
        const intentTokens = tokenize(intent);
        let overlap = 0;
        for (const t of intentTokens) if (goalTokens.has(t)) overlap++;
        if (overlap > bestScore) {
          bestScore = overlap;
          best = m.name;
        }
      }
    }
    if (bestScore < minScore) return { cartridge: null, score: bestScore };
    return { cartridge: best, score: bestScore };
  }
}

// ────────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────────

function normalizeFlowsRaw(value: unknown): Record<string, unknown> {
  if (Array.isArray(value)) {
    const flat: Record<string, unknown> = {};
    for (const item of value) {
      if (item && typeof item === "object") Object.assign(flat, item);
    }
    return flat;
  }
  if (value && typeof value === "object") return value as Record<string, unknown>;
  return {};
}

function resolveRelPath(base: string, rel: string): string {
  // Posix-style resolution inside IndexedDB path keys.
  if (rel.startsWith("/")) return rel.replace(/^\/+/, "");
  const parts = [...base.split("/"), ...rel.split("/")].filter(Boolean);
  const stack: string[] = [];
  for (const p of parts) {
    if (p === "." || p === "") continue;
    if (p === "..") stack.pop();
    else stack.push(p);
  }
  return stack.join("/");
}
