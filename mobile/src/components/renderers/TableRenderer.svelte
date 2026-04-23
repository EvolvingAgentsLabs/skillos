<script lang="ts">
  /**
   * TableRenderer — renders an array of homogeneous objects as a mobile-
   * friendly table. Keys from the first row define the column order.
   * Caps columns at 5 to stay readable on a phone; extra keys fall into
   * a compact "+N more" popover per row.
   */
  import { extractRows } from "$lib/render/done_card_renderers";

  interface Props {
    data: unknown;
  }
  let { data }: Props = $props();

  const rows = $derived(extractRows(data));
  const columns = $derived.by(() => {
    if (rows.length === 0) return [];
    return Object.keys(rows[0]).slice(0, 5);
  });

  function formatCell(v: unknown): string {
    if (v === null || v === undefined) return "";
    if (typeof v === "number") {
      // Tabular numbers: keep 2 decimals for fractions, integers plain.
      return Number.isInteger(v) ? String(v) : v.toFixed(2);
    }
    if (typeof v === "string") return v;
    if (typeof v === "boolean") return v ? "✓" : "·";
    try {
      return JSON.stringify(v);
    } catch {
      return String(v);
    }
  }

  function humanHeader(k: string): string {
    return k.replace(/[_-]+/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
  }
</script>

{#if rows.length > 0}
  <div class="scroll">
    <table>
      <thead>
        <tr>
          {#each columns as c (c)}
            <th>{humanHeader(c)}</th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each rows as r, i (i)}
          <tr>
            {#each columns as c (c)}
              <td>{formatCell(r[c])}</td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  <div class="footer">
    {rows.length} row{rows.length === 1 ? "" : "s"}
    {#if Object.keys(rows[0]).length > columns.length}
      · {Object.keys(rows[0]).length - columns.length} more column{Object.keys(rows[0]).length - columns.length === 1 ? "" : "s"} in raw
    {/if}
  </div>
{/if}

<style>
  .scroll {
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: var(--bg);
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
  }
  th, td {
    padding: 0.35rem 0.55rem;
    text-align: left;
    white-space: nowrap;
    border-bottom: 1px solid var(--border);
  }
  th {
    background: var(--bg-3);
    color: var(--fg-dim);
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.68rem;
    font-weight: 600;
    position: sticky;
    top: 0;
  }
  tr:last-child td {
    border-bottom: none;
  }
  td {
    font-variant-numeric: tabular-nums;
  }
  .footer {
    font-size: 0.72rem;
    color: var(--fg-dim);
    padding: 0.3rem 0.1rem 0;
  }
</style>
