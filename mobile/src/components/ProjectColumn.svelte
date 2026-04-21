<script lang="ts">
  import Card from "$components/Card.svelte";
  import {
    laneCards,
    moveCard,
    removeCard,
    type Lane,
    type Project,
    type ProjectCard,
  } from "$lib/state/projects.svelte";

  interface Props {
    project: Project;
    running?: boolean;
    onaddcard?: () => void;
    onrun?: () => void;
    onsettings?: () => void;
  }

  let { project, running = false, onaddcard, onrun, onsettings }: Props = $props();

  const lanes: { key: Lane; label: string }[] = [
    { key: "planned", label: "Planned" },
    { key: "executing", label: "In Execution" },
    { key: "done", label: "Done" },
  ];

  async function handleMove(card: ProjectCard, lane: Lane) {
    await moveCard(project.id, card.id, lane);
  }
  async function handleRemove(card: ProjectCard) {
    await removeCard(project.id, card.id);
  }
</script>

<section class="column">
  <header class="column-head">
    <div class="name-block">
      <div class="name">{project.name}</div>
      <div class="cartridge">{project.cartridge ?? "no cartridge"}</div>
    </div>
    <div class="head-actions">
      <button class="icon" onclick={() => onsettings?.()} aria-label="Provider settings">⚙</button>
      {#if project.cartridge}
        <button class="run" onclick={() => onrun?.()} disabled={running} aria-label="Run">
          {running ? "…" : "▶ run"}
        </button>
      {/if}
      <button class="icon" onclick={() => onaddcard?.()} aria-label="Add card">＋</button>
    </div>
  </header>

  <div class="lanes">
    {#each lanes as lane (lane.key)}
      {@const cards = laneCards(project, lane.key)}
      <div class="lane lane-{lane.key}">
        <div class="lane-head">
          <span class="lane-label">{lane.label}</span>
          <span class="lane-count">{cards.length}</span>
        </div>
        <div class="lane-body">
          {#if cards.length === 0}
            <div class="lane-empty">—</div>
          {:else}
            {#each cards as card (card.id)}
              <Card
                {card}
                onmove={(l) => handleMove(card, l)}
                onremove={() => handleRemove(card)}
              />
            {/each}
          {/if}
        </div>
      </div>
    {/each}
  </div>
</section>

<style>
  .column {
    flex: 0 0 100%;
    width: 100%;
    height: 100%;
    scroll-snap-align: start;
    display: flex;
    flex-direction: column;
    background: var(--bg);
  }
  .column-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.6rem 1rem;
    border-bottom: 1px solid var(--border);
    background: var(--bg-2);
  }
  .name {
    font-weight: 600;
    letter-spacing: 0.01em;
  }
  .cartridge {
    font-size: 0.75rem;
    color: var(--fg-dim);
  }
  .head-actions {
    display: flex;
    gap: 0.35rem;
    align-items: center;
  }
  .head-actions button {
    font-size: 0.8rem;
    padding: 0.3rem 0.55rem;
  }
  .head-actions .icon {
    width: 2rem;
    padding: 0.3rem 0;
    text-align: center;
  }
  .head-actions .run {
    background: var(--accent);
    color: var(--bg);
    border: none;
    font-weight: 600;
  }
  .head-actions .run:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .lanes {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
    overscroll-behavior: contain;
  }
  .lane {
    display: flex;
    flex-direction: column;
    border-bottom: 1px solid var(--border);
    min-height: 33.33%;
  }
  .lane:last-child {
    border-bottom: none;
  }
  .lane-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.4rem 1rem;
    background: var(--bg-2);
    position: sticky;
    top: 0;
    z-index: 1;
    font-size: 0.8rem;
    color: var(--fg-dim);
    border-bottom: 1px solid var(--border);
  }
  .lane-label {
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .lane-count {
    background: var(--bg-3);
    border-radius: 9999px;
    padding: 0.05rem 0.5rem;
    font-variant-numeric: tabular-nums;
  }
  .lane-body {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.6rem 1rem 1rem;
  }
  .lane-empty {
    color: var(--fg-dim);
    font-size: 0.8rem;
    text-align: center;
    padding: 0.4rem 0;
  }
  .lane-planned .lane-label {
    color: var(--accent);
  }
  .lane-executing .lane-label {
    color: var(--warn);
  }
  .lane-done .lane-label {
    color: var(--ok);
  }
</style>
