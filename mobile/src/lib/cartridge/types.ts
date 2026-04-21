/**
 * Cartridge data contracts — mirrors dataclasses in
 * C:\evolvingagents\skillos\cartridge_runtime.py lines 192-248.
 */

export type AgentTier = "cheap" | "capable";

export interface AgentSpec {
  name: string;
  path: string;
  body: string;
  needs: string[];
  produces: string[];
  produces_schema: string;
  produces_description: string;
  tools: string[];
  max_turns: number;
  description: string;
  /**
   * Routing hint for M11 `resolveProvider`. `cheap` (default) prefers the
   * project's primary provider; `capable` skips local-first routing and goes
   * straight to the fallback when one is configured.
   */
  tier: AgentTier;
}

export interface SkillStep {
  skill: string;
  needs: string[];
  produces: string[];
  produces_schema: string;
  data_map: Record<string, string>;
  defaults: Record<string, unknown>;
}

export type FlowStep = string | SkillStep;

export type FlowMode = "standard" | "agentic";

export interface FlowDef {
  steps: FlowStep[];
  mode: FlowMode;
}

export function isSkillStep(step: FlowStep): step is SkillStep {
  return typeof step !== "string";
}

export function stepName(step: FlowStep): string {
  return typeof step === "string" ? step : step.skill;
}

export type CartridgeType = "standard" | "js-skills";

export type PreferredTier = "local" | "cloud" | "auto";

export interface CartridgeManifest {
  name: string;
  path: string;
  description: string;
  entry_intents: string[];
  flows: Record<string, string[]>; // legacy: list of step names
  flow_defs: Record<string, FlowDef>;
  blackboard_schema: Record<string, string>;
  validators: string[];
  max_turns_per_agent: number;
  default_flow: string;
  variables: Record<string, unknown>;
  type: CartridgeType;
  skills_source: string;
  /**
   * M11 routing hint. `local` asks the smart router to prefer the project's
   * local provider; `cloud` always uses a cloud primary/fallback; `auto`
   * (default) respects the project's primary choice and only falls back on
   * validation failure.
   */
  preferred_tier: PreferredTier;
}

export interface BlackboardEntry {
  value: unknown;
  schema_ref: string;
  produced_by: string;
  description: string;
  created_at: string;
}

export interface BlackboardSnapshot {
  [key: string]: {
    value: unknown;
    schema_ref: string;
    produced_by: string;
    description: string;
    created_at: string;
  };
}

export interface ValidationResult {
  ok: boolean;
  message: string;
}

export type SchemaValidator = (value: unknown, schemaRef: string) => ValidationResult;
