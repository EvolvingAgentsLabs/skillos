<script lang="ts">
  /**
   * ForgeRecipeSheet — the capability-gap ceremony.
   *
   * When `goal_router` returns `mode: "synthesize"`, the existing flow
   * quietly told the user to "run an empty project then promote." That
   * hides the moment SkillOS's positioning is built around — the first
   * time the Cloud synthesizes a new Recipe so every subsequent run is
   * local and free. This sheet turns that moment into a deliberate UX:
   *
   *   1. Capability-gap acknowledgment ("I don't know this yet")
   *   2. Proposed plan preview (human-readable steps)
   *   3. Cost estimate + Teach-me button
   *   4. Synthesis progress
   *   5. "New Recipe Acquired" reveal on success
   *
   * For v1 we synthesize a single Gallery skill via the existing
   * skill_synth pipeline and treat it as the new Recipe. Full multi-agent
   * composition synthesis is the follow-up once we have a ProposedPlan
   * data model the runner can execute.
   */
  import type { LLMProvider } from "$lib/llm/provider";
  import type { RouterSynthesizeDecision } from "$lib/routing/goal_router";
  import { synthesizeSkill, type SynthResult } from "$lib/skills/skill_synth";
  import { saveSkill } from "$lib/state/library.svelte";
  import { loadSkillsProviderConfig } from "$lib/skills/skill_llm_proxy";
  import { buildProvider } from "$lib/llm/build_provider";
  import { library, loadLibrary } from "$lib/state/library.svelte";

  interface Props {
    decision: RouterSynthesizeDecision;
    goal: string;
    projectName: string;
    /** The cartridge we'll host the new skill inside. If null, we pick the first skills-source cartridge. */
    hostCartridge: string | null;
    oncancel: () => void;
    onacquired: (payload: { cartridge: string; skillName: string }) => void;
  }

  let { decision, goal, projectName, hostCartridge, oncancel, onacquired }: Props = $props();

  type Phase = "intro" | "synthesizing" | "acquired" | "error";

  let phase = $state<Phase>("intro");
  let errorMessage = $state("");
  let synthResult = $state<SynthResult | null>(null);
  let acquiredCartridge = $state("");

  // Heuristic plan preview. Without an authored plan-synth pipeline yet,
  // derive 3 plausible steps from the goal + the router's suggestedName.
  // This is transparently a preview — on acquire we run skill synthesis
  // for real. When a ProposedPlan data model lands, swap this in.
  const planSteps = $derived.by(() => {
    const g = goal.trim();
    const suggested = decision.suggestedName || "user-recipe";
    const steps = [
      {
        label: "Understand the request",
        detail: `Parse "${truncate(g, 60)}" into typed inputs`,
      },
      {
        label: `Build ${suggested}`,
        detail: decision.nearestSkill
          ? `Start from ${decision.nearestSkill} as a seed`
          : "Generate deterministic JS matching the output shape",
      },
      {
        label: "Save offline",
        detail: "Pin as a permanent button — runs local, $0 thereafter",
      },
    ];
    return steps;
  });

  // Rough cost estimate: one LLM call for synthesis at ~2k tokens
  // (prompt + response) on a cheap cloud model. Display as a range so
  // we don't claim precision we don't have.
  const costEstimate = "~$0.01–0.03";

  function truncate(s: string, n: number): string {
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
  }

  async function acquire() {
    errorMessage = "";
    const cfg = await loadSkillsProviderConfig();
    if (!cfg) {
      errorMessage =
        "No cloud provider configured. Open ⚙ → Skills Provider to add one, then try again.";
      phase = "error";
      return;
    }

    // Pick a host cartridge: preferred hostCartridge if it has a skills
    // source, else first library cartridge that does.
    await loadLibrary();
    const hostable = library.cartridges.filter((c) => c.manifest.skills_source);
    let host = hostCartridge
      ? hostable.find((c) => c.name === hostCartridge) ?? null
      : null;
    if (!host && hostable.length > 0) host = hostable[0];
    if (!host) {
      errorMessage =
        "No cartridge can host a new skill yet. Create or install one with a skills_source first.";
      phase = "error";
      return;
    }

    phase = "synthesizing";
    let llm: LLMProvider;
    try {
      llm = await buildProvider(cfg);
    } catch (e) {
      errorMessage = `Provider build failed: ${e instanceof Error ? e.message : String(e)}`;
      phase = "error";
      return;
    }

    try {
      const result = await synthesizeSkill(llm, {
        goal,
        cardTitle: decision.suggestedName,
        cardSubtitle: decision.description,
        projectName,
        projectCartridge: host.name,
      });
      synthResult = result;
      if (!result.ok || !result.skillName) {
        errorMessage =
          `Synthesis response could not be parsed. ${result.errors.join("; ") || "Unknown error."}`;
        phase = "error";
        return;
      }
      await saveSkill(host.name, result.skillName, {
        skillMd: result.skillMd,
        indexJs: result.indexJs,
      });
      acquiredCartridge = host.name;
      phase = "acquired";
    } catch (e) {
      errorMessage = e instanceof Error ? e.message : String(e);
      phase = "error";
    }
  }

  function finish() {
    if (phase === "acquired" && synthResult) {
      onacquired({ cartridge: acquiredCartridge, skillName: synthResult.skillName });
    } else {
      oncancel();
    }
  }
