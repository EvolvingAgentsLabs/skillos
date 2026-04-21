<script lang="ts">
  import type { ProjectCard } from "$lib/state/projects.svelte";

  interface Props {
    card: ProjectCard;
    onmove?: (lane: ProjectCard["lane"]) => void;
    onremove?: () => void;
  }

  let { card, onmove, onremove }: Props = $props();

  const icon = $derived(
    card.kind === "goal"
      ? "🎯"
      : card.kind === "agent"
        ? "🤖"
        : card.kind === "skill"
          ? "🧩"
          : "📄",
  );

  const relTime = $derived(formatRel(card.created_at));

  function formatRel(iso: string): string {
    const then = new Date(iso).getTime();
    const delta = Date.now() - then;
    const m = Math.round(delta / 60_000);
    if (m < 1) return "just now";
    if (m < 60) return `${m}m ago`;
    const h = Math.round(m / 60);
    if (h < 24) return `${h}h ago`;
    const d = Math.round(h / 24);
    return `${d}d ago`;
  }

  let expanded = $state(false);
</script>

<article class="card kind-{card.kind}" class:expanded>
  <header>
    <span class="icon" aria-hidden="true">{icon}</span>
    <div class="title-block">
      <div class="title">{card.title}</div>
      {#if card.subtitle}<div class="subtitle">{card.subtitle}</div>{/if}
    </div>
    <button class="chevron" aria-label="expand" onclick={() => (expanded = !expanded)}>
      {expanded ? "▾" : "▸"}
    </button>
  </header>

  <div class="meta">
    {#if card.produced_by}<span class="chip">{card.produced_by}</span>{/if}
    <span class="chip muted">{relTime}</span>
    {#if card.schema_ref}<span class="chip muted">{card.schema_ref}</span>{/if}
  </div>

  {#if expanded}
    <div class="body">
      {#if card.data !== undefined}
        <pre class="json">{JSON.stringify(card.data, null, 2)}</pre>
      {:else}
        <div class="empty">No payload yet.</div>
      {/if}
      <div class="actions">
        {#if card.lane !== "planned"}
          <button onclick={() => onmove?.("planned")}>→ Planned</button>
        {/if}
        {#if card.lane !== "executing"}
          <button onclick={() => onmove?.("executing")}>→ In Execution</button>
        {/if}
        {#if card.lane !== "done"}
          <button onclick={() => onmove?.("done")}>→ Done</button>
        {/if}
        <button class="danger" onclick={() => onremove?.()}>Delete</button>
      </div>
    </div>
  {/if}
</article>

<style>
  .card {
    border: 1px solid var(--border);
    background: var(--bg-2);
    border-radius: 10px;
    padding: 0.7rem 0.8rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    transition: transform 0.18s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    animation: cardIn 0.2s ease-out;
  }
  @keyframes cardIn {
    from {
      opacity: 0;
      transform: translateY(6px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  .card:active {
    transform: scale(0.98);
  }
  .kind-goal {
    border-left: 3px solid var(--accent);
  }
  .kind-agent {
    border-left: 3px solid var(--accent-2);
  }
  .kind-skill {
    border-left: 3px solid var(--warn);
  }
  .kind-document {
    border-left: 3px solid var(--ok);
  }
  header {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
  }
  .icon {
    font-size: 1.2rem;
    flex: 0 0 auto;
  }
  .title-block {
    flex: 1;
    min-width: 0;
  }
  .title {
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    line-clamp: 2;
  }
  .subtitle {
    font-size: 0.82rem;
    color: var(--fg-dim);
    margin-top: 0.15rem;
  }
  .chevron {
    background: transparent;
    border: none;
    color: var(--fg-dim);
    padding: 0.1rem 0.3rem;
    cursor: pointer;
  }
  .meta {
    display: flex;
    gap: 0.3rem;
    flex-wrap: wrap;
    font-size: 0.72rem;
  }
  .chip {
    background: var(--bg-3);
    border-radius: 9999px;
    padding: 0.1rem 0.55rem;
    color: var(--fg);
  }
  .chip.muted {
    color: var(--fg-dim);
  }
  .body {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
    border-top: 1px dashed var(--border);
    padding-top: 0.5rem;
  }
  .json {
    background: var(--bg);
    border-radius: 6px;
    padding: 0.5rem;
    max-height: 30vh;
    overflow: auto;
    font-size: 0.78rem;
    white-space: pre-wrap;
    word-break: break-word;
    margin: 0;
  }
  .empty {
    color: var(--fg-dim);
    font-size: 0.82rem;
  }
  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
  }
  .actions button {
    font-size: 0.78rem;
    padding: 0.35rem 0.6rem;
  }
  .danger {
    color: var(--err);
    border-color: var(--err);
  }
</style>
