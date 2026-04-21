/**
 * CartridgeRunner — TS port of
 * C:\evolvingagents\skillos\cartridge_runtime.py CartridgeRunner class
 * (lines 480-1274).
 *
 * Orchestrates a cartridge flow:
 *   - standard sequential flow: list of agent names + SkillSteps
 *   - agentic flow: LLM given load_skill + run_js tools, decides autonomously
 *   - js-skills cartridge: param-extractor → js-executor path
 *
 * Dependencies (injected at construction):
 *   - CartridgeRegistry — for manifest + agent lookup
 *   - LLMClient — for agent LLM calls
 *   - SkillHostBridge — for Gallery skill execution (iframe)
 *
 * Emits RunEvent callbacks so the UI (M6) can animate card lane transitions.
 */

import { type LLMClient } from "../llm/client";
import { runGoal, type RunGoalEvent, type ToolFunction } from "../llm/run_goal";
import type { SkillDefinition } from "../skills/skill_loader";
import { SkillRegistry } from "../skills/skill_loader";
import { skillHostBridge, type LLMProxy } from "../skills/skill_host_bridge";
import { skillResultToLlmString } from "../skills/skill_result";
import { Blackboard } from "./blackboard";
import { tokenize } from "./registry";
import type { CartridgeRegistry } from "./registry";
import { BUILTIN_VALIDATORS } from "./validators_builtin";
import type {
  AgentSpec,
  BlackboardSnapshot,
  CartridgeManifest,
  FlowDef,
  FlowStep,
  SkillStep,
} from "./types";
import { isSkillStep } from "./types";

// ────────────────────────────────────────────────────────────────────────
// Result types
// ────────────────────────────────────────────────────────────────────────

export interface StepResult {
  agent: string;
  produced_keys: string[];
  raw_output: string;
  validated: boolean;
  message: string;
  attempts: number;
}

export interface RunResult {
  cartridge: string;
  flow: string;
  goal: string;
  steps: StepResult[];
  blackboard: BlackboardSnapshot;
  validator_messages: string[];
  ok: boolean;
  final_summary: string;
}

export type RunEvent =
  | { type: "run-start"; cartridge: string; flow: string; goal: string }
  | { type: "step-start"; agent: string }
  | { type: "llm-turn"; agent: string; turn: number; delta?: string }
  | { type: "tool-call"; agent: string; tool: string; args: Record<string, unknown> }
  | { type: "tool-result"; agent: string; tool: string; result: unknown }
  | { type: "blackboard-put"; agent: string; key: string; ok: boolean; message: string }
  | { type: "step-end"; step: StepResult }
  | { type: "validator"; message: string; ok: boolean }
  | { type: "run-end"; result: RunResult };

export interface RunOptions {
  flow?: string;
  initialInputs?: Record<string, unknown>;
  maxRetriesPerStep?: number;
  onEvent?: (e: RunEvent) => void;
  signal?: AbortSignal;
}

// ────────────────────────────────────────────────────────────────────────
// Runner
// ────────────────────────────────────────────────────────────────────────

const PRODUCES_RE = /<produces>([\s\S]*?)<\/produces>/;

export class CartridgeRunner {
  private _skillRegs = new Map<string, SkillRegistry>();

  constructor(
    private readonly registry: CartridgeRegistry,
    private readonly llm: LLMClient,
  ) {}

