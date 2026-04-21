/**
 * File sync — bidirectional round-trip between IndexedDB (runtime state) and
 * the device's Documents folder via Capacitor Filesystem.
 *
 * Export writes every `files` record plus each project's state/pipeline_state.md
 * and the SmartMemory log. Import rehydrates IndexedDB from a previously-exported
 * folder so the desktop Python runner's workspace can seed the mobile app.
 *
 * Works only when Capacitor is available; in pure-PWA mode the calls throw
 * "not available".
 */

import { listExperiences, renderExperienceMarkdown } from "../memory/smart_memory";
import { getDB, listFiles, getFileText, putFile } from "./db";
import { listProjectRecords } from "./project_store";

/**
 * Minimal structural type for the `@capacitor/filesystem` plugin so we can
 * compile without the package installed (the real module is loaded via a
 * dynamic import at runtime — only present when running inside Capacitor).
 */
interface CapacitorFilesystem {
  writeFile(options: {
    path: string;
    data: string;
    directory: string;
    encoding?: string;
    recursive?: boolean;
  }): Promise<unknown>;
  readFile(options: {
    path: string;
    directory: string;
    encoding?: string;
  }): Promise<{ data: string }>;
  readdir(options: { path: string; directory: string }): Promise<{ files: Array<{ name: string; type: string }> }>;
  mkdir(options: { path: string; directory: string; recursive?: boolean }): Promise<unknown>;
  stat(options: { path: string; directory: string }): Promise<{ type: string }>;
}

interface CapacitorWindow {
  Capacitor?: {
    isNativePlatform?: () => boolean;
    Plugins?: { Filesystem?: CapacitorFilesystem };
  };
}

const BASE = "SkillOS";
const DOCUMENTS = "DOCUMENTS";

function getFs(): CapacitorFilesystem {
  const w = globalThis as unknown as CapacitorWindow;
  const fs = w.Capacitor?.Plugins?.Filesystem;
  if (!fs) throw new Error("Capacitor Filesystem not available (run in the native app)");
  return fs;
}

/**
 * Render the in-memory projects + SmartMemory log + every IndexedDB file back
 * out to <Documents>/SkillOS/… so a desktop Python runner can resume the
 * state. Returns the number of files written.
 */
export async function exportToFiles(): Promise<{ files: number; path: string }> {
  const fs = getFs();
  let count = 0;

  // 1. Every file record → <BASE>/<path>
  const allPaths = await listFiles();
  for (const p of allPaths) {
    const text = await getFileText(p);
    if (text === undefined) continue;
    await fs.writeFile({
      path: `${BASE}/${p}`,
      data: text,
      directory: DOCUMENTS,
      encoding: "utf8",
      recursive: true,
    });
    count++;
  }

  // 2. SmartMemory log → <BASE>/system/SmartMemory.md (overwrites)
  const experiences = await listExperiences();
  if (experiences.length > 0) {
    const md = experiences.map(renderExperienceMarkdown).join("\n");
    await fs.writeFile({
      path: `${BASE}/system/SmartMemory.md`,
      data: md,
      directory: DOCUMENTS,
      encoding: "utf8",
      recursive: true,
    });
    count++;
  }

  // 3. Each project → <BASE>/projects/<name>/state/pipeline_state.md
  const projects = await listProjectRecords();
  for (const p of projects) {
    const pipelineMd = renderPipelineState(p);
    await fs.writeFile({
      path: `${BASE}/projects/${safeName(p.name)}/state/pipeline_state.md`,
      data: pipelineMd,
      directory: DOCUMENTS,
      encoding: "utf8",
      recursive: true,
    });
    count++;
    for (const card of p.cards) {
      await fs.writeFile({
        path: `${BASE}/projects/${safeName(p.name)}/cards/${card.id}.md`,
        data: renderCardMarkdown(card),
        directory: DOCUMENTS,
        encoding: "utf8",
        recursive: true,
      });
      count++;
    }
  }

  return { files: count, path: `${DOCUMENTS}/${BASE}` };
}

/**
 * Walk <Documents>/SkillOS/ and load every .md/.yaml/.json/.js back into
 * IndexedDB `files`. Does not overwrite the `projects` store — use
 * exportToFiles → import round-trip to reset project state.
 */
export async function importFromFiles(
  subpath = "",
): Promise<{ files: number }> {
  const fs = getFs();
  let count = 0;

  async function walk(relPath: string): Promise<void> {
    const { files } = await fs.readdir({
      path: `${BASE}/${relPath}`.replace(/\/+$/, ""),
      directory: DOCUMENTS,
    });
    for (const entry of files) {
      const child = relPath ? `${relPath}/${entry.name}` : entry.name;
      if (entry.type === "directory") {
        await walk(child);
      } else if (entry.type === "file") {
        // Skip binary-ish content; only textual files survive round-trip.
        if (!/\.(md|ya?ml|json|js|ts|html|css|txt)$/i.test(entry.name)) continue;
        const { data } = await fs.readFile({
          path: `${BASE}/${child}`,
          directory: DOCUMENTS,
          encoding: "utf8",
        });
        await putFile(child, data);
        count++;
      }
    }
  }

  await walk(subpath);
  return { files: count };
}

// ────────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────────

interface StoredProjectLike {
  id: string;
  name: string;
  cartridge: string | null;
  created_at: string;
  updated_at: string;
  cards: Array<{
    id: string;
    kind: string;
    lane: string;
    title: string;
    subtitle?: string;
    produced_by?: string;
    created_at: string;
    data?: unknown;
  }>;
}

function renderPipelineState(p: StoredProjectLike): string {
  const stages = p.cards
    .filter((c) => c.kind === "agent")
    .map((c) => ({
      name: c.title,
      agent: c.title,
      status: c.lane === "done" ? "completed" : c.lane === "executing" ? "running" : "pending",
      output: c.subtitle ?? null,
    }));
  const fm = [
    "---",
    `project: ${p.name}`,
    `cartridge: ${p.cartridge ?? "none"}`,
    `created_at: ${p.created_at}`,
    `updated_at: ${p.updated_at}`,
    `status: ${p.cards.some((c) => c.lane === "executing") ? "in_progress" : "idle"}`,
    "stages:",
    ...stages.map(
      (s) =>
        `  - name: ${s.name}\n    agent: ${s.agent}\n    status: ${s.status}\n    output: ${s.output ?? "null"}`,
    ),
    "---",
    "",
    `# ${p.name}`,
  ];
  return fm.join("\n");
}

function renderCardMarkdown(card: StoredProjectLike["cards"][number]): string {
  const fm = [
    "---",
    `id: ${card.id}`,
    `kind: ${card.kind}`,
    `lane: ${card.lane}`,
    `produced_by: ${card.produced_by ?? "user"}`,
    `created_at: ${card.created_at}`,
    "---",
    "",
    `# ${card.title}`,
    "",
    card.subtitle ?? "",
  ];
  if (card.data !== undefined) {
    fm.push("", "```json", JSON.stringify(card.data, null, 2), "```");
  }
  return fm.join("\n");
}

function safeName(name: string): string {
  return name.replace(/[^a-zA-Z0-9_\-]/g, "_").replace(/_+/g, "_") || "project";
}

export function isFileSyncAvailable(): boolean {
  const w = globalThis as unknown as CapacitorWindow;
  return (
    Boolean(w.Capacitor?.isNativePlatform?.()) &&
    Boolean(w.Capacitor?.Plugins?.Filesystem)
  );
}
