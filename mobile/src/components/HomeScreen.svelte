<script lang="ts">
  /**
   * HomeScreen — the Recipe grid.
   *
   * This is the reframe from "Projects" default landing to "app-launcher
   * of Recipes you built." Per the unit-of-value principle (see
   * skillos_recipe_principle.md in memory), each tile is a Recipe — a
   * composition of plan + agents + skills + memory attachments — and
   * tapping a tile runs the whole composition. The "New…" tile is the
   * escape hatch to the Forge ceremony for capabilities the user doesn't
   * yet have.
   *
   * This surface supersedes the old "swipe through projects" default
   * without removing it — ProjectSwiper lives on behind the Runs tab
   * for the active-work view.
   */
  import { onMount } from "svelte";
  import { CartridgeRegistry } from "$lib/cartridge/registry";
  import type { CartridgeManifest } from "$lib/cartridge/types";
  import { loadProviderConfig } from "$lib/state/provider_config";
  import {
    createProject,
    loadProjects,
    projects,
  } from "$lib/state/projects.svelte";
  import { countActiveTeachingsAll } from "$lib/memory/teachings";
  import { runProject } from "$lib/state/run_project";
  import GoalComposer from "$components/GoalComposer.svelte";
  import ProviderSettingsSheet from "$components/ProviderSettingsSheet.svelte";

  interface Props {
    onopenproject: (projectId: string) => void;
  }

  let { onopenproject }: Props = $props();

  let registry = $state<CartridgeRegistry | null>(null);
  let cartridges = $state<CartridgeManifest[]>([]);
  let teachings = $state<Record<string, number>>({});
  let composerOpen = $state(false);
  let settingsForProject = $state<string | null>(null);
  let pendingRunProject = $state<string | null>(null);
  let loaded = $state(false);

  async function refreshTeachings() {
    teachings = await countActiveTeachingsAll();
  }

  onMount(async () => {
    const reg = new CartridgeRegistry();
    await reg.init();
    registry = reg;
    cartridges = reg.list();
    await Promise.all([loadProjects(), refreshTeachings()]);
    loaded = true;
  });

  // Group cartridges by category so Home has visible structure. Cartridges
  // without a category fall into "Other" — still visible, never hidden.
  // This is the minimal form of Job-style grouping (G2): same-category
  // recipes cluster together on Home.
  interface CategoryGroup {
    category: string;
    cartridges: CartridgeManifest[];
  }

  const groups = $derived.by<CategoryGroup[]>(() => {
    const byCat = new Map<string, CartridgeManifest[]>();
    for (const m of cartridges) {
      const cat = (m.category ?? "Other").trim() || "Other";
      if (!byCat.has(cat)) byCat.set(cat, []);
      byCat.get(cat)!.push(m);
    }
    // Stable order: categories alphabetical; "Other" last.
    const entries = Array.from(byCat.entries());
    entries.sort(([a], [b]) => {
      if (a === "Other" && b !== "Other") return 1;
      if (b === "Other" && a !== "Other") return -1;
      return a.localeCompare(b);
    });
    return entries.map(([category, list]) => ({
      category,
      cartridges: list.sort((a, b) => a.name.localeCompare(b.name)),
    }));
  });

  async function activateRecipe(m: CartridgeManifest) {
    // Reuse an existing project for this cartridge if there is one, so the
    // user doesn't accumulate duplicate projects per recipe. First-run for
    // the cartridge creates a new one.
    const existing = projects.items.find((p) => p.cartridge === m.name);
    const projectId = existing
      ? existing.id
      : (await createProject({
          name: m.name,
          cartridge: m.name,
          initialGoal: m.description || `Run ${m.name}`,
        })).id;

    // If no provider configured, route through settings so the first run
    // actually completes instead of silently failing.
    const cfg = await loadProviderConfig(projectId);
    if (!cfg) {
      pendingRunProject = projectId;
      settingsForProject = projectId;
      return;
    }
    if (!registry) return;
    onopenproject(projectId);
    await runProject(projectId, { registry });
  }

  async function handleCreate(v: { name: string; cartridge: string | null; goal: string }) {
    composerOpen = false;
    const p = await createProject({
      name: v.name || "Untitled",
      cartridge: v.cartridge,
      initialGoal: v.goal,
    });
    onopenproject(p.id);
  }

  async function onSettingsSaved(projectId: string) {
    settingsForProject = null;
    if (pendingRunProject === projectId && registry) {
      pendingRunProject = null;
      onopenproject(projectId);
      await runProject(projectId, { registry });
    }
  }

  function iconFor(m: CartridgeManifest): string {
    // Heuristic — use the category to pick a deliberately mundane emoji that
    // reinforces "this is a tool you built." Neutral defaults: no magic wand.
    const cat = (m.category ?? "").toLowerCase();
    if (/(finance|invoice|expense|money)/.test(cat)) return "💰";
    if (/(food|menu|recipe|meal)/.test(cat)) return "🍴";
    if (/(plan|schedule|calendar|itinerary)/.test(cat)) return "🗓";
    if (/(engineer|electrical|field|site|report)/.test(cat)) return "⚡";
    if (/(writing|article|note|doc)/.test(cat)) return "📝";
    if (/(health|mood|journal|medical)/.test(cat)) return "❤️";
    return "🧩";
  }
