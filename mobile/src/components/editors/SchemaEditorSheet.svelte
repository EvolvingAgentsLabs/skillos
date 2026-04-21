<script lang="ts">
  import { getFileText } from "$lib/storage/db";
  import { saveSchema } from "$lib/state/library.svelte";
  import { onDestroy, onMount } from "svelte";

  interface Props {
    cartridge: string;
    ref: string;
    oncancel: () => void;
    onsaved: () => void;
  }
  let { cartridge, ref, oncancel, onsaved }: Props = $props();

  let parent: HTMLDivElement | null = $state(null);
  let editor: { view: { state: { doc: { toString(): string } } } } | null = $state(null);
  let saving = $state(false);
  let error = $state("");

  onMount(async () => {
    const path = `cartridges/${cartridge}/schemas/${ref}`;
    const body = (await getFileText(path)) ?? "{}";
    if (!parent) return;
    const { createEditor } = await import("$lib/editors/codemirror_setup");
    const { lintJsonSchema } = await import("$lib/editors/lint");
    editor = createEditor(parent, {
      doc: body,
      lang: "json",
      lint: (doc) => lintJsonSchema(doc),
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
      const parsed = JSON.parse(text);
      await saveSchema(cartridge, ref, parsed);
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
      <div class="title">{cartridge} · {ref}</div>
      <div class="sub">JSON Schema — live ajv validation</div>
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
