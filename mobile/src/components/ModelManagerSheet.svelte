<script lang="ts">
  import { onMount } from "svelte";
  import {
    MODEL_CATALOG,
    type ModelCatalogEntry,
  } from "$lib/llm/local/model_catalog";
  import {
    deleteInstalledModel,
    downloadModel,
    estimateFreeStorage,
    isModelInstalled,
    listInstalledModels,
    type DownloadProgress,
  } from "$lib/llm/local/model_store";
  import { isProviderNative } from "$lib/state/provider_config";

  interface Props {
    oncancel: () => void;
  }
  let { oncancel }: Props = $props();

  const isNative = isProviderNative();
  let installed = $state<Set<string>>(new Set());
  let progress = $state<Record<string, DownloadProgress | null>>({});
  let abortCtrls = $state<Record<string, AbortController | null>>({});
  let freeBytes = $state<number>(-1);
  let busyId = $state<string | null>(null);
  let error = $state<string>("");

  async function refresh() {
    const blobs = await listInstalledModels();
    installed = new Set(blobs.map((b) => b.id));
    freeBytes = await estimateFreeStorage();
  }

  onMount(refresh);

  function fmtMB(bytes: number): string {
    if (bytes < 0) return "unknown";
    if (bytes < 1e9) return `${(bytes / 1e6).toFixed(0)} MB`;
    return `${(bytes / 1e9).toFixed(1)} GB`;
  }

  function available(entry: ModelCatalogEntry): boolean {
    if (entry.backend === "litert") return isNative;
    if (entry.backend === "chrome-prompt-api") return false;
    return true;
  }

  async function onDownload(entry: ModelCatalogEntry) {
    if (busyId) return;
    busyId = entry.id;
    error = "";
    const ctrl = new AbortController();
    abortCtrls[entry.id] = ctrl;
    try {
      await downloadModel(
        entry,
        (p) => {
          progress[entry.id] = p;
        },
        ctrl.signal,
      );
      await refresh();
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      busyId = null;
      abortCtrls[entry.id] = null;
    }
  }

  function onCancel(entry: ModelCatalogEntry) {
    abortCtrls[entry.id]?.abort();
  }

  async function onDelete(entry: ModelCatalogEntry) {
    if (busyId) return;
    busyId = entry.id;
    try {
      await deleteInstalledModel(entry.id);
      delete progress[entry.id];
      progress = { ...progress };
      await refresh();
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      busyId = null;
    }
  }
</script>

