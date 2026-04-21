<script lang="ts">
  import { exportToFiles, importFromFiles, isFileSyncAvailable } from "$lib/storage/file_sync";
  import { seedIfNeeded } from "$lib/storage/seed";
  import { fileCount, listFiles } from "$lib/storage/db";
  import { listExperiences } from "$lib/memory/smart_memory";
  import EvalsScreen from "$components/EvalsScreen.svelte";
  import { onMount } from "svelte";

  interface Props {
    oncancel: () => void;
  }

  let { oncancel }: Props = $props();
  let evalsOpen = $state(false);

  let fileTotal = $state(0);
  let projectCount = $state(0);
  let cartridgeCount = $state(0);
  let experienceCount = $state(0);
  let status = $state("");
  let busy = $state(false);
  const native = isFileSyncAvailable();

  onMount(async () => {
    fileTotal = await fileCount();
    const cartridgePaths = await listFiles("cartridges/");
    cartridgeCount = new Set(cartridgePaths.map((p) => p.split("/")[1]).filter(Boolean)).size;
    const projectPaths = await listFiles("projects/");
    projectCount = new Set(projectPaths.map((p) => p.split("/")[1]).filter(Boolean)).size;
    experienceCount = (await listExperiences()).length;
  });

  async function onResync() {
    busy = true;
    status = "resyncing seed…";
    try {
      const res = await seedIfNeeded(() => {}, { force: true });
      status = res.message ?? `done (${res.completed})`;
    } catch (err) {
      status = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }

  async function onExport() {
    busy = true;
    status = "exporting to Documents/SkillOS…";
    try {
      const res = await exportToFiles();
      status = `exported ${res.files} files → ${res.path}`;
    } catch (err) {
      status = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }

  async function onImport() {
    busy = true;
    status = "importing from Documents/SkillOS…";
    try {
      const res = await importFromFiles();
      status = `imported ${res.files} files`;
    } catch (err) {
      status = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }
</script>

<button type="button" class="backdrop" onclick={oncancel} aria-label="Close"></button>
<section class="sheet">
  <div class="handle"></div>
  <h2>Settings</h2>

  <div class="stats">
    <div><strong>{fileTotal}</strong> files seeded</div>
    <div><strong>{cartridgeCount}</strong> cartridges</div>
    <div><strong>{projectCount}</strong> seeded projects</div>
    <div><strong>{experienceCount}</strong> SmartMemory entries</div>
  </div>

  <div class="row">
    <button onclick={onResync} disabled={busy}>Resync from bundle</button>
    <div class="hint">Reloads the seeded cartridges + example project from the app bundle.</div>
  </div>

  <div class="row" class:disabled={!native}>
    <button onclick={onExport} disabled={busy || !native}>Export to Files…</button>
    <div class="hint">
      Writes every IndexedDB file to <code>Documents/SkillOS/</code> so the desktop
      Python runner can pick them up.
      {#if !native}<br /><em>Requires the installed native app.</em>{/if}
    </div>
  </div>

  <div class="row" class:disabled={!native}>
    <button onclick={onImport} disabled={busy || !native}>Import from Files…</button>
    <div class="hint">
      Walks <code>Documents/SkillOS/</code> and re-loads markdown/yaml into IndexedDB.
      {#if !native}<br /><em>Requires the installed native app.</em>{/if}
    </div>
  </div>

  {#if status}
    <div class="status">{status}</div>
  {/if}

  <div class="row">
    <button onclick={() => (evalsOpen = true)}>Run cartridge evals…</button>
    <div class="hint">
      Execute every cartridge's <code>evals/cases.yaml</code> against your configured
      provider and report pass rates.
    </div>
  </div>

  <div class="actions">
    <button class="ghost" onclick={oncancel}>Close</button>
  </div>
</section>

{#if evalsOpen}
  <EvalsScreen oncancel={() => (evalsOpen = false)} />
{/if}

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
    padding: 0.7rem 1.1rem 1.3rem;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
    z-index: 11;
    padding-bottom: calc(1.3rem + env(safe-area-inset-bottom));
    max-height: 88vh;
    overflow-y: auto;
  }
  .handle {
    width: 36px;
    height: 4px;
    background: var(--bg-3);
    border-radius: 2px;
    align-self: center;
  }
  h2 {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 500;
  }
  .stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.2rem 0.8rem;
    padding: 0.55rem 0.75rem;
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.85rem;
    color: var(--fg-dim);
  }
  .stats strong {
    color: var(--fg);
    font-variant-numeric: tabular-nums;
    margin-right: 0.25rem;
  }
  .row {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }
  .row button {
    align-self: flex-start;
    font-size: 0.85rem;
  }
  .row.disabled button {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .hint {
    color: var(--fg-dim);
    font-size: 0.78rem;
  }
  code {
    background: var(--bg-3);
    padding: 0.05rem 0.3rem;
    border-radius: 4px;
  }
  .status {
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.55rem 0.7rem;
    font-size: 0.82rem;
    color: var(--fg);
  }
  .actions {
    display: flex;
    justify-content: flex-end;
  }
  .ghost {
    background: transparent;
  }
</style>
