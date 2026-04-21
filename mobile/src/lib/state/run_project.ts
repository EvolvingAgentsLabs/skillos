/**
 * runProject — orchestrates a cartridge run for a given project and wires the
 * CartridgeRunner's event stream to the reactive card state, the live run log,
 * and the SmartMemory append.
 */

import { CartridgeRegistry } from "../cartridge/registry";
import { CartridgeRunner, type RunEvent } from "../cartridge/runner";
import { buildProvider } from "../llm/build_provider";
import { recordExperience } from "../memory/smart_memory";
import { loadProviderConfig, type ProviderConfigStored } from "./provider_config";
import {
  addCard,
  moveCard,
  projects,
  type Lane,
  type Project,
  type ProjectCard,
} from "./projects.svelte";
import { beginRun, endRun, pushEvent } from "./run_events.svelte";

export interface RunProjectOptions {
  /** Override provider config instead of reading from IndexedDB. */
  providerConfig?: ProviderConfigStored;
  /** Override the goal (otherwise uses the first goal card in Planned/Executing). */
  goalOverride?: string;
  /** Shared registry — will be created if omitted. */
  registry?: CartridgeRegistry;
  signal?: AbortSignal;
}

export interface RunOutcome {
  ok: boolean;
  message: string;
  durationSeconds: number;
}

function firstGoalCard(p: Project): ProjectCard | undefined {
  // Most-recent goal in planned/executing, else any goal.
  const sorted = [...p.cards].sort((a, b) => b.created_at.localeCompare(a.created_at));
  return (
    sorted.find((c) => c.kind === "goal" && (c.lane === "planned" || c.lane === "executing")) ??
    sorted.find((c) => c.kind === "goal")
  );
}

export async function runProject(
  projectId: string,
  opts: RunProjectOptions = {},
): Promise<RunOutcome> {
  const project = projects.items.find((p) => p.id === projectId);
  if (!project) return { ok: false, message: "project not found", durationSeconds: 0 };
  if (!project.cartridge) {
    return {
      ok: false,
      message: "project has no cartridge configured",
      durationSeconds: 0,
    };
  }

  const cfg = opts.providerConfig ?? (await loadProviderConfig(projectId));
  if (!cfg) {
    return {
      ok: false,
      message: "provider not configured for this project",
      durationSeconds: 0,
    };
  }

  const goalCard = firstGoalCard(project);
  const goal = opts.goalOverride ?? goalCard?.title ?? project.name;

  // Move the goal card → executing.
  if (goalCard && goalCard.lane !== "executing") {
    await moveCard(projectId, goalCard.id, "executing");
  }

  const cartridgeName: string = project.cartridge;
  const registry = opts.registry ?? new CartridgeRegistry();
  if (!registry.get(cartridgeName)) await registry.init();

  const llm = await buildProvider(cfg);
  const runner = new CartridgeRunner(registry, llm);

  beginRun(projectId);
  const stepCardByAgent = new Map<string, string>(); // agent → card id
  const startedAt = Date.now();

  async function onEvent(e: RunEvent): Promise<void> {
    pushEvent(e);
    switch (e.type) {
      case "step-start": {
        const card = await addCard(projectId, {
          kind: inferKind(e.agent, cartridgeName),
          lane: "executing",
          title: e.agent,
          subtitle: "running…",
          produced_by: "runner",
        });
        if (card) stepCardByAgent.set(e.agent, card.id);
        break;
      }
      case "blackboard-put":
        if (e.ok) {
          await addCard(projectId, {
            kind: "document",
            lane: "done",
            title: e.key,
            subtitle: e.message,
            produced_by: e.agent,
          });
        }
        break;
      case "step-end": {
        const cid = stepCardByAgent.get(e.step.agent);
        if (cid) {
          const lane: Lane = e.step.validated ? "done" : "executing";
          await moveCard(projectId, cid, lane);
        }
        break;
      }
      case "run-end":
        if (goalCard) {
          await moveCard(projectId, goalCard.id, "done");
        }
        break;
    }
  }

  try {
    const result = await runner.run(cartridgeName, goal, {
      signal: opts.signal,
      onEvent: (e) => {
        // Fire-and-forget; the handler is ordered by awaiting each addCard
        // inside the switch, but we don't block the runner. Mutations are
        // applied through the rune store so the UI sees them immediately.
        void onEvent(e);
      },
    });
    const duration = Math.round((Date.now() - startedAt) / 1000);
    const components = Array.from(
      new Set(result.steps.map((s) => s.agent).concat(result.steps.flatMap((s) => s.produced_keys))),
    );
    await recordExperience({
      session_id: `sess_${startedAt.toString(36)}`,
      project: project.name,
      goal,
      outcome: result.ok ? "success" : "partial",
      components_used: components,
      duration_seconds: duration,
      output_summary: result.final_summary,
    });
    endRun();
    return {
      ok: result.ok,
      message: result.ok ? "run completed" : "run completed with issues",
      durationSeconds: duration,
    };
  } catch (err) {
    endRun();
    const msg = err instanceof Error ? err.message : String(err);
    const duration = Math.round((Date.now() - startedAt) / 1000);
    await recordExperience({
      session_id: `sess_${startedAt.toString(36)}`,
      project: project.name,
      goal,
      outcome: "failure",
      components_used: [],
      duration_seconds: duration,
      output_summary: msg,
    });
    return { ok: false, message: msg, durationSeconds: duration };
  }
}

function inferKind(
  agentName: string,
  _cartridge: string,
): ProjectCard["kind"] {
  // js-executor + any Gallery skill renders as a "skill" card; everything else
  // an agent. The heuristic is intentionally thin — we just need the right icon
  // on the lifecycle cards.
  if (agentName === "js-executor" || agentName === "agentic-flow") return "skill";
  if (agentName.endsWith("-skill") || agentName.includes("/")) return "skill";
  return "agent";
}
