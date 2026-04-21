/**
 * Offline queue — persists cloud LLM requests that failed with network errors
 * so they can be retried when the device reconnects.
 *
 * M18 uses this from `LLMClient`'s catch path after `withRetry` exhausts.
 * The queue persists to IndexedDB `meta.offline_queue` so backgrounding the
 * app doesn't lose pending work. When `navigator.onLine` flips to true, the
 * queue drains oldest-first; each entry fires its captured `fn` again.
 *
 * v1 scope: queue entries are in-memory callbacks keyed by a string id;
 * persistence stores only the id + projectId + timestamp so rehydration on
 * app restart marks them as abandoned (caller must re-initiate). A future
 * milestone can promote this to fully-serialized request bodies if needed.
 */

import { getMeta, setMeta } from "../storage/db";

export interface QueuedEntry {
  id: string;
  projectId: string;
  enqueued_at: string;
  /** Last error message (displayed in UI toast). */
  lastError?: string;
}

export interface QueuedTask extends QueuedEntry {
  /** Retry fn, held in memory for the lifetime of this session. */
  fn: () => Promise<void>;
}

const META_KEY = "offline_queue";
const inMemory = new Map<string, QueuedTask>();

export async function enqueue(
  projectId: string,
  fn: () => Promise<void>,
  opts: { lastError?: string } = {},
): Promise<string> {
  const id = `oq_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
  const task: QueuedTask = {
    id,
    projectId,
    enqueued_at: new Date().toISOString(),
    lastError: opts.lastError,
    fn,
  };
  inMemory.set(id, task);
  await persist();
  return id;
}

export async function dequeue(id: string): Promise<void> {
  inMemory.delete(id);
  await persist();
}

export function listQueue(): QueuedEntry[] {
  return [...inMemory.values()].map(
    ({ id, projectId, enqueued_at, lastError }) => ({
      id,
      projectId,
      enqueued_at,
      lastError,
    }),
  );
}

/** Drain the queue oldest-first. Stops on the first hard failure. */
export async function flushQueue(): Promise<{ drained: number; remaining: number }> {
  const sorted = [...inMemory.values()].sort((a, b) =>
    a.enqueued_at.localeCompare(b.enqueued_at),
  );
  let drained = 0;
  for (const task of sorted) {
    try {
      await task.fn();
      inMemory.delete(task.id);
      drained++;
    } catch (err) {
      task.lastError = err instanceof Error ? err.message : String(err);
      break;
    }
  }
  await persist();
  return { drained, remaining: inMemory.size };
}

export async function invalidateProject(projectId: string): Promise<void> {
  for (const [id, task] of inMemory) {
    if (task.projectId === projectId) inMemory.delete(id);
  }
  await persist();
}

async function persist(): Promise<void> {
  // Only stable fields — the fn closure lives in memory only.
  const entries: QueuedEntry[] = [...inMemory.values()].map(
    ({ id, projectId, enqueued_at, lastError }) => ({
      id,
      projectId,
      enqueued_at,
      lastError,
    }),
  );
  await setMeta(META_KEY, entries).catch(() => {});
}

export async function loadPersistedQueueSummary(): Promise<QueuedEntry[]> {
  return (await getMeta<QueuedEntry[]>(META_KEY)) ?? [];
}

/**
 * Wire up online/offline listeners so the queue auto-flushes when connectivity
 * returns. Safe to call multiple times — idempotent.
 */
let wired = false;
export function installOnlineListeners(): void {
  if (wired) return;
  if (typeof window === "undefined") return;
  window.addEventListener("online", () => {
    void flushQueue();
  });
  wired = true;
}
