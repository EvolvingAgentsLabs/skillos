<script lang="ts">
  /**
   * CompositionStepper — the clean, user-facing view of a recipe run.
   *
   * Collapses the raw RunEvent stream (tool-calls, blackboard puts, llm-turn
   * deltas, validator pings) into a handful of named steps the user can
   * actually follow. This is the surface that makes composition *visible*
   * without dumping internals. Raw events remain available in the same
   * drawer behind a "Details" toggle, kept for the Dev mental model.
   */
  import { runStream } from "$lib/state/run_events.svelte";
  import type { RunEvent } from "$lib/cartridge/runner";

  type StepStatus = "active" | "done" | "error";

  interface StepModel {
    agent: string;
    status: StepStatus;
    tier: "primary" | "fallback" | "unknown";
    lastMessage?: string;
  }

  // Deriving the step model from the event stream. A step appears on the
  // first `step-start` for an agent and is finalized by `step-end`.
  // `tool-call` updates the caption; `tier-switch` flips the tier badge
  // between local-first (primary) and cloud (fallback).
  const steps = $derived.by<StepModel[]>(() => {
    const byAgent = new Map<string, StepModel>();
    const order: string[] = [];
    for (const e of runStream.events as RunEvent[]) {
      if (e.type === "step-start") {
        if (!byAgent.has(e.agent)) {
          byAgent.set(e.agent, {
            agent: e.agent,
            status: "active",
            tier: "primary",
          });
          order.push(e.agent);
        } else {
          const s = byAgent.get(e.agent)!;
          s.status = "active";
        }
        for (const [k, s] of byAgent) {
          if (k !== e.agent && s.status === "active") s.status = "done";
        }
      } else if (e.type === "step-end") {
        const s = byAgent.get(e.step.agent);
        if (s) {
          s.status = e.step.validated ? "done" : "error";
          s.lastMessage = e.step.message;
        }
      } else if (e.type === "tool-call") {
        const s = byAgent.get(e.agent);
        if (s && s.status === "active") s.lastMessage = `→ ${e.tool}`;
      } else if (e.type === "tier-switch") {
        const s = byAgent.get(e.agent);
        if (s) s.tier = e.to;
      }
    }
    return order.map((a) => byAgent.get(a)!);
  });

  const finalOk = $derived.by<boolean | null>(() => {
    if (runStream.running) return null;
    const last = runStream.events[runStream.events.length - 1];
    if (last && last.type === "run-end") return last.result.ok;
    return null;
  });

  function humanAgent(name: string): string {
    // agents are often slug-kebab — render as "Title Case" without jargon
    return name
      .replace(/[-_]+/g, " ")
      .replace(/\bagent\b/gi, "")
      .trim()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
</script>

{#if steps.length > 0 || runStream.running}
  <ol class="stepper" aria-label="Recipe composition">
    {#each steps as s, i (i + s.agent)}
      <li class="step status-{s.status}">
        <span class="marker" aria-hidden="true">
          {#if s.status === "active"}
            <span class="pulse"></span>
          {:else if s.status === "done"}
            ✓
          {:else}
            ✗
          {/if}
        </span>
        <div class="body">
          <div class="row1">
            <span class="name">{humanAgent(s.agent)}</span>
            <span class="tier tier-{s.tier}" aria-label="Execution tier">
              {s.tier === "fallback" ? "☁" : "⚡"}
            </span>
          </div>
          {#if s.lastMessage}
            <div class="caption">{s.lastMessage}</div>
          {/if}
        </div>
      </li>
    {/each}
    {#if runStream.running && steps.length === 0}
      <li class="step status-active">
        <span class="marker"><span class="pulse"></span></span>
        <div class="body">
          <div class="row1"><span class="name">Planning…</span></div>
        </div>
      </li>
    {/if}
  </ol>
  {#if finalOk !== null}
    <div class="final" class:ok={finalOk} class:bad={!finalOk}>
      {finalOk ? "Recipe finished" : "Recipe finished with issues"}
    </div>
  {/if}
{/if}

<style>
  .stepper {
    list-style: none;
    padding: 0.2rem 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .step {
    display: grid;
    grid-template-columns: 1.5rem 1fr;
    align-items: start;
    gap: 0.55rem;
    position: relative;
  }
  .step:not(:last-child)::before {
    content: "";
    position: absolute;
    left: 0.69rem;
    top: 1.5rem;
    bottom: -0.5rem;
    width: 1px;
    background: var(--border);
  }
  .marker {
    width: 1.4rem;
    height: 1.4rem;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    line-height: 1;
    background: var(--bg-3);
    color: var(--fg-dim);
    border: 1px solid var(--border);
    flex: 0 0 auto;
  }
  .status-done .marker {
    background: color-mix(in srgb, var(--ok) 18%, var(--bg-3));
    color: var(--ok);
    border-color: color-mix(in srgb, var(--ok) 45%, var(--border));
  }
  .status-error .marker {
    background: color-mix(in srgb, var(--err) 18%, var(--bg-3));
    color: var(--err);
    border-color: color-mix(in srgb, var(--err) 45%, var(--border));
  }
  .status-active .marker {
    background: color-mix(in srgb, var(--accent) 18%, var(--bg-3));
    border-color: color-mix(in srgb, var(--accent) 55%, var(--border));
  }
  .pulse {
    width: 0.55rem;
    height: 0.55rem;
    border-radius: 50%;
    background: var(--accent);
    animation: stepPulse 1.2s ease-in-out infinite;
  }
  .body {
    min-width: 0;
  }
  .row1 {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  .name {
    font-size: 0.88rem;
    color: var(--fg);
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .status-active .name {
    color: var(--accent);
  }
  .tier {
    font-size: 0.72rem;
    line-height: 1;
    padding: 0.05rem 0.35rem;
    border-radius: 9999px;
    background: var(--bg-3);
    border: 1px solid var(--border);
    color: var(--fg-dim);
  }
  .tier-primary {
    color: var(--ok);
    border-color: color-mix(in srgb, var(--ok) 40%, var(--border));
  }
  .tier-fallback {
    color: var(--warn);
    border-color: color-mix(in srgb, var(--warn) 40%, var(--border));
  }
  .caption {
    font-size: 0.76rem;
    color: var(--fg-dim);
    margin-top: 0.12rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .final {
    margin-top: 0.55rem;
    padding: 0.3rem 0.55rem;
    border-radius: 6px;
    font-size: 0.78rem;
    border: 1px solid var(--border);
    background: var(--bg-3);
  }
  .final.ok {
    color: var(--ok);
    border-color: color-mix(in srgb, var(--ok) 45%, var(--border));
    background: color-mix(in srgb, var(--ok) 10%, var(--bg-3));
  }
  .final.bad {
    color: var(--warn);
    border-color: color-mix(in srgb, var(--warn) 45%, var(--border));
    background: color-mix(in srgb, var(--warn) 10%, var(--bg-3));
  }
  @keyframes stepPulse {
    0%, 100% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.4); opacity: 0.55; }
  }
</style>
