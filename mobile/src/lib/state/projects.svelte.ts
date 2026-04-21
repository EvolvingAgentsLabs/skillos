/**
 * In-memory reactive project store.
 *
 * The UI reads `projects` directly (Svelte rune). Mutations write through to
 * IndexedDB via project_store.ts; subsequent app launches rehydrate from disk.
 */

import {
  deleteProjectRecord,
  listProjectRecords,
  putProjectRecord,
  type StoredProject,
} from "../storage/project_store";

export type CardKind = "goal" | "agent" | "skill" | "document";
export type Lane = "planned" | "executing" | "done";

export interface ProjectCard {
  id: string;
  kind: CardKind;
  lane: Lane;
  title: string;
  subtitle?: string;
  produced_by?: string;
  schema_ref?: string;
  created_at: string;
  /** For document cards: raw blackboard value. */
  data?: unknown;
}

export interface Project {
  id: string;
  name: string;
  cartridge: string | null;
  created_at: string;
  updated_at: string;
  cards: ProjectCard[];
}

export const projects = $state<{ items: Project[]; loaded: boolean }>({
  items: [],
  loaded: false,
});

function newId(prefix: string): string {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
}

function nowIso(): string {
  return new Date().toISOString();
}

function toStored(p: Project): StoredProject {
  return {
    id: p.id,
    name: p.name,
    cartridge: p.cartridge,
    created_at: p.created_at,
    updated_at: p.updated_at,
    cards: p.cards,
  };
}

function fromStored(s: StoredProject): Project {
  return {
    id: s.id,
    name: s.name,
    cartridge: s.cartridge,
    created_at: s.created_at,
    updated_at: s.updated_at,
    cards: Array.isArray(s.cards) ? s.cards : [],
  };
}

export async function loadProjects(): Promise<void> {
  const stored = await listProjectRecords();
  projects.items = stored
    .map(fromStored)
    .sort((a, b) => b.updated_at.localeCompare(a.updated_at));
  projects.loaded = true;
}

export async function createProject(opts: {
  name: string;
  cartridge: string | null;
  initialGoal?: string;
}): Promise<Project> {
  const now = nowIso();
  const id = newId("prj");
  const cards: ProjectCard[] = [];
  if (opts.initialGoal && opts.initialGoal.trim()) {
    cards.push({
      id: newId("card"),
      kind: "goal",
      lane: "planned",
      title: opts.initialGoal.trim(),
      produced_by: "user",
      created_at: now,
    });
  }
  const p: Project = {
    id,
    name: opts.name.trim() || "Untitled project",
    cartridge: opts.cartridge,
    created_at: now,
    updated_at: now,
    cards,
  };
  projects.items = [p, ...projects.items];
  await putProjectRecord(toStored(p));
  return p;
}

async function persist(p: Project): Promise<void> {
  p.updated_at = nowIso();
  await putProjectRecord(toStored(p));
}

export async function deleteProject(projectId: string): Promise<void> {
  projects.items = projects.items.filter((p) => p.id !== projectId);
  await deleteProjectRecord(projectId);
}

export async function addCard(
  projectId: string,
  card: Omit<ProjectCard, "id" | "created_at">,
): Promise<ProjectCard | undefined> {
  const p = projects.items.find((x) => x.id === projectId);
  if (!p) return undefined;
  const full: ProjectCard = {
    id: newId("card"),
    created_at: nowIso(),
    ...card,
  };
  p.cards = [...p.cards, full];
  await persist(p);
  return full;
}

export async function moveCard(
  projectId: string,
  cardId: string,
  lane: Lane,
): Promise<void> {
  const p = projects.items.find((x) => x.id === projectId);
  if (!p) return;
  const idx = p.cards.findIndex((c) => c.id === cardId);
  if (idx < 0) return;
  if (p.cards[idx].lane === lane) return;
  p.cards[idx] = { ...p.cards[idx], lane };
  p.cards = [...p.cards];
  await persist(p);
}

export async function removeCard(projectId: string, cardId: string): Promise<void> {
  const p = projects.items.find((x) => x.id === projectId);
  if (!p) return;
  p.cards = p.cards.filter((c) => c.id !== cardId);
  await persist(p);
}

export function laneCards(project: Project, lane: Lane): ProjectCard[] {
  return project.cards.filter((c) => c.lane === lane);
}
