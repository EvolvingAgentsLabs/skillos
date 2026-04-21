<script lang="ts">
  import { onMount } from "svelte";
  import { seedIfNeeded, type SeedProgress } from "$lib/storage/seed";
  import { getMeta } from "$lib/storage/db";
  import LibraryScreen from "$components/LibraryScreen.svelte";
  import Onboarding from "$components/Onboarding.svelte";
  import ProjectSwiper from "$components/ProjectSwiper.svelte";
  import SkillHostIframe from "$components/SkillHostIframe.svelte";

  let progress = $state<SeedProgress>({ phase: "idle", completed: 0, total: 0 });
  let authoringFlag = $state(false);
  let tab = $state<"projects" | "library">("projects");

  const pct = $derived(
    progress.total > 0 ? Math.round((progress.completed / progress.total) * 100) : 0,
  );
  const booting = $derived(
    progress.phase === "idle" ||
      progress.phase === "fetching-manifest" ||
      progress.phase === "seeding",
  );

  onMount(async () => {
    await seedIfNeeded((p) => (progress = p));
    authoringFlag = Boolean(await getMeta("authoring_mode"));
    // Poll the flag on visibility change so Settings → Authoring mode takes
    // effect without requiring a reload. Cheap enough on a mobile device.
    document.addEventListener("visibilitychange", async () => {
      if (document.visibilityState === "visible") {
        authoringFlag = Boolean(await getMeta("authoring_mode"));
      }
    });
  });
</script>

<main>
  {#if booting}
    <div class="boot">
      <h1>SkillOS</h1>
      <div class="sub">Pure-Markdown OS · Mobile</div>
      <div class="bar"><div class="fill" style:width="{pct}%"></div></div>
      <div class="status">
        {#if progress.phase === "fetching-manifest"}
          Fetching seed manifest…
        {:else if progress.phase === "seeding"}
          Seeding {progress.completed} / {progress.total}
          {#if progress.current}<br /><code>{progress.current}</code>{/if}
        {:else if progress.phase === "error"}
          <span class="err">Seed failed: {progress.message}</span>
        {:else}
          Starting…
        {/if}
      </div>
    </div>
  {:else if progress.phase === "error"}
    <div class="boot">
      <h1>SkillOS</h1>
      <div class="status err">Seed failed: {progress.message}</div>
      <button onclick={() => location.reload()}>Retry</button>
    </div>
  {:else}
    {#if tab === "projects"}
      <ProjectSwiper />
    {:else}
      <LibraryScreen />
    {/if}
    {#if authoringFlag}
      <nav class="tabbar" aria-label="Sections">
        <button class:active={tab === "projects"} onclick={() => (tab = "projects")}>
          Projects
        </button>
        <button class:active={tab === "library"} onclick={() => (tab = "library")}>
          Library
        </button>
      </nav>
    {/if}
    <SkillHostIframe />
    <Onboarding />
  {/if}
</main>

<style>
  .tabbar {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    display: grid;
    grid-template-columns: 1fr 1fr;
    background: var(--bg-2);
    border-top: 1px solid var(--border);
    padding-bottom: env(safe-area-inset-bottom);
    z-index: 6;
  }
  .tabbar button {
    background: transparent;
    border: none;
    color: var(--fg-dim);
    padding: 0.65rem 0;
    font-size: 0.85rem;
    font-weight: 500;
    cursor: pointer;
  }
  .tabbar button.active {
    color: var(--accent);
    border-top: 2px solid var(--accent);
  }
  main {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  .boot {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 2rem;
    text-align: center;
  }
  h1 {
    margin: 0 0 0.2em;
    font-weight: 500;
    font-size: 2rem;
    letter-spacing: 0.02em;
  }
  .sub {
    color: var(--fg-dim);
    font-size: 0.95rem;
    margin-bottom: 2.5rem;
  }
  .bar {
    width: min(320px, 80vw);
    height: 6px;
    background: var(--bg-3);
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 1rem;
  }
  .fill {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--accent-2));
    transition: width 0.2s ease;
  }
  .status {
    color: var(--fg-dim);
    font-size: 0.9rem;
    min-height: 3em;
  }
  .err {
    color: var(--err);
  }
</style>
