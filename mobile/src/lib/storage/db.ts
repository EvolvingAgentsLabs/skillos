/**
 * IndexedDB schema v1.
 *
 * Object stores:
 *   files       — seeded + user-edited markdown/yaml/schema/json content, keyed by posix path
 *   projects    — per-project state snapshots
 *   blackboards — serialized blackboards (cartridge run outputs)
 *   memory      — SmartMemory experience log entries
 *   secrets     — provider keys and per-skill secrets
 *   meta        — app-level key/value (seed_version, etc.)
 */

import { type DBSchema, type IDBPDatabase, openDB } from "idb";

export interface ModelBlobRecord {
  id: string;
  blob: ArrayBuffer;
  size: number;
  sha256?: string;
  downloaded_at: string;
  /** Backend the blob is for; duplicated from catalog for resilience. */
  backend: "wllama" | "litert" | "chrome-prompt-api";
  /** Optional native file path for LiteRT (M10 fills this after copy to cache). */
  native_path?: string;
}

export interface CheckpointRecord {
  /** Equal to `project_id` — one live checkpoint per project. */
  id: string;
  project_id: string;
  cartridge: string;
  flow: string;
  goal: string;
  /** Blackboard snapshot at the last completed step boundary. */
  blackboard: Record<string, unknown>;
  /** Names of steps that have completed successfully so far. */
  completed_steps: string[];
  /** Which provider the run was using (id + model only; keys never serialized). */
  provider_id?: string;
  provider_model?: string;
  created_at: string;
  updated_at: string;
}

export interface FileRecord {
  path: string;
  content: ArrayBuffer;
  sha1: string;
  size: number;
  updated_at: string;
  /**
   * M12: true when a user edit wrote this file. Seed-refresh skips paths
   * with this flag so we don't overwrite customizations on app updates.
   */
  user_edited?: boolean;
}

export interface ProjectRecord {
  id: string;
  name: string;
  cartridge: string | null;
  created_at: string;
  updated_at: string;
}

export interface BlackboardRecord {
  id: string;
  project_id: string;
  run_id: string;
  cartridge: string;
  flow: string;
  snapshot: Record<string, unknown>;
  created_at: string;
}

export interface MemoryRecord {
  experience_id: string;
  timestamp: string;
  session_id: string;
  project: string;
  goal: string;
  outcome: "success" | "partial" | "failure" | "success_with_recovery";
  components_used: string[];
  quality_score: number;
  cost_estimate_usd: number;
  duration_seconds: number;
  output_summary?: string;
  learnings?: string;
}

export interface SecretRecord {
  key: string;
  value: string;
  updated_at: string;
}

export interface MetaRecord {
  key: string;
  value: unknown;
}

/**
 * TeachingRecord — a user-supplied correction attached to a Recipe (cartridge),
 * created via the post-run "Teach this Recipe" affordance. Teachings are the
 * substrate of the per-recipe learning patina: their count is what the UI
 * shows as "learned N things from you", and they are (future work) prepended
 * to agent prompts when the recipe runs.
 */
export interface TeachingRecord {
  id: string;
  cartridge: string;
  text: string;
  /** Optional agent/step the correction applies to. Empty = applies to whole recipe. */
  target_step?: string;
  created_at: string;
  /** Soft-delete flag; retain history even when the user dismisses one. */
  active: boolean;
}

interface SkillOSDB extends DBSchema {
  files: {
    key: string;
    value: FileRecord;
    indexes: { "by-prefix": string };
  };
  projects: {
    key: string;
    value: ProjectRecord;
  };
  blackboards: {
    key: string;
    value: BlackboardRecord;
    indexes: { "by-project": string };
  };
  memory: {
    key: string;
    value: MemoryRecord;
    indexes: { "by-project": string };
  };
  secrets: {
    key: string;
    value: SecretRecord;
  };
  meta: {
    key: string;
    value: MetaRecord;
  };
  models: {
    key: string;
    value: ModelBlobRecord;
  };
  checkpoints: {
    key: string;
    value: CheckpointRecord;
  };
  teachings: {
    key: string;
    value: TeachingRecord;
    indexes: { "by-cartridge": string };
  };
}

const DB_NAME = "skillos";
const DB_VERSION = 4;

let _dbPromise: Promise<IDBPDatabase<SkillOSDB>> | null = null;

/** Test helper: reset cached DB handle (after swapping indexedDB impl). */
export function _resetDBForTests(): void {
  _dbPromise = null;
}

