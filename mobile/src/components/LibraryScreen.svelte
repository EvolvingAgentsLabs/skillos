<script lang="ts">
  import { onMount } from "svelte";
  import {
    cloneCartridge,
    deleteCartridge,
    library,
    loadLibrary,
  } from "$lib/state/library.svelte";
  import type {
    AgentSpec,
    CartridgeManifest,
  } from "$lib/cartridge/types";
  import type { SkillDefinition } from "$lib/skills/skill_loader";
  import AgentEditorSheet from "$components/editors/AgentEditorSheet.svelte";
  import CartridgeWizard from "$components/CartridgeWizard.svelte";
  import SchemaEditorSheet from "$components/editors/SchemaEditorSheet.svelte";
  import SkillEditorSheet from "$components/editors/SkillEditorSheet.svelte";

  let selected = $state<string | null>(null);
  let busy = $state(false);
  let status = $state("");
  let editAgent = $state<{ cartridge: string; agent: AgentSpec } | null>(null);
  let editSchema = $state<{ cartridge: string; ref: string } | null>(null);
  let editSkill = $state<{ cartridge: string; skill: SkillDefinition } | null>(null);
  let newCartridgeOpen = $state(false);

  onMount(async () => {
    await loadLibrary();
  });

  async function onClone(c: CartridgeManifest) {
    const dst = prompt(`Clone "${c.name}" as…`, `${c.name}-copy`);
    if (!dst) return;
    busy = true;
    status = "";
    try {
      await cloneCartridge(c.name, dst);
      status = `cloned → ${dst}`;
      selected = dst;
    } catch (err) {
      status = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }

  async function onDelete(c: CartridgeManifest) {
    if (!confirm(`Delete cartridge "${c.name}"? This cannot be undone.`)) return;
    busy = true;
    status = "";
    try {
      await deleteCartridge(c.name);
      if (selected === c.name) selected = null;
      status = `deleted ${c.name}`;
    } catch (err) {
      status = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }

  const selectedLib = $derived(
    selected
      ? library.cartridges.find((c) => c.name === selected) ?? null
      : null,
  );
</script>

<section class="lib">
  <header>
    <h1>Library</h1>
    <button class="primary" onclick={() => (newCartridgeOpen = true)}>+ New</button>
  </header>

  {#if !library.loaded}
    <div class="empty">Loading…</div>
  {:else if library.error}
    <div class="err">{library.error}</div>
  {:else if library.cartridges.length === 0}
    <div class="empty">
      <div class="empty-title">No cartridges yet</div>
      <div class="empty-hint">
        Resync from bundle via Settings, or use <strong>+ New</strong> to create one.
      </div>
    </div>
  {:else}
    <div class="grid">
      <aside class="list">
        {#each library.cartridges as c (c.name)}
          <button
            class="row"
            class:active={selected === c.name}
            onclick={() => (selected = c.name)}
          >
            <div class="row-name">{c.name}</div>
            <div class="row-sub">
              {c.manifest.type}
              · {Object.keys(c.manifest.flows).length} flow{Object.keys(c.manifest.flows).length === 1 ? "" : "s"}
              · {c.agents.length} agent{c.agents.length === 1 ? "" : "s"}
              {#if c.skills.length > 0}· {c.skills.length} skill{c.skills.length === 1 ? "" : "s"}{/if}
            </div>
          </button>
        {/each}
      </aside>

      <div class="detail">
        {#if !selectedLib}
          <div class="empty">Pick a cartridge.</div>
        {:else}
          {@const c = selectedLib}
          <div class="detail-head">
            <div>
              <h2>{c.name}</h2>
              <p class="sub">{c.manifest.description || "(no description)"}</p>
            </div>
            <div class="actions">
              <button disabled={busy} onclick={() => onClone(c.manifest)}>Clone…</button>
              <button class="danger" disabled={busy} onclick={() => onDelete(c.manifest)}>Delete</button>
            </div>
          </div>

          <div class="meta">
            <span class="chip">preferred_tier: {c.manifest.preferred_tier}</span>
            <span class="chip">default_flow: {c.manifest.default_flow || "—"}</span>
            {#if c.manifest.validators.length > 0}
              <span class="chip">{c.manifest.validators.length} validator{c.manifest.validators.length === 1 ? "" : "s"}</span>
            {/if}
          </div>

          <h3>Agents</h3>
          <ul class="items">
            {#each c.agents as a (a.name)}
              <li>
                <button class="linkish" onclick={() => (editAgent = { cartridge: c.name, agent: a })}>
                  {a.name} <span class="muted">({a.tier}{a.produces.length ? ` → ${a.produces.join(", ")}` : ""})</span>
                </button>
              </li>
            {/each}
            {#if c.agents.length === 0}<li class="muted">no agents</li>{/if}
          </ul>

          <h3>Schemas</h3>
          <ul class="items">
            {#each Object.entries(c.manifest.blackboard_schema) as [key, ref] (ref)}
              <li>
                <button class="linkish" onclick={() => (editSchema = { cartridge: c.name, ref })}>
                  {ref} <span class="muted">(for {key})</span>
                </button>
              </li>
            {/each}
            {#if Object.keys(c.manifest.blackboard_schema).length === 0}
              <li class="muted">no schemas</li>
            {/if}
          </ul>

          {#if c.skills.length > 0}
            <h3>Gallery skills</h3>
            <ul class="items">
              {#each c.skills as s (s.name)}
                <li>
                  <button class="linkish" onclick={() => (editSkill = { cartridge: c.name, skill: s })}>
                    {s.name} <span class="muted">— {s.description}</span>
                  </button>
                </li>
              {/each}
            </ul>
          {/if}
        {/if}
      </div>
    </div>
  {/if}

  {#if status}<div class="status">{status}</div>{/if}
</section>

{#if editAgent}
  <AgentEditorSheet
    cartridge={editAgent.cartridge}
    agent={editAgent.agent}
    oncancel={() => (editAgent = null)}
    onsaved={() => (editAgent = null)}
  />
{/if}

{#if editSchema}
  <SchemaEditorSheet
    cartridge={editSchema.cartridge}
    ref={editSchema.ref}
    oncancel={() => (editSchema = null)}
    onsaved={() => (editSchema = null)}
  />
{/if}

{#if editSkill}
  <SkillEditorSheet
    cartridge={editSkill.cartridge}
    skill={editSkill.skill}
    oncancel={() => (editSkill = null)}
    onsaved={() => (editSkill = null)}
  />
{/if}

{#if newCartridgeOpen}
  <CartridgeWizard
    oncancel={() => (newCartridgeOpen = false)}
    oncreated={(name) => {
      newCartridgeOpen = false;
      selected = name;
    }}
  />
{/if}

<style>
  .lib {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }
  header {
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
  .primary {
    background: var(--accent);
    color: var(--bg);
    border: none;
    font-weight: 600;
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
    font-size: 1.2rem;
    color: var(--fg);
  }
  .grid {
    flex: 1;
    display: grid;
    grid-template-columns: minmax(180px, 30%) 1fr;
    overflow: hidden;
  }
  .list {
    overflow-y: auto;
    border-right: 1px solid var(--border);
    background: var(--bg-2);
  }
  .row {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.55rem 0.85rem;
    border: none;
    border-bottom: 1px solid var(--border);
    background: transparent;
    color: var(--fg);
    cursor: pointer;
  }
  .row.active {
    background: var(--bg-3);
  }
  .row-name {
    font-weight: 500;
  }
  .row-sub {
    color: var(--fg-dim);
    font-size: 0.75rem;
    margin-top: 0.1rem;
  }
  .detail {
    padding: 1rem 1rem 2rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }
  .detail-head {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 0.6rem;
  }
  h2 {
    margin: 0;
    font-size: 1.2rem;
  }
  .sub {
    margin: 0.15rem 0 0;
    color: var(--fg-dim);
    font-size: 0.85rem;
  }
  .actions {
    display: flex;
    gap: 0.4rem;
  }
  .actions button {
    font-size: 0.78rem;
    padding: 0.3rem 0.55rem;
  }
  .danger {
    color: var(--err);
    border-color: var(--err);
  }
  .meta {
    display: flex;
    gap: 0.3rem;
    flex-wrap: wrap;
  }
  .chip {
    background: var(--bg-3);
    border-radius: 9999px;
    padding: 0.1rem 0.55rem;
    font-size: 0.72rem;
    color: var(--fg-dim);
  }
  h3 {
    margin: 0.6rem 0 0.1rem;
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--fg-dim);
  }
  .items {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }
  .items li {
    padding: 0.25rem 0;
  }
  .linkish {
    background: transparent;
    border: none;
    color: var(--accent);
    padding: 0;
    cursor: pointer;
    text-align: left;
    font-size: 0.88rem;
  }
  .muted {
    color: var(--fg-dim);
    font-size: 0.78rem;
  }
  .status {
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.45rem 0.7rem;
    margin: 0.5rem 1rem;
    font-size: 0.8rem;
  }
</style>
