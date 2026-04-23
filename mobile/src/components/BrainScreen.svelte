<script lang="ts">
  import { onMount } from "svelte";
  import type { MemoryRecord, TeachingRecord } from "$lib/storage/db";
  import {
    deleteExperience,
    listExperiences,
  } from "$lib/memory/smart_memory";
  import {
    deleteTeaching,
    listTeachingsForCartridge,
  } from "$lib/memory/teachings";
  import { getDB } from "$lib/storage/db";
  import TeachRecipeSheet from "$components/TeachRecipeSheet.svelte";

  type Mode = "runs" | "recipes";

  let records = $state<MemoryRecord[]>([]);
  let teachings = $state<TeachingRecord[]>([]);
  let loaded = $state(false);
  let deleting = $state<string | null>(null);
  let mode = $state<Mode>("runs");
  let teachCartridge = $state<string | null>(null);

  async function loadAll() {
    const db = await getDB();
    const [r, t] = await Promise.all([
      listExperiences(),
      db.getAll("teachings") as Promise<TeachingRecord[]>,
    ]);
    records = r;
    teachings = t;
    loaded = true;
  }

  onMount(async () => {
    await loadAll();
  });

  async function onDelete(rec: MemoryRecord) {
    if (!confirm(`Delete this memory? "${trim(rec.goal, 80)}"`)) return;
    deleting = rec.experience_id;
    try {
      await deleteExperience(rec.experience_id);
      records = records.filter((r) => r.experience_id !== rec.experience_id);
    } finally {
      deleting = null;
    }
  }

  async function onDeleteTeaching(t: TeachingRecord) {
    if (!confirm(`Delete this teaching? "${trim(t.text, 80)}"`)) return;
    await deleteTeaching(t.id);
    teachings = teachings.filter((x) => x.id !== t.id);
  }

  // ── Recipes view ──────────────────────────────────────────────────────
  // A cluster per cartridge, merging all the structured memory we have about
  // it: the teachings attached to it (bidirectional — they belong to the
  // recipe, not a single run) and the recent experiences that mention it in
  // `components_used`. This is how the Brain tab delivers the
  // recipes↔memory visibility from the UI roadmap.

  interface RecipeCluster {
    cartridge: string;
    teachings: TeachingRecord[];
    experiences: MemoryRecord[];
  }

  const clusters = $derived.by<RecipeCluster[]>(() => {
    const byName = new Map<string, RecipeCluster>();
    function ensure(name: string): RecipeCluster {
      let c = byName.get(name);
      if (!c) {
        c = { cartridge: name, teachings: [], experiences: [] };
        byName.set(name, c);
      }
      return c;
    }
    for (const t of teachings) {
      if (!t.active) continue;
      ensure(t.cartridge).teachings.push(t);
    }
    for (const r of records) {
      // `project` on a MemoryRecord is usually the cartridge name for
      // cartridge-driven runs — that's the most reliable cluster key here.
      if (r.project) ensure(r.project).experiences.push(r);
    }
    return Array.from(byName.values()).sort((a, b) => {
      // Prefer clusters with teachings (they're the ones that "know you"),
      // then by experience count.
      const at = a.teachings.length, bt = b.teachings.length;
      if (at !== bt) return bt - at;
      return b.experiences.length - a.experiences.length;
    });
  });

  // ── Grouping by recency ───────────────────────────────────────────────
  type Bucket = "today" | "yesterday" | "this_week" | "earlier";
  const BUCKET_LABELS: Record<Bucket, string> = {
    today: "Today",
    yesterday: "Yesterday",
    this_week: "This week",
    earlier: "Earlier",
  };
  const BUCKET_ORDER: Bucket[] = ["today", "yesterday", "this_week", "earlier"];

  function bucketFor(iso: string): Bucket {
    const then = new Date(iso);
    const now = new Date();
    const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const t = then.getTime();
    if (t >= startOfToday) return "today";
    if (t >= startOfToday - 86_400_000) return "yesterday";
    if (t >= startOfToday - 7 * 86_400_000) return "this_week";
    return "earlier";
  }

  const grouped = $derived.by<Record<Bucket, MemoryRecord[]>>(() => {
    const out: Record<Bucket, MemoryRecord[]> = {
      today: [],
      yesterday: [],
      this_week: [],
      earlier: [],
    };
    for (const r of records) out[bucketFor(r.timestamp)].push(r);
    return out;
  });

  // ── Totals strip ──────────────────────────────────────────────────────
  function usedLlm(r: MemoryRecord): boolean {
    if (!r.components_used) return false;
    return r.components_used.some((c) => c.startsWith("llm:"));
  }

  const totals = $derived.by(() => {
    let totalCost = 0;
    let totalSeconds = 0;
    let successes = 0;
    let cloudRuns = 0;
    let localRuns = 0;
    for (const r of records) {
      totalCost += r.cost_estimate_usd || 0;
      totalSeconds += r.duration_seconds || 0;
      if (r.outcome === "success" || r.outcome === "success_with_recovery") successes += 1;
      if (usedLlm(r)) cloudRuns += 1;
      else localRuns += 1;
    }
    const cloudPct = records.length > 0 ? Math.round((cloudRuns / records.length) * 100) : 0;
    return {
      count: records.length,
      successes,
      successRate: records.length > 0 ? Math.round((successes / records.length) * 100) : 0,
      totalCostUsd: totalCost,
      totalMinutes: Math.round(totalSeconds / 60),
      cloudRuns,
      localRuns,
      cloudPct,
      localPct: 100 - cloudPct,
    };
  });

  // ── Formatting helpers ────────────────────────────────────────────────
  function trim(s: string, n: number): string {
    if (!s) return "";
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
  }

  function formatCost(usd: number): string {
    if (!usd || usd < 0.0001) return "$0";
    if (usd < 0.01) return `$${usd.toFixed(4)}`;
    return `$${usd.toFixed(2)}`;
  }

  function formatDuration(seconds: number): string {
    if (!seconds || seconds < 1) return "<1s";
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
    return `${(seconds / 3600).toFixed(1)}h`;
  }

  function formatTime(iso: string): string {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString(undefined, {
        hour: "numeric",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  }

  function outcomeIcon(o: MemoryRecord["outcome"]): string {
    switch (o) {
      case "success":
        return "✅";
      case "success_with_recovery":
        return "🛠";
      case "partial":
        return "⚠️";
      case "failure":
        return "❌";
      default:
        return "·";
    }
  }
</script>

<section class="brain">
  <header class="top">
    <h1>Brain</h1>
    <div class="sub">Everything this OS has done — and what it has learned from you.</div>
    <nav class="mode-switch" aria-label="Brain view">
      <button
        class:active={mode === "runs"}
        onclick={() => (mode = "runs")}
      >Runs</button>
      <button
        class:active={mode === "recipes"}
        onclick={() => (mode = "recipes")}
      >Recipes</button>
    </nav>
  </header>

  {#if !loaded}
    <div class="empty">Loading…</div>
  {:else if records.length === 0 && teachings.length === 0}
    <div class="empty">
      <div class="empty-title">No memories yet</div>
      <div class="empty-hint">
        When you run a recipe or teach one a correction, an entry appears here.
        Your audit trail of what actually happened — and what the OS has learned.
      </div>
    </div>
  {:else}
    <div class="totals">
      <div class="stat">
        <span class="stat-n">{totals.count}</span>
        <span class="stat-lbl">runs</span>
      </div>
      <div class="stat">
        <span class="stat-n">{totals.successRate}%</span>
        <span class="stat-lbl">success</span>
      </div>
      <div class="stat">
        <span class="stat-n">{formatCost(totals.totalCostUsd)}</span>
        <span class="stat-lbl">cloud spend</span>
      </div>
      <div class="stat">
        <span class="stat-n">{totals.totalMinutes}m</span>
        <span class="stat-lbl">runtime</span>
      </div>
    </div>

    <div class="mix" aria-label="Local vs cloud split">
      <div class="mix-bar" role="img" aria-label="{totals.localPct}% local, {totals.cloudPct}% cloud">
        <span class="mix-local" style:width="{totals.localPct}%"></span>
        <span class="mix-cloud" style:width="{totals.cloudPct}%"></span>
      </div>
      <div class="mix-legend">
        <span class="legend-dot dot-local" aria-hidden="true"></span>
        <span>⚡ {totals.localRuns} local</span>
        <span class="legend-sep" aria-hidden="true">·</span>
        <span class="legend-dot dot-cloud" aria-hidden="true"></span>
        <span>☁ {totals.cloudRuns} cloud</span>
      </div>
    </div>

    {#if mode === "runs"}
      <div class="feed">
        {#each BUCKET_ORDER as b (b)}
          {#if grouped[b].length > 0}
            <section class="group">
              <div class="group-head">
                <span class="group-label">{BUCKET_LABELS[b]}</span>
                <span class="group-count">{grouped[b].length}</span>
              </div>
              {#each grouped[b] as rec (rec.experience_id)}
                <article class="rec outcome-{rec.outcome}">
                  <div class="rec-head">
                    <span class="outcome" aria-hidden="true">{outcomeIcon(rec.outcome)}</span>
                    <div class="goal-block">
                      <div class="goal">{trim(rec.goal, 200)}</div>
                      <div class="meta">
                        <span class="chip muted">{rec.project}</span>
                        <span class="chip muted">{formatTime(rec.timestamp)}</span>
                        <span class="chip muted">{formatDuration(rec.duration_seconds)}</span>
                        {#if rec.cost_estimate_usd > 0}
                          <span class="chip warn">{formatCost(rec.cost_estimate_usd)}</span>
                        {/if}
                        {#if rec.quality_score > 0}
                          <span class="chip muted">q {rec.quality_score.toFixed(1)}</span>
                        {/if}
                      </div>
                    </div>
                    <button
                      class="del"
                      aria-label="Delete memory"
                      disabled={deleting === rec.experience_id}
                      onclick={() => onDelete(rec)}
                    >×</button>
                  </div>
                  {#if rec.components_used && rec.components_used.length > 0}
                    <div class="components">
                      {#each rec.components_used as c (c)}
                        <span class="chip small">{c}</span>
                      {/each}
                    </div>
                  {/if}
                  {#if rec.output_summary}
                    <div class="summary">{trim(rec.output_summary, 260)}</div>
                  {/if}
                  {#if rec.learnings}
                    <div class="learnings">
                      <span class="learn-label">Learnings</span>
                      <span class="learn-text">{trim(rec.learnings, 260)}</span>
                    </div>
                  {/if}
                </article>
              {/each}
            </section>
          {/if}
        {/each}
      </div>
    {:else}
      <div class="feed">
        {#if clusters.length === 0}
          <div class="empty-inline">
            No recipes with memory yet — run one or teach one a correction.
          </div>
        {:else}
          {#each clusters as cl (cl.cartridge)}
            <article class="cluster">
              <header class="cluster-head">
                <div class="cluster-name">{cl.cartridge}</div>
                <div class="cluster-meta">
                  {#if cl.teachings.length > 0}
                    <span class="chip accent">learned {cl.teachings.length}</span>
                  {/if}
                  {#if cl.experiences.length > 0}
                    <span class="chip muted">{cl.experiences.length} run{cl.experiences.length === 1 ? "" : "s"}</span>
                  {/if}
                  <button
                    class="teach-inline"
                    onclick={() => (teachCartridge = cl.cartridge)}
                    aria-label="Teach this Recipe"
                    title="Teach this Recipe"
                  >✎</button>
                </div>
              </header>

              {#if cl.teachings.length > 0}
                <div class="teachings-block">
                  <div class="block-label">What this recipe has learned about you</div>
                  <ul class="teachings-list">
                    {#each cl.teachings as t (t.id)}
                      <li>
                        <div class="t-text">{t.text}</div>
                        <div class="t-meta">
                          {#if t.target_step}<span class="t-step">{t.target_step}</span>{/if}
                          <span class="t-time">{formatTime(t.created_at)}</span>
                          <button
                            class="t-del"
                            aria-label="Delete teaching"
                            onclick={() => onDeleteTeaching(t)}
                          >×</button>
                        </div>
                      </li>
                    {/each}
                  </ul>
                </div>
              {/if}

              {#if cl.experiences.length > 0}
                <div class="exps-block">
                  <div class="block-label">Recent runs</div>
                  <ul class="exps-list">
                    {#each cl.experiences.slice(0, 5) as rec (rec.experience_id)}
                      <li class="outcome-{rec.outcome}">
                        <span class="outcome" aria-hidden="true">{outcomeIcon(rec.outcome)}</span>
                        <span class="goal-inline">{trim(rec.goal, 100)}</span>
                        <span class="chip muted small">{formatTime(rec.timestamp)}</span>
                      </li>
                    {/each}
                    {#if cl.experiences.length > 5}
                      <li class="more">… and {cl.experiences.length - 5} more in Runs</li>
                    {/if}
                  </ul>
                </div>
              {/if}
            </article>
          {/each}
        {/if}
      </div>
    {/if}
  {/if}
</section>

{#if teachCartridge}
  <TeachRecipeSheet
    cartridge={teachCartridge}
    oncancel={() => (teachCartridge = null)}
    onsaved={() => {
      void loadAll();
    }}
  />
{/if}

<style>
  .brain {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }
  .top {
    padding: 0.7rem 1rem 0.4rem;
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
    gap: 0.4rem;
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
  .totals {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
    padding: 0.6rem 0.8rem;
    border-bottom: 1px solid var(--border);
    background: var(--bg-2);
  }
  .stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.1rem;
  }
  .stat-n {
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    font-size: 1rem;
  }
  .stat-lbl {
    font-size: 0.7rem;
    color: var(--fg-dim);
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }
  .mix {
    padding: 0.5rem 0.8rem 0.7rem;
    border-bottom: 1px solid var(--border);
    background: var(--bg-2);
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }
  .mix-bar {
    display: flex;
    width: 100%;
    height: 6px;
    border-radius: 3px;
    overflow: hidden;
    background: var(--bg-3);
  }
  .mix-local {
    background: var(--ok);
  }
  .mix-cloud {
    background: var(--warn);
  }
  .mix-legend {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.75rem;
    color: var(--fg-dim);
  }
  .legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 4px;
    display: inline-block;
  }
  .dot-local {
    background: var(--ok);
  }
  .dot-cloud {
    background: var(--warn);
  }
  .legend-sep {
    opacity: 0.55;
  }
  .feed {
    flex: 1;
    overflow-y: auto;
    padding: 0.6rem 0.8rem calc(4rem + env(safe-area-inset-bottom));
  }
  .group {
    margin-bottom: 1rem;
  }
  .group-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    padding: 0 0.15rem 0.3rem;
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
  .rec {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.55rem 0.7rem;
    margin-bottom: 0.45rem;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  .outcome-success {
    border-left: 3px solid var(--ok);
  }
  .outcome-success_with_recovery {
    border-left: 3px solid var(--accent);
  }
  .outcome-partial {
    border-left: 3px solid var(--warn);
  }
  .outcome-failure {
    border-left: 3px solid var(--err);
  }
  .rec-head {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 0.45rem;
    align-items: flex-start;
  }
  .outcome {
    font-size: 1.05rem;
    line-height: 1.2;
  }
  .goal-block {
    min-width: 0;
  }
  .goal {
    font-weight: 500;
    line-height: 1.3;
    word-break: break-word;
  }
  .meta {
    display: flex;
    gap: 0.25rem;
    flex-wrap: wrap;
    margin-top: 0.25rem;
  }
  .chip {
    display: inline-block;
    padding: 0.05rem 0.45rem;
    border-radius: 9999px;
    font-size: 0.7rem;
    background: var(--bg-3);
    color: var(--fg);
  }
  .chip.muted {
    color: var(--fg-dim);
  }
  .chip.warn {
    background: color-mix(in srgb, var(--warn) 18%, var(--bg-3));
    color: var(--fg);
  }
  .chip.small {
    font-size: 0.68rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  }
  .components {
    display: flex;
    gap: 0.25rem;
    flex-wrap: wrap;
  }
  .summary {
    font-size: 0.82rem;
    color: var(--fg-dim);
    line-height: 1.4;
  }
  .learnings {
    display: flex;
    gap: 0.4rem;
    font-size: 0.8rem;
    background: var(--bg-3);
    border-radius: 6px;
    padding: 0.35rem 0.5rem;
  }
  .learn-label {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.65rem;
    color: var(--fg-dim);
    align-self: center;
  }
  .learn-text {
    color: var(--fg);
  }
  .del {
    background: transparent;
    border: none;
    color: var(--fg-dim);
    font-size: 1.1rem;
    line-height: 1;
    padding: 0.1rem 0.4rem;
    cursor: pointer;
    border-radius: 6px;
  }
  .del:hover {
    background: var(--bg-3);
    color: var(--err);
  }
  .del:disabled {
    opacity: 0.4;
    cursor: progress;
  }

  /* Mode switch */
  .mode-switch {
    display: inline-flex;
    gap: 0;
    margin-top: 0.5rem;
    border: 1px solid var(--border);
    border-radius: 9999px;
    overflow: hidden;
    background: var(--bg-3);
  }
  .mode-switch button {
    background: transparent;
    border: none;
    color: var(--fg-dim);
    padding: 0.3rem 0.8rem;
    font-size: 0.78rem;
    cursor: pointer;
  }
  .mode-switch button.active {
    background: var(--bg);
    color: var(--fg);
  }

  /* Recipes cluster view */
  .cluster {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.65rem 0.7rem;
    margin-bottom: 0.7rem;
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
  }
  .cluster-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }
  .cluster-name {
    font-weight: 600;
    font-size: 0.92rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .cluster-meta {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    flex-shrink: 0;
  }
  .chip.accent {
    background: color-mix(in srgb, var(--accent) 18%, var(--bg-3));
    color: var(--accent);
  }
  .teach-inline {
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
  .teach-inline:hover {
    border-color: var(--accent);
  }
  .block-label {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.65rem;
    color: var(--fg-dim);
    margin-bottom: 0.3rem;
  }
  .teachings-list,
  .exps-list {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }
  .teachings-list li {
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.4rem 0.55rem;
  }
  .t-text {
    font-size: 0.85rem;
  }
  .t-meta {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.2rem;
    font-size: 0.7rem;
    color: var(--fg-dim);
  }
  .t-step {
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 9999px;
    padding: 0.05rem 0.45rem;
    color: var(--accent);
  }
  .t-time {
    flex: 1;
  }
  .t-del {
    background: transparent;
    border: none;
    color: var(--fg-dim);
    font-size: 1rem;
    line-height: 1;
    cursor: pointer;
    padding: 0 0.2rem;
  }
  .t-del:hover {
    color: var(--err);
  }
  .exps-list li {
    display: grid;
    grid-template-columns: 1.1rem 1fr auto;
    gap: 0.4rem;
    align-items: center;
    font-size: 0.8rem;
    padding: 0.25rem 0.3rem;
    border-radius: 6px;
  }
  .exps-list li.outcome-failure { color: var(--err); }
  .exps-list li.outcome-partial { color: var(--warn); }
  .goal-inline {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .more {
    font-size: 0.75rem;
    color: var(--fg-dim);
    font-style: italic;
    padding-left: 1.5rem;
  }
  .empty-inline {
    text-align: center;
    color: var(--fg-dim);
    padding: 2rem;
    font-size: 0.88rem;
  }
</style>
