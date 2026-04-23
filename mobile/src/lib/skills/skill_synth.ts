/**
 * Skill synthesis — turns a successful project-card run into a reusable
 * Gallery-format skill (SKILL.md + scripts/index.js).
 *
 * The goal of Surface 2 ("Promote to Skill") is to capture the shape of a
 * one-off task so the user gets a permanent, offline, deterministic button.
 * The LLM is used once, at synthesis time; the generated index.js is pure JS
 * that runs in the sandboxed iframe and never needs the cloud again.
 *
 * The first-shot quality of LLM synthesis is inherently noisy, so:
 *   - the parser tolerates a variety of response shapes (fenced blocks,
 *     yaml-then-js, single JSON blob),
 *   - on parse failure the caller still gets the raw response so the user
 *     can hand-edit a draft.
 *
 * The return shape is stable; rendering the editable preview lives in
 * PromoteToSkillSheet.svelte.
 */

import yaml from "js-yaml";
import type { LLMProvider } from "../llm/provider";
import type { SkillInputSchema } from "./skill_loader";

export interface SynthSource {
  /** What the user asked for originally (the project goal card). */
  goal: string;
  /** The card being promoted — usually a done-lane card. */
  cardTitle: string;
  cardSubtitle?: string;
  cardSchemaRef?: string;
  /** Structured/text payload of the card, if any (rendered as JSON in the prompt). */
  cardData?: unknown;
  /** Optional project-level context (cartridge name, sibling card titles). */
  projectName: string;
  projectCartridge: string | null;
  relatedCardTitles?: string[];
  /**
   * Fork/evolve mode: include the full source of an existing skill along with
   * a `changeRequest` instruction. The model is asked to produce a new variant
   * rather than a fresh skill from scratch.
   */
  existingSkillMd?: string;
  existingIndexJs?: string;
  changeRequest?: string;
}

export interface SynthResult {
  ok: boolean;
  /** Slug-safe skill name ("photo-invoice"); used as the folder name. */
  skillName: string;
  /** Full SKILL.md body including YAML frontmatter. */
  skillMd: string;
  /** scripts/index.js body. */
  indexJs: string;
  /** Parsed input_schema (if the model produced one and it was valid). */
  inputSchema?: SkillInputSchema;
  /** Raw LLM response — always populated so UI can show it on parse failure. */
  raw: string;
  /** Human-readable parse/synthesis errors (non-fatal). */
  errors: string[];
}

// ────────────────────────────────────────────────────────────────────────────

const SYSTEM_PROMPT = `You turn a one-off user task into a reusable "Gallery skill" — a small pure-JavaScript program that runs offline on the user's phone.

A skill is made of two files:
1. SKILL.md — YAML frontmatter + markdown body, describing the skill.
2. scripts/index.js — browser-side JS that registers a dispatch function.

The iframe runtime:
- Injects the script. The script MUST assign \`globalThis.ai_edge_gallery_get_result\` (and only that) to an async function.
- Calls it as \`await ai_edge_gallery_get_result(dataString, secret)\`. \`dataString\` is a JSON string matching input_schema. \`secret\` is a string or empty.
- Expects the function to return a JSON STRING of the form \`{"result": "..."}\` or \`{"error": "..."}\`. Optional extra fields: \`image: {base64, mimeType}\`, \`webview: {url}\`.

The runtime provides \`globalThis.__skillos.llm.chat(prompt, options)\` (returns a Promise<string>) if the skill needs an LLM. AVOID it when pure JS suffices — the whole point is offline determinism.

Rules:
- Prefer pure JS math / string formatting over LLM calls. If the task is "calculate X from Y", write the formula.
- input_schema follows JSON Schema draft-07: \`{type: "object", properties: {...}, required: [...]}\`. Keep properties small and typed.
- No network access, no node-only modules, no \`require\`, no \`import\`. Browser globals only (crypto.subtle, TextEncoder, Intl, Math, JSON, Date).
- Wrap the body in try/catch and return \`JSON.stringify({error: e.message})\` on failure — never throw.`;

