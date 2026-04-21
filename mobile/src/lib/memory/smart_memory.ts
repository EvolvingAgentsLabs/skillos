/**
 * SmartMemory — TS port of the append-only experience log at
 * C:\evolvingagents\skillos\system\SmartMemory.md.
 *
 * Each run of a cartridge appends a record; downstream surfaces (project
 * history, evals, cost tracking) query the `memory` store.
 */

import { getDB, type MemoryRecord } from "../storage/db";

export type Outcome =
  | "success"
  | "partial"
  | "failure"
  | "success_with_recovery";

export interface RecordExperienceInput {
  session_id: string;
  project: string;
  goal: string;
  outcome: Outcome;
  components_used: string[];
  quality_score?: number;
  cost_estimate_usd?: number;
  duration_seconds: number;
  output_summary?: string;
  learnings?: string;
}

function newExperienceId(): string {
  return `exp_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
}

export async function recordExperience(input: RecordExperienceInput): Promise<MemoryRecord> {
  const rec: MemoryRecord = {
    experience_id: newExperienceId(),
    timestamp: new Date().toISOString(),
    session_id: input.session_id,
    project: input.project,
    goal: input.goal,
    outcome: input.outcome,
    components_used: [...input.components_used],
    quality_score: input.quality_score ?? 0,
    cost_estimate_usd: input.cost_estimate_usd ?? 0,
    duration_seconds: input.duration_seconds,
    output_summary: input.output_summary,
    learnings: input.learnings,
  };
  const db = await getDB();
  await db.put("memory", rec);
  return rec;
}

export async function listExperiences(): Promise<MemoryRecord[]> {
  const db = await getDB();
  const all = await db.getAll("memory");
  return all.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
}

export async function experiencesForProject(project: string): Promise<MemoryRecord[]> {
  const db = await getDB();
  const all = await db.getAllFromIndex("memory", "by-project", project);
  return all.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
}

/**
 * Render a single experience back to the SmartMemory.md frontmatter form.
 * Used by the M7 file-sync export.
 */
export function renderExperienceMarkdown(rec: MemoryRecord): string {
  const lines: string[] = [];
  lines.push("---");
  lines.push(`experience_id: ${rec.experience_id}`);
  lines.push(`timestamp: ${rec.timestamp}`);
  lines.push(`session_id: ${rec.session_id}`);
  lines.push(`project: ${rec.project}`);
  lines.push(`goal: ${JSON.stringify(rec.goal)}`);
  lines.push(`outcome: ${rec.outcome}`);
  lines.push(`components_used: ${JSON.stringify(rec.components_used)}`);
  lines.push(`quality_score: ${rec.quality_score}`);
  lines.push(`cost_estimate_usd: ${rec.cost_estimate_usd}`);
  lines.push(`duration_seconds: ${rec.duration_seconds}`);
  lines.push("---");
  lines.push("");
  if (rec.output_summary) {
    lines.push("## Output Summary");
    lines.push("");
    lines.push(rec.output_summary);
    lines.push("");
  }
  if (rec.learnings) {
    lines.push("## Learnings");
    lines.push("");
    lines.push(rec.learnings);
    lines.push("");
  }
  return lines.join("\n");
}
