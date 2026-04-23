<script lang="ts">
  import { onMount } from "svelte";
  import { buildProvider } from "$lib/llm/build_provider";
  import type { CartridgeManifest } from "$lib/cartridge/types";
  import {
    library,
    loadLibrary,
    saveSkill,
  } from "$lib/state/library.svelte";
  import type { ProjectCard } from "$lib/state/projects.svelte";
  import { loadSkillsProviderConfig } from "$lib/skills/skill_llm_proxy";
  import {
    synthesizeSkill,
    type SynthResult,
    type SynthSource,
  } from "$lib/skills/skill_synth";

  interface Props {
    card: ProjectCard;
    projectName: string;
    projectCartridge: string | null;
    goal: string;
    relatedCardTitles?: string[];
    oncancel: () => void;
    onsaved: (payload: { cartridge: string; skillName: string }) => void;
  }

  let {
    card,
    projectName,
    projectCartridge,
    goal,
    relatedCardTitles,
    oncancel,
    onsaved,
  }: Props = $props();

  let targetCartridge = $state<string | null>(null);
  let skillName = $state("");
  let synthesizing = $state(false);
  let saving = $state(false);
  let synth = $state<SynthResult | null>(null);
  let error = $state("");
  let noProviderConfigured = $state(false);

  // Preview buffers — initialized from `synth`, then user may edit them before save.
  let mdDraft = $state("");
  let jsDraft = $state("");

  // Only cartridges that have a skills_source can host new skills. (Others
  // are validator-only or agent-only cartridges.)
  const hostableCartridges = $derived<CartridgeManifest[]>(
    library.cartridges.map((c) => c.manifest).filter((m) => !!m.skills_source),
  );

  onMount(async () => {
    await loadLibrary();
    // Prefer the project's own cartridge if it can host skills.
    const preferred = hostableCartridges.find((m) => m.name === projectCartridge);
    targetCartridge =
      preferred?.name ?? hostableCartridges[0]?.name ?? null;
    // Best-effort default name from the card title.
    skillName = slugify(card.title) || "user-skill";
    // Check provider config up front so we can show a helpful hint.
    const cfg = await loadSkillsProviderConfig();
    noProviderConfigured = !cfg;
  });

  function slugify(s: string): string {
    return (
      s
        .toLowerCase()
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
        error = "No provider configured for skill synthesis. Open the Skills tab → ⚙ to set one.";
        noProviderConfigured = true;
        return;
      }
      const provider = await buildProvider(cfg);
      const source: SynthSource = {
        goal,
        cardTitle: card.title,
        cardSubtitle: card.subtitle,
        cardSchemaRef: card.schema_ref,
        cardData: card.data,
        projectName,
        projectCartridge,
        relatedCardTitles,
      };
      const result = await synthesizeSkill(provider, source);
      synth = result;
      if (result.skillName && !skillName) skillName = result.skillName;
      mdDraft = result.skillMd;
      jsDraft = result.indexJs;
      if (result.errors.length > 0 && result.ok === false) {
        // Surface as a soft warning, user can still save and edit.
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
    const name = slugify(skillName);
    if (!name) {
      error = "Skill name is required.";
      return;
    }
    if (!mdDraft.trim() || !jsDraft.trim()) {
      error = "Synthesize or paste SKILL.md and index.js before saving.";
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
      <h2>Save as Skill</h2>
      <p class="sub">Turn this one-off result into a reusable, offline skill.</p>
    </div>
    <button class="ghost close" onclick={oncancel} aria-label="Close">✕</button>
  </header>

  <div class="section">
    <div class="context">
      <div class="ctx-label">From card</div>
      <div class="ctx-title">{card.title}</div>
      {#if card.subtitle}<div class="ctx-sub">{card.subtitle}</div>{/if}
      <div class="ctx-meta">
        project <strong>{projectName}</strong>
        {#if projectCartridge}· cartridge <strong>{projectCartridge}</strong>{/if}
      </div>
    </div>
  </div>

  <div class="section row">
    <label class="field">
      <span>Skill name</span>
      <input type="text" autocomplete="off" bind:value={skillName} />
      <span class="hint">used as folder name (slug)</span>
    </label>
    <label class="field">
      <span>Target cartridge</span>
      <select bind:value={targetCartridge} disabled={hostableCartridges.length === 0}>
        {#if hostableCartridges.length === 0}
          <option value={null}>— no cartridges can host skills —</option>
        {:else}
          {#each hostableCartridges as m (m.name)}
            <option value={m.name}>{m.name}</option>
          {/each}
        {/if}
      </select>
      <span class="hint">cartridge must declare <code>skills_source</code></span>
    </label>
  </div>

  {#if noProviderConfigured}
    <div class="banner">
      No cloud provider configured for synthesis. Open <strong>Skills tab → ⚙</strong> to set one,
      then come back. You can also skip synthesis and write SKILL.md + index.js by hand below.
    </div>
  {/if}

  <div class="section">
    <div class="actions-row">
      <button
        class="primary"
        disabled={synthesizing || !targetCartridge}
        onclick={onSynthesize}
      >
        {synthesizing ? "Synthesizing…" : synth ? "Regenerate" : "✨ Synthesize"}
      </button>
      {#if synth && synth.errors.length > 0}
        <span class="warn">{synth.errors.length} warning{synth.errors.length === 1 ? "" : "s"}</span>
      {/if}
    </div>
  </div>

  <div class="section previews">
    <label class="field">
      <span>SKILL.md</span>
      <textarea rows="8" spellcheck="false" bind:value={mdDraft}></textarea>
    </label>
    <label class="field">
      <span>scripts/index.js</span>
      <textarea rows="10" spellcheck="false" bind:value={jsDraft}></textarea>
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
      {saving ? "Saving…" : "Save skill"}
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
  .context {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.5rem 0.7rem;
  }
  .ctx-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--fg-dim);
  }
  .ctx-title {
    font-weight: 600;
    font-size: 0.95rem;
    margin-top: 0.15rem;
  }
  .ctx-sub {
    color: var(--fg-dim);
    font-size: 0.82rem;
  }
  .ctx-meta {
    font-size: 0.78rem;
    color: var(--fg-dim);
    margin-top: 0.25rem;
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
  .hint {
    text-transform: none !important;
    letter-spacing: 0 !important;
    font-size: 0.72rem !important;
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
    align-items: center;
    gap: 0.6rem;
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
  .warn {
    font-size: 0.8rem;
    color: var(--err);
  }
  .banner {
    margin: 0.2rem 1rem 0;
    padding: 0.5rem 0.7rem;
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    font-size: 0.82rem;
    color: var(--fg-dim);
    line-height: 1.4;
  }
  .err {
    margin: 0.2rem 1rem;
    padding: 0.45rem 0.7rem;
    background: var(--bg-3);
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
  code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.78rem;
    background: var(--bg-3);
    padding: 0 0.25rem;
    border-radius: 3px;
  }
</style>
