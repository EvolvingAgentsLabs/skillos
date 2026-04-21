<script lang="ts">
  import type { CartridgeManifest } from "$lib/cartridge/types";

  interface Props {
    cartridges: CartridgeManifest[];
    onsubmit: (v: { name: string; cartridge: string | null; goal: string }) => void;
    oncancel: () => void;
  }

  let { cartridges, onsubmit, oncancel }: Props = $props();

  let name = $state("");
  let cartridge = $state<string | null>(null);
  let goal = $state("");

  function submit(e: Event) {
    e.preventDefault();
    if (!name.trim() && !goal.trim()) return;
    onsubmit({ name, cartridge, goal });
  }
</script>

<button type="button" class="backdrop" onclick={oncancel} aria-label="Close"></button>
<form class="sheet" onsubmit={submit}>
  <div class="handle"></div>
  <h2>New project</h2>

  <label class="field">
    <span>Name</span>
    <input
      type="text"
      autocomplete="off"
      placeholder="e.g. Sunday menu"
      bind:value={name}
    />
  </label>

  <label class="field">
    <span>Cartridge</span>
    <select bind:value={cartridge}>
      <option value={null}>— none —</option>
      {#each cartridges as c (c.name)}
        <option value={c.name}>{c.name}</option>
      {/each}
    </select>
  </label>

  <label class="field">
    <span>Initial goal (optional)</span>
    <textarea
      rows="3"
      placeholder="Plan meals for the week…"
      bind:value={goal}
    ></textarea>
  </label>

  <div class="actions">
    <button type="button" class="ghost" onclick={oncancel}>Cancel</button>
    <button type="submit" class="primary">Create</button>
  </div>
</form>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    z-index: 10;
    border: none;
    padding: 0;
    cursor: pointer;
  }
  .sheet {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--bg-2);
    border-top: 1px solid var(--border);
    border-radius: 14px 14px 0 0;
    padding: 0.7rem 1.1rem 1.3rem;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
    z-index: 11;
    padding-bottom: calc(1.3rem + env(safe-area-inset-bottom));
    max-height: 80vh;
    overflow-y: auto;
  }
  .handle {
    width: 36px;
    height: 4px;
    background: var(--bg-3);
    border-radius: 2px;
    align-self: center;
    margin-bottom: 0.25rem;
  }
  h2 {
    margin: 0 0 0.1rem;
    font-size: 1.15rem;
    font-weight: 500;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    font-size: 0.85rem;
    color: var(--fg-dim);
  }
  input,
  textarea,
  select {
    font: inherit;
    color: var(--fg);
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.55rem 0.7rem;
    width: 100%;
  }
  textarea {
    resize: vertical;
  }
  .actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
    margin-top: 0.3rem;
  }
  .primary {
    background: var(--accent);
    color: var(--bg);
    border: none;
    font-weight: 600;
  }
  .ghost {
    background: transparent;
  }
</style>
