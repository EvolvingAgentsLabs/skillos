<script lang="ts">
  import type { AgentSpec } from "$lib/cartridge/types";
  import { saveAgent } from "$lib/state/library.svelte";
  import { onDestroy, onMount } from "svelte";
  import yaml from "js-yaml";

  interface Props {
    cartridge: string;
    agent: AgentSpec;
    oncancel: () => void;
    onsaved: () => void;
  }
  let { cartridge, agent, oncancel, onsaved }: Props = $props();

  // Snapshot the agent at mount so the editor opens with the initial state
  // even after the parent remounts us. Svelte's runes correctly warn us
  // that accessing agent.* at module scope captures only the first value —
  // we want that here, so route via a local.
  const agentSnapshot = agent;
  const initialFrontmatter = {
    name: agentSnapshot.name,
    tier: agentSnapshot.tier,
    needs: agentSnapshot.needs,
    produces: agentSnapshot.produces,
    produces_schema: agentSnapshot.produces_schema,
    produces_description: agentSnapshot.produces_description,
    tools: agentSnapshot.tools,
    max_turns: agentSnapshot.max_turns,
    description: agentSnapshot.description,
  };

  const initialDoc = `---\n${yaml.dump(initialFrontmatter, { sortKeys: false, noRefs: true }).trimEnd()}\n---\n\n${agentSnapshot.body}`;

  let parent: HTMLDivElement | null = $state(null);
  let editor: { view: { state: { doc: { toString(): string } } } } | null = $state(null);
  let saving = $state(false);
  let error = $state("");

  onMount(async () => {
    if (!parent) return;
    const { createEditor } = await import("$lib/editors/codemirror_setup");
    const { lintMarkdownFrontmatter } = await import("$lib/editors/lint");
    editor = createEditor(parent, {
      doc: initialDoc,
      lang: "markdown",
      lint: (doc) => lintMarkdownFrontmatter(doc, ["name"]),
    });
  });

  onDestroy(() => {
    (editor?.view as unknown as { destroy?: () => void })?.destroy?.();
  });

  async function onSave() {
    if (!editor) return;
    saving = true;
    error = "";
    try {
      const text = editor.view.state.doc.toString();
      const fmMatch = /^---\n([\s\S]*?)\n---\n?([\s\S]*)$/.exec(text);
      if (!fmMatch) throw new Error("file must begin with a `---` frontmatter block");
      const fm = yaml.load(fmMatch[1]);
      if (!fm || typeof fm !== "object") throw new Error("frontmatter is empty");
      const body = fmMatch[2];
      await saveAgent(cartridge, agent.name, fm as Record<string, unknown>, body);
      onsaved();
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      saving = false;
    }
  }
</script>

<button type="button" class="backdrop" onclick={oncancel} aria-label="Close"></button>
<section class="sheet">
  <header>
    <div>
      <div class="title">{cartridge} · {agent.name}</div>
      <div class="sub">edit agent frontmatter + body</div>
    </div>
    <div class="actions">
      <button onclick={oncancel}>Cancel</button>
      <button class="primary" disabled={saving} onclick={onSave}>
        {saving ? "Saving…" : "Save"}
      </button>
    </div>
  </header>
  {#if error}<div class="err">{error}</div>{/if}
  <div class="editor" bind:this={parent}></div>
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
    inset: 2% 2% 2% 2%;
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 10px;
    z-index: 11;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 0.65rem 0.8rem;
    border-bottom: 1px solid var(--border);
    background: var(--bg-2);
  }
  .title {
    font-weight: 600;
  }
  .sub {
    color: var(--fg-dim);
    font-size: 0.75rem;
  }
  .actions {
    display: flex;
    gap: 0.35rem;
  }
  .actions button {
    font-size: 0.8rem;
    padding: 0.3rem 0.7rem;
  }
  .primary {
    background: var(--accent);
    color: var(--bg);
    border: none;
    font-weight: 600;
  }
  .err {
    color: var(--err);
    padding: 0.4rem 0.8rem;
    background: rgba(255, 138, 138, 0.08);
    border-bottom: 1px solid var(--border);
    font-size: 0.78rem;
  }
  .editor {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
  .editor :global(.cm-editor) {
    height: 100%;
  }
</style>
