<script lang="ts">
  /**
   * ReaderRenderer — text output (markdown / prose / skill-result strings)
   * rendered in a comfortable reader view. Deliberately minimal — no
   * external markdown lib yet, just paragraph splits and monospace
   * fenced blocks so the common cases (article summaries, reports,
   * plain skill results) feel like content instead of payload.
   */
  import { extractReaderText } from "$lib/render/done_card_renderers";

  interface Props {
    data: unknown;
  }
  let { data }: Props = $props();

  const text = $derived(extractReaderText(data));

  // Lightweight paragraph splitter. Preserves fenced code blocks as-is
  // so JSON/code inside a skill result still reads naturally.
  interface Block {
    kind: "text" | "code";
    content: string;
  }

  const blocks = $derived.by<Block[]>(() => {
    if (!text) return [];
    const out: Block[] = [];
    const parts = text.split(/```/g);
    parts.forEach((part, i) => {
      if (i % 2 === 1) {
        // inside a fence
        out.push({ kind: "code", content: part.replace(/^\w*\n/, "") });
      } else {
        const paragraphs = part
          .split(/\n\s*\n/)
          .map((p) => p.trim())
          .filter((p) => p.length > 0);
        for (const p of paragraphs) out.push({ kind: "text", content: p });
      }
    });
    return out;
  });
</script>

{#if blocks.length > 0}
  <article class="reader">
    {#each blocks as b, i (i)}
      {#if b.kind === "code"}
        <pre><code>{b.content}</code></pre>
      {:else}
        <p>{b.content}</p>
      {/if}
    {/each}
  </article>
{/if}

<style>
  .reader {
    max-height: 50vh;
    overflow-y: auto;
    padding: 0.25rem 0.1rem;
    line-height: 1.55;
    font-size: 0.92rem;
    color: var(--fg);
  }
  .reader p {
    margin: 0 0 0.8em;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .reader p:last-child {
    margin-bottom: 0;
  }
  .reader pre {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.55rem 0.7rem;
    overflow-x: auto;
    font-size: 0.82rem;
    margin: 0 0 0.8em;
  }
  .reader code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    color: var(--fg);
  }
</style>