</script>

<button
  type="button"
  class="backdrop"
  onclick={phase === "synthesizing" ? undefined : oncancel}
  aria-label="Dismiss"
></button>
<div class="sheet" role="dialog" aria-label="Acquire new Recipe" tabindex="-1">
  {#if phase === "intro"}
    <header class="head">
      <div class="ico">✨</div>
      <div>
        <div class="title">I don't know how to do this yet</div>
        <div class="subtitle">
          Nothing in your library matches this goal. I can learn it once — then
          every future run is local, free, and offline.
        </div>
      </div>
    </header>

    <div class="goal-block">
      <div class="lbl">Goal</div>
      <div class="goal">{goal}</div>
    </div>

    <div class="plan">
      <div class="lbl">Proposed plan</div>
      <ol class="steps">
        {#each planSteps as s, i (i)}
          <li>
            <span class="num">{i + 1}</span>
            <div class="body">
              <div class="step-title">{s.label}</div>
              <div class="step-detail">{s.detail}</div>
            </div>
          </li>
        {/each}
      </ol>
    </div>

    <div class="cost-row">
      <span class="cost-lbl">One-time cloud cost</span>
      <span class="cost-val">{costEstimate}</span>
    </div>

    <div class="actions">
      <button class="ghost" onclick={oncancel}>Not now</button>
      <button class="primary" onclick={acquire}>✨ Teach me</button>
    </div>
  {:else if phase === "synthesizing"}
    <div class="progress">
      <div class="spinner" aria-hidden="true"></div>
      <div class="progress-title">Synthesizing recipe…</div>
      <div class="progress-detail">
        Writing the JS, schema, and agent card. This runs once — every future
        call stays on your phone.
      </div>
    </div>
  {:else if phase === "acquired"}
    <div class="acquired" role="status">
      <div class="ribbon">⚡ New Recipe Acquired</div>
      <div class="new-name">{synthResult?.skillName ?? "user-recipe"}</div>
      <div class="acquired-sub">
        Pinned to <code>{acquiredCartridge}</code>. Tap it anytime — it runs
        locally, no internet needed.
      </div>
      <button class="primary big" onclick={finish}>Use it now</button>
    </div>
  {:else}
    <div class="err-block">
      <div class="err-title">Couldn't teach the recipe</div>
      <div class="err-msg">{errorMessage}</div>
      <div class="actions">
        <button class="ghost" onclick={oncancel}>Close</button>
        <button class="primary" onclick={() => (phase = "intro")}>Try again</button>
      </div>
    </div>
  {/if}
</div>

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.6);
    border: none;
    padding: 0;
    cursor: pointer;
    z-index: 20;
  }
  .sheet {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--bg-2);
    border-top: 1px solid var(--border);
    border-radius: 14px 14px 0 0;
    padding: 1.1rem 1.1rem calc(1.3rem + env(safe-area-inset-bottom));
    max-height: 90vh;
    overflow-y: auto;
    z-index: 21;
    box-shadow: 0 -12px 32px rgba(0, 0, 0, 0.4);
    animation: sheetIn 0.18s ease-out;
  }
  @keyframes sheetIn {
    from { transform: translateY(18px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }

  /* Intro */
  .head {
    display: flex;
    gap: 0.7rem;
    margin-bottom: 0.9rem;
  }
  .ico {
    font-size: 1.7rem;
    line-height: 1;
    flex: 0 0 auto;
    padding-top: 0.15rem;
  }
  .title {
    font-size: 1.05rem;
    font-weight: 600;
  }
  .subtitle {
    color: var(--fg-dim);
    font-size: 0.85rem;
    line-height: 1.4;
    margin-top: 0.2rem;
  }
  .lbl {
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.66rem;
    color: var(--fg-dim);
    margin-bottom: 0.25rem;
    font-weight: 600;
  }
  .goal-block {
    background: var(--bg-3);
    border-radius: 8px;
    padding: 0.5rem 0.65rem;
    margin-bottom: 0.8rem;
  }
  .goal {
    font-size: 0.88rem;
    line-height: 1.4;
    word-break: break-word;
  }
  .plan {
    margin-bottom: 0.9rem;
  }
  .steps {
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
  }
  .steps li {
    display: grid;
    grid-template-columns: 1.6rem 1fr;
    gap: 0.55rem;
    align-items: start;
  }
  .num {
    width: 1.4rem;
    height: 1.4rem;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: color-mix(in srgb, var(--accent) 18%, var(--bg-3));
    color: var(--accent);
    border: 1px solid color-mix(in srgb, var(--accent) 45%, var(--border));
    font-size: 0.78rem;
    font-weight: 600;
    flex: 0 0 auto;
  }
  .step-title {
    font-size: 0.88rem;
    color: var(--fg);
    font-weight: 500;
  }
  .step-detail {
    font-size: 0.78rem;
    color: var(--fg-dim);
    margin-top: 0.1rem;
  }
  .cost-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.5rem 0.7rem;
    margin-bottom: 0.9rem;
  }
  .cost-lbl {
    font-size: 0.8rem;
    color: var(--fg-dim);
  }
  .cost-val {
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--warn);
    font-variant-numeric: tabular-nums;
  }
  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.45rem;
  }
  .actions button,
  .primary.big {
    padding: 0.6rem 1rem;
    border-radius: 8px;
    border: 1px solid var(--border);
    background: var(--bg-3);
    color: var(--fg);
    font-size: 0.9rem;
    cursor: pointer;
  }
  .actions .primary,
  .primary.big {
    background: var(--accent);
    border-color: var(--accent);
    color: var(--bg);
    font-weight: 600;
  }
  .primary.big {
    width: 100%;
    padding: 0.75rem 1rem;
    font-size: 0.95rem;
    margin-top: 1rem;
  }

  /* Synthesizing */
  .progress {
    text-align: center;
    padding: 1.5rem 1rem;
  }
  .spinner {
    width: 2.4rem;
    height: 2.4rem;
    border: 3px solid var(--bg-3);
    border-top-color: var(--accent);
    border-radius: 50%;
    margin: 0 auto 0.9rem;
    animation: spin 0.9s linear infinite;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  .progress-title {
    font-size: 1rem;
    font-weight: 600;
  }
  .progress-detail {
    color: var(--fg-dim);
    font-size: 0.85rem;
    margin-top: 0.4rem;
    line-height: 1.4;
  }

  /* Acquired */
  .acquired {
    text-align: center;
    padding: 0.5rem 0.3rem 0.4rem;
  }
  .ribbon {
    display: inline-block;
    background: color-mix(in srgb, var(--ok) 20%, var(--bg-3));
    color: var(--ok);
    border: 1px solid color-mix(in srgb, var(--ok) 55%, var(--border));
    padding: 0.25rem 0.8rem;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    animation: ribbonIn 0.3s ease-out;
  }
  @keyframes ribbonIn {
    from { transform: scale(0.8); opacity: 0; }
    to { transform: scale(1); opacity: 1; }
  }
  .new-name {
    font-size: 1.4rem;
    font-weight: 600;
    margin: 0.6rem 0 0.25rem;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    color: var(--accent);
    animation: nameIn 0.4s ease-out 0.15s backwards;
  }
  @keyframes nameIn {
    from { transform: translateY(8px); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
  }
  .acquired-sub {
    color: var(--fg-dim);
    font-size: 0.85rem;
    line-height: 1.4;
    max-width: 32ch;
    margin: 0 auto;
  }
  .acquired-sub code {
    background: var(--bg-3);
    padding: 0 0.3rem;
    border-radius: 4px;
    font-size: 0.78rem;
    color: var(--fg);
  }

  /* Error */
  .err-block {
    padding: 0.4rem 0.2rem;
  }
  .err-title {
    font-weight: 600;
    color: var(--err);
    margin-bottom: 0.4rem;
  }
  .err-msg {
    color: var(--fg);
    font-size: 0.88rem;
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.5rem 0.65rem;
    margin-bottom: 0.9rem;
    white-space: pre-wrap;
    word-break: break-word;
  }
</style>
