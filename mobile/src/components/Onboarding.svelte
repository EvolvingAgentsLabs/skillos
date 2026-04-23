<script lang="ts">
  import { onMount } from "svelte";
  import { getMeta, setMeta } from "$lib/storage/db";

  let open = $state(false);
  let step = $state(0);

  const pages = [
    {
      title: "Welcome to SkillOS",
      body:
        "Turn any one-off ChatGPT answer into a permanent, offline, free button on your phone. Each button is a Recipe — a little team of agents and tools that runs the same job, your way, every time.",
    },
    {
      title: "A Recipe is a composition",
      body:
        "Under each Recipe sits a plan, a few agents, the skills they use, and the facts it's learned about you. You don't pick skills one by one — you run the Recipe and it orchestrates them.",
    },
    {
      title: "Run, watch, keep",
      body:
        "Swipe between Recipes. Tap one and fill in the typed fields. Watch the composition step through — Extracting → Validating → Done. Outputs render as rich cards you can reuse.",
    },
    {
      title: "Write once, run forever",
      body:
        "The first run may ask the cloud for help synthesizing the Recipe. After that, tap ⚙ to pick a provider (OpenRouter, Gemini, or on-device). Subsequent runs stay local — free, private, offline.",
    },
  ];

  onMount(async () => {
    const seen = await getMeta<boolean>("onboarding_seen");
    if (!seen) open = true;
  });

  async function dismiss() {
    await setMeta("onboarding_seen", true);
    open = false;
  }

  function next() {
    if (step < pages.length - 1) step += 1;
    else void dismiss();
  }
</script>

{#if open}
  <button
    type="button"
    class="backdrop"
    onclick={dismiss}
    aria-label="Skip onboarding"
  ></button>
  <section class="card">
    <div class="dots">
      {#each pages as _, i (i)}
        <span class="dot" class:active={i === step}></span>
      {/each}
    </div>
    <h2>{pages[step].title}</h2>
    <p>{pages[step].body}</p>
    <div class="actions">
      <button class="ghost" onclick={dismiss}>Skip</button>
      <button class="primary" onclick={next}>
        {step < pages.length - 1 ? "Next" : "Let's go"}
      </button>
    </div>
  </section>
{/if}

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.65);
    z-index: 20;
    border: none;
    padding: 0;
    cursor: pointer;
  }
  .card {
    position: fixed;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    width: min(90vw, 420px);
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 1.3rem 1.4rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.8rem;
    z-index: 21;
  }
  .dots {
    display: flex;
    justify-content: center;
    gap: 0.35rem;
  }
  .dot {
    width: 6px;
    height: 6px;
    border-radius: 3px;
    background: var(--bg-3);
    transition: background 0.15s, width 0.15s;
  }
  .dot.active {
    background: var(--accent);
    width: 18px;
  }
  h2 {
    margin: 0;
    font-size: 1.15rem;
    font-weight: 600;
  }
  p {
    margin: 0;
    color: var(--fg-dim);
    line-height: 1.5;
  }
  .actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
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
