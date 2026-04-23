/**
 * Teachings — per-recipe corrections captured via the post-run
 * "Teach this Recipe" affordance.
 *
 * Conceptually these live alongside SmartMemory experiences but serve a
 * different role: experiences are *what happened*, teachings are *what
 * the user said should happen differently next time*. They compound
 * per-cartridge and drive the learning patina (visible count on each
 * recipe tile) as well as — future work — agent prompt preambles so the
 * recipe actually acts on the correction on subsequent runs.
 */

import { getDB, type TeachingRecord } from "../storage/db";

export type { TeachingRecord };

function newTeachingId(): string {
  return `tch_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
}

export interface AddTeachingInput {
  cartridge: string;
  text: string;
  target_step?: string;
}

export async function addTeaching(input: AddTeachingInput): Promise<TeachingRecord> {
  const rec: TeachingRecord = {
    id: newTeachingId(),
    cartridge: input.cartridge,
    text: input.text.trim(),
    target_step: input.target_step?.trim() || undefined,
    created_at: new Date().toISOString(),
    active: true,
  };
  const db = await getDB();
  await db.put("teachings", rec);
  return rec;
}

export async function listTeachingsForCartridge(
  cartridge: string,
): Promise<TeachingRecord[]> {
  const db = await getDB();
  const all = await db.getAllFromIndex("teachings", "by-cartridge", cartridge);
  return all.sort((a, b) => b.created_at.localeCompare(a.created_at));
}

export async function countActiveTeachings(cartridge: string): Promise<number> {
  const all = await listTeachingsForCartridge(cartridge);
  return all.reduce((n, t) => (t.active ? n + 1 : n), 0);
}

/** Count active teachings for every cartridge in one pass. */
export async function countActiveTeachingsAll(): Promise<Record<string, number>> {
  const db = await getDB();
  const all = await db.getAll("teachings");
  const out: Record<string, number> = {};
  for (const t of all) {
    if (!t.active) continue;
    out[t.cartridge] = (out[t.cartridge] ?? 0) + 1;
  }
  return out;
}

export async function setTeachingActive(id: string, active: boolean): Promise<void> {
  const db = await getDB();
  const rec = await db.get("teachings", id);
  if (!rec) return;
  rec.active = active;
  await db.put("teachings", rec);
}

export async function deleteTeaching(id: string): Promise<void> {
  const db = await getDB();
  await db.delete("teachings", id);
}
