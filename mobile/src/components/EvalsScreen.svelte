<script lang="ts">
  import { CartridgeRegistry } from "$lib/cartridge/registry";
  import {
    discoverEvalFiles,
    runEvalCase,
    type CaseResult,
    type CartridgeEvalFile,
  } from "$lib/evals/evals";
  import { loadProviderConfig, type ProviderConfigStored } from "$lib/state/provider_config";
  import { projects } from "$lib/state/projects.svelte";
  import { onMount } from "svelte";

  interface Props {
    oncancel: () => void;
  }
  let { oncancel }: Props = $props();

  let files = $state<CartridgeEvalFile[]>([]);
  let providerCfg = $state<ProviderConfigStored | null>(null);
  let running = $state(false);
  let results = $state<CaseResult[]>([]);
  let statusText = $state("");

  const totalCases = $derived(files.reduce((s, f) => s + f.cases.length, 0));
  const passed = $derived(results.filter((r) => r.ok).length);

  onMount(async () => {
    files = await discoverEvalFiles();
    // Pick any project's provider config as the default — evals aren't
    // scoped to a single project.
    for (const p of projects.items) {
      const cfg = await loadProviderConfig(p.id);
      if (cfg) {
        providerCfg = cfg;
        break;
      }
    }
  });

  async function runAll() {
    if (!providerCfg) {
      statusText = "No provider configured on any project — open a project's ⚙ first.";
      return;
    }
    running = true;
    results = [];
    statusText = `Running ${totalCases} cases…`;
    const registry = new CartridgeRegistry();
    await registry.init();
    for (const f of files) {
      for (const c of f.cases) {
        statusText = `running ${f.cartridge} / ${c.id}`;
        const r = await runEvalCase(registry, providerCfg, f.cartridge, c);
        results = [...results, r];
      }
    }
    running = false;
    statusText = `done — ${passed}/${totalCases} passed`;
  }
</script>

<button type="button" class="backdrop" onclick={oncancel} aria-label="Close"></button>
<section class="sheet">
  <div class="handle"></div>
  <h2>Cartridge evals</h2>

  <div class="summary">
    {totalCases} case{totalCases === 1 ? "" : "s"} across {files.length} cartridge{files.length === 1 ? "" : "s"}.
    {#if providerCfg}
      <br />Provider: <code>{providerCfg.providerId}</code>
      ({providerCfg.model || "default model"})
    {:else}
      <br /><em>No provider configured — set one on a project first.</em>
    {/if}
  </div>

  <div class="actions">
    <button class="primary" disabled={running || !providerCfg} onclick={runAll}>
      {running ? "running…" : "Run all"}
    </button>
    <button class="ghost" onclick={oncancel}>Close</button>
  </div>

  {#if statusText}
    <div class="status">{statusText}</div>
  {/if}

  <div class="list">
    {#each results as r (r.cartridge + "/" + r.case_id)}
      <div class="row" class:ok={r.ok} class:fail={!r.ok}>
        <div class="row-head">
          <span class="icon">{r.ok ? "✓" : "✗"}</span>
          <span class="cart">{r.cartridge}</span>
          <span class="sep">/</span>
          <span class="id">{r.case_id}</span>
          <span class="time">{r.duration_seconds}s</span>
        </div>
        {#if !r.run_ok && r.error}
          <div class="err">runtime error: {r.error}</div>
        {:else}
          {#each r.assertions.filter((a) => !a.ok) as a, i (i)}
            <div class="err">— {a.assertion.key}: {a.message}</div>
          {/each}
        {/if}
      </div>
    {/each}
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
    top: 0;
    bottom: 0;
    background: var(--bg);
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 1rem 1rem 1.3rem;
    z-index: 11;
    padding-bottom: calc(1.3rem + env(safe-area-inset-bottom));
    padding-top: calc(1rem + env(safe-area-inset-top));
    overflow-y: auto;
  }
  .handle {
    display: none;
  }
  h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 500;
  }
  .summary {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.6rem 0.8rem;
    color: var(--fg-dim);
    font-size: 0.85rem;
  }
  .actions {
    display: flex;
    gap: 0.5rem;
  }
  .primary {
    background: var(--accent);
    color: var(--bg);
    border: none;
    font-weight: 600;
  }
  .primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .ghost {
    background: transparent;
  }
  .status {
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.45rem 0.7rem;
    font-size: 0.82rem;
  }
  .list {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
  }
  .row {
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.55rem 0.75rem;
    background: var(--bg-2);
  }
  .row-head {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.85rem;
  }
  .icon {
    font-weight: 700;
  }
  .row.ok .icon {
    color: var(--ok);
  }
  .row.fail .icon {
    color: var(--err);
  }
  .cart {
    color: var(--fg);
  }
  .sep {
    color: var(--fg-dim);
  }
  .id {
    color: var(--fg-dim);
  }
  .time {
    margin-left: auto;
    color: var(--fg-dim);
    font-variant-numeric: tabular-nums;
  }
  .err {
    margin-top: 0.3rem;
    color: var(--err);
    font-size: 0.78rem;
    font-family: ui-monospace, Menlo, monospace;
    white-space: pre-wrap;
    word-break: break-word;
  }
</style>
