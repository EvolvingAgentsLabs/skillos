<script lang="ts">
  import {
    PROVIDER_CONFIGS,
    isLocalProvider,
    type ProviderId,
  } from "$lib/llm/providers";
  import { catalogFor, MODEL_CATALOG } from "$lib/llm/local/model_catalog";
  import { isModelInstalled } from "$lib/llm/local/model_store";
  import {
    isProviderNative,
    loadProjectRouting,
    saveProjectRouting,
    type ProviderConfigStored,
  } from "$lib/state/provider_config";
  import { getMeta } from "$lib/storage/db";
  import ModelManagerSheet from "$components/ModelManagerSheet.svelte";
  import { onMount } from "svelte";

  interface Props {
    projectId: string;
    onsaved: (cfg: ProviderConfigStored) => void;
    oncancel: () => void;
  }

  let { projectId, onsaved, oncancel }: Props = $props();

  const isNative = isProviderNative();
  let onDeviceFlag = $state(false);
  let modelsOpen = $state(false);
  let modelInstalled = $state<Record<string, boolean>>({});
  let tab = $state<"primary" | "fallback">("primary");
  let fallbackEnabled = $state(false);

  // Show cloud/LAN providers always; local providers appear only under the flag.
  const visibleProviderIds = $derived(
    (Object.keys(PROVIDER_CONFIGS) as ProviderId[]).filter((id) =>
      onDeviceFlag ? true : !isLocalProvider(id),
    ),
  );

  // Primary slot
  let pProviderId = $state<ProviderId>("openrouter-qwen");
  let pBaseUrl = $state("");
  let pModel = $state("");
  let pApiKey = $state("");

  // Fallback slot
  let fProviderId = $state<ProviderId>("openrouter-qwen");
  let fBaseUrl = $state("");
  let fModel = $state("");
  let fApiKey = $state("");

  function currentCfgFor(id: ProviderId) {
    return PROVIDER_CONFIGS[id];
  }

  const pCfg = $derived(currentCfgFor(pProviderId));
  const fCfg = $derived(currentCfgFor(fProviderId));
  const pIsLocal = $derived(isLocalProvider(pProviderId));
  const fIsLocal = $derived(isLocalProvider(fProviderId));
  const pAvailable = $derived(
    (!pCfg.lanOnly || isNative) && (!pCfg.nativeOnly || isNative),
  );
  const fAvailable = $derived(
    (!fCfg.lanOnly || isNative) && (!fCfg.nativeOnly || isNative),
  );

  function installedForSlot(id: ProviderId) {
    if (!isLocalProvider(id)) return [];
    const backend =
      id === "wllama-local" ? "wllama" : id === "litert-local" ? "litert" : "chrome-prompt-api";
    return catalogFor(backend).filter((m) => modelInstalled[m.id]);
  }
  const pInstalled = $derived(installedForSlot(pProviderId));
  const fInstalled = $derived(installedForSlot(fProviderId));

  async function refreshInstalled() {
    const out: Record<string, boolean> = {};
    for (const m of MODEL_CATALOG) {
      out[m.id] = await isModelInstalled(m.id);
    }
    modelInstalled = out;
  }

  onMount(async () => {
    onDeviceFlag = Boolean(await getMeta("experimental_on_device_llm"));
    await refreshInstalled();
    const routing = await loadProjectRouting(projectId);
    if (routing?.primary) {
      pProviderId = routing.primary.providerId;
      pBaseUrl = routing.primary.baseUrl ?? "";
      pModel = routing.primary.model ?? "";
      pApiKey = routing.primary.apiKey ?? "";
    }
    if (routing?.fallback) {
      fallbackEnabled = true;
      fProviderId = routing.fallback.providerId;
      fBaseUrl = routing.fallback.baseUrl ?? "";
      fModel = routing.fallback.model ?? "";
      fApiKey = routing.fallback.apiKey ?? "";
    }
  });

  function onProviderChange(slot: "primary" | "fallback") {
    if (slot === "primary") {
      pBaseUrl = "";
      pModel = "";
      if (!pCfg.requiresKey) pApiKey = "";
    } else {
      fBaseUrl = "";
      fModel = "";
      if (!fCfg.requiresKey) fApiKey = "";
    }
  }

  async function onSubmit(e: Event) {
    e.preventDefault();
    if (!pAvailable) return;
    if (fallbackEnabled && !fAvailable) return;
    const primary: ProviderConfigStored = {
      providerId: pProviderId,
      baseUrl: pBaseUrl.trim() || undefined,
      model: pModel.trim() || undefined,
      apiKey: pApiKey.trim() || undefined,
    };
    const fallback: ProviderConfigStored | undefined = fallbackEnabled
      ? {
          providerId: fProviderId,
          baseUrl: fBaseUrl.trim() || undefined,
          model: fModel.trim() || undefined,
          apiKey: fApiKey.trim() || undefined,
        }
      : undefined;
    await saveProjectRouting(projectId, { primary, fallback });
    onsaved(primary);
  }

  // Validity — primary must be valid; fallback (if enabled) too.
  const primaryNeedsModel = $derived(pIsLocal && !pModel);
  const fallbackNeedsModel = $derived(fallbackEnabled && fIsLocal && !fModel);
  const saveDisabled = $derived(
    !pAvailable ||
      primaryNeedsModel ||
      (fallbackEnabled && (!fAvailable || fallbackNeedsModel)),
  );
