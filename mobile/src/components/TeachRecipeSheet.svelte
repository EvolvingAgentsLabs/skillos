<script lang="ts">
  /**
   * TeachRecipeSheet — post-run affordance that lets the user tell a recipe
   * what to do differently next time. Each teaching attaches to the recipe
   * (cartridge), not a single output, so the correction compounds across
   * runs. The count surfaces on the recipe tile as the learning patina.
   */
  import {
    addTeaching,
    deleteTeaching,
    listTeachingsForCartridge,
    type TeachingRecord,
  } from "$lib/memory/teachings";

  interface Props {
    cartridge: string;
    /** Agent or step name the correction should target — optional. */
    suggestedStep?: string;
    oncancel: () => void;
    onsaved?: (t: TeachingRecord) => void;
  }

  let { cartridge, suggestedStep, oncancel, onsaved }: Props = $props();

  let text = $state("");
  let step = $state(suggestedStep ?? "");
  let saving = $state(false);
  let error = $state("");
  let existing = $state<TeachingRecord[]>([]);
  let loaded = $state(false);

  async function refresh() {
    existing = await listTeachingsForCartridge(cartridge);
    loaded = true;
  }

  $effect(() => {
    void refresh();
  });

  async function save() {
    const trimmed = text.trim();
    if (!trimmed) {
      error = "Type what the recipe should do differently next time.";
      return;
    }
    error = "";
    saving = true;
    try {
      const t = await addTeaching({
        cartridge,
        text: trimmed,
        target_step: step.trim() || undefined,
      });
      text = "";
      step = suggestedStep ?? "";
      await refresh();
      onsaved?.(t);
    } catch (e) {
      error = e instanceof Error ? e.message : String(e);
    } finally {
      saving = false;
    }
  }

  async function remove(id: string) {
    await deleteTeaching(id);
    await refresh();
  }
</script>

<button
  type="button"
  class="backdrop"
  onclick={oncancel}
  aria-label="Dismiss teach sheet"
></button>
<div class="sheet" role="dialog" aria-label="Teach this Recipe" tabindex="-1">
  <header>
    <div>
      <div class="title">Teach this Recipe</div>
      <div class="subtitle">Corrections attach to <code>{cartridge}</code> and compound over runs.</div>
    </div>
    <button class="close" onclick={oncancel} aria-label="Close">×</button>
  </header>

  <div class="body">
    <label class="field">
      <span class="lbl">What should the recipe do differently next time?</span>
      <textarea
        bind:value={text}
        placeholder={"e.g. round totals up to 2 decimals, skip mileage under 5km, use last month's categories"}
        rows="3"
        aria-invalid={!!error}
      ></textarea>
    </label>
    <label class="field">
      <span class="lbl">Apply to step <span class="hint">(optional)</span></span>
      <input
        type="text"
        bind:value={step}
        placeholder="agent or step name — leave empty for whole recipe"
      />
    </label>
    {#if error}
      <div class="err">{error}</div>
    {/if}
    <div class="actions">
      <button class="ghost" onclick={oncancel} disabled={saving}>Cancel</button>
      <button class="primary" onclick={save} disabled={saving || !text.trim()}>
        {saving ? "Saving…" : "Save teaching"}
      </button>
    </div>

    <div class="divider"></div>
    <div class="existing-head">
      <span>What this recipe has learned</span>
      <span class="count">{existing.filter((t) => t.active).length}</span>
    </div>
    {#if !loaded}
      <div class="muted">Loading…</div>
    {:else if existing.length === 0}
      <div class="muted">No teachings yet — this recipe runs exactly as synthesized.</div>
    {:else}
      <ul class="teachings">
        {#each existing as t (t.id)}
          <li class:inactive={!t.active}>
            <div class="t-text">{t.text}</div>
            <div class="t-meta">
              {#if t.target_step}<span class="t-step">{t.target_step}</span>{/if}
              <span class="t-time">{new Date(t.created_at).toLocaleString()}</span>
              <button class="t-del" onclick={() => remove(t.id)} aria-label="Delete teaching">×</button>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    border: none;
    padding: 0;
    cursor: pointer;
    z-index: 15;
  }
  .sheet {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--bg-2);
    border-top: 1px solid var(--border);
    border-radius: 14px 14px 0 0;
    padding: 1rem 1rem calc(1rem + env(safe-area-inset-bottom));
    max-height: 84vh;
    overflow-y: auto;
    z-index: 16;
    box-shadow: 0 -12px 28px rgba(0, 0, 0, 0.4);
    animation: sheetIn 0.18s ease-out;
  }
  @keyframes sheetIn {
    from { transform: translateY(14px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }
  header {
    display: flex;
    align-items: start;
    justify-content: space-between;
    gap: 0.5rem;
    margin-bottom: 0.9rem;
  }
  .title {
    font-weight: 600;
    font-size: 1.05rem;
  }
  .subtitle {
    font-size: 0.78rem;
    color: var(--fg-dim);
    margin-top: 0.12rem;
  }
  code {
    background: var(--bg-3);
    padding: 0 0.3rem;
    border-radius: 4px;
    font-size: 0.75rem;
  }
  .close {
    background: transparent;
    border: none;
    color: var(--fg-dim);
    font-size: 1.5rem;
    line-height: 1;
    cursor: pointer;
    padding: 0 0.25rem;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    margin-bottom: 0.8rem;
  }
  .lbl {
    font-size: 0.82rem;
    color: var(--fg);
  }
  .hint {
    color: var(--fg-dim);
    font-weight: normal;
  }
  textarea, input[type="text"] {
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.5rem 0.6rem;
    color: var(--fg);
    font: inherit;
    font-size: 0.88rem;
    resize: vertical;
  }
  textarea:focus, input[type="text"]:focus {
    outline: none;
    border-color: var(--accent);
  }
  .err {
    color: var(--err);
    font-size: 0.78rem;
    margin-bottom: 0.6rem;
  }
  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.4rem;
  }
  .actions button {
    padding: 0.5rem 0.9rem;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: var(--bg-3);
    color: var(--fg);
    font-size: 0.88rem;
    cursor: pointer;
  }
  .actions .primary {
    background: var(--accent);
    border-color: var(--accent);
    color: var(--bg);
    font-weight: 600;
  }
  .actions .primary:disabled {
    opacity: 0.55;
    cursor: not-allowed;
  }
  .divider {
    border-top: 1px solid var(--border);
    margin: 1.2rem 0 0.7rem;
  }
  .existing-head {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: var(--fg-dim);
    margin-bottom: 0.45rem;
  }
  .count {
    background: var(--bg-3);
    border-radius: 9999px;
    padding: 0 0.55rem;
    font-variant-numeric: tabular-nums;
  }
  .muted {
    color: var(--fg-dim);
    font-size: 0.82rem;
    padding: 0.4rem 0;
  }
  .teachings {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  .teachings li {
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.55rem 0.7rem;
  }
  .teachings li.inactive {
    opacity: 0.5;
  }
  .t-text {
    font-size: 0.88rem;
    color: var(--fg);
    white-space: pre-wrap;
  }
  .t-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.3rem;
    font-size: 0.74rem;
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
    font-size: 1.1rem;
    line-height: 1;
    cursor: pointer;
    padding: 0 0.25rem;
  }
  .t-del:hover {
    color: var(--err);
  }
</style>
