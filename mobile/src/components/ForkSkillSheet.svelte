<script lang="ts">
  import { onMount } from "svelte";
  import { buildProvider } from "$lib/llm/build_provider";
  import type { CartridgeManifest } from "$lib/cartridge/types";
  import {
    library,
    loadLibrary,
    saveSkill,
  } from "$lib/state/library.svelte";
  import type { SkillDefinition } from "$lib/skills/skill_loader";
  import { loadSkillsProviderConfig } from "$lib/skills/skill_llm_proxy";
  import {
    synthesizeSkill,
    type SynthResult,
    type SynthSource,
  } from "$lib/skills/skill_synth";
  import { getFileText } from "$lib/storage/db";

  interface Props {
    skill: SkillDefinition;
    cartridge: string;
    oncancel: () => void;
    onsaved: (payload: { cartridge: string; skillName: string }) => void;
  }

  let { skill, cartridge, oncancel, onsaved }: Props = $props();

  let targetCartridge = $state<string | null>(null);
  let variantName = $state("");
  let changeRequest = $state("");
  let synthesizing = $state(false);
  let saving = $state(false);
  let synth = $state<SynthResult | null>(null);
  let error = $state("");
  let noProviderConfigured = $state(false);

  let mdDraft = $state("");
  let jsDraft = $state("");

  // Original source loaded from IndexedDB — fed to the synth prompt.
  let originalMd = $state("");
  let originalJs = $state("");

  const hostableCartridges = $derived<CartridgeManifest[]>(
    library.cartridges.map((c) => c.manifest).filter((m) => !!m.skills_source),
  );

  onMount(async () => {
    await loadLibrary();
    const preferred = hostableCartridges.find((m) => m.name === cartridge);
    targetCartridge = preferred?.name ?? hostableCartridges[0]?.name ?? null;
    variantName = `${skill.name}-v2`;
    originalMd = (await getFileText(`${skill.skill_dir}/SKILL.md`)) ?? "";
    originalJs = (await getFileText(`${skill.skill_dir}/scripts/index.js`)) ?? "";
    const cfg = await loadSkillsProviderConfig();
    noProviderConfigured = !cfg;
  });

  function slugify(s: string): string {
    return (
      s.toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, "")
        .slice(0, 60) || ""
    );
  }

  async function onSynthesize() {
    error = "";
    synthesizing = true;
    synth = null;
    try {
      const cfg = await loadSkillsProviderConfig();
      if (!cfg) {
        error = "No provider configured. Open Skills tab → ⚙ to set one.";
        noProviderConfigured = true;
        return;
      }
      if (!changeRequest.trim()) {
        error = "Describe what should change.";
        return;
      }
      const provider = await buildProvider(cfg);
      const source: SynthSource = {
        goal: `Evolve skill: ${skill.name}`,
        cardTitle: variantName || `${skill.name}-variant`,
        cardSubtitle: skill.description,
        projectName: `fork:${skill.name}`,
        projectCartridge: cartridge,
        existingSkillMd: originalMd,
        existingIndexJs: originalJs,
        changeRequest: changeRequest.trim(),
      };
      const result = await synthesizeSkill(provider, source);
      synth = result;
      if (result.skillName && !variantName) variantName = result.skillName;
      mdDraft = result.skillMd;
      jsDraft = result.indexJs;
      if (result.errors.length > 0 && !result.ok) {
        error = `Partial synthesis — ${result.errors.join("; ")}`;
      }
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      synthesizing = false;
    }
  }

  async function onSave() {
    if (!targetCartridge) {
      error = "Pick a target cartridge.";
      return;
    }
    const name = slugify(variantName);
    if (!name) {
      error = "Variant name is required.";
      return;
    }
    if (name === skill.name && targetCartridge === cartridge) {
      error = "Choose a different name or cartridge — this would overwrite the original.";
      return;
    }
    if (!mdDraft.trim() || !jsDraft.trim()) {
      error = "Synthesize the variant first.";
      return;
    }
    saving = true;
    error = "";
    try {
      await saveSkill(targetCartridge, name, {
        skillMd: mdDraft,
        indexJs: jsDraft,
      });
      onsaved({ cartridge: targetCartridge, skillName: name });
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      saving = false;
    }
  }
</script>

