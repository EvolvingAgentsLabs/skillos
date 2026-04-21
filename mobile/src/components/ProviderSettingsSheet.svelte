<script lang="ts">
  import {
    PROVIDER_CONFIGS,
    type ProviderId,
  } from "$lib/llm/providers";
  import {
    isProviderNative,
    loadProviderConfig,
    saveProviderConfig,
    type ProviderConfigStored,
  } from "$lib/state/provider_config";
  import { onMount } from "svelte";

  interface Props {
    projectId: string;
    onsaved: (cfg: ProviderConfigStored) => void;
    oncancel: () => void;
  }

  let { projectId, onsaved, oncancel }: Props = $props();

  const isNative = isProviderNative();
  const providerIds = Object.keys(PROVIDER_CONFIGS) as ProviderId[];

  let providerId = $state<ProviderId>("openrouter-qwen");
  let baseUrl = $state("");
  let model = $state("");
  let apiKey = $state("");

  const currentCfg = $derived(PROVIDER_CONFIGS[providerId]);
  const available = $derived(!currentCfg.lanOnly || isNative);

  onMount(async () => {
    const existing = await loadProviderConfig(projectId);
    if (existing) {
      providerId = existing.providerId;
      baseUrl = existing.baseUrl ?? "";
      model = existing.model ?? "";
      apiKey = existing.apiKey ?? "";
    }
  });

  function onProviderChange() {
    // Reset overrides when switching provider so defaults take over.
    baseUrl = "";
    model = "";
    if (!currentCfg.requiresKey) apiKey = "";
  }

  async function onSubmit(e: Event) {
    e.preventDefault();
    if (!available) return;
    const cfg: ProviderConfigStored = {
      providerId,
      baseUrl: baseUrl.trim() || undefined,
      model: model.trim() || undefined,
      apiKey: apiKey.trim() || undefined,
    };
    await saveProviderConfig(projectId, cfg);
    onsaved(cfg);
  }
</script>

<button type="button" class="backdrop" onclick={oncancel} aria-label="Close"></button>
<form class="sheet" onsubmit={onSubmit}>
  <div class="handle"></div>
  <h2>Provider settings</h2>
  <p class="sub">Used for LLM calls and in-skill sub-calls for this project.</p>

  <label class="field">
    <span>Provider</span>
    <select bind:value={providerId} onchange={onProviderChange}>
      {#each providerIds as id (id)}
        <option value={id} disabled={PROVIDER_CONFIGS[id].lanOnly && !isNative}>
          {PROVIDER_CONFIGS[id].label}{PROVIDER_CONFIGS[id].lanOnly && !isNative ? " — needs native app" : ""}
        </option>
      {/each}
    </select>
  </label>

  <label class="field">
    <span>Base URL <small>(override)</small></span>
    <input
      type="url"
      placeholder={currentCfg.defaultBaseUrl}
      bind:value={baseUrl}
    />
  </label>

  <label class="field">
    <span>Model</span>
    <input type="text" placeholder={currentCfg.defaultModel} bind:value={model} />
  </label>

  {#if currentCfg.requiresKey}
    <label class="field">
      <span>API key</span>
      <input
        type="password"
        autocomplete="off"
        placeholder="sk-…"
        bind:value={apiKey}
      />
    </label>
  {/if}

  {#if !available}
    <div class="warn">
      This provider requires cleartext LAN access. Install the native SkillOS app
      (Capacitor) to use it.
    </div>
  {/if}

  <div class="actions">
    <button type="button" class="ghost" onclick={oncancel}>Cancel</button>
    <button type="submit" class="primary" disabled={!available}>Save</button>
  </div>
</form>

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
    gap: 0.65rem;
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
  .sub {
    margin: 0;
    color: var(--fg-dim);
    font-size: 0.85rem;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.85rem;
    color: var(--fg-dim);
  }
  input,
  select {
    font: inherit;
    color: var(--fg);
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.55rem 0.7rem;
  }
  .warn {
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.55rem 0.7rem;
    color: var(--warn);
    font-size: 0.82rem;
  }
  .actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 0.3rem;
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
  small {
    color: var(--fg-dim);
    opacity: 0.8;
  }
</style>
