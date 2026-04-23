<script lang="ts">
  import { onMount } from "svelte";
  import { library, loadLibrary } from "$lib/state/library.svelte";
  import { countActiveTeachingsAll } from "$lib/memory/teachings";
  import { SKILLS_PROVIDER_PROJECT_ID } from "$lib/skills/skill_llm_proxy";
  import type { SkillDefinition } from "$lib/skills/skill_loader";
  import ForkSkillSheet from "$components/ForkSkillSheet.svelte";
  import ProviderSettingsSheet from "$components/ProviderSettingsSheet.svelte";
  import SkillCard from "$components/SkillCard.svelte";
  import SkillEditorSheet from "$components/editors/SkillEditorSheet.svelte";
  import TeachRecipeSheet from "$components/TeachRecipeSheet.svelte";

  let editSkill = $state<{ cartridge: string; skill: SkillDefinition } | null>(null);
  let forkSkill = $state<{ cartridge: string; skill: SkillDefinition } | null>(null);
  let teachCartridge = $state<string | null>(null);
  let providerOpen = $state(false);
  let savedToast = $state("");
  let teachings = $state<Record<string, number>>({});

  async function refreshTeachings() {
    teachings = await countActiveTeachingsAll();
  }

  onMount(async () => {
    await Promise.all([loadLibrary(), refreshTeachings()]);
  });

  const totalSkills = $derived(
    library.cartridges.reduce((n, c) => n + c.skills.length, 0),
  );

  // Only show cartridges that have at least one skill — otherwise the user
  // sees a long list of empty sections with just a cartridge header.
  const cartridgesWithSkills = $derived(
    library.cartridges.filter((c) => c.skills.length > 0),
  );
</script>

<section class="skills">
  <header class="top">
    <h1>Skills</h1>
    <button
      class="icon-btn"
      onclick={() => (providerOpen = true)}
      aria-label="Skills provider settings"
    >⚙</button>
  </header>

  {#if !library.loaded}
    <div class="empty">Loading…</div>
  {:else if library.error}
    <div class="err">{library.error}</div>
  {:else if totalSkills === 0}
    <div class="empty">
      <div class="empty-title">No skills yet</div>
      <div class="empty-hint">
        Skills are small runnable tools built from a cartridge. Seed or create a cartridge
        with a skill, then it appears here as a runnable card.
      </div>
    </div>
  {:else}
    <div class="feed">
      {#each cartridgesWithSkills as c (c.name)}
        <section class="cart-group">
          <div class="cart-head">
            <span class="cart-name">{c.name}</span>
            <span class="cart-sub">
              {c.skills.length} skill{c.skills.length === 1 ? "" : "s"}
              {#if teachings[c.name]}
                · <span class="patina">learned {teachings[c.name]}</span>
              {/if}
            </span>
            <button
              class="teach-btn"
              onclick={() => (teachCartridge = c.name)}
              aria-label="Teach this Recipe"
              title="Teach this Recipe"
            >✎</button>
          </div>
          {#each c.skills as s (s.name)}
            <SkillCard
              skill={s}
              cartridge={c.name}
              oneditrequested={() => (editSkill = { cartridge: c.name, skill: s })}
              onforkrequested={() => (forkSkill = { cartridge: c.name, skill: s })}
            />
          {/each}
        </section>
      {/each}
    </div>
  {/if}
</section>

{#if editSkill}
  <SkillEditorSheet
    cartridge={editSkill.cartridge}
    skill={editSkill.skill}
    oncancel={() => (editSkill = null)}
    onsaved={() => (editSkill = null)}
  />
{/if}

{#if forkSkill}
  <ForkSkillSheet
    cartridge={forkSkill.cartridge}
    skill={forkSkill.skill}
    oncancel={() => (forkSkill = null)}
    onsaved={(payload) => {
      forkSkill = null;
      savedToast = `Forked → ${payload.skillName} in ${payload.cartridge}`;
      setTimeout(() => (savedToast = ""), 4000);
      loadLibrary();
    }}
  />
{/if}

{#if teachCartridge}
  <TeachRecipeSheet
    cartridge={teachCartridge}
    oncancel={() => (teachCartridge = null)}
    onsaved={() => {
      savedToast = "Teaching saved — will apply next run";
      setTimeout(() => (savedToast = ""), 3000);
      void refreshTeachings();
    }}
  />
{/if}

{#if savedToast}
  <div class="toast" role="status">{savedToast}</div>
{/if}

{#if providerOpen}
  <ProviderSettingsSheet
    projectId={SKILLS_PROVIDER_PROJECT_ID}
    onsaved={() => (providerOpen = false)}
    oncancel={() => (providerOpen = false)}
  />
{/if}

<style>
  .skills {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }
  .top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.7rem 1rem;
    border-bottom: 1px solid var(--border);
    background: var(--bg-2);
  }
  h1 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  .icon-btn {
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--fg-dim);
    width: 2rem;
    height: 2rem;
    font-size: 1rem;
    cursor: pointer;
  }
  .icon-btn:hover {
    color: var(--fg);
  }
  .empty,
  .err {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    padding: 2rem;
    color: var(--fg-dim);
    text-align: center;
  }
  .err {
    color: var(--err);
  }
  .empty-title {
    font-size: 1.1rem;
    color: var(--fg);
  }
  .empty-hint {
    max-width: 32ch;
    font-size: 0.85rem;
    line-height: 1.4;
  }
  .feed {
    flex: 1;
    overflow-y: auto;
    padding: 0.8rem 0.8rem calc(4rem + env(safe-area-inset-bottom));
  }
  .cart-group {
    margin-bottom: 1.2rem;
  }
  .cart-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    padding: 0 0.2rem 0.4rem;
  }
  .cart-name {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--fg-dim);
    font-weight: 600;
  }
  .cart-sub {
    font-size: 0.72rem;
    color: var(--fg-dim);
    flex: 1;
    text-align: right;
    margin-right: 0.5rem;
  }
  .cart-sub .patina {
    color: var(--accent);
    font-weight: 500;
  }
  .teach-btn {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--accent);
    width: 1.8rem;
    height: 1.5rem;
    border-radius: 6px;
    font-size: 0.85rem;
    line-height: 1;
    cursor: pointer;
    padding: 0;
  }
  .teach-btn:hover {
    border-color: var(--accent);
  }
  .toast {
    position: fixed;
    left: 50%;
    bottom: calc(4.5rem + env(safe-area-inset-bottom));
    transform: translateX(-50%);
    background: var(--bg-2);
    border: 1px solid var(--accent);
    color: var(--fg);
    padding: 0.5rem 0.9rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    z-index: 15;
    animation: toastIn 0.2s ease-out;
  }
  @keyframes toastIn {
    from { opacity: 0; transform: translate(-50%, 6px); }
    to { opacity: 1; transform: translate(-50%, 0); }
  }
</style>