  async run(cartridge: string, goal: string, opts: RunOptions = {}): Promise<RunResult> {
    const manifest = this.registry.get(cartridge);
    if (!manifest) throw new Error(`unknown cartridge: ${cartridge}`);

    const flowName = opts.flow ?? this.selectFlow(manifest, goal);
    const agentSequence = manifest.flows[flowName];
    if (!agentSequence) throw new Error(`unknown flow '${flowName}' in ${cartridge}`);

    const flowDef: FlowDef =
      manifest.flow_defs[flowName] ?? { steps: agentSequence, mode: "standard" };

    const validator = await this.registry.getValidator(cartridge);
    const bb = new Blackboard(validator);
    bb.put("user_goal", goal, { produced_by: "user", description: "The original user request" });
    for (const [k, v] of Object.entries(opts.initialInputs ?? {})) {
      bb.put(k, v, { produced_by: "user", description: `User-supplied input: ${k}` });
    }

    // Install an LLM proxy on the skill bridge so __skillos.llm works.
    skillHostBridge.setLLMProxy(this.makeLLMProxy());

    // For js-skills cartridges, pre-select a skill and seed context.
    if (manifest.type === "js-skills" && flowDef.mode !== "agentic") {
      await this.prepareJsSkillsContext(manifest, goal, bb);
    }

    const result: RunResult = {
      cartridge,
      flow: flowName,
      goal,
      steps: [],
      blackboard: {},
      validator_messages: [],
      ok: false,
      final_summary: "",
    };
    opts.onEvent?.({ type: "run-start", cartridge, flow: flowName, goal });

    if (flowDef.mode === "agentic") {
      const step = await this.runAgenticFlow(manifest, goal, bb, opts);
      result.steps.push(step);
      opts.onEvent?.({ type: "step-end", step });
    } else {
      const maxRetries = opts.maxRetriesPerStep ?? 1;
      for (const stepDef of flowDef.steps) {
        const primary = await this.executeFlowStep(manifest, stepDef, bb, "", opts);
        let step = primary;
        if (!step.validated && maxRetries > 0) {
          step.attempts += 1;
          const retry = await this.executeFlowStep(manifest, stepDef, bb, step.message, opts);
          retry.attempts = step.attempts + retry.attempts;
          step = retry;
        }
        result.steps.push(step);
        opts.onEvent?.({ type: "step-end", step });
      }
    }

    result.validator_messages = this.runValidators(manifest, bb, opts);
    result.blackboard = bb.snapshot();
    result.ok =
      result.steps.every((s) => s.validated) &&
      result.validator_messages.every((m) => m.startsWith("ok"));
    result.final_summary = this.renderSummary(
      manifest,
      flowName,
      result.steps,
      result.validator_messages,
      bb,
    );
    opts.onEvent?.({ type: "run-end", result });
    return result;
  }

  // ────────────────────────────────────────────────────────────────────

  private async executeFlowStep(
    manifest: CartridgeManifest,
    stepDef: FlowStep,
    bb: Blackboard,
    retryFeedback: string,
    opts: RunOptions,
  ): Promise<StepResult> {
    if (typeof stepDef === "string") {
      if (manifest.type === "js-skills" && stepDef === "js-executor") {
        return this.runJsSkill(manifest, bb, opts);
      }
      return this.runAgent(manifest, stepDef, bb, retryFeedback, opts);
    }
    return this.runSkillStep(manifest, stepDef, bb, opts);
  }

