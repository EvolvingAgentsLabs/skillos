<script lang="ts">
  import type { SkillDefinition, SkillInputSchema } from "$lib/skills/skill_loader";
  import { skillHostBridge } from "$lib/skills/skill_host_bridge";
  import { ensureSkillsProxyInstalled } from "$lib/skills/skill_llm_proxy";
  import type { SkillResult } from "$lib/skills/skill_result";
  import { recordExperience } from "$lib/memory/smart_memory";
  import ProvenanceBadge from "$components/ProvenanceBadge.svelte";

  interface Props {
    skill: SkillDefinition;
    cartridge: string;
    /** Called when the user taps "Edit" — host opens the SkillEditorSheet. */
    oneditrequested?: () => void;
    /** Called when the user taps "Fork & tweak" — host opens ForkSkillSheet. */
    onforkrequested?: () => void;
  }

  let { skill, cartridge, oneditrequested, onforkrequested }: Props = $props();

  // ── State ──────────────────────────────────────────────────────────────
  // For skills with an input_schema, `typedInputs` holds one value per property.
  // For skills without, `freeformInput` holds a single JSON/text payload.
  const hasSchema = $derived.by(() => {
    const s = skill.input_schema;
    return !!s && !!s.properties && Object.keys(s.properties).length > 0;
  });

  const propEntries = $derived.by<Array<[string, NonNullable<SkillInputSchema["properties"]>[string]]>>(
    () => {
      const props = skill.input_schema?.properties;
      if (!props) return [];
      return Object.entries(props);
    },
  );

  let typedInputs = $state<Record<string, unknown>>(initialTypedInputs(skill));
  let freeformInput = $state("{}");
  let secret = $state("");

  let running = $state(false);
  let result = $state<SkillResult | null>(null);
  let menuOpen = $state(false);
  let bodyExpanded = $state(true);

  function initialTypedInputs(s: SkillDefinition): Record<string, unknown> {
    const out: Record<string, unknown> = {};
    const props = s.input_schema?.properties;
    if (!props) return out;
    for (const [k, def] of Object.entries(props)) {
      if (def.default !== undefined) {
        out[k] = def.default;
      } else if (def.type === "boolean") {
        out[k] = false;
      } else if (def.type === "number" || def.type === "integer") {
        out[k] = "";
      } else {
        out[k] = "";
      }
    }
    return out;
  }

  function coerceTypedInputs(): Record<string, unknown> {
    const out: Record<string, unknown> = {};
    const props = skill.input_schema?.properties ?? {};
    for (const [k, def] of Object.entries(props)) {
      const raw = typedInputs[k];
      if (def.type === "number" || def.type === "integer") {
        if (raw === "" || raw === null || raw === undefined) continue;
        const n = Number(raw);
        out[k] = Number.isFinite(n) ? (def.type === "integer" ? Math.trunc(n) : n) : raw;
      } else if (def.type === "boolean") {
        out[k] = Boolean(raw);
      } else {
        out[k] = raw ?? "";
      }
    }
    return out;
  }

  async function onRun() {
    running = true;
    result = null;
    menuOpen = false;
    // Best-effort LLM proxy — won't block pure-JS skills.
    await ensureSkillsProxyInstalled();
    const startedAt = Date.now();
    try {
      let data: unknown;
      if (hasSchema) {
        data = coerceTypedInputs();
      } else {
        const txt = freeformInput.trim();
        if (!txt) {
          data = {};
        } else {
          try {
            data = JSON.parse(txt);
          } catch {
            // Not valid JSON — pass through as a plain string. Bridge will
            // stringify it for the iframe.
            data = txt;
          }
        }
      }
      result = await skillHostBridge.runSkill(skill, {
        data,
        secret: secret || undefined,
      });
    } catch (err) {
      result = { ok: false, error: err instanceof Error ? err.message : String(err) };
    } finally {
      running = false;
      void logToMemory(startedAt);
    }
  }

  async function logToMemory(startedAt: number): Promise<void> {
    // Telemetry is best-effort: if IndexedDB writes fail, don't surface to
    // the user — the skill result itself is what they care about.
    try {
      if (!result) return;
      const prov = result.provenance;
      const durationSeconds =
        prov?.durationMs != null
          ? Math.max(0, Math.round(prov.durationMs / 1000))
          : Math.max(0, Math.round((Date.now() - startedAt) / 1000));
      const components = [skill.name];
      if (prov?.llmCalls && prov.llmProvider) {
        components.push(`llm:${prov.llmProvider}`);
      }
      await recordExperience({
        session_id: `sess_${startedAt.toString(36)}`,
        project: `skills:${cartridge}`,
        goal: skill.description || skill.name,
        outcome: result.ok ? "success" : "failure",
        components_used: components,
        duration_seconds: durationSeconds,
        output_summary: result.ok
          ? result.result?.slice(0, 500)
          : result.error?.slice(0, 500),
      });
    } catch (err) {
      // eslint-disable-next-line no-console
      console.warn("[SkillCard] recordExperience failed:", err);
    }
  }

  function onEdit() {
    menuOpen = false;
    oneditrequested?.();
  }
