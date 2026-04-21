<script lang="ts">
  import { getFileText } from "$lib/storage/db";
  import type { SkillDefinition } from "$lib/skills/skill_loader";
  import { skillHostBridge } from "$lib/skills/skill_host_bridge";
  import { saveSkill } from "$lib/state/library.svelte";
  import { onDestroy, onMount } from "svelte";

  interface Props {
    cartridge: string;
    skill: SkillDefinition;
    oncancel: () => void;
    onsaved: () => void;
  }
  let { cartridge, skill, oncancel, onsaved }: Props = $props();

  let tab = $state<"skill_md" | "index_js">("skill_md");
  let mdParent: HTMLDivElement | null = $state(null);
  let jsParent: HTMLDivElement | null = $state(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let mdEditor: any = null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let jsEditor: any = null;

  let mdDoc = $state("");
  let jsDoc = $state("");
  let saving = $state(false);
  let error = $state("");

  // Test panel
  let sampleData = $state("{}");
  let secret = $state("");
  let useRealLLM = $state(false);
  let testOut = $state("");
  let testing = $state(false);

  onMount(async () => {
    mdDoc = (await getFileText(`${skill.skill_dir}/SKILL.md`)) ?? "";
    jsDoc = (await getFileText(`${skill.skill_dir}/scripts/index.js`)) ?? "";
    const { createEditor } = await import("$lib/editors/codemirror_setup");
    const { lintMarkdownFrontmatter } = await import("$lib/editors/lint");
    if (mdParent) {
      mdEditor = createEditor(mdParent, {
        doc: mdDoc,
        lang: "markdown",
        lint: (d) => lintMarkdownFrontmatter(d, ["name", "description"]),
        onChange: (d) => (mdDoc = d),
      });
    }
    if (jsParent) {
      jsEditor = createEditor(jsParent, {
        doc: jsDoc,
        lang: "javascript",
        onChange: (d) => (jsDoc = d),
      });
    }
  });

  onDestroy(() => {
    mdEditor?.view?.destroy?.();
    jsEditor?.view?.destroy?.();
  });

  async function onSave() {
    saving = true;
    error = "";
    try {
      await saveSkill(cartridge, skill.name, {
        skillMd: mdDoc,
        indexJs: jsDoc,
      });
      onsaved();
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
    } finally {
      saving = false;
    }
  }

  async function onTest() {
    testing = true;
    testOut = "";
    // Sandbox LLM unless user explicitly opts in to real provider.
    if (!useRealLLM) {
      skillHostBridge.setLLMProxy({
        chat: async (prompt) => `[sandbox] echo: ${String(prompt).slice(0, 60)}`,
        chatJSON: async () => ({ sandbox: true }),
      });
    }
    try {
      // Persist the current buffer first so the iframe loads the edited source.
      await saveSkill(cartridge, skill.name, { skillMd: mdDoc, indexJs: jsDoc });
      // Cap max_tokens for test runs to avoid accidental cost blowups.
      const data = sampleData.trim() || "{}";
      const res = await skillHostBridge.runSkill(skill, { data, secret });
      testOut = JSON.stringify(
        {
          ok: res.ok,
          result: res.result,
          error: res.error,
          webview: res.webview,
          image: res.image ? { mimeType: res.image.mimeType, base64: "<omitted>" } : undefined,
        },
        null,
        2,
      );
    } catch (err) {
      testOut = String(err);
    } finally {
      testing = false;
    }
  }
</script>

<button type="button" class="backdrop" onclick={oncancel} aria-label="Close"></button>
<section class="sheet">
  <header>
    <div>
      <div class="title">{cartridge} · {skill.name}</div>
      <div class="sub">
        Gallery skill editor
        {#if skill.require_secret}<span class="warn-chip">requires secret</span>{/if}
      </div>
    </div>
    <div class="actions">
      <button onclick={oncancel}>Cancel</button>
      <button class="primary" disabled={saving} onclick={onSave}>
        {saving ? "Saving…" : "Save"}
      </button>
    </div>
  </header>
  {#if error}<div class="err">{error}</div>{/if}

  <nav class="tabs">
    <button class:active={tab === "skill_md"} onclick={() => (tab = "skill_md")}>SKILL.md</button>
    <button class:active={tab === "index_js"} onclick={() => (tab = "index_js")}>index.js</button>
  </nav>

  <div class="panes">
    <div class="editor" style:display={tab === "skill_md" ? "block" : "none"} bind:this={mdParent}></div>
    <div class="editor" style:display={tab === "index_js" ? "block" : "none"} bind:this={jsParent}></div>
  </div>

  <aside class="test">
    <div class="test-head">Test panel</div>
    <label class="field">
      <span>sample data (JSON)</span>
      <textarea rows="3" bind:value={sampleData}></textarea>
    </label>
    {#if skill.require_secret}
      <label class="field">
        <span>secret</span>
        <input type="password" bind:value={secret} autocomplete="off" />
      </label>
    {/if}
    <label class="inline">
      <input type="checkbox" bind:checked={useRealLLM} />
      <span>Use real provider (otherwise: sandboxed echo)</span>
    </label>
    <div class="test-actions">
      <button class="primary" disabled={testing} onclick={onTest}>
        {testing ? "Running…" : "Run"}
      </button>
    </div>
    {#if testOut}<pre class="out">{testOut}</pre>{/if}
  </aside>
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
    display: grid;
    grid-template-rows: auto auto auto 1fr auto;
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
    display: flex;
    gap: 0.35rem;
    align-items: center;
  }
  .warn-chip {
    background: rgba(255, 209, 102, 0.15);
    color: var(--warn);
    border-radius: 9999px;
    padding: 0.05rem 0.5rem;
    font-size: 0.68rem;
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
  .tabs {
    display: flex;
    gap: 0;
    border-bottom: 1px solid var(--border);
  }
  .tabs button {
    flex: 1;
    background: transparent;
    color: var(--fg-dim);
    border: none;
    padding: 0.4rem 0.7rem;
    cursor: pointer;
    font-size: 0.78rem;
  }
  .tabs button.active {
    color: var(--accent);
    border-bottom: 2px solid var(--accent);
  }
  .panes {
    overflow: hidden;
    min-height: 0;
  }
  .editor {
    height: 100%;
    overflow: hidden;
  }
  .editor :global(.cm-editor) {
    height: 100%;
  }
  .test {
    border-top: 1px solid var(--border);
    padding: 0.5rem 0.8rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    max-height: 34%;
    overflow-y: auto;
  }
  .test-head {
    text-transform: uppercase;
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    color: var(--fg-dim);
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    font-size: 0.78rem;
    color: var(--fg-dim);
  }
  .field input,
  .field textarea {
    font: inherit;
    color: var(--fg);
    background: var(--bg-3);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.35rem 0.5rem;
    font-family: ui-monospace, Menlo, monospace;
    font-size: 0.78rem;
  }
  .inline {
    display: flex;
    gap: 0.4rem;
    align-items: center;
    font-size: 0.78rem;
    color: var(--fg-dim);
  }
  .test-actions {
    display: flex;
    justify-content: flex-end;
  }
  .out {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.45rem;
    font-size: 0.72rem;
    white-space: pre-wrap;
    margin: 0;
    max-height: 200px;
    overflow: auto;
  }
</style>