function userPrompt(src: SynthSource): string {
  const related = src.relatedCardTitles?.length
    ? `\nOther cards in this project:\n${src.relatedCardTitles.map((t) => `- ${t}`).join("\n")}`
    : "";
  const dataSection =
    src.cardData !== undefined
      ? `\nExample output from the run:\n\`\`\`json\n${safeJson(src.cardData)}\n\`\`\``
      : "";
  // Fork / evolve mode: a prior skill exists and the user wants a modified
  // variant. We hand the model the full source + the change request so it
  // can edit rather than re-invent.
  if (src.existingSkillMd && src.existingIndexJs) {
    return `The user has an existing skill and wants to evolve it.

Original goal: ${src.goal}
Requested change: ${src.changeRequest ?? "(no change text — infer from context)"}

Project: ${src.projectName}${src.projectCartridge ? ` (cartridge: ${src.projectCartridge})` : ""}${related}${dataSection}

Existing SKILL.md:
\`\`\`markdown
${src.existingSkillMd}
\`\`\`

Existing scripts/index.js:
\`\`\`javascript
${src.existingIndexJs}
\`\`\`

Produce a new variant that applies the requested change. Keep the inputs/output shape compatible unless the change requires otherwise. Give the variant a new slug-like name (e.g. "<original>-<variant-hint>").

Respond with EXACTLY this structure, nothing else:

\`\`\`yaml
name: <slug-with-variant-suffix>
description: <one-line, under 80 chars>
metadata:
  input_schema:
    type: object
    properties: {...}
    required: [...]
\`\`\`

\`\`\`markdown
<body describing the variant and how it differs from the original>
\`\`\`

\`\`\`javascript
globalThis.ai_edge_gallery_get_result = async (dataString, secret) => {
  try {
    const data = JSON.parse(dataString);
    // ...your evolved implementation...
    return JSON.stringify({ result: "..." });
  } catch (e) {
    return JSON.stringify({ error: e && e.message ? e.message : String(e) });
  }
};
\`\`\``;
  }
  return `The user ran a task once and wants to turn it into a permanent skill.

Original goal: ${src.goal}

Promoted result card: ${src.cardTitle}${src.cardSubtitle ? ` — ${src.cardSubtitle}` : ""}${src.cardSchemaRef ? `\nResult schema ref: ${src.cardSchemaRef}` : ""}
Project: ${src.projectName}${src.projectCartridge ? ` (cartridge: ${src.projectCartridge})` : ""}${related}${dataSection}

Design the reusable shape. Identify the typed inputs the user would supply each time (not the values they used this time — the variables). Write deterministic JS that produces a result of the same shape.

Respond with EXACTLY this structure, and nothing else:

\`\`\`yaml
name: <slug-like-this>
description: <one-line, under 80 chars>
metadata:
  input_schema:
    type: object
    properties:
      <field_name>:
        type: <string|number|integer|boolean>
        title: <Human Label>
        description: <one-line help>
    required: [<field_name>, ...]
\`\`\`

\`\`\`markdown
<body of SKILL.md — 1-3 short paragraphs describing what the skill does and when to use it. Do NOT repeat the frontmatter.>
\`\`\`

\`\`\`javascript
// scripts/index.js
globalThis.ai_edge_gallery_get_result = async (dataString, secret) => {
  try {
    const data = JSON.parse(dataString);
    // Use the typed fields from input_schema (data.fieldName).
    // Compute deterministically, no network calls.
    const answer = /* your logic here, using data.<field> values */ "...";
    return JSON.stringify({ result: String(answer) });
  } catch (e) {
    return JSON.stringify({ error: e && e.message ? e.message : String(e) });
  }
};
\`\`\``;
}

function safeJson(v: unknown): string {
  try {
    const s = JSON.stringify(v, null, 2);
    return s.length > 2000 ? s.slice(0, 2000) + "\n... [truncated]" : s;
  } catch {
    return String(v);
  }
}