</script>

<section class="home">
  <header class="top">
    <h1>Home</h1>
    <div class="sub">Your pinned Recipes. Tap to run.</div>
  </header>

  {#if !loaded}
    <div class="empty">Loading…</div>
  {:else if cartridges.length === 0}
    <div class="empty">
      <div class="empty-title">No Recipes yet</div>
      <div class="empty-hint">
        Tap the + tile to teach SkillOS a new one. The first time runs in the cloud;
        after that it lives on your phone, free and offline.
      </div>
      <button class="new-big" onclick={() => (composerOpen = true)}>
        ✨ Teach me a Recipe
      </button>
    </div>
  {:else}
    <div class="scroll">
      {#each groups as g (g.category)}
        <section class="group">
          <div class="group-head">
            <span class="group-label">{g.category}</span>
            <span class="group-count">{g.cartridges.length}</span>
          </div>
          <div class="grid">
            {#each g.cartridges as m (m.name)}
              <button
                class="tile"
                onclick={() => activateRecipe(m)}
                aria-label="Run recipe {m.name}"
              >
                <span class="tile-ico" aria-hidden="true">{iconFor(m)}</span>
                <span class="tile-name">{m.name}</span>
                {#if teachings[m.name]}
                  <span class="tile-patina">learned {teachings[m.name]}</span>
                {/if}
              </button>
            {/each}
          </div>
        </section>
      {/each}

      <section class="group">
        <div class="group-head">
          <span class="group-label">New</span>
        </div>
        <div class="grid">
          <button
            class="tile new"
            onclick={() => (composerOpen = true)}
            aria-label="Teach a new Recipe"
          >
            <span class="tile-ico" aria-hidden="true">✨</span>
            <span class="tile-name">Teach a Recipe</span>
            <span class="tile-patina">first run uses cloud</span>
          </button>
        </div>
      </section>
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
</section>

<style>
  .home {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }
  .top {
    padding: 0.7rem 1rem 0.5rem;
    border-bottom: 1px solid var(--border);
    background: var(--bg-2);
  }
  h1 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  .sub {
    color: var(--fg-dim);
    font-size: 0.8rem;
    margin-top: 0.15rem;
  }
  .empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    padding: 2rem;
    color: var(--fg-dim);
    text-align: center;
  }
  .empty-title {
    font-size: 1.1rem;
    color: var(--fg);
  }
  .empty-hint {
    max-width: 34ch;
    font-size: 0.85rem;
    line-height: 1.4;
  }
  .new-big {
    margin-top: 1rem;
    padding: 0.75rem 1.2rem;
    background: var(--accent);
    color: var(--bg);
    border: none;
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
  }
  .scroll {
    flex: 1;
    overflow-y: auto;
    padding: 0.8rem 0.8rem calc(4rem + env(safe-area-inset-bottom));
  }
  .group {
    margin-bottom: 1.1rem;
  }
  .group-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    padding: 0 0.2rem 0.4rem;
  }
  .group-label {
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--fg-dim);
    font-weight: 600;
  }
  .group-count {
    font-size: 0.72rem;
    color: var(--fg-dim);
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(9.5rem, 1fr));
    gap: 0.55rem;
  }
  .tile {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.9rem 0.7rem 0.75rem;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.35rem;
    cursor: pointer;
    transition: transform 0.1s ease, border-color 0.15s ease, background 0.15s ease;
    min-height: 6.5rem;
    text-align: left;
    color: var(--fg);
    font: inherit;
  }
  .tile:hover, .tile:active {
    border-color: var(--accent);
    background: color-mix(in srgb, var(--accent) 6%, var(--bg-2));
  }
  .tile:active {
    transform: scale(0.98);
  }
  .tile-ico {
    font-size: 1.6rem;
    line-height: 1;
  }
  .tile-name {
    font-weight: 500;
    font-size: 0.92rem;
    line-height: 1.25;
    word-break: break-word;
  }
  .tile-patina {
    font-size: 0.7rem;
    color: var(--accent);
    background: color-mix(in srgb, var(--accent) 14%, var(--bg-3));
    border-radius: 9999px;
    padding: 0.1rem 0.5rem;
    margin-top: auto;
  }
  .tile.new {
    border-style: dashed;
    background: transparent;
  }
  .tile.new .tile-patina {
    color: var(--fg-dim);
    background: var(--bg-3);
  }
</style>
