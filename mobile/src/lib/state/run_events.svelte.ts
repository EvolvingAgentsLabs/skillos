/**
 * Reactive stream of the most recent RunEvents for the UI (run log drawer).
 * Separate from the per-project card state so streaming deltas don't thrash
 * IndexedDB writes.
 */

import type { RunEvent } from "../cartridge/runner";

export const runStream = $state<{
  projectId: string | null;
  running: boolean;
  events: RunEvent[];
  currentAssistant: string;
}>({
  projectId: null,
  running: false,
  events: [],
  currentAssistant: "",
});

const MAX_EVENTS = 200;

export function beginRun(projectId: string): void {
  runStream.projectId = projectId;
  runStream.running = true;
  runStream.events = [];
  runStream.currentAssistant = "";
}

export function pushEvent(e: RunEvent): void {
  runStream.events = [...runStream.events.slice(-MAX_EVENTS + 1), e];
  if (e.type === "llm-turn" && typeof e.delta === "string") {
    runStream.currentAssistant += e.delta;
  } else if (e.type === "step-start" || e.type === "tool-call" || e.type === "step-end") {
    runStream.currentAssistant = "";
  }
}

export function endRun(): void {
  runStream.running = false;
}