<button type="button" class="backdrop" onclick={oncancel} aria-label="Close"></button>
<section class="sheet">
  <div class="handle"></div>
  <h2>On-device models</h2>
  <p class="sub">
    Downloads a model into this device's storage. Files are large (up to ~1.6 GB).
    {#if freeBytes >= 0}
      <br />Free storage: <strong>{fmtMB(freeBytes)}</strong>
    {/if}
  </p>

  {#if error}
    <div class="err">{error}</div>
  {/if}

  <div class="list">
    {#each MODEL_CATALOG as entry (entry.id)}
      {@const p = progress[entry.id]}
      {@const isInstalled = installed.has(entry.id)}
      {@const avail = available(entry)}
      <div class="row" class:installed={isInstalled} class:unavailable={!avail}>
        <header>
          <div class="title-block">
            <div class="name">{entry.name}</div>
            <div class="desc">{entry.description}</div>
            <div class="meta">
              <span class="chip">{entry.backend}</span>
              <span class="chip">{fmtMB(entry.sizeBytes)}</span>
              <span class="chip">{entry.contextTokens} ctx</span>
              <span class="chip muted">{entry.license}</span>
            </div>
          </div>
          <div class="actions">
            {#if !avail}
              <div class="unavail">native only</div>
            {:else if isInstalled}
              <button class="danger" onclick={() => onDelete(entry)} disabled={busyId !== null}>
                Delete
              </button>
            {:else if busyId === entry.id}
              <button class="ghost" onclick={() => onCancel(entry)}>Cancel</button>
            {:else}
              <button class="primary" onclick={() => onDownload(entry)} disabled={busyId !== null}>
                Download
              </button>
            {/if}
          </div>
        </header>
        {#if p && (p.phase === "fetching" || p.phase === "committing")}
          <div class="progress">
            <div class="bar">
              <div
                class="fill"
                style:width="{Math.min(100, (p.bytesDone / p.bytesTotal) * 100)}%"
              ></div>
            </div>
            <div class="progress-meta">
              {fmtMB(p.bytesDone)} / {fmtMB(p.bytesTotal)}
              {#if p.ratekBps}· {(p.ratekBps / 1024).toFixed(1)} MB/s{/if}
            </div>
          </div>
        {:else if p && p.phase === "error"}
          <div class="err">download failed: {p.message}</div>
        {:else if p && p.phase === "cancelled"}
          <div class="muted">cancelled</div>
        {/if}
      </div>
    {/each}
  </div>

  <div class="foot">
    <button class="ghost" onclick={oncancel}>Close</button>
  </div>
</section>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    z-index: 10;
    border: none;
    padding: 0;
    cursor: pointer;
  }
  .sheet {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--bg-2);
    border-top: 1px solid var(--border);
    border-radius: 14px 14px 0 0;
    padding: 0.7rem 1rem 1rem;
    z-index: 11;
    padding-bottom: calc(1rem + env(safe-area-inset-bottom));
    max-height: 88vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
  }
  .handle {
    width: 36px;
    height: 4px;
    background: var(--bg-3);
    border-radius: 2px;
    align-self: center;
  }
  h2 { margin: 0; font-size: 1.15rem; font-weight: 500; }
  .sub { margin: 0; color: var(--fg-dim); font-size: 0.85rem; }
  .err {
    background: var(--bg-3);
    border: 1px solid var(--err);
    color: var(--err);
    padding: 0.5rem 0.7rem;
    border-radius: 8px;
    font-size: 0.82rem;
  }
  .list { display: flex; flex-direction: column; gap: 0.55rem; }
  .row {
    border: 1px solid var(--border);
    border-radius: 10px;
    background: var(--bg-2);
    padding: 0.7rem 0.9rem;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  .row.installed {
    border-left: 3px solid var(--ok);
  }
  .row.unavailable {
    opacity: 0.6;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 0.6rem;
  }
  .title-block { flex: 1; min-width: 0; }
  .name { font-weight: 500; }
  .desc { color: var(--fg-dim); font-size: 0.8rem; margin-top: 0.1rem; }
  .meta {
    display: flex;
    gap: 0.3rem;
    flex-wrap: wrap;
    font-size: 0.7rem;
    margin-top: 0.35rem;
  }
  .chip {
    background: var(--bg-3);
    border-radius: 9999px;
    padding: 0.05rem 0.55rem;
  }
  .chip.muted { color: var(--fg-dim); }
  .actions button {
    font-size: 0.78rem;
    padding: 0.35rem 0.7rem;
  }
  .primary { background: var(--accent); color: var(--bg); border: none; font-weight: 600; }
  .danger { color: var(--err); border-color: var(--err); background: transparent; }
  .ghost { background: transparent; }
  .unavail {
    color: var(--fg-dim);
    font-size: 0.75rem;
    font-style: italic;
  }
  .progress { display: flex; flex-direction: column; gap: 0.25rem; }
  .bar {
    width: 100%;
    height: 4px;
    background: var(--bg-3);
    border-radius: 2px;
    overflow: hidden;
  }
  .fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    transition: width 0.2s;
  }
  .progress-meta { color: var(--fg-dim); font-size: 0.72rem; }
  .muted { color: var(--fg-dim); font-size: 0.78rem; }
  .foot { display: flex; justify-content: flex-end; }
</style>
