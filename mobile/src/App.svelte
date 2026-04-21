<script lang="ts">
  import { onMount } from "svelte";
  import { seedIfNeeded, type SeedProgress } from "$lib/storage/seed";
  import Onboarding from "$components/Onboarding.svelte";
  import ProjectSwiper from "$components/ProjectSwiper.svelte";
  import SkillHostIframe from "$components/SkillHostIframe.svelte";

  let progress = $state<SeedProgress>({ phase: "idle", completed: 0, total: 0 });

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
    <ProjectSwiper />
    <SkillHostIframe />
    <Onboarding />
  {/if}
</main>

<style>
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
