<script lang="ts">
  import { onMount } from "svelte";
  import { getMeta, setMeta } from "$lib/storage/db";

  let open = $state(false);
  let step = $state(0);

  const pages = [
    {
      title: "Welcome to SkillOS Mobile",
      body:
        "A pure-JavaScript port of the SkillOS Pure-Markdown OS. Every agent, skill, and cartridge from the desktop repo runs on your phone — no backend required.",
    },
    {
      title: "Swipe between projects",
      body:
        "Each project fills the screen. Swipe horizontally to switch. Tap + in the header to create a new one and attach a cartridge.",
    },
    {
      title: "Three lifecycle lanes",
      body:
        "Every project has three lanes — Planned, In Execution, Done. Cards move automatically as the cartridge runner fires agents and validates their outputs.",
    },
    {
      title: "Run a cartridge",
      body:
        "Tap ⚙ to configure your provider (OpenRouter, Gemini, or Ollama over LAN in the native app), then ▶ run to let the agents and Gallery skills work. Watch the run log at the bottom.",
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