</script>

<article class="skill-card" class:collapsed={!bodyExpanded}>
  <header>
    <button
      class="toggle"
      onclick={() => (bodyExpanded = !bodyExpanded)}
      aria-expanded={bodyExpanded}
      aria-label="Toggle skill"
    >
      <span class="chev">{bodyExpanded ? "▾" : "▸"}</span>
      <span class="icon" aria-hidden="true">🧩</span>
      <span class="title-block">
        <span class="name">{skill.name}</span>
        {#if skill.description}<span class="desc">{skill.description}</span>{/if}
      </span>
    </button>
    <div class="menu-wrap">
      <button
        class="menu-btn"
        onclick={() => (menuOpen = !menuOpen)}
        aria-haspopup="menu"
        aria-expanded={menuOpen}
        aria-label="Skill actions"
      >⋮</button>
      {#if menuOpen}
        <button
          type="button"
          class="menu-backdrop"
          aria-label="Close menu"
          onclick={() => (menuOpen = false)}
        ></button>
        <ul class="menu" role="menu">
          {#if onforkrequested}
            <li>
              <button onclick={() => { menuOpen = false; onforkrequested?.(); }}>
                🧬 Fork &amp; tweak…
              </button>
            </li>
          {/if}
          <li><button onclick={onEdit}>Edit source…</button></li>
          {#if skill.homepage}
            <li>
              <a class="menu-link" href={skill.homepage} target="_blank" rel="noopener">
                Open homepage ↗
              </a>
            </li>
          {/if}
          <li class="menu-sep" aria-hidden="true"></li>
          <li class="menu-hint" aria-hidden="true">in cartridge <strong>{cartridge}</strong></li>
        </ul>
      {/if}
    </div>
  </header>

  {#if bodyExpanded}
    <div class="body">
      {#if hasSchema}
        <div class="form">
          {#each propEntries as [key, def] (key)}
            {@const label = def.title ?? key}
            {@const required = skill.input_schema?.required?.includes(key)}
            <label class="field">
              <span class="field-label">
                {label}{#if required}<span class="req" aria-hidden="true">*</span>{/if}
              </span>
              {#if def.description}<span class="field-desc">{def.description}</span>{/if}

              {#if def.enum && def.enum.length > 0}
                <select bind:value={typedInputs[key]}>
                  {#each def.enum as v (String(v))}
                    <option value={v}>{String(v)}</option>
                  {/each}
                </select>
              {:else if def.type === "boolean"}
                <span class="toggle-row">
                  <input
                    type="checkbox"
                    checked={Boolean(typedInputs[key])}
                    onchange={(e) =>
                      (typedInputs[key] = (e.currentTarget as HTMLInputElement).checked)}
                  />
                  <span class="toggle-on-off">{typedInputs[key] ? "on" : "off"}</span>
                </span>
              {:else if def.type === "number" || def.type === "integer"}
                <input
                  type="number"
                  step={def.type === "integer" ? 1 : "any"}
                  min={def.minimum}
                  max={def.maximum}
                  bind:value={typedInputs[key]}
                />
              {:else if def.multiline}
                <textarea rows={3} bind:value={typedInputs[key]}></textarea>
              {:else}
                <input type="text" bind:value={typedInputs[key]} />
              {/if}
            </label>
          {/each}
        </div>
      {:else}
        <label class="field">
          <span class="field-label">Input</span>
          <span class="field-desc">JSON or plain text — passed to the skill as <code>data</code>.</span>
          <textarea rows={4} bind:value={freeformInput}></textarea>
        </label>
      {/if}

      {#if skill.require_secret}
        <label class="field">
          <span class="field-label">
            Secret <span class="hint">({skill.require_secret_description || "required by this skill"})</span>
          </span>
          <input type="password" autocomplete="off" bind:value={secret} />
        </label>
      {/if}

      <div class="run-row">
        <button class="run" disabled={running} onclick={onRun}>
          {running ? "Running…" : "▶ Run"}
        </button>
      </div>

      {#if result}
        <div class="result" class:err={!result.ok}>
          <div class="result-head">
            <div class="result-label">{result.ok ? "Result" : "Error"}</div>
            {#if result.provenance}
              <ProvenanceBadge provenance={result.provenance} />
            {/if}
          </div>
          {#if !result.ok}
            <pre class="result-text">{result.error ?? "unknown error"}</pre>
          {:else}
            {#if result.result}
              <pre class="result-text">{result.result}</pre>
            {/if}
            {#if result.image?.base64}
              <img
                class="result-img"
                src={`data:${result.image.mimeType ?? "image/png"};base64,${result.image.base64}`}
                alt="skill output"
              />
            {/if}
            {#if result.webview?.url}
              <iframe
                class="result-webview"
                src={result.webview.url}
                title="{skill.name} webview"
                sandbox="allow-scripts"
              ></iframe>
            {/if}
            {#if !result.result && !result.image && !result.webview}
              <div class="result-empty">(empty result)</div>
            {/if}
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</article>

<style>
  .skill-card {
    display: flex;
    flex-direction: column;
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin: 0 0 0.6rem;
    overflow: hidden;
  }
  header {
    display: grid;
    grid-template-columns: 1fr auto;
    align-items: center;
    gap: 0.4rem;
    padding: 0.55rem 0.7rem;
  }
  .toggle {
    display: grid;
    grid-template-columns: auto auto 1fr;
    align-items: center;
    gap: 0.5rem;
    background: transparent;
    border: none;
    text-align: left;
    padding: 0;
    cursor: pointer;
    color: inherit;
    font: inherit;
    min-width: 0;
  }
  .chev {
    color: var(--fg-dim);
    width: 1rem;
    text-align: center;
  }
  .icon {
    font-size: 1.1rem;
  }
  .title-block {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  .name {
    font-weight: 600;
    font-size: 0.95rem;
    line-height: 1.2;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .desc {
    color: var(--fg-dim);
    font-size: 0.78rem;
    line-height: 1.25;
    margin-top: 0.1rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .menu-wrap {
    position: relative;
  }
  .menu-btn {
    background: transparent;
    border: none;
    color: var(--fg-dim);
    font-size: 1.2rem;
    padding: 0.2rem 0.45rem;
    cursor: pointer;
    border-radius: 6px;
  }
  .menu-btn:hover {
    background: var(--bg-3);
  }
  .menu-backdrop {
    position: fixed;
    inset: 0;
    background: transparent;
    border: none;
    z-index: 9;
    cursor: default;
  }
  .menu {
    position: absolute;
    top: calc(100% + 0.2rem);
    right: 0;
    background: var(--bg-2);
    border: 1px solid var(--border);
    border-radius: 8px;
    list-style: none;
    margin: 0;
    padding: 0.25rem 0;
    min-width: 180px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2);
    z-index: 10;
  }
  .menu li {
    display: block;
  }
  .menu button,
  .menu-link {
    display: block;
    width: 100%;
    text-align: left;
    background: transparent;
    border: none;
    padding: 0.4rem 0.75rem;
    font-size: 0.85rem;
    cursor: pointer;
    color: var(--fg);
    text-decoration: none;
  }
  .menu button:hover,
  .menu-link:hover {
    background: var(--bg-3);
  }
  .menu-sep {
    height: 1px;
    background: var(--border);
    margin: 0.2rem 0;
  }
  .menu-hint {
    padding: 0.25rem 0.75rem 0.4rem;
    font-size: 0.72rem;
    color: var(--fg-dim);
  }
  .body {
    padding: 0 0.7rem 0.7rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .form {
    display: flex;
    flex-direction: column;
    gap: 0.55rem;
  }
  .field {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }
  .field-label {
    font-size: 0.78rem;
    color: var(--fg-dim);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .req {
    color: var(--accent);
    margin-left: 0.1em;
  }
  .field-desc {
    font-size: 0.75rem;
    color: var(--fg-dim);
    line-height: 1.3;
  }
  .hint {
    text-transform: none;
    letter-spacing: 0;
    font-weight: 400;
  }
  .field input[type="text"],
  .field input[type="password"],
  .field input[type="number"],
  .field select,
  .field textarea {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.4rem 0.55rem;
    font: inherit;
    color: var(--fg);
    min-width: 0;
  }
  .field textarea {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.82rem;
    resize: vertical;
  }
  .toggle-row {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
  }
  .toggle-on-off {
    font-size: 0.78rem;
    color: var(--fg-dim);
  }
  .run-row {
    display: flex;
    justify-content: flex-end;
  }
  .run {
    background: var(--accent);
    color: var(--bg);
    border: none;
    border-radius: 8px;
    padding: 0.45rem 0.95rem;
    font-weight: 600;
    cursor: pointer;
  }
  .run:disabled {
    opacity: 0.6;
    cursor: progress;
  }
  .result {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.5rem 0.6rem;
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }
  .result.err {
    border-color: var(--err);
  }
  .result-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.4rem;
    flex-wrap: wrap;
  }
  .result-label {
    font-size: 0.72rem;
    color: var(--fg-dim);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .result.err .result-label {
    color: var(--err);
  }
  .result-text {
    margin: 0;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.82rem;
    line-height: 1.35;
  }
  .result-img {
    max-width: 100%;
    border-radius: 6px;
  }
  .result-webview {
    width: 100%;
    aspect-ratio: 16 / 10;
    border: 1px solid var(--border);
    border-radius: 6px;
  }
  .result-empty {
    font-size: 0.82rem;
    color: var(--fg-dim);
  }
  code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.78rem;
    background: var(--bg-3);
    padding: 0 0.25rem;
    border-radius: 3px;
  }
</style>