  private async runAgent(
    manifest: CartridgeManifest,
    agentName: string,
    bb: Blackboard,
    retryFeedback: string,
    opts: RunOptions,
  ): Promise<StepResult> {
    const spec = await this.registry.loadAgent(manifest.name, agentName);
    if (!spec) {
      return stepFailure(agentName, `agent spec not found: ${agentName}`);
    }
    const missing = spec.needs.filter((k) => !bb.has(k));
    if (missing.length > 0) {
      return stepFailure(agentName, `blackboard missing inputs: ${JSON.stringify(missing)}`);
    }
    opts.onEvent?.({ type: "step-start", agent: agentName });

    const inputDescriptions = bb.describe(spec.needs);
    const task = this.composeTask(spec, inputDescriptions, retryFeedback);

    let raw = "";
    try {
      raw = await runGoal(this.llm, task, {
        systemPrompt: spec.body,
        tools: {},
        maxTurns: spec.max_turns,
        signal: opts.signal,
        onEvent: (e) => this.forwardRunGoalEvent(agentName, e, opts),
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return { ...stepFailure(agentName, `delegation error: ${msg}`), raw_output: msg };
    }

    if (spec.produces.length === 0) {
      return {
        agent: agentName,
        produced_keys: [],
        raw_output: raw,
        validated: true,
        message: "ok (no produces)",
        attempts: 0,
      };
    }

    const produced = this.extractProduced(raw);
    if (produced === null) {
      return {
        agent: agentName,
        produced_keys: [],
        raw_output: raw,
        validated: false,
        message: "no <produces>{...}</produces> JSON block found",
        attempts: 0,
      };
    }

    const validated: string[] = [];
    const statusMsgs: string[] = [];
    for (const key of spec.produces) {
      if (!(key in produced)) {
        statusMsgs.push(`missing key '${key}' in produces JSON`);
        continue;
      }
      const schemaRef = manifest.blackboard_schema[key] ?? spec.produces_schema;
      const res = bb.put(key, produced[key], {
        schema_ref: schemaRef,
        produced_by: agentName,
        description: spec.produces_description || `Produced by ${agentName}`,
      });
      opts.onEvent?.({
        type: "blackboard-put",
        agent: agentName,
        key,
        ok: res.ok,
        message: res.message,
      });
      if (res.ok) validated.push(key);
      else statusMsgs.push(`${key}: ${res.message}`);
    }
    const allPresent = validated.length === spec.produces.length;
    return {
      agent: agentName,
      produced_keys: validated,
      raw_output: raw,
      validated: allPresent && statusMsgs.length === 0,
      message:
        allPresent && statusMsgs.length === 0 ? "ok" : statusMsgs.join("; ") || "partial",
      attempts: 0,
    };
  }

  private async runSkillStep(
    manifest: CartridgeManifest,
    step: SkillStep,
    bb: Blackboard,
    opts: RunOptions,
  ): Promise<StepResult> {
    const skillReg = await this.getSkillRegistry(manifest);
    const skill = skillReg.get(step.skill);
    if (!skill) return stepFailure(step.skill, `skill '${step.skill}' not found`);
    const missing = step.needs.filter((k) => !bb.has(k));
    if (missing.length > 0) {
      return stepFailure(step.skill, `blackboard missing: ${JSON.stringify(missing)}`);
    }
    opts.onEvent?.({ type: "step-start", agent: step.skill });

    const data: Record<string, unknown> = {};
    if (Object.keys(step.data_map).length > 0) {
      for (const [target, source] of Object.entries(step.data_map)) {
        data[target] = bb.value(source);
      }
    } else {
      for (const k of step.needs) data[k] = bb.value(k);
    }
    for (const [k, v] of Object.entries(step.defaults)) {
      if (!(k in data)) data[k] = v;
    }
    // Smart mapping (cartridge_runtime.py:827-845) — for single-need string values
    // with no data_map, try to map to the first field mentioned in SKILL.md.
    if (
      Object.keys(step.data_map).length === 0 &&
      skill.instructions &&
      step.needs.length === 1
    ) {
      const key = step.needs[0];
      const val = data[key];
      if (typeof val === "string") {
        const fieldMatches = [...skill.instructions.matchAll(/[-*]\s+\*?\*?(\w+)\*?\*?:\s/g)];
        if (fieldMatches.length > 0) {
          const mapped: Record<string, unknown> = { [fieldMatches[0][1]]: val };
          if (fieldMatches.some((m) => m[1].toLowerCase() === "lang")) mapped.lang = "en";
          for (const [k, v] of Object.entries(step.defaults)) mapped[k] = v;
          Object.keys(data).forEach((k) => delete data[k]);
          Object.assign(data, mapped);
        } else if (key === "user_goal") {
          Object.keys(data).forEach((k) => delete data[k]);
          data.text = val;
          for (const [k, v] of Object.entries(step.defaults)) data[k] = v;
        }
      }
    }

    const res = await skillHostBridge.runSkill(skill, { data });
    if (!res.ok) {
      return stepFailure(step.skill, res.error || "skill execution failed");
    }
    const resultData = (res.raw && typeof res.raw === "object" ? res.raw : {}) as Record<
      string,
      unknown
    >;
    if (step.produces.length > 0) {
      if (step.produces.length === 1 && "result" in resultData) {
        const key = step.produces[0];
        const schemaRef = manifest.blackboard_schema[key] ?? step.produces_schema;
        const putRes = bb.put(key, resultData.result, {
          schema_ref: schemaRef,
          produced_by: step.skill,
          description: `Output from ${step.skill}`,
        });
        opts.onEvent?.({
          type: "blackboard-put",
          agent: step.skill,
          key,
          ok: putRes.ok,
          message: putRes.message,
        });
      } else {
        for (const key of step.produces) {
          const v = resultData[key] ?? resultData.result ?? "";
          const schemaRef = manifest.blackboard_schema[key] ?? step.produces_schema;
          const putRes = bb.put(key, v, {
            schema_ref: schemaRef,
            produced_by: step.skill,
            description: `Output from ${step.skill}`,
          });
          opts.onEvent?.({
            type: "blackboard-put",
            agent: step.skill,
            key,
            ok: putRes.ok,
            message: putRes.message,
          });
        }
      }
    }
    return {
      agent: step.skill,
      produced_keys: [...step.produces],
      raw_output: skillResultToLlmString(res),
      validated: true,
      message: "ok",
      attempts: 0,
    };
  }

  private async runJsSkill(
    manifest: CartridgeManifest,
    bb: Blackboard,
    opts: RunOptions,
  ): Promise<StepResult> {
    opts.onEvent?.({ type: "step-start", agent: "js-executor" });
    let params = bb.value<unknown>("skill_params");
    if (params === undefined || params === null) {
      return stepFailure("js-executor", "skill_params not found on blackboard");
    }
    if (typeof params === "string") {
      try {
        params = JSON.parse(params);
      } catch {
        return stepFailure("js-executor", `skill_params is not valid JSON: ${String(params).slice(0, 200)}`);
      }
    }
    if (!params || typeof params !== "object") {
      return stepFailure("js-executor", "skill_params is not an object");
    }
    const p = params as Record<string, unknown>;
    const skillName = String(p.skill_name ?? "");
    const data = p.data ?? "{}";
    const secret = String(p.secret ?? "");
    const skillReg = await this.getSkillRegistry(manifest);
    const skill = skillReg.get(skillName);
    if (!skill) {
      return stepFailure(
        "js-executor",
        `skill '${skillName}' not found. Available: ${skillReg.names().join(", ")}`,
      );
    }
    const res = await skillHostBridge.runSkill(skill, { data, secret });
    const resultData = (res.raw && typeof res.raw === "object" ? res.raw : {}) as Record<
      string,
      unknown
    >;
    const schemaRef = manifest.blackboard_schema.skill_result ?? "";
    const putRes = bb.put("skill_result", resultData, {
      schema_ref: schemaRef,
      produced_by: "js-executor",
      description: `JS execution result from ${skillName}`,
    });
    opts.onEvent?.({
      type: "blackboard-put",
      agent: "js-executor",
      key: "skill_result",
      ok: putRes.ok,
      message: putRes.message,
    });
    const validated = res.ok && putRes.ok;
    return {
      agent: "js-executor",
      produced_keys: validated ? ["skill_result"] : [],
      raw_output: skillResultToLlmString(res),
      validated,
      message: validated ? "ok" : res.error ?? putRes.message ?? "execution failed",
      attempts: 0,
    };
  }

  private async runAgenticFlow(
    manifest: CartridgeManifest,
    goal: string,
    bb: Blackboard,
    opts: RunOptions,
  ): Promise<StepResult> {
    opts.onEvent?.({ type: "step-start", agent: "agentic-flow" });
    const skillReg = await this.getSkillRegistry(manifest);
    const skillList = skillReg.descriptions();
    const system = [
      "You are an AI assistant that helps users by answering questions and completing tasks using skills.",
      "",
      "For EVERY new task or request, follow these steps:",
      "1. Find the most relevant skill from:",
      skillList,
      "",
      "2. If a relevant skill exists, use the `load_skill` tool to read its instructions.",
      "3. Follow the skill's instructions exactly to call `run_js`.",
      "4. Present the result to the user.",
      "5. If no skill is relevant, answer directly from your knowledge.",
      "",
      "Output ONLY the final result.",
    ].join("\n");

    const tools: Record<string, ToolFunction> = {
      load_skill: async (args) => {
        const name = String(args.skill_name ?? "").trim();
        const s = skillReg.get(name);
        if (!s) return `Skill '${name}' not found. Available: ${skillReg.names().join(", ")}`;
        return `# Skill: ${s.name}\n\n${s.instructions}`;
      },
      run_js: async (args) => {
        const name = String(args.skill_name ?? "").trim();
        const s = skillReg.get(name);
        if (!s) return `Error: skill '${name}' not found`;
        const data = args.data ?? "{}";
        const res = await skillHostBridge.runSkill(s, { data });
        return skillResultToLlmString(res);
      },
    };
    const toolInstr = [
      "",
      "## AVAILABLE TOOLS",
      "",
      "### load_skill",
      '<tool_call name="load_skill">\n{"skill_name": "the-skill-name"}\n</tool_call>',
      "",
      "### run_js",
      '<tool_call name="run_js">\n{"skill_name": "the-skill-name", "data": "{}"}\n</tool_call>',
      "",
      "When you have the answer, wrap it:",
      "<final_answer>...</final_answer>",
    ].join("\n");

    let raw = "";
    try {
      raw = await runGoal(this.llm, `USER GOAL: ${goal}`, {
        systemPrompt: `${system}\n${toolInstr}`,
        tools,
        maxTurns: manifest.max_turns_per_agent + 2,
        signal: opts.signal,
        onEvent: (e) => this.forwardRunGoalEvent("agentic-flow", e, opts),
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      return stepFailure("agentic-flow", `agentic error: ${msg}`);
    }

    if (raw) {
      bb.put("agentic_output", raw, {
        produced_by: "agentic-flow",
        description: "Full output from agentic skill execution",
      });
    }
    return {
      agent: "agentic-flow",
      produced_keys: raw ? ["agentic_output"] : [],
      raw_output: raw,
      validated: Boolean(raw),
      message: raw ? "ok" : "no output from agentic flow",
      attempts: 0,
    };
  }

  // ────────────────────────────────────────────────────────────────────

  private async prepareJsSkillsContext(
    manifest: CartridgeManifest,
    goal: string,
    bb: Blackboard,
  ): Promise<void> {
    const skillReg = await this.getSkillRegistry(manifest);
    const selected = this.routeToSkill(skillReg, goal);
    const skill = selected ? skillReg.get(selected) : undefined;
    if (skill) {
      bb.put("selected_skill", skill.name, {
        produced_by: "router",
        description: `Selected Gallery JS skill: ${skill.name}`,
      });
      bb.put("skill_instructions", skill.instructions, {
        produced_by: "router",
        description: `SKILL.md instructions for ${skill.name}`,
      });
      bb.put("skill_descriptions", skillReg.descriptions(), {
        produced_by: "registry",
        description: "All available skills with descriptions",
      });
    } else {
      bb.put("selected_skill", "", {
        produced_by: "router",
        description: "No specific skill selected",
      });
      bb.put("skill_instructions", "", {
        produced_by: "router",
        description: "No skill instructions",
      });
      bb.put("skill_descriptions", skillReg.descriptions(), {
        produced_by: "registry",
        description: "All available skills with descriptions",
      });
    }
  }

  /** Keyword-overlap router — LLM-based routing is deferred post-M5. */
  private routeToSkill(skillReg: SkillRegistry, goal: string): string | null {
    const names = skillReg.names();
    if (names.length === 0) return null;
    const goalTokens = tokenize(goal);
    let best = names[0];
    let bestScore = 0;
    for (const name of names) {
      const nameTokens = tokenize(name.replace(/-/g, " "));
      const skill = skillReg.get(name);
      const descTokens = skill ? tokenize(skill.description) : new Set<string>();
      const all = new Set<string>([...nameTokens, ...descTokens]);
      let score = 0;
      for (const t of all) if (goalTokens.has(t)) score++;
      if (score > bestScore) {
        bestScore = score;
        best = name;
      }
    }
    return bestScore > 0 ? best : null;
  }

  private async getSkillRegistry(manifest: CartridgeManifest): Promise<SkillRegistry> {
    const cached = this._skillRegs.get(manifest.name);
    if (cached) return cached;
    const reg = new SkillRegistry();
    const dirs: string[] = [];
    if (manifest.skills_source) dirs.push(manifest.skills_source);
    dirs.push(`${manifest.path}/skills`);
    await reg.scan(...dirs);
    this._skillRegs.set(manifest.name, reg);
    return reg;
  }

  // ────────────────────────────────────────────────────────────────────

  private selectFlow(manifest: CartridgeManifest, goal: string): string {
    const flowNames = Object.keys(manifest.flows);
    if (flowNames.length === 0) throw new Error(`cartridge ${manifest.name} has no flows`);
    const goalTokens = tokenize(goal);
    let best = manifest.default_flow || flowNames[0];
    let bestScore = 0;
    for (const fname of flowNames) {
      const fTokens = tokenize(fname.replace(/-/g, " "));
      let score = 0;
      for (const t of fTokens) if (goalTokens.has(t)) score++;
      if (score > bestScore) {
        bestScore = score;
        best = fname;
      }
    }
    return best;
  }

  private composeTask(spec: AgentSpec, inputDescriptions: string, retryFeedback: string): string {
    let producesClause = "";
    if (spec.produces.length > 0) {
      const jsonKeys = spec.produces.map((k) => `  "${k}": ...`).join(",\n");
      producesClause =
        "\n\n## REQUIRED OUTPUT\n\n" +
        "CRITICAL: You MUST include a `<produces>` JSON block in your response.\n" +
        "Do NOT use write_file. Put the `<produces>` block INSIDE your `<final_answer>` tags.\n\n" +
        `Produce exactly these keys: ${JSON.stringify(spec.produces)}\n` +
        (spec.produces_schema ? `Conform to schema: ${spec.produces_schema}\n` : "") +
        "\nWrap the JSON object in `<produces>` tags, like this:\n\n" +
        "<final_answer>\n<produces>\n{\n" +
        jsonKeys +
        "\n}\n</produces>\n</final_answer>\n\n" +
        "Do NOT put anything between the opening `<produces>` and the `{`. " +
        "Do NOT include commentary inside the JSON.";
    }
    let retryClause = "";
    if (retryFeedback) {
      retryClause =
        "\n\n## RETRY FEEDBACK\n\n" +
        `Previous attempt failed validation: ${retryFeedback}\n` +
        "Fix the issue and produce a compliant `<produces>` block.";
    }
    return (
      `# Agent Role\n\n${spec.body}\n\n` +
      `## INPUTS\n\nYou will receive these blackboard entries:\n${inputDescriptions}\n` +
      producesClause +
      retryClause
    );
  }

  private extractProduced(response: string): Record<string, unknown> | null {
    const candidates: string[] = [];
    const m = PRODUCES_RE.exec(response);
    if (m) candidates.push(m[1].trim());
    for (const fenced of response.matchAll(/```json\s*([\s\S]*?)```/g)) {
      candidates.push(fenced[1].trim());
    }
    const bal = extractFirstJsonObject(response);
    if (bal) candidates.push(bal);
    for (const c of candidates) {
      try {
        const parsed = JSON.parse(c);
        if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
          return parsed as Record<string, unknown>;
        }
      } catch {
        /* next */
      }
    }
    return null;
  }

  private runValidators(
    manifest: CartridgeManifest,
    bb: Blackboard,
    opts: RunOptions,
  ): string[] {
    const messages: string[] = [];
    for (const rel of manifest.validators) {
      const fn = BUILTIN_VALIDATORS[rel];
      if (!fn) {
        messages.push(`validator missing: ${rel}`);
        opts.onEvent?.({ type: "validator", message: `missing: ${rel}`, ok: false });
        continue;
      }
      try {
        const result = fn(bb.snapshot());
        const prefix = result.ok ? "ok" : "FAIL";
        const line = `${prefix} [${rel}]: ${result.message}`;
        messages.push(line);
        opts.onEvent?.({ type: "validator", message: line, ok: result.ok });
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        const line = `validator error [${rel}]: ${msg}`;
        messages.push(line);
        opts.onEvent?.({ type: "validator", message: line, ok: false });
      }
    }
    return messages;
  }

  private renderSummary(
    manifest: CartridgeManifest,
    flowName: string,
    steps: StepResult[],
    validatorMessages: string[],
    bb: Blackboard,
  ): string {
    const lines: string[] = [];
    lines.push("");
    lines.push("============================================================");
    lines.push(`  Cartridge: ${manifest.name}   Flow: ${flowName}`);
    lines.push("============================================================");
    for (const s of steps) {
      const icon = s.validated ? "✅" : "⚠️";
      lines.push(
        `  ${icon} ${s.agent}: ${s.message} (produced=${JSON.stringify(s.produced_keys)}, attempts=${s.attempts + 1})`,
      );
    }
    if (validatorMessages.length > 0) {
      lines.push("");
      lines.push("  Validators:");
      for (const m of validatorMessages) lines.push(`    - ${m}`);
    }
    lines.push("");
    lines.push(`  Blackboard keys: ${JSON.stringify(bb.keys())}`);
    return lines.join("\n");
  }

  private forwardRunGoalEvent(agent: string, e: RunGoalEvent, opts: RunOptions): void {
    if (!opts.onEvent) return;
    if (e.type === "assistant-delta") {
      opts.onEvent({ type: "llm-turn", agent, turn: e.turn ?? 0, delta: e.content });
    } else if (e.type === "tool-call") {
      opts.onEvent({
        type: "tool-call",
        agent,
        tool: e.tool ?? "?",
        args: e.args ?? {},
      });
    } else if (e.type === "tool-result") {
      opts.onEvent({
        type: "tool-result",
        agent,
        tool: e.tool ?? "?",
        result: e.result,
      });
    }
  }

  private makeLLMProxy(): LLMProxy {
    const llm = this.llm;
    return {
      async chat(prompt, options) {
        const messages = options?.system
          ? [
              { role: "system" as const, content: options.system },
              { role: "user" as const, content: prompt },
            ]
          : [{ role: "user" as const, content: prompt }];
        const r = await llm.chat(messages, {
          stream: false,
          temperature: options?.temperature,
          maxTokens: options?.max_tokens,
        });
        return r.content;
      },
      async chatJSON(prompt, schema, options) {
        const suffix = schema
          ? `\n\nRespond with valid JSON matching this schema:\n${JSON.stringify(schema, null, 2)}`
          : "\n\nRespond with valid JSON only. No markdown, no explanation.";
        const messages = options?.system
          ? [
              { role: "system" as const, content: options.system },
              { role: "user" as const, content: prompt + suffix },
            ]
          : [{ role: "user" as const, content: prompt + suffix }];
        const r = await llm.chat(messages, {
          stream: false,
          temperature: 0.1,
          maxTokens: options?.max_tokens,
        });
        const m = /```(?:json)?\s*([\s\S]*?)```/.exec(r.content);
        const cleaned = (m ? m[1] : r.content).trim();
        return JSON.parse(cleaned);
      },
    };
  }
}

// ────────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────────

function stepFailure(agent: string, message: string): StepResult {
  return {
    agent,
    produced_keys: [],
    raw_output: "",
    validated: false,
    message,
    attempts: 0,
  };
}

function extractFirstJsonObject(text: string): string | null {
  const start = text.indexOf("{");
  if (start < 0) return null;
  let depth = 0;
  let inStr = false;
  let escape = false;
  for (let i = start; i < text.length; i++) {
    const c = text[i];
    if (escape) {
      escape = false;
      continue;
    }
    if (c === "\\") {
      escape = true;
      continue;
    }
    if (c === '"') {
      inStr = !inStr;
      continue;
    }
    if (inStr) continue;
    if (c === "{") depth++;
    else if (c === "}") {
      depth--;
      if (depth === 0) return text.slice(start, i + 1);
    }
  }
  return null;
}

// isSkillStep is imported from ./types; re-export so consumers can tree-shake.
export { isSkillStep };