</script>

<button type="button" class="backdrop" onclick={oncancel} aria-label="Close"></button>
<form class="sheet" onsubmit={onSubmit}>
  <div class="handle"></div>
  <h2>Provider settings</h2>
  <p class="sub">
    <strong>Primary</strong> runs every turn by default. <strong>Fallback</strong>
    takes over for agents marked <code>tier: capable</code> or when the primary's
    output fails schema validation.
  </p>

  <nav class="tabs" aria-label="Provider slot">
    <button type="button" class:active={tab === "primary"} onclick={() => (tab = "primary")}>
      Primary
    </button>
    <button
      type="button"
      class:active={tab === "fallback"}
      onclick={() => (tab = "fallback")}
    >
      Fallback {fallbackEnabled ? "✓" : "(off)"}
    </button>
  </nav>

  {#if tab === "primary"}
    <label class="field">
      <span>Provider</span>
      <select bind:value={pProviderId} onchange={() => onProviderChange("primary")}>
        {#each visibleProviderIds as id (id)}
          {@const cfg = PROVIDER_CONFIGS[id]}
          {@const nativeNeeded = (cfg.lanOnly || cfg.nativeOnly) && !isNative}
          <option value={id} disabled={nativeNeeded}>
            {cfg.label}{nativeNeeded ? " — needs native app" : ""}
          </option>
        {/each}
      </select>
    </label>

    {#if pIsLocal}
      <label class="field">
        <span>Model</span>
        {#if pInstalled.length > 0}
          <select bind:value={pModel}>
            <option value="">— pick a model —</option>
            {#each pInstalled as m (m.id)}
              <option value={m.id}>{m.name}</option>
            {/each}
          </select>
        {:else}
          <div class="warn">
            No local models installed.
            <button type="button" class="link" onclick={() => (modelsOpen = true)}>
              Open Model Manager
            </button>
          </div>
        {/if}
      </label>
    {:else}
      <label class="field">
        <span>Base URL <small>(override)</small></span>
        <input type="url" placeholder={pCfg.defaultBaseUrl} bind:value={pBaseUrl} />
      </label>
      <label class="field">
        <span>Model</span>
        <input type="text" placeholder={pCfg.defaultModel} bind:value={pModel} />
      </label>
      {#if pCfg.requiresKey}
        <label class="field">
          <span>API key</span>
          <input type="password" autocomplete="off" placeholder="sk-…" bind:value={pApiKey} />
        </label>
      {/if}
    {/if}

    {#if !pAvailable}
      <div class="warn">This provider requires the native SkillOS app (Capacitor).</div>
    {/if}
  {:else}
    <label class="inline">
      <input type="checkbox" bind:checked={fallbackEnabled} />
      <span>Enable a fallback provider for this project</span>
    </label>

    {#if fallbackEnabled}
      <label class="field">
        <span>Provider</span>
        <select bind:value={fProviderId} onchange={() => onProviderChange("fallback")}>
          {#each visibleProviderIds as id (id)}
            {@const cfg = PROVIDER_CONFIGS[id]}
            {@const nativeNeeded = (cfg.lanOnly || cfg.nativeOnly) && !isNative}
            <option value={id} disabled={nativeNeeded}>
              {cfg.label}{nativeNeeded ? " — needs native app" : ""}
            </option>
          {/each}
        </select>
      </label>

      {#if fIsLocal}
        <label class="field">
          <span>Model</span>
          {#if fInstalled.length > 0}
            <select bind:value={fModel}>
              <option value="">— pick a model —</option>
              {#each fInstalled as m (m.id)}
                <option value={m.id}>{m.name}</option>
              {/each}
            </select>
          {:else}
            <div class="warn">
              No local models installed for this backend.
              <button type="button" class="link" onclick={() => (modelsOpen = true)}>
                Open Model Manager
              </button>
            </div>
          {/if}
        </label>
      {:else}
        <label class="field">
          <span>Base URL <small>(override)</small></span>
          <input type="url" placeholder={fCfg.defaultBaseUrl} bind:value={fBaseUrl} />
        </label>
        <label class="field">
          <span>Model</span>
          <input type="text" placeholder={fCfg.defaultModel} bind:value={fModel} />
        </label>
        {#if fCfg.requiresKey}
          <label class="field">
            <span>API key</span>
            <input
              type="password"
              autocomplete="off"
              placeholder="sk-…"
              bind:value={fApiKey}
            />
          </label>
        {/if}
      {/if}

      {#if !fAvailable}
        <div class="warn">This provider requires the native SkillOS app (Capacitor).</div>
      {/if}

      <div class="hint">
        Common pairing: <code>On-device · wllama</code> as primary,
        <code>OpenRouter · Qwen</code> or <code>Google · Gemini</code> as fallback.
        The runner escalates on the first validation failure of a step and caps at one
        switch per step.
      </div>
    {/if}
  {/if}

  <div class="actions">
    <button type="button" class="ghost" onclick={oncancel}>Cancel</button>
    <button type="submit" class="primary" disabled={saveDisabled}>Save</button>
  </div>
</form>

{#if modelsOpen}
  <ModelManagerSheet
    oncancel={async () => {
      modelsOpen = false;
      await refreshInstalled();
    }}
  />
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
  .link {
    background: transparent;
    border: none;
    color: var(--accent);
    padding: 0;
    margin-left: 0.3rem;
    text-decoration: underline;
    cursor: pointer;
  }
  .tabs {
    display: flex;
    gap: 0;
    border-bottom: 1px solid var(--border);
    margin-top: 0.2rem;
  }
  .tabs button {
    flex: 1;
    background: transparent;
    color: var(--fg-dim);
    border: none;
    padding: 0.45rem 0.6rem;
    cursor: pointer;
    font-size: 0.85rem;
  }
  .tabs button.active {
    color: var(--accent);
    border-bottom: 2px solid var(--accent);
    font-weight: 600;
  }
  .inline {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    font-size: 0.9rem;
    color: var(--fg);
    padding: 0.3rem 0;
  }
  .inline input {
    transform: scale(1.1);
    accent-color: var(--accent);
  }
  .hint {
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.5rem 0.7rem;
    color: var(--fg-dim);
    font-size: 0.78rem;
    line-height: 1.5;
  }
  .hint code {
    background: var(--bg);
    padding: 0 0.3rem;
    border-radius: 4px;
    font-size: 0.78rem;
  }
  .sub code {
    background: var(--bg-3);
    padding: 0 0.25rem;
    border-radius: 3px;
    font-size: 0.78rem;
  }
</style>