// ────────────────────────────────────────────────────────────────────────────
// Parsing
// ────────────────────────────────────────────────────────────────────────────

function extractFence(raw: string, langs: string[]): string | undefined {
  for (const lang of langs) {
    const re = new RegExp("```" + lang + "\\s*\\n([\\s\\S]*?)```", "i");
    const m = re.exec(raw);
    if (m) return m[1].trim();
  }
  return undefined;
}

function slugify(s: string): string {
  return (
    s
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .slice(0, 60) || "user-skill"
  );
}

function parseFrontmatter(yamlText: string): {
  name?: string;
  description?: string;
  inputSchema?: SkillInputSchema;
  errors: string[];
} {
  const errors: string[] = [];
  try {
    const parsed = yaml.load(yamlText);
    if (!parsed || typeof parsed !== "object") {
      errors.push("frontmatter is not an object");
      return { errors };
    }
    const obj = parsed as Record<string, unknown>;
    const name = typeof obj.name === "string" ? obj.name : undefined;
    const description =
      typeof obj.description === "string" ? obj.description : undefined;
    let inputSchema: SkillInputSchema | undefined;
    const meta = obj.metadata;
    if (meta && typeof meta === "object" && !Array.isArray(meta)) {
      const is = (meta as Record<string, unknown>).input_schema;
      if (is && typeof is === "object" && !Array.isArray(is)) {
        inputSchema = is as SkillInputSchema;
      }
    }
    return { name, description, inputSchema, errors };
  } catch (err) {
    errors.push(`yaml parse error: ${err instanceof Error ? err.message : String(err)}`);
    return { errors };
  }
}

export function parseSynthResponse(
  raw: string,
  fallbackName: string,
): SynthResult {
  const errors: string[] = [];
  const yamlText = extractFence(raw, ["yaml", "yml"]);
  const markdownBody = extractFence(raw, ["markdown", "md"]);
  const jsText = extractFence(raw, ["javascript", "js"]);

  if (!yamlText) errors.push("missing ```yaml frontmatter block");
  if (!jsText) errors.push("missing ```javascript code block");

  const parsed = yamlText
    ? parseFrontmatter(yamlText)
    : { name: undefined, description: undefined, inputSchema: undefined, errors: [] };
  errors.push(...parsed.errors);

  const skillName = slugify(parsed.name ?? fallbackName);

  const frontmatterOut = yamlText
    ? yamlText
    : yaml.dump(
        {
          name: skillName,
          description: parsed.description ?? "",
          metadata: { input_schema: { type: "object", properties: {} } },
        },
        { sortKeys: false, noRefs: true },
      ).trimEnd();

  const body = markdownBody ?? "(no description)";
  const skillMd = `---\n${frontmatterOut.trim()}\n---\n\n${body.trim()}\n`;

  return {
    ok: errors.length === 0,
    skillName,
    skillMd,
    indexJs:
      jsText ??
      "// synthesis failed — edit this skill to add an implementation.\nglobalThis.ai_edge_gallery_get_result = async () =>\n  JSON.stringify({ error: 'not implemented' });\n",
    inputSchema: parsed.inputSchema,
    raw,
    errors,
  };
}

// ────────────────────────────────────────────────────────────────────────────
// LLM call
// ────────────────────────────────────────────────────────────────────────────

export interface SynthesizeOptions {
  /** Optional abort signal plumbed through the provider. */
  temperature?: number;
  maxTokens?: number;
}

export async function synthesizeSkill(
  llm: LLMProvider,
  source: SynthSource,
  opts: SynthesizeOptions = {},
): Promise<SynthResult> {
  const fallbackName = slugify(source.cardTitle || source.goal || "user-skill");
  const r = await llm.chat(
    [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: userPrompt(source) },
    ],
    {
      stream: false,
      temperature: opts.temperature ?? 0.2,
      maxTokens: opts.maxTokens ?? 2048,
    },
  );
  return parseSynthResponse(r.content, fallbackName);
}
