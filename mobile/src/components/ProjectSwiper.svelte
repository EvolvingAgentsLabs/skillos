<script lang="ts">
  import { onMount } from "svelte";
  import { CartridgeRegistry } from "$lib/cartridge/registry";
  import type { CartridgeManifest } from "$lib/cartridge/types";
  import { loadProviderConfig } from "$lib/state/provider_config";
  import {
    addCard,
    createProject,
    loadProjects,
    projects,
  } from "$lib/state/projects.svelte";
  import { runStream } from "$lib/state/run_events.svelte";
  import { runProject } from "$lib/state/run_project";
  import GoalComposer from "$components/GoalComposer.svelte";
  import ProjectColumn from "$components/ProjectColumn.svelte";
  import ProviderSettingsSheet from "$components/ProviderSettingsSheet.svelte";
  import RunLogDrawer from "$components/RunLogDrawer.svelte";
  import SettingsSheet from "$components/SettingsSheet.svelte";

  let registry = $state<CartridgeRegistry | null>(null);
  let cartridges = $state<CartridgeManifest[]>([]);
  let composerOpen = $state(false);
  let settingsForProject = $state<string | null>(null);
  let appSettingsOpen = $state(false);
  let pendingRunProject = $state<string | null>(null);
  let pagerEl: HTMLDivElement | null = $state(null);
  let activeIndex = $state(0);

  onMount(async () => {
    const reg = new CartridgeRegistry();
    await reg.init();
    registry = reg;
    cartridges = reg.list();
    await loadProjects();
  });

  async function handleCreate(v: { name: string; cartridge: string | null; goal: string }) {
    composerOpen = false;
    const p = await createProject({
      name: v.name || "Untitled project",
      cartridge: v.cartridge,
      initialGoal: v.goal,
    });
    // Scroll to the new project (index 0) after the DOM updates.
    requestAnimationFrame(() => scrollToIndex(0));
    void p;
  }

  async function addQuickCard(projectId: string) {
    await addCard(projectId, {
      kind: "goal",
      lane: "planned",
      title: "New goal",
      produced_by: "user",
    });
  }

  async function startRun(projectId: string) {
    const cfg = await loadProviderConfig(projectId);
    if (!cfg) {
      pendingRunProject = projectId;
      settingsForProject = projectId;
      return;
    }
    if (!registry) return;
    await runProject(projectId, { registry });
  }

  async function onSettingsSaved(projectId: string) {
    settingsForProject = null;
    if (pendingRunProject === projectId) {
      pendingRunProject = null;
      await startRun(projectId);
    }
  }

  function scrollToIndex(i: number) {
    if (!pagerEl) return;
    const w = pagerEl.clientWidth;
    pagerEl.scrollTo({ left: i * w, behavior: "smooth" });
  }

  function onPagerScroll() {
    if (!pagerEl) return;
    const w = pagerEl.clientWidth;
    if (w <= 0) return;
    activeIndex = Math.round(pagerEl.scrollLeft / w);
  }
</script>

<section class="app">
  <header class="top">
    <button class="brand" onclick={() => (appSettingsOpen = true)} aria-label="App settings">SkillOS</button>
    <div class="dots" aria-hidden="true">
      {#each projects.items as _, i (i)}
        <span class="dot" class:active={i === activeIndex}></span>
      {/each}
    </div>
    <button class="add" aria-label="New project" onclick={() => (composerOpen = true)}>+</button>
  </header>

  {#if !projects.loaded}
    <div class="empty">Loading…</div>
  {:else if projects.items.length === 0}
    <div class="empty">
      <div class="empty-title">No projects yet</div>
      <div class="empty-hint">
        Tap <span class="kbd">+</span> to create one.
        {cartridges.length > 0
          ? `${cartridges.length} cartridge${cartridges.length === 1 ? "" : "s"} available.`
          : "Seeding not yet complete."}
      </div>
    </div>
  {:else}
    <div class="pager" bind:this={pagerEl} onscroll={onPagerScroll}>
      {#each projects.items as p (p.id)}
        <ProjectColumn
          project={p}
          running={runStream.running && runStream.projectId === p.id}
          onaddcard={() => addQuickCard(p.id)}
          onrun={() => startRun(p.id)}
          onsettings={() => (settingsForProject = p.id)}
        />
      {/each}
    </div>
  {/if}

  {#if composerOpen}
    <GoalComposer
      {cartridges}
      onsubmit={handleCreate}
      oncancel={() => (composerOpen = false)}
    />
  {/if}

  {#if settingsForProject}
    <ProviderSettingsSheet
      projectId={settingsForProject}
      onsaved={() => onSettingsSaved(settingsForProject!)}
      oncancel={() => {
        settingsForProject = null;
        pendingRunProject = null;
      }}
    />
  {/if}

  {#if appSettingsOpen}
    <SettingsSheet oncancel={() => (appSettingsOpen = false)} />
  {/if}

  <RunLogDrawer />
</section>

<style>
  .app {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }
  .top {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    padding: 0.7rem 1rem;
    border-bottom: 1px solid var(--border);
    background: var(--bg-2);
  }
  .brand {
    font-weight: 600;
    letter-spacing: 0.03em;
    background: transparent;
    border: none;
    padding: 0.25rem 0.4rem;
    justify-self: start;
    color: inherit;
    cursor: pointer;
    font-size: inherit;
  }
  .dots {
    display: flex;
    gap: 0.3rem;
    justify-self: center;
  }
  .dot {
    width: 6px;
    height: 6px;
    border-radius: 3px;
    background: var(--bg-3);
    transition: background 0.15s ease, width 0.15s ease;
  }
  .dot.active {
    width: 18px;
    background: var(--accent);
  }
  .add {
    justify-self: end;
    width: 2rem;
    height: 2rem;
    border-radius: 1rem;
    padding: 0;
    font-size: 1.2rem;
    line-height: 1;
    background: var(--accent);
    color: var(--bg);
    border: none;
    font-weight: 600;
  }
  .pager {
    flex: 1;
    display: flex;
    flex-direction: row;
    overflow-x: auto;
    overflow-y: hidden;
    scroll-snap-type: x mandatory;
    scrollbar-width: none;
    overscroll-behavior-x: contain;
  }
  .pager::-webkit-scrollbar {
    display: none;
  }
  .empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 2rem;
    text-align: center;
  }
  .empty-title {
    font-size: 1.2rem;
  }
  .empty-hint {
    color: var(--fg-dim);
    max-width: 30ch;
  }
  .kbd {
    display: inline-block;
    padding: 0 0.4rem;
    border: 1px solid var(--border);
    border-radius: 4px;
    background: var(--bg-3);
    font-family: monospace;
  }
</style>
