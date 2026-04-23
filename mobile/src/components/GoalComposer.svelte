<script lang="ts">
  import { onMount } from "svelte";
  import { buildProvider } from "$lib/llm/build_provider";
  import type { CartridgeManifest } from "$lib/cartridge/types";
  import { loadSkillsProviderConfig } from "$lib/skills/skill_llm_proxy";
  import { library, loadLibrary } from "$lib/state/library.svelte";
  import {
    routeGoal,
    type RouterCatalog,
    type RouterDecision,
  } from "$lib/routing/goal_router";
  import ForgeRecipeSheet from "$components/ForgeRecipeSheet.svelte";

  interface Props {
    cartridges: CartridgeManifest[];
    onsubmit: (v: {
      name: string;
      cartridge: string | null;
      goal: string;
      router?: RouterDecision;
    }) => void;
    oncancel: () => void;
  }

  let { cartridges, onsubmit, oncancel }: Props = $props();
  let forgeOpen = $state(false);

  // Auto mode lets SkillOS pick the cartridge. Manual mode restores the
  // original select-a-cartridge-yourself flow. Auto is the default — one
  // part of the autonomy phase is removing the dev-centric cartridge picker
  // from the user's onboarding path.
  let autoMode = $state(true);
  let name = $state("");
  let cartridge = $state<string | null>(null);
  let goal = $state("");
  let routing = $state(false);
  let decision = $state<RouterDecision | null>(null);
  let routerError = $state<string>("");

  onMount(async () => {
    // Hydrate the skills list so the router has something to match against
    // beyond the cartridges passed in via props.
    await loadLibrary();
  });

  async function buildCatalog(): Promise<RouterCatalog> {
    // Compose from the props (source of truth for cartridges) + the library
    // rune (source of truth for skills per cartridge).
    const skills: RouterCatalog["skills"] = [];
    for (const c of library.cartridges) {
      for (const s of c.skills) {
        skills.push({ cartridge: c.name, skill: s });
      }
    }
    return { cartridges, skills };
  }

  async function runRouter() {
    routing = true;
    routerError = "";
    decision = null;
    try {
      const catalog = await buildCatalog();
      const cfg = await loadSkillsProviderConfig();
      const llm = cfg ? await safeBuild(cfg) : null;
      const d = await routeGoal(goal, catalog, llm);
      decision = d;
      if (d.mode === "cartridge" || d.mode === "ad-hoc") {
        cartridge = d.cartridge;
      }
    } catch (err) {
      routerError = err instanceof Error ? err.message : String(err);
    } finally {
      routing = false;
    }
  }

  async function safeBuild(cfg: Parameters<typeof buildProvider>[0]) {
    try {
      return await buildProvider(cfg);
    } catch {
      return null;
    }
  }

  async function submit(e: Event) {
    e.preventDefault();
    if (!name.trim() && !goal.trim()) return;
    if (autoMode && goal.trim() && !decision) {
      // First tap in auto mode: resolve the plan, then let the user confirm.
      await runRouter();
      return;
    }
    onsubmit({
      name,
      cartridge: autoMode ? cartridge : cartridge,
      goal,
      router: decision ?? undefined,
    });
  }

  function switchToManual() {
    autoMode = false;
    decision = null;
    routerError = "";
  }

  function decisionIcon(d: RouterDecision): string {
    if (d.mode === "cartridge") return "📦";
    if (d.mode === "ad-hoc") return "🧩";
    if (d.mode === "synthesize") return "✨";
    return "❓";
  }

  function decisionTitle(d: RouterDecision): string {
    if (d.mode === "cartridge") return `Run cartridge ${d.cartridge}`;
    if (d.mode === "ad-hoc") return `Use skill${d.skills.length === 1 ? "" : "s"}: ${d.skills.join(", ")}`;
    if (d.mode === "synthesize") return `Synthesize a new skill: ${d.suggestedName}`;
    return "No match";
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
    <span>What do you want to do?</span>
    <textarea
      rows="3"
      placeholder="Plan a vegetarian dinner for Wednesday…"
      bind:value={goal}
    ></textarea>
  </label>

  <div class="mode-row">
    {#if autoMode}
      <span class="mode-chip">
        <span class="mode-ico" aria-hidden="true">✨</span>
        <span>SkillOS will pick</span>
      </span>
      <button type="button" class="link" onclick={switchToManual}>Pick manually</button>
    {:else}
      <span class="mode-chip">Manual</span>
      <button type="button" class="link" onclick={() => (autoMode = true)}>
        Let SkillOS pick
      </button>
    {/if}
  </div>

  {#if !autoMode}
    <label class="field">
      <span>Cartridge</span>
      <select bind:value={cartridge}>
        <option value={null}>— none —</option>
        {#each cartridges as c (c.name)}
          <option value={c.name}>{c.name}</option>
        {/each}
      </select>
    </label>
  {/if}

  {#if autoMode && decision}
    <div class="plan plan-{decision.mode}">
      <div class="plan-head">
        <span class="plan-ico" aria-hidden="true">{decisionIcon(decision)}</span>
        <span class="plan-title">{decisionTitle(decision)}</span>
      </div>
      <div class="plan-reason">{decision.reason}</div>
      {#if decision.mode === "synthesize"}
        <div class="plan-hint">
          Nothing in your library matches yet. Teach SkillOS this Recipe once — after
          that, it runs local, free, and offline every time.
        </div>
        <button type="button" class="forge-cta" onclick={() => (forgeOpen = true)}>
          ✨ Teach me this Recipe
        </button>
      {/if}
    </div>
  {/if}

  {#if forgeOpen && decision && decision.mode === "synthesize"}
    <ForgeRecipeSheet
      decision={decision}
      goal={goal}
      projectName={name || decision.suggestedName}
      hostCartridge={cartridge}
      oncancel={() => (forgeOpen = false)}
      onacquired={(payload) => {
        forgeOpen = false;
        // A recipe was forged — continue to project creation so the user
        // sees the new skill pinned and can run it immediately.
        onsubmit({
          name: name || payload.skillName,
          cartridge: payload.cartridge,
          goal,
          router: {
            mode: "ad-hoc",
            cartridge: payload.cartridge,
            skills: [payload.skillName],
            reason: "just-forged recipe",
            confidence: 1,
          },
        });
      }}
    />
  {/if}

  {#if routerError}
    <div class="err">{routerError}</div>
  {/if}

  <div class="actions">
    <button type="button" class="ghost" onclick={oncancel}>Cancel</button>
    <button type="submit" class="primary" disabled={routing}>
      {#if routing}
        Planning…
      {:else if autoMode && goal.trim() && !decision}
        Plan with SkillOS
      {:else}
        Create
      {/if}
    </button>
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
    max-height: 85vh;
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
  .forge-cta {
    margin-top: 0.6rem;
    background: var(--accent);
    color: var(--bg);
    border: none;
    border-radius: 8px;
    padding: 0.55rem 0.9rem;
    font-weight: 600;
    font-size: 0.9rem;
    cursor: pointer;
    width: 100%;
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
  .mode-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    font-size: 0.82rem;
  }
  .mode-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.2rem 0.6rem;
    border-radius: 9999px;
    background: color-mix(in srgb, var(--accent) 12%, var(--bg-3));
    border: 1px solid color-mix(in srgb, var(--accent) 40%, var(--border));
    color: var(--fg);
  }
  .mode-ico {
    font-size: 0.9rem;
  }
  .link {
    background: transparent;
    border: none;
    color: var(--accent);
    cursor: pointer;
    font: inherit;
    padding: 0;
  }
  .link:hover {
    text-decoration: underline;
  }
  .plan {
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.55rem 0.7rem;
    background: var(--bg);
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }
  .plan-cartridge {
    border-left: 3px solid var(--ok);
  }
  .plan-ad-hoc {
    border-left: 3px solid var(--accent);
  }
  .plan-synthesize {
    border-left: 3px solid var(--warn);
  }
  .plan-none {
    border-left: 3px solid var(--err);
  }
  .plan-head {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.92rem;
    font-weight: 600;
  }
  .plan-ico {
    font-size: 1.05rem;
  }
  .plan-reason {
    color: var(--fg-dim);
    font-size: 0.8rem;
    line-height: 1.35;
  }
  .plan-hint {
    font-size: 0.78rem;
    color: var(--fg-dim);
    line-height: 1.4;
    background: var(--bg-3);
    border-radius: 6px;
    padding: 0.4rem 0.55rem;
    margin-top: 0.1rem;
  }
  .err {
    background: color-mix(in srgb, var(--err) 15%, var(--bg-3));
    border: 1px solid var(--err);
    color: var(--err);
    border-radius: 8px;
    padding: 0.4rem 0.6rem;
    font-size: 0.82rem;
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
  .primary:disabled {
    opacity: 0.55;
    cursor: progress;
  }
  .ghost {
    background: transparent;
  }
</style>
