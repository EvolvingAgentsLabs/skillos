/**
 * Scaffold a new cartridge from zero.
 *
 * Emits a `cartridge.yaml`, a minimal `<agent>.md` stub for each declared
 * agent, and optional empty schemas. The wizard UI in
 * `CartridgeWizard.svelte` pipes the user's inputs through this then hands
 * the resulting files to `saveCartridge()`.
 */

import yaml from "js-yaml";
import type { CartridgeFiles } from "./registry_mutations";

export interface ScaffoldInput {
  name: string;
  description?: string;
  preferredTier?: "local" | "cloud" | "auto";
  entryIntents?: string[];
  /** Map of blackboard key → schema ref filename. */
  blackboardSchema?: Record<string, string>;
  /** Ordered list of agent names that form the default flow. */
  agents?: string[];
  defaultFlow?: string;
}

export function scaffoldCartridge(input: ScaffoldInput): CartridgeFiles {
  const {
    name,
    description = "",
    preferredTier = "auto",
    entryIntents = [],
    blackboardSchema = {},
    agents = [],
    defaultFlow = agents.length > 0 ? "default" : "",
  } = input;

  if (!name.trim()) throw new Error("cartridge name is required");
  const safeName = name.trim();

  const manifest: Record<string, unknown> = {
    name: safeName,
    description,
    preferred_tier: preferredTier,
  };
  if (entryIntents.length > 0) manifest.entry_intents = entryIntents;
  if (agents.length > 0) {
    manifest.flows = { default: agents };
    manifest.default_flow = defaultFlow || "default";
  }
  if (Object.keys(blackboardSchema).length > 0) {
    manifest.blackboard_schema = blackboardSchema;
  }
  manifest.max_turns_per_agent = 3;

  const agentFiles: Record<string, string> = {};
  for (const a of agents) {
    agentFiles[a] = scaffoldAgent(a, blackboardSchema);
  }

  const schemaFiles: Record<string, string> = {};
  for (const ref of Object.values(blackboardSchema)) {
    schemaFiles[ref] = emptySchema(ref);
  }

  return {
    manifestYaml: yaml.dump(manifest, { sortKeys: false, noRefs: true }),
    agents: agentFiles,
    schemas: schemaFiles,
  };
}

function scaffoldAgent(
  name: string,
  blackboardSchema: Record<string, string>,
): string {
  const producedKey = Object.keys(blackboardSchema)[0] ?? "";
  const producedSchema = producedKey ? blackboardSchema[producedKey] : "";
  const frontmatter: Record<string, unknown> = {
    name,
    tier: "cheap",
    needs: name === Object.keys(blackboardSchema)[0] ? [] : ["user_goal"],
    produces: producedKey ? [producedKey] : [],
    produces_schema: producedSchema,
    produces_description: "",
    tools: [],
    max_turns: 3,
    description: `Stub for ${name} — replace this with the real agent prompt.`,
  };
  const fm = yaml.dump(frontmatter, { sortKeys: false, noRefs: true }).trimEnd();
  const body = [
    `# ${name}`,
    "",
    "You are a placeholder agent. Replace this body with the actual",
    "role, tools, reasoning scaffolds, and any few-shot examples the",
    "user wants this agent to follow.",
    "",
    "Remember: your final turn must emit a `<produces>{…}</produces>`",
    "block inside `<final_answer>` tags conforming to the schema",
    producedSchema ? `at \`schemas/${producedSchema}\`.` : "declared in the manifest.",
  ].join("\n");
  return `---\n${fm}\n---\n\n${body}\n`;
}

function emptySchema(ref: string): string {
  const title = ref.replace(/\.schema\.json$/, "").replace(/[_-]/g, " ");
  return JSON.stringify(
    {
      $schema: "https://json-schema.org/draft/2020-12/schema",
      title,
      type: "object",
      properties: {},
      additionalProperties: true,
    },
    null,
    2,
  );
}
