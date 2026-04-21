/**
 * Run checkpoint — persist partial cartridge-run state between step boundaries
 * so a backgrounded/killed app can resume from where it left off.
 *
 * iOS WKWebView aggressively suspends JavaScript when an app backgrounds;
 * M17 captures the blackboard + completed-step list after every `step-end`
 * event and clears on `run-end`. On app start, `runProject()` checks for an
 * existing checkpoint and offers "Resume?" (UI hook in ProjectSwiper).
 *
 * Shape is intentionally small: Blackboard.snapshot() values + completed
 * step names + (cartridge, flow, goal) + the provider id/model used. API
 * keys are never serialized.
 */

import {
  deleteCheckpoint,
  getCheckpoint,
  listCheckpoints,
  putCheckpoint,
  type CheckpointRecord,
} from "../storage/db";
import type { BlackboardSnapshot } from "../cartridge/types";

export interface CheckpointInput {
  projectId: string;
  cartridge: string;
  flow: string;
  goal: string;
  blackboard: BlackboardSnapshot;
  completedSteps: string[];
  providerId?: string;
  providerModel?: string;
}

export async function saveCheckpoint(input: CheckpointInput): Promise<void> {
  const now = new Date().toISOString();
  const existing = await getCheckpoint(input.projectId);
  const rec: CheckpointRecord = {
    id: input.projectId,
    project_id: input.projectId,
    cartridge: input.cartridge,
    flow: input.flow,
    goal: input.goal,
    blackboard: input.blackboard as Record<string, unknown>,
    completed_steps: input.completedSteps,
    provider_id: input.providerId,
    provider_model: input.providerModel,
    created_at: existing?.created_at ?? now,
    updated_at: now,
  };
  await putCheckpoint(rec);
}

export async function loadCheckpoint(projectId: string): Promise<CheckpointRecord | undefined> {
  return getCheckpoint(projectId);
}

export async function clearCheckpoint(projectId: string): Promise<void> {
  await deleteCheckpoint(projectId);
}

export async function listAllCheckpoints(): Promise<CheckpointRecord[]> {
  return listCheckpoints();
}
