/**
 * First-boot seeding.
 *
 * Reads /seed/manifest.json (written by scripts/seed-build.mjs) and fetches every
 * listed file into IndexedDB `files`. Idempotent: skipped when `meta.seed_version`
 * matches the manifest version already in the DB.
 */

import { fileCount, getMeta, putFile, setMeta } from "./db";

export interface SeedManifestEntry {
  path: string;
  sha1: string;
  size: number;
}

export interface SeedManifest {
  seed_version: string;
  source_root: string;
  file_count: number;
  files: SeedManifestEntry[];
}

export interface SeedProgress {
  phase: "idle" | "fetching-manifest" | "seeding" | "done" | "skipped" | "error";
  completed: number;
  total: number;
  current?: string;
  message?: string;
  error?: Error;
}

export type SeedProgressListener = (p: SeedProgress) => void;

const MANIFEST_URL = "/seed/manifest.json";
const META_KEY = "seed_version";

export async function seedIfNeeded(
  onProgress: SeedProgressListener = () => {},
  opts: { force?: boolean } = {},
): Promise<SeedProgress> {
  try {
    onProgress({ phase: "fetching-manifest", completed: 0, total: 0 });

    const res = await fetch(MANIFEST_URL, { cache: "no-store" });
    if (!res.ok) {
      throw new Error(`manifest fetch failed: ${res.status}`);
    }
    const manifest = (await res.json()) as SeedManifest;

    const existing = await getMeta<string>(META_KEY);
    const already = await fileCount();
    if (!opts.force && existing === manifest.seed_version && already >= manifest.file_count) {
      const p: SeedProgress = {
        phase: "skipped",
        completed: already,
        total: manifest.file_count,
        message: `already at seed_version ${manifest.seed_version}`,
      };
      onProgress(p);
      return p;
    }

    const total = manifest.files.length;
    let completed = 0;
    onProgress({ phase: "seeding", completed, total });

    // Fetch in small batches so we don't open 400 concurrent requests.
    const BATCH = 8;
    for (let i = 0; i < manifest.files.length; i += BATCH) {
      const batch = manifest.files.slice(i, i + BATCH);
      await Promise.all(
        batch.map(async (entry) => {
          const url = `/seed/${entry.path}`;
          const r = await fetch(url);
          if (!r.ok) {
            throw new Error(`seed fetch failed for ${entry.path}: ${r.status}`);
          }
          const blob = await r.blob();
          await putFile(entry.path, blob, { sha1: entry.sha1 });
          completed++;
          onProgress({ phase: "seeding", completed, total, current: entry.path });
        }),
      );
    }

    await setMeta(META_KEY, manifest.seed_version);
    const done: SeedProgress = {
      phase: "done",
      completed,
      total,
      message: `seeded ${completed} files @ ${manifest.seed_version}`,
    };
    onProgress(done);
    return done;
  } catch (err) {
    const error = err instanceof Error ? err : new Error(String(err));
    const p: SeedProgress = {
      phase: "error",
      completed: 0,
      total: 0,
      error,
      message: error.message,
    };
    onProgress(p);
    return p;
  }
}
