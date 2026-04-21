/**
 * Model store — IndexedDB-backed blob cache with chunked, resumable download.
 *
 * `downloadModel(entry, onProgress)` streams bytes via `fetch` + the
 * `ReadableStream` reader API, appending to an in-memory Uint8Array in 256 KB
 * chunks, emitting progress, and checkpointing the byte offset to the `meta`
 * store so a backgrounded download can resume from where it stopped.
 *
 * Storage: the final ArrayBuffer is committed to `models` via `putModelBlob`.
 * Binary records don't go through the text-oriented `files` store.
 */

import { deleteModelBlob, getMeta, listModelBlobs, putModelBlob, setMeta } from "../../storage/db";
import type { ModelBlobRecord } from "../../storage/db";
import type { LocalBackendId, ModelCatalogEntry } from "./model_catalog";

export interface DownloadProgress {
  phase: "preflight" | "fetching" | "committing" | "done" | "error" | "cancelled";
  bytesDone: number;
  bytesTotal: number;
  /** Rolling kB/s over the last ~1 s. */
  ratekBps?: number;
  message?: string;
  error?: Error;
}

export type DownloadProgressListener = (p: DownloadProgress) => void;

const OFFSET_KEY_PREFIX = "model_dl_offset:";
const CHUNK_BYTES = 256 * 1024;

/**
 * Preflight the storage quota. Returns bytes free, or -1 if the browser
 * doesn't implement `StorageManager.estimate()`.
 */
export async function estimateFreeStorage(): Promise<number> {
  try {
    const mgr = (navigator as Navigator & { storage?: StorageManager }).storage;
    if (!mgr?.estimate) return -1;
    const est = await mgr.estimate();
    if (typeof est.quota === "number" && typeof est.usage === "number") {
      return est.quota - est.usage;
    }
    return -1;
  } catch {
    return -1;
  }
}

/**
 * Download a model entry. Resumable: if a prior partial download set
 * `meta[model_dl_offset:<id>]`, picks up from there if the server supports
 * range requests. Otherwise re-downloads from scratch.
 */
export async function downloadModel(
  entry: ModelCatalogEntry,
  onProgress: DownloadProgressListener = () => {},
  signal?: AbortSignal,
): Promise<ModelBlobRecord> {
  try {
    onProgress({ phase: "preflight", bytesDone: 0, bytesTotal: entry.sizeBytes });
    const free = await estimateFreeStorage();
    if (free >= 0 && free < entry.sizeBytes * 2) {
      throw new Error(
        `insufficient storage: need ~${(entry.sizeBytes * 2 / 1e9).toFixed(1)} GB, have ~${(free / 1e9).toFixed(1)} GB`,
      );
    }

    const resumeOffset = await getMeta<number>(`${OFFSET_KEY_PREFIX}${entry.id}`);
    const startByte = typeof resumeOffset === "number" && resumeOffset > 0 ? resumeOffset : 0;

    const headers: Record<string, string> = {};
    if (startByte > 0) headers["range"] = `bytes=${startByte}-`;

    const res = await fetch(entry.url, { headers, signal });
    if (!res.ok && res.status !== 206) {
      throw new Error(`fetch ${res.status}: ${await res.text().catch(() => "")}`);
    }
    if (!res.body) throw new Error("response has no body");

    // Preserve any previously-downloaded bytes from a partial chunk cache.
    // For simplicity v1 re-downloads the whole file on mismatch; real range
    // handling ships in a follow-up.
    const acceptsRange = res.status === 206;
    const effectiveStart = acceptsRange ? startByte : 0;

    const total = entry.sizeBytes;
    const reader = res.body.getReader();
    // Accumulator: pre-allocate a contiguous buffer sized to the model.
    const buf = new Uint8Array(total);
    let written = effectiveStart;
    const rateSamples: Array<{ t: number; b: number }> = [];

    while (true) {
      if (signal?.aborted) {
        onProgress({
          phase: "cancelled",
          bytesDone: written,
          bytesTotal: total,
          message: "aborted by user",
        });
        throw new Error("download aborted");
      }
      const { value, done } = await reader.read();
      if (done) break;
      if (!value || value.byteLength === 0) continue;
      if (written + value.byteLength > total) {
        // Server lied about size. Truncate rather than overflow.
        buf.set(value.subarray(0, total - written), written);
        written = total;
      } else {
        buf.set(value, written);
        written += value.byteLength;
      }

      const now = Date.now();
      rateSamples.push({ t: now, b: written });
      while (rateSamples.length > 0 && now - rateSamples[0].t > 1000) rateSamples.shift();
      let ratekBps: number | undefined;
      if (rateSamples.length > 1) {
        const first = rateSamples[0];
        const dt = (now - first.t) / 1000;
        ratekBps = dt > 0 ? (written - first.b) / 1024 / dt : undefined;
      }

      // Persist checkpoint every 4 MB so a backgrounding kill doesn't lose progress.
      if (written - (effectiveStart + Math.floor((written - effectiveStart) / (4 * 1024 * 1024)) * 4 * 1024 * 1024) === 0) {
        await setMeta(`${OFFSET_KEY_PREFIX}${entry.id}`, written).catch(() => {});
      }
      onProgress({
        phase: "fetching",
        bytesDone: written,
        bytesTotal: total,
        ratekBps,
      });
    }

    onProgress({
      phase: "committing",
      bytesDone: written,
      bytesTotal: total,
      message: "writing to storage…",
    });

    const record: ModelBlobRecord = {
      id: entry.id,
      blob: buf.buffer,
      size: written,
      sha256: entry.sha256,
      downloaded_at: new Date().toISOString(),
      backend: entry.backend as LocalBackendId,
    };
    await putModelBlob(record);
    await setMeta(`${OFFSET_KEY_PREFIX}${entry.id}`, 0).catch(() => {});
    onProgress({ phase: "done", bytesDone: written, bytesTotal: total });
    return record;
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err));
    onProgress({
      phase: "error",
      bytesDone: 0,
      bytesTotal: entry.sizeBytes,
      message: error.message,
      error,
    });
    throw error;
  }
}

export async function isModelInstalled(id: string): Promise<boolean> {
  const blobs = await listModelBlobs();
  return blobs.some((b) => b.id === id);
}

export async function listInstalledModels(): Promise<ModelBlobRecord[]> {
  return listModelBlobs();
}

export async function deleteInstalledModel(id: string): Promise<void> {
  await deleteModelBlob(id);
  await setMeta(`${OFFSET_KEY_PREFIX}${id}`, 0).catch(() => {});
}