export function getDB(): Promise<IDBPDatabase<SkillOSDB>> {
  if (!_dbPromise) {
    _dbPromise = openDB<SkillOSDB>(DB_NAME, DB_VERSION, {
      upgrade(db, _oldVersion) {
        if (!db.objectStoreNames.contains("files")) {
          const store = db.createObjectStore("files", { keyPath: "path" });
          store.createIndex("by-prefix", "path");
        }
        if (!db.objectStoreNames.contains("projects")) {
          db.createObjectStore("projects", { keyPath: "id" });
        }
        if (!db.objectStoreNames.contains("blackboards")) {
          const store = db.createObjectStore("blackboards", { keyPath: "id" });
          store.createIndex("by-project", "project_id");
        }
        if (!db.objectStoreNames.contains("memory")) {
          const store = db.createObjectStore("memory", { keyPath: "experience_id" });
          store.createIndex("by-project", "project");
        }
        if (!db.objectStoreNames.contains("secrets")) {
          db.createObjectStore("secrets", { keyPath: "key" });
        }
        if (!db.objectStoreNames.contains("meta")) {
          db.createObjectStore("meta", { keyPath: "key" });
        }
        // v2: on-device model blob store. Separate from `files` because
        // entries are 0.5–2 GB and would skew the sha1/path contract.
        if (!db.objectStoreNames.contains("models")) {
          db.createObjectStore("models", { keyPath: "id" });
        }
        // v3: partial-run checkpoints (M17). Keyed by project id.
        if (!db.objectStoreNames.contains("checkpoints")) {
          db.createObjectStore("checkpoints", { keyPath: "id" });
        }
        // v4: per-recipe teachings (post-run corrections). Keyed by id with
        // a by-cartridge index so the learning patina can count in O(log n).
        if (!db.objectStoreNames.contains("teachings")) {
          const store = db.createObjectStore("teachings", { keyPath: "id" });
          store.createIndex("by-cartridge", "cartridge");
        }
      },
    });
  }
  return _dbPromise;
}

// ─────────────────────────────────────────────────────────────────────
// Model blob helpers (v2)

export async function putModelBlob(rec: ModelBlobRecord): Promise<void> {
  const db = await getDB();
  await db.put("models", rec);
}

export async function getModelBlob(id: string): Promise<ModelBlobRecord | undefined> {
  const db = await getDB();
  return db.get("models", id);
}

export async function listModelBlobs(): Promise<ModelBlobRecord[]> {
  const db = await getDB();
  return db.getAll("models");
}

export async function deleteModelBlob(id: string): Promise<void> {
  const db = await getDB();
  await db.delete("models", id);
}

// ─────────────────────────────────────────────────────────────────────
// Checkpoint helpers (v3) — one live checkpoint per project.

export async function putCheckpoint(rec: CheckpointRecord): Promise<void> {
  const db = await getDB();
  await db.put("checkpoints", rec);
}

export async function getCheckpoint(projectId: string): Promise<CheckpointRecord | undefined> {
  const db = await getDB();
  return db.get("checkpoints", projectId);
}

export async function listCheckpoints(): Promise<CheckpointRecord[]> {
  const db = await getDB();
  return db.getAll("checkpoints");
}

export async function deleteCheckpoint(projectId: string): Promise<void> {
  const db = await getDB();
  await db.delete("checkpoints", projectId);
}

// ─────────────────────────────────────────────────────────────────────
// File helpers

async function toArrayBuffer(input: Blob | string | ArrayBuffer | Uint8Array): Promise<ArrayBuffer> {
  if (input instanceof ArrayBuffer) return input;
  if (input instanceof Uint8Array) {
    const copy = new Uint8Array(input.byteLength);
    copy.set(input);
    return copy.buffer;
  }
  if (typeof input === "string") {
    return new TextEncoder().encode(input).buffer;
  }
  return await input.arrayBuffer();
}

export async function putFile(
  filePath: string,
  content: Blob | string | ArrayBuffer | Uint8Array,
  opts: { sha1?: string; user_edited?: boolean } = {},
): Promise<void> {
  const buf = await toArrayBuffer(content);
  const record: FileRecord = {
    path: filePath,
    content: buf,
    sha1: opts.sha1 ?? "",
    size: buf.byteLength,
    updated_at: new Date().toISOString(),
    user_edited: opts.user_edited === true ? true : undefined,
  };
  const db = await getDB();
  await db.put("files", record);
}

export async function deleteFile(filePath: string): Promise<void> {
  const db = await getDB();
  await db.delete("files", filePath);
}

export async function getFile(filePath: string): Promise<FileRecord | undefined> {
  const db = await getDB();
  return db.get("files", filePath);
}

export async function getFileText(filePath: string): Promise<string | undefined> {
  const rec = await getFile(filePath);
  if (!rec) return undefined;
  return new TextDecoder("utf-8").decode(rec.content);
}

export async function listFiles(prefix = ""): Promise<string[]> {
  const db = await getDB();
  const all = await db.getAllKeys("files");
  if (!prefix) return all as string[];
  return (all as string[]).filter((k) => k.startsWith(prefix));
}

export async function fileCount(): Promise<number> {
  const db = await getDB();
  return await db.count("files");
}

// ─────────────────────────────────────────────────────────────────────
// Meta helpers

export async function getMeta<T = unknown>(key: string): Promise<T | undefined> {
  const db = await getDB();
  const rec = await db.get("meta", key);
  return rec?.value as T | undefined;
}

export async function setMeta(key: string, value: unknown): Promise<void> {
  const db = await getDB();
  await db.put("meta", { key, value });
}
