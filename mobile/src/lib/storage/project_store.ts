/**
 * Projects persistence layer.
 *
 * Stores full project records (metadata + card list) in the IndexedDB
 * `projects` object store. M7 additionally re-serializes each project as a
 * tree of markdown files under files/projects/<id>/… for desktop
 * round-tripping; that is intentionally not done here to keep writes cheap.
 */

import type { ProjectCard } from "../state/projects.svelte";
import { getDB, type ProjectRecord } from "./db";

export interface StoredProject extends ProjectRecord {
  cards: ProjectCard[];
}

export async function listProjectRecords(): Promise<StoredProject[]> {
  const db = await getDB();
  const all = (await db.getAll("projects")) as unknown as StoredProject[];
  return all;
}

export async function putProjectRecord(p: StoredProject): Promise<void> {
  const db = await getDB();
  await db.put("projects", p as unknown as ProjectRecord);
}

export async function deleteProjectRecord(id: string): Promise<void> {
  const db = await getDB();
  await db.delete("projects", id);
}

export async function getProjectRecord(id: string): Promise<StoredProject | undefined> {
  const db = await getDB();
  const rec = (await db.get("projects", id)) as unknown as StoredProject | undefined;
  return rec;
}
