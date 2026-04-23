<script lang="ts">
  import { onMount } from "svelte";
  import { seedIfNeeded, type SeedProgress } from "$lib/storage/seed";
  import { getMeta } from "$lib/storage/db";
  import BrainScreen from "$components/BrainScreen.svelte";
  import HomeScreen from "$components/HomeScreen.svelte";
  import LibraryScreen from "$components/LibraryScreen.svelte";
  import OfflineBanner from "$components/OfflineBanner.svelte";
  import Onboarding from "$components/Onboarding.svelte";
  import ProjectSwiper from "$components/ProjectSwiper.svelte";
  import SkillHostIframe from "$components/SkillHostIframe.svelte";
  import SkillsScreen from "$components/SkillsScreen.svelte";

  // Tab order is deliberate: Home first (grid of Recipes — the write-once/
  // run-forever-locally unit of value), Runs second (history of active work;
  // the old Projects surface is still here, just no longer the default
  // landing), then Skills / Brain, with Library as a dev-authoring tab.
  type Tab = "home" | "runs" | "skills" | "brain" | "library";

  let progress = $state<SeedProgress>({ phase: "idle", completed: 0, total: 0 });
  let authoringFlag = $state(false);
  let tab = $state<Tab>("home");

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
        // If the user turned off authoring while viewing the Library tab,
        // bounce them back to Projects so we don't leave a hidden tab selected.
        if (!authoringFlag && tab === "library") tab = "home";
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
    {#if tab === "home"}
      <HomeScreen onopenproject={() => (tab = "runs")} />
    {:else if tab === "runs"}
      <ProjectSwiper />
    {:else if tab === "skills"}
      <SkillsScreen />
    {:else if tab === "brain"}
      <BrainScreen />
    {:else}
      <LibraryScreen />
    {/if}
    <nav
      class="tabbar"
      class:cols-5={authoringFlag}
      aria-label="Sections"
    >
      <button class:active={tab === "home"} onclick={() => (tab = "home")}>
        Home
      </button>
      <button class:active={tab === "runs"} onclick={() => (tab = "runs")}>
        Runs
      </button>
      <button class:active={tab === "skills"} onclick={() => (tab = "skills")}>
        Skills
      </button>
      <button class:active={tab === "brain"} onclick={() => (tab = "brain")}>
        Brain
      </button>
      {#if authoringFlag}
        <button class:active={tab === "library"} onclick={() => (tab = "library")}>
          Library
        </button>
      {/if}
    </nav>
    <SkillHostIframe />
    <OfflineBanner />
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
    grid-template-columns: repeat(4, 1fr);
    background: var(--bg-2);
    border-top: 1px solid var(--border);
    padding-bottom: env(safe-area-inset-bottom);
    z-index: 6;
  }
  .tabbar.cols-5 {
    grid-template-columns: repeat(5, 1fr);
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
