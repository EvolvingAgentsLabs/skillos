<script lang="ts">
  import { runStream } from "$lib/state/run_events.svelte";
  import CompositionStepper from "$components/CompositionStepper.svelte";

  // The drawer has two modes:
  //   - default: clean composition stepper (see CompositionStepper.svelte)
  //   - details: raw RunEvent log, for Dev inspection / debugging
  // Stepper is the primary surface because it matches the Recipe mental
  // model ("watch a small team step through the job"); the raw log stays
  // reachable but is no longer the first thing users see.
  let showDetails = $state(false);
  const recent = $derived(runStream.events.slice(-40));
</script>

{#if runStream.running || runStream.events.length > 0}
  <aside class="drawer" class:active={runStream.running}>
    <header>
      <span class="dot" class:running={runStream.running}></span>
      <span class="label">
        {runStream.running ? "Running recipe…" : "Last run"}
      </span>
      <button
        type="button"
        class="toggle"
        onclick={() => (showDetails = !showDetails)}
        aria-expanded={showDetails}
      >
        {showDetails ? "Hide details" : "Details"}
      </button>
    </header>

    {#if !showDetails}
      <CompositionStepper />
    {:else}
      <div class="log">
        {#each recent as e, i (i + e.type)}
          <div class="row row-{e.type}">
            {#if e.type === "run-start"}
              ▶ {e.cartridge} / {e.flow}
            {:else if e.type === "step-start"}
              ‣ step: {e.agent}
            {:else if e.type === "tool-call"}
              ⚒ {e.tool}({trunc(JSON.stringify(e.args), 60)})
            {:else if e.type === "tool-result"}
              ↩ {trunc(String(e.result), 80)}
            {:else if e.type === "blackboard-put"}
              {e.ok ? "✅" : "⚠️"} {e.key}
            {:else if e.type === "step-end"}
              {e.step.validated ? "✓" : "✗"} {e.step.agent} — {e.step.message}
            {:else if e.type === "validator"}
              {e.ok ? "✓" : "✗"} {e.message}
            {:else if e.type === "tier-switch"}
              ↪ {e.agent}: {e.from} → {e.to} ({e.reason})
            {:else if e.type === "run-end"}
              ■ {e.result.ok ? "ok" : "partial"}
            {/if}
          </div>
        {/each}
        {#if runStream.running && runStream.currentAssistant}
          <div class="row row-llm-turn">
            <span class="llm">{trunc(runStream.currentAssistant, 200)}</span>
          </div>
        {/if}
      </div>
    {/if}
  </aside>
{/if}

<script module lang="ts">
  export function trunc(s: string, n: number): string {
    return s.length > n ? `${s.slice(0, n)}…` : s;
  }
</script>

<style>
  .drawer {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--bg-2);
    border-top: 1px solid var(--border);
    padding: 0.5rem 0.8rem calc(0.5rem + env(safe-area-inset-bottom));
    max-height: 38vh;
    overflow-y: auto;
    font-size: 0.8rem;
    z-index: 5;
    box-shadow: 0 -8px 20px rgba(0, 0, 0, 0.35);
  }
  header {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.15rem 0 0.45rem;
    color: var(--fg-dim);
    position: sticky;
    top: 0;
    background: var(--bg-2);
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 4px;
    background: var(--fg-dim);
  }
  .dot.running {
    background: var(--ok);
    animation: pulse 1.2s ease-in-out infinite;
  }
  .label {
    flex: 1;
  }
  .toggle {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--fg-dim);
    font-size: 0.72rem;
    padding: 0.15rem 0.5rem;
    border-radius: 9999px;
    cursor: pointer;
  }
  .toggle:hover {
    color: var(--fg);
    border-color: var(--accent);
  }
  .log {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    font-family: ui-monospace, Menlo, Consolas, monospace;
  }
  .row {
    white-space: pre-wrap;
    word-break: break-word;
  }
  .row-blackboard-put,
  .row-run-end {
    color: var(--ok);
  }
  .row-step-start,
  .row-tool-call {
    color: var(--accent);
  }
  .row-validator {
    color: var(--warn);
  }
  .row-tier-switch {
    color: var(--accent-2);
    font-weight: 500;
  }
  .llm {
    color: var(--fg-dim);
    font-style: italic;
  }
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.4;
    }
  }
</style>
