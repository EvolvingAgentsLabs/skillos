<script lang="ts">
  import { saveCartridge } from "$lib/state/library.svelte";
  import { scaffoldCartridge } from "$lib/cartridge/scaffold";

  interface Props {
    oncancel: () => void;
    oncreated: (name: string) => void;
  }
  let { oncancel, oncreated }: Props = $props();

  let step = $state(0);
  let busy = $state(false);
  let error = $state("");

  // Form state
  let name = $state("");
  let description = $state("");
  let preferredTier = $state<"local" | "cloud" | "auto">("auto");
  let entryIntentsText = $state("");
  let blackboardRaw = $state(""); // lines like "weekly_menu: weekly_menu.schema.json"
  let agentsText = $state(""); // comma or newline separated

  const steps = [
    "Identity",
    "Intents",
    "Blackboard",
    "Agents & Flow",
    "Review",
  ];

  function parseBlackboard(text: string): Record<string, string> {
    const out: Record<string, string> = {};
    for (const line of text.split(/\n+/)) {
      const m = /^\s*([\w-]+)\s*:\s*(.+?)\s*$/.exec(line);
      if (m) out[m[1]] = m[2].endsWith(".json") ? m[2] : `${m[2]}.schema.json`;
    }
    return out;
  }

  function parseList(text: string): string[] {
    return text
      .split(/[\n,]+/)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  async function onCreate() {
    busy = true;
    error = "";
    try {
      const files = scaffoldCartridge({
        name,
        description,
        preferredTier,
        entryIntents: parseList(entryIntentsText),
        blackboardSchema: parseBlackboard(blackboardRaw),
        agents: parseList(agentsText),
      });
      await saveCartridge(name, files);
      oncreated(name);
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      busy = false;
    }
  }

  const canAdvance = $derived(
    step === 0 ? name.trim().length > 0 : true,
  );
</script>

<button type="button" class="backdrop" onclick={oncancel} aria-label="Close"></button>
<section class="sheet">
  <header>
    <h2>New cartridge</h2>
    <div class="dots">
      {#each steps as _, i (i)}
        <span class="dot" class:active={i === step}></span>
      {/each}
    </div>
  </header>

  <div class="content">
    {#if step === 0}
      <h3>{steps[0]}</h3>
      <label class="field">
        <span>Name</span>
        <input type="text" bind:value={name} placeholder="e.g. weekend-planner" />
      </label>
      <label class="field">
        <span>Description</span>
        <textarea bind:value={description} rows="2"></textarea>
      </label>
      <label class="field">
        <span>Preferred tier</span>
        <select bind:value={preferredTier}>
          <option value="auto">auto (default)</option>
          <option value="local">local (on-device first)</option>
          <option value="cloud">cloud (always fallback)</option>
        </select>
      </label>
    {:else if step === 1}
      <h3>{steps[1]}</h3>
      <p class="hint">
        Phrases that route this cartridge when a user types a bare goal.
        One per line.
      </p>
      <label class="field">
        <span>Entry intents</span>
        <textarea bind:value={entryIntentsText} rows="4" placeholder={"plan my weekend\nsaturday itinerary"}></textarea>
      </label>
    {:else if step === 2}
      <h3>{steps[2]}</h3>
      <p class="hint">
        Map each blackboard key to a schema file. Format:
        <code>key_name: filename.schema.json</code>
      </p>
      <label class="field">
        <span>Blackboard schema</span>
        <textarea bind:value={blackboardRaw} rows="4" placeholder={"itinerary: itinerary.schema.json"}></textarea>
      </label>
    {:else if step === 3}
      <h3>{steps[3]}</h3>
      <p class="hint">
        Ordered list of agent names. A stub file is created for each; edit
        later from the Library.
      </p>
      <label class="field">
        <span>Agents (in order)</span>
        <textarea bind:value={agentsText} rows="4" placeholder={"day-planner\nactivity-finder"}></textarea>
      </label>
    {:else}
      <h3>{steps[4]}</h3>
      <p class="hint">Create the cartridge with the settings below.</p>
      <dl class="review">
        <dt>Name</dt><dd>{name || "—"}</dd>
        <dt>Description</dt><dd>{description || "—"}</dd>
        <dt>Preferred tier</dt><dd>{preferredTier}</dd>
        <dt>Entry intents</dt><dd>{parseList(entryIntentsText).join(" · ") || "—"}</dd>
        <dt>Blackboard keys</dt><dd>{Object.keys(parseBlackboard(blackboardRaw)).join(", ") || "—"}</dd>
        <dt>Agents</dt><dd>{parseList(agentsText).join(" → ") || "—"}</dd>
      </dl>
      {#if error}<div class="err">{error}</div>{/if}
    {/if}
  </div>

  <footer>
    <button class="ghost" onclick={oncancel}>Cancel</button>
    <div class="spacer"></div>
    {#if step > 0}
      <button onclick={() => step -= 1}>Back</button>
    {/if}
    {#if step < steps.length - 1}
      <button class="primary" disabled={!canAdvance} onclick={() => step += 1}>Next</button>
    {:else}
      <button class="primary" disabled={busy || !name.trim()} onclick={onCreate}>
        {busy ? "Creating…" : "Create"}
      </button>
    {/if}
  </footer>
</section>

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
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    width: min(520px, 92vw);
    max-height: 88vh;
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    z-index: 11;
    display: grid;
    grid-template-rows: auto 1fr auto;
    overflow: hidden;
  }
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.7rem 1rem;
    border-bottom: 1px solid var(--border);
  }
  h2 {
    margin: 0;
    font-size: 1.1rem;
    font-weight: 500;
  }
  .dots {
    display: flex;
    gap: 0.3rem;
  }
  .dot {
    width: 6px;
    height: 6px;
    border-radius: 3px;
    background: var(--bg-3);
  }
  .dot.active {
    width: 18px;
    background: var(--accent);
  }
  .content {
    padding: 0.9rem 1rem;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }
  h3 {
    margin: 0;
    font-size: 0.85rem;
    color: var(--fg-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .hint {
    margin: 0;
    color: var(--fg-dim);
    font-size: 0.82rem;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
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
    padding: 0.5rem 0.65rem;
  }
  textarea {
    font-family: ui-monospace, Menlo, monospace;
    font-size: 0.82rem;
    resize: vertical;
  }
  code {
    background: var(--bg-3);
    padding: 0 0.3rem;
    border-radius: 4px;
    font-size: 0.78rem;
  }
  .review {
    display: grid;
    grid-template-columns: 130px 1fr;
    gap: 0.35rem 0.6rem;
    font-size: 0.82rem;
  }
  .review dt {
    color: var(--fg-dim);
  }
  .review dd {
    margin: 0;
  }
  .err {
    color: var(--err);
    font-size: 0.8rem;
  }
  footer {
    display: flex;
    gap: 0.35rem;
    padding: 0.7rem 1rem;
    border-top: 1px solid var(--border);
    padding-bottom: calc(0.7rem + env(safe-area-inset-bottom));
  }
  .spacer {
    flex: 1;
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
  footer button {
    font-size: 0.8rem;
  }
</style>
