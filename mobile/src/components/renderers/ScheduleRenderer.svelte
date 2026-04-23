<script lang="ts">
  /**
   * ScheduleRenderer — renders dated items as a day-by-day list. Used for
   * weekly menus, itineraries, and calendar-style outputs. Not a full
   * grid calendar (too much for a phone); a chronological stack that
   * groups items under their day heading is clearer and scales better.
   */
  import { extractRows } from "$lib/render/done_card_renderers";

  interface Props {
    data: unknown;
  }
  let { data }: Props = $props();

  const rows = $derived(extractRows(data));

  interface Event {
    dateLabel: string;
    dateSortKey: string;
    title: string;
    detail: string;
  }

  function findDateField(r: Record<string, unknown>): string | undefined {
    const keys = ["date", "day", "when", "at", "timestamp", "start", "start_date"];
    for (const k of Object.keys(r)) {
      if (keys.includes(k.toLowerCase()) && typeof r[k] === "string") {
        return r[k] as string;
      }
    }
    return undefined;
  }

  function findTitle(r: Record<string, unknown>): string {
    const titleKeys = ["title", "name", "label", "meal", "activity", "event"];
    for (const k of Object.keys(r)) {
      if (titleKeys.includes(k.toLowerCase()) && typeof r[k] === "string") {
        return r[k] as string;
      }
    }
    // Fallback: first string field that isn't the date.
    for (const [k, v] of Object.entries(r)) {
      if (typeof v === "string" && !["date", "day", "when", "at", "timestamp"].includes(k.toLowerCase())) {
        return v;
      }
    }
    return "(untitled)";
  }

  function findDetail(r: Record<string, unknown>, skipKeys: Set<string>): string {
    const parts: string[] = [];
    for (const [k, v] of Object.entries(r)) {
      if (skipKeys.has(k.toLowerCase())) continue;
      if (typeof v === "string") parts.push(`${k}: ${v}`);
      else if (typeof v === "number") parts.push(`${k}: ${v}`);
      else if (typeof v === "boolean") parts.push(`${k}: ${v ? "yes" : "no"}`);
    }
    return parts.join(" · ");
  }

  function formatDateLabel(raw: string): string {
    try {
      const d = new Date(raw);
      if (Number.isNaN(d.getTime())) return raw;
      return d.toLocaleDateString(undefined, {
        weekday: "short",
        month: "short",
        day: "numeric",
      });
    } catch {
      return raw;
    }
  }

  const events = $derived.by<Event[]>(() => {
    const skip = new Set([
      "date", "day", "when", "at", "timestamp", "start", "start_date",
      "title", "name", "label", "meal", "activity", "event",
    ]);
    const out: Event[] = [];
    for (const r of rows) {
      const raw = findDateField(r);
      if (!raw) continue;
      out.push({
        dateLabel: formatDateLabel(raw),
        dateSortKey: raw,
        title: findTitle(r),
        detail: findDetail(r, skip),
      });
    }
    out.sort((a, b) => a.dateSortKey.localeCompare(b.dateSortKey));
    return out;
  });

  const byDate = $derived.by(() => {
    const map = new Map<string, Event[]>();
    for (const e of events) {
      if (!map.has(e.dateLabel)) map.set(e.dateLabel, []);
      map.get(e.dateLabel)!.push(e);
    }
    return Array.from(map.entries());
  });
</script>

{#if events.length > 0}
  <div class="schedule">
    {#each byDate as [date, list] (date)}
      <section class="day">
        <header>{date}</header>
        <ul>
          {#each list as e, i (i)}
            <li>
              <div class="title">{e.title}</div>
              {#if e.detail}<div class="detail">{e.detail}</div>{/if}
            </li>
          {/each}
        </ul>
      </section>
    {/each}
  </div>
{/if}

<style>
  .schedule {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
    max-height: 50vh;
    overflow-y: auto;
  }
  .day {
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--bg);
  }
  .day header {
    padding: 0.35rem 0.6rem;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--fg-dim);
    background: var(--bg-3);
    border-bottom: 1px solid var(--border);
    border-radius: 8px 8px 0 0;
  }
  .day ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .day li {
    padding: 0.4rem 0.6rem;
    border-bottom: 1px solid var(--border);
  }
  .day li:last-child {
    border-bottom: none;
  }
  .title {
    font-size: 0.88rem;
    color: var(--fg);
    font-weight: 500;
  }
  .detail {
    font-size: 0.76rem;
    color: var(--fg-dim);
    margin-top: 0.15rem;
    word-break: break-word;
  }
</style>
