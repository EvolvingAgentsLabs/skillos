<script lang="ts">
  import type { SkillResultProvenance } from "$lib/skills/skill_result";

  interface Props {
    provenance: SkillResultProvenance;
  }

  let { provenance }: Props = $props();

  // Classify the run. A skill always executes JS locally in the iframe sandbox;
  // what varies is whether it made LLM calls during that run, and where those
  // calls went. This keeps the badge honest: it reports observed behavior,
  // not stated intent.
  const kind = $derived.by<"local-js" | "cloud-llm" | "on-device-llm">(() => {
    if (provenance.llmCalls <= 0) return "local-js";
    return provenance.llmLocation === "on-device" ? "on-device-llm" : "cloud-llm";
  });

  const icon = $derived(
    kind === "local-js" ? "⚡" : kind === "on-device-llm" ? "🦙" : "☁",
  );

  const label = $derived.by(() => {
    if (kind === "local-js") return "Local · deterministic JS";
    if (kind === "on-device-llm") {
      return provenance.llmProvider
        ? `On-device · ${provenance.llmProvider}`
        : "On-device LLM";
    }
    return provenance.llmProvider ? `Cloud · ${provenance.llmProvider}` : "Cloud LLM";
  });

  const durationText = $derived.by(() => {
    const ms = provenance.durationMs;
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(ms < 10_000 ? 2 : 1)}s`;
  });

  const llmCallsText = $derived.by(() =>
    provenance.llmCalls > 0
      ? `${provenance.llmCalls} LLM call${provenance.llmCalls === 1 ? "" : "s"}`
      : null,
  );
</script>

<span class="prov kind-{kind}" title={label} aria-label="Provenance: {label}">
  <span class="ico" aria-hidden="true">{icon}</span>
  <span class="lbl">{label}</span>
  <span class="dot" aria-hidden="true">·</span>
  <span class="metric">{durationText}</span>
  {#if llmCallsText}
    <span class="dot" aria-hidden="true">·</span>
    <span class="metric">{llmCallsText}</span>
  {/if}
</span>

<style>
  .prov {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.15rem 0.55rem;
    border-radius: 9999px;
    border: 1px solid var(--border);
    background: var(--bg-3);
    font-size: 0.72rem;
    color: var(--fg-dim);
    white-space: nowrap;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .ico {
    font-size: 0.85rem;
    line-height: 1;
  }
  .lbl {
    color: var(--fg);
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 18ch;
  }
  .dot {
    color: var(--fg-dim);
    opacity: 0.6;
  }
  .metric {
    font-variant-numeric: tabular-nums;
  }
  /* Local → cool, confidence-inspiring. */
  .kind-local-js {
    border-color: color-mix(in srgb, var(--ok) 55%, var(--border));
    background: color-mix(in srgb, var(--ok) 10%, var(--bg-3));
  }
  .kind-local-js .ico {
    color: var(--ok);
  }
  /* Cloud LLM → warm, "money changed hands" visual. */
  .kind-cloud-llm {
    border-color: color-mix(in srgb, var(--warn) 55%, var(--border));
    background: color-mix(in srgb, var(--warn) 10%, var(--bg-3));
  }
  /* On-device LLM → accent, "your phone is doing real work". */
  .kind-on-device-llm {
    border-color: color-mix(in srgb, var(--accent) 55%, var(--border));
    background: color-mix(in srgb, var(--accent) 12%, var(--bg-3));
  }
</style>