<button type="button" class="backdrop" onclick={oncancel} aria-label="Close"></button>
<section class="sheet" role="dialog" aria-modal="true">
  <div class="handle"></div>
  <header>
    <div>
      <h2>Fork &amp; tweak</h2>
      <p class="sub">Evolve <strong>{skill.name}</strong> into a new variant.</p>
    </div>
    <button class="ghost close" onclick={oncancel} aria-label="Close">✕</button>
  </header>

  <div class="section row">
    <label class="field">
      <span>Variant name</span>
      <input type="text" autocomplete="off" bind:value={variantName} />
    </label>
    <label class="field">
      <span>Target cartridge</span>
      <select bind:value={targetCartridge} disabled={hostableCartridges.length === 0}>
        {#if hostableCartridges.length === 0}
          <option value={null}>— no host cartridges —</option>
        {:else}
          {#each hostableCartridges as m (m.name)}
            <option value={m.name}>{m.name}</option>
          {/each}
        {/if}
      </select>
    </label>
  </div>

  <div class="section">
    <label class="field">
      <span>What should change?</span>
      <textarea
        rows="3"
        placeholder="Take a currency code parameter and convert the result instead of assuming USD."
        bind:value={changeRequest}
      ></textarea>
    </label>
  </div>

  {#if noProviderConfigured}
    <div class="banner">
      No provider configured. Open <strong>Skills tab → ⚙</strong> to set one, then come back.
    </div>
  {/if}

  <div class="section">
    <div class="actions-row">
      <button
        class="primary"
        disabled={synthesizing || !targetCartridge || !changeRequest.trim()}
        onclick={onSynthesize}
      >
        {synthesizing ? "Synthesizing…" : synth ? "Regenerate" : "✨ Synthesize variant"}
      </button>
    </div>
  </div>

  <div class="section previews">
    <label class="field">
      <span>SKILL.md (variant)</span>
      <textarea rows="7" spellcheck="false" bind:value={mdDraft}></textarea>
    </label>
    <label class="field">
      <span>scripts/index.js (variant)</span>
      <textarea rows="9" spellcheck="false" bind:value={jsDraft}></textarea>
    </label>
  </div>

  {#if error}<div class="err">{error}</div>{/if}

  <footer class="footer">
    <button type="button" class="ghost" onclick={oncancel}>Cancel</button>
    <button
      type="button"
      class="primary"
      disabled={saving || !mdDraft.trim() || !jsDraft.trim() || !targetCartridge}
      onclick={onSave}
    >
      {saving ? "Saving…" : "Save variant"}
    </button>
  </footer>
</section>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    border: none;
    z-index: 19;
  }
  .sheet {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    max-height: 92vh;
    background: var(--bg);
    color: var(--fg);
    border-top-left-radius: 14px;
    border-top-right-radius: 14px;
    display: flex;
    flex-direction: column;
    z-index: 20;
    padding-bottom: env(safe-area-inset-bottom);
    overflow: hidden;
  }
  .handle {
    width: 36px;
    height: 4px;
    border-radius: 2px;
    background: var(--border);
    margin: 0.4rem auto 0.1rem;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 0.4rem 1rem 0.2rem;
  }
  h2 {
    margin: 0;
    font-size: 1.1rem;
  }
  .sub {
    margin: 0.15rem 0 0;
    color: var(--fg-dim);
    font-size: 0.82rem;
  }
  .close {
    background: transparent;
    border: none;
    font-size: 1.1rem;
    color: var(--fg-dim);
    cursor: pointer;
  }
  .section {
    padding: 0.45rem 1rem;
  }
  .section.row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.6rem;
  }
  .previews {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding-bottom: 0.6rem;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    min-width: 0;
  }
  .field > span {
    font-size: 0.78rem;
    color: var(--fg-dim);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .field input,
  .field select,
  .field textarea {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.45rem 0.55rem;
    font: inherit;
    color: var(--fg);
    min-width: 0;
  }
  .field textarea {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.82rem;
    resize: vertical;
  }
  .actions-row {
    display: flex;
    gap: 0.6rem;
    align-items: center;
  }
  .primary {
    background: var(--accent);
    color: var(--bg);
    border: none;
    border-radius: 8px;
    padding: 0.5rem 0.95rem;
    font-weight: 600;
    cursor: pointer;
  }
  .primary:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
  .ghost {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--fg);
    border-radius: 8px;
    padding: 0.45rem 0.9rem;
    cursor: pointer;
  }
  .banner {
    margin: 0.2rem 1rem 0;
    padding: 0.5rem 0.7rem;
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.82rem;
    color: var(--fg-dim);
  }
  .err {
    margin: 0.2rem 1rem;
    padding: 0.45rem 0.7rem;
    background: color-mix(in srgb, var(--err) 15%, var(--bg-3));
    border: 1px solid var(--err);
    color: var(--err);
    border-radius: 8px;
    font-size: 0.82rem;
  }
  .footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    padding: 0.55rem 1rem 0.8rem;
    border-top: 1px solid var(--border);
    background: var(--bg-2);
  }
</style>
