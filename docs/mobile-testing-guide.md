# SkillOS Mobile — Feature Testing Guide

Hands-on checklist to exercise every user-facing surface of the mobile app (`mobile/`). Organized by tab and flow so you can verify one area at a time, note what works, note what doesn't, and reproduce bugs.

> This is a **testing** guide. For install, architecture, Capacitor builds, round-trip-to-desktop, and the evals harness, see [`tutorial-mobile.md`](./tutorial-mobile.md).

---

## 0. Prerequisites

| What | Minimum |
|---|---|
| Node | 18 LTS or 20 LTS |
| Browser | Chromium 115+ or Firefox 120+ (Safari Tech Preview OK) |
| Provider key (optional but recommended) | OpenRouter, Gemini, or Anthropic — needed for cloud-LLM tests and for the Forge ceremony |
| Disk | ~2 GB free if you plan to download on-device models |

```bash
cd skillos/mobile
npm install
npm test       # should report 129/129 passing
npm run dev    # vite on http://localhost:5173/
```

Open the URL in a fresh browser profile (or incognito) for a clean slate. First boot seeds IndexedDB with 170+ cartridge files (~8 MB); you'll see a progress bar labelled *"Seeding N/M"*. Wait for it to finish before touching anything.

> **Upgrading an existing install:** the DB schema bumped from v3 to v4 to add a `teachings` store. The upgrade is additive — existing data is preserved, a new empty object store is created on first load. If you see the seed flow run again, that's unrelated (the seed version probably changed too); data in `projects`, `memory`, `files`, `blackboards` is not cleared by the schema bump.

---

## Map of the app

Bottom nav has **four always-visible tabs** plus one hidden behind a flag:

| Tab | Default | Purpose |
|---|---|---|
| **Home** | ✅ (default landing) | Grid of your Recipes. Tap a tile to run; tap the dashed "Teach a Recipe" tile to open the Forge ceremony for a new one. |
| **Runs** | ✅ | History of active / in-progress work. The old Projects swiper — create, watch, manage cartridge runs here. |
| **Skills** | ✅ | Browse and run every installed skill as a form-driven card. |
| **Brain** | ✅ | Two views: **Runs** (audit trail of every execution, recency-grouped) and **Recipes** (per-cartridge clusters of teachings + runs). |
| **Library** | Hidden unless authoring mode on | Edit cartridges, agents, schemas, skills in-app. |

**Where's the old Projects tab?** Renamed to **Runs** and demoted from default landing. The underlying ProjectSwiper surface is unchanged; Home is a new launcher layer on top.

Settings: tap the **"SkillOS"** brand in the **Runs** tab header → opens the app settings sheet.

---

## 1. First-boot flow

**Goal**: confirm seed completes and you land on the new Home tab.

1. Clear browser storage for `localhost:5173` (DevTools → Application → Clear storage).
2. Reload. The boot splash should show:
   - SkillOS wordmark
   - "Fetching seed manifest…" → "Seeding N / M" with the current path
   - Progress bar advances to 100%
3. After seed completes, you should land on **Home** tab showing grouped Recipe tiles — one per installed cartridge, bucketed by category (e.g. "cooking", "engineer", "Other").

**Pass criteria**
- [ ] Seeding completes without error.
- [ ] Bottom nav shows **Home · Runs · Skills · Brain** (four items).
- [ ] Home shows a grid of recipe tiles grouped by category, with a dashed "Teach a Recipe" tile in a "New" group at the bottom.
- [ ] Tapping **Brain** shows the Runs/Recipes mode switch with the Runs empty state ("No memories yet") or any pre-existing runs.
- [ ] Tapping **Skills** shows the pre-seeded skills grouped by cartridge (171 cartridges ship; most include 1+ skill).

**Common failures**
- *Seed stalls on a specific path* → check DevTools console for a 404. Usually means `npm run seed` wasn't run before `npm run dev`. The `predev` script handles this automatically.
- *Only three tabs visible (missing Home)* → you're on an old build; hard-reload.
- *Land on Runs instead of Home* → you've got a stale `tab` state somewhere; try Clear storage + reload.

---

## 2. Home tab (Recipe grid)

### 2.1 Tile activation

1. Scroll through the category groups on Home.
2. Pick any tile (e.g., one under `cooking`) and tap it.
3. The app should:
   - Create a project for that cartridge if none exists (or reuse an existing one for this cartridge).
   - If a provider is configured, immediately start the run.
   - If no provider is configured, open the ProviderSettingsSheet.
4. After tap → app switches to the **Runs** tab and shows the activated project.

**Pass**
- [ ] Tap → tab switches to Runs.
- [ ] First tap on a recipe creates a new project; second tap on the same recipe reuses it (no duplicate projects).
- [ ] The recipe's cartridge name appears as the project's cartridge label.
- [ ] Provider-missing case prompts for settings instead of silently failing.

### 2.2 Learning patina

If you've completed §4 (Teach this Recipe) below for any cartridge, its tile on Home should display a chip like **"learned 3"** at the bottom.

**Pass**
- [ ] Before teaching: no patina chip.
- [ ] After saving a teaching for that cartridge: reload Home → chip present with the right count.
- [ ] Deleting all teachings for that cartridge → patina disappears.

### 2.3 Forge ceremony ("Teach a Recipe" tile)

This is the new capability-gap ceremony. Only runs if you have a cloud provider configured under `_skills` (see §6).

1. Tap the dashed **Teach a Recipe** tile in the "New" group.
2. GoalComposer opens.
3. **Name**: leave blank or type something distinctive.
4. **Goal**: type something the router will fail to match against any cartridge. Example: `"convert my timestamps from UTC to Buenos Aires and format them for my kids' school"`
5. Tap **Plan with SkillOS**. After a brief "Planning…" state, the composer should show the synthesize decision: `✨ Synthesize a new skill: <slug>`.
6. A new blue **✨ Teach me this Recipe** button appears. Tap it.
7. **ForgeRecipeSheet** slides up in `intro` phase:
   - "I don't know how to do this yet" header
   - Your goal echoed back
   - A 3-step proposed plan (Understand → Build → Save offline)
   - One-time cloud cost estimate (~$0.01–0.03)
   - **Not now** and **✨ Teach me** buttons
8. Tap **✨ Teach me**. The sheet flips to `synthesizing` — spinner + "Synthesizing recipe…" subtitle.
9. On success, the sheet enters the `acquired` phase:
   - "⚡ NEW RECIPE ACQUIRED" ribbon (animated)
   - The slug-style name in accent color
   - Pinned-to-cartridge confirmation line
   - **Use it now** full-width button
10. Tap **Use it now** — returns to GoalComposer → submits → creates a project using the just-forged skill as its ad-hoc plan.

**Pass**
- [ ] The `intro` screen shows a plausible plan (not literal "todo"/empty placeholders).
- [ ] The `synthesizing` spinner animates; the sheet's backdrop is not clickable while synthesizing.
- [ ] On success, the ribbon animation and name entrance are visible (300–400 ms of motion).
- [ ] The newly-acquired skill appears in the Skills tab under the host cartridge.
- [ ] Home's patina chip on that cartridge reflects any teachings you add post-acquisition.

**Common failures**
- *"No cloud provider configured"* → configure a provider under Skills tab ⚙ (§6) first.
- *"Synthesis response could not be parsed"* → the LLM returned malformed YAML/JS. Tap **Try again** — model variance, usually succeeds on retry.
- *"No cartridge can host a new skill"* → no installed cartridge has a `skills_source` field. Unusual on a fresh seed; happens if you've been deleting cartridges in Library.

---

## 3. Runs tab (was Projects)

This is the old project-swiper surface. All prior functionality intact; the tab just moved from default-landing to second-tab.

### 3.1 Create a project (manual path)

1. Navigate to **Runs** tab.
2. Tap `+` top-right → GoalComposer sheet opens.
3. **Name**: "Test plan meals"
4. **Cartridge**: in manual mode (tap *Pick manually*), pick `cooking`.
5. **Initial goal**: "plan a vegetarian dinner for Wednesday"
6. Tap **Create**.

**Pass**
- [ ] Sheet closes, swiper shows your new project as the first column.
- [ ] Header dots at the top reflect project count.
- [ ] A single card exists in the **Planned** lane with your goal text.

### 3.2 Provider settings (per-project)

1. Tap the ⚙ in the project column header → ProviderSettingsSheet opens.
2. Pick **openrouter-qwen** as primary (or any cloud provider you have a key for).
3. Enter API key + model (e.g. `qwen/qwen-2.5-72b-instruct`).
4. (Optional) Enable **Fallback** tab and add a second provider for tier escalation.
5. Tap **Save**.

**Pass**
- [ ] Sheet closes with no error banner.
- [ ] Tapping the ⚙ again reloads your saved values (proves the write hit IndexedDB).

### 3.3 Run a project + composition stepper

1. With primary provider configured, tap the **▶ run** button in the project header.
2. The **Run drawer** should slide up from the bottom. **By default it renders the Composition Stepper** (see §5): a clean vertical list of agent steps with status markers.
3. Each step transitions: pending → active (pulsing dot) → done (green ✓) or error (red ✗).
4. Cards should auto-populate in **In Execution** lane as steps fire, then move to **Done** when they validate.

**Pass**
- [ ] Stepper shows one entry per agent; active step has a visible pulse.
- [ ] Each entry shows the human-readable agent name (kebab → "Title Case") plus a tier badge (⚡ local or ☁ cloud).
- [ ] When the run completes, a "Recipe finished" / "Recipe finished with issues" summary chip appears below the stepper.
- [ ] Tapping **Details** in the drawer header flips to the raw event log (same content as the old RunLogDrawer).
- [ ] Tapping **Hide details** flips back.
- [ ] At least one card ends up in **Done** with a typed renderer (see §7).

**Common failures**
- *"missing provider config"* → you skipped §3.2. The run button opens the settings sheet automatically.
- *Stepper shows no entries* → the run failed before emitting any `step-start`. Flip to Details and look for the first error event.

### 3.4 Card lanes + manipulation

1. Expand any card by tapping its `▸` chevron.
2. The card body now shows a **typed renderer** (table / schedule / reader) by default for structured payloads — see §7.
3. Use the `→ Planned` / `→ In Execution` / `→ Done` buttons to move it between lanes.
4. Use **Delete** to remove one.

**Pass**
- [ ] Card movements persist across a browser reload (check IndexedDB `projects` store).
- [ ] Deleted cards do not reappear.

### 3.5 Project swiper

1. Create a second project (any cartridge).
2. Swipe horizontally (trackpad drag or touch) — the column should snap to the next project.
3. Header dots should update the active indicator.

**Pass**
- [ ] Smooth snap-scroll; no torn scroll position.
- [ ] Creating a new project scrolls to index 0 automatically.

---

## 4. Teach this Recipe (post-run refinement)

Each teaching attaches to the cartridge (recipe), not a single output. Teachings compound per-recipe and show up as the learning patina on Home tiles and Skills groups.

> **Scope note**: teachings are *stored and displayed* today, but not yet *applied at runtime* (i.e., the cartridge runner doesn't prepend them to agent prompts). That plumbing is a follow-up. The UI surface exists so you can verify the capture/display loop end-to-end.

### 4.1 Open the Teach sheet from Runs

**Precondition**: a project with a cartridge attached and at least one card in the **Done** lane.

1. In Runs tab, scroll to such a project.
2. Next to the ⚙ and ▶ run buttons in the header, there should now be a **✎** icon (Teach this Recipe). If it isn't visible, your project doesn't yet have a done card.
3. Tap ✎ → **TeachRecipeSheet** slides up.

**Pass**
- [ ] Sheet header shows "Teach this Recipe" + the cartridge name in a `<code>` chip.
- [ ] Empty state line: "No teachings yet — this recipe runs exactly as synthesized."

### 4.2 Save a teaching

1. In the textarea, type a correction like: `round totals up to 2 decimals`
2. (Optional) In the "Apply to step" field, type an agent name if the correction is step-specific. Leave empty for whole-recipe teachings.
3. Tap **Save teaching**.

**Pass**
- [ ] Sheet scrolls down to show the new teaching card in the "What this recipe has learned" list with timestamp + optional step chip.
- [ ] Toast on the Runs column: "Teaching saved — will apply next run".
- [ ] Cartridge header under the project name now shows "· learned 1" (patina).

### 4.3 Open the Teach sheet from Skills

Same sheet, different entry point — useful for teaching a recipe you're browsing.

1. **Skills** tab → find any cartridge group header.
2. On the right side of the cart-head, there's a **✎** button.
3. Tap → same TeachRecipeSheet opens.

**Pass**
- [ ] Teachings from §4.2 show up here (same underlying store).
- [ ] Cartridge group header shows "· learned N" patina after saving.

### 4.4 Delete a teaching

1. In the Teach sheet's list, tap the × on any teaching.
2. It disappears immediately.

**Pass**
- [ ] Deleted teachings are gone after sheet close + reopen.
- [ ] Patina count decreases accordingly.
- [ ] In the Brain tab Recipes view (§8), the teaching is gone there too.

---

## 5. Composition stepper + details log

Default run-time surface for every `▶ run`. Replaces the raw log as the landing view.

**Goal**: see a recipe run as a clean stepper, not as an event dump.

### 5.1 Observation

1. Start any run (§3.3).
2. The bottom drawer should render the stepper by default with an active pulse on the current step.
3. Tier badges per step:
   - ⚡ primary (local default)
   - ☁ fallback (cloud — appears only if the runner emits a `tier-switch` event)
4. The step's last-known tool invocation shows as a caption under the agent name.

### 5.2 Details toggle

1. While a run is active or after it completes, tap **Details** in the drawer header.
2. The drawer flips to the raw event log — same content as the pre-reframe RunLogDrawer.
3. Tap **Hide details** to flip back.

**Pass**
- [ ] Stepper is the default view on both active and last-run states.
- [ ] The Details toggle round-trips without re-running anything.
- [ ] Tier-switch events (if they fire) change the step badge in place from ⚡ to ☁.
- [ ] The "Recipe finished" / "Recipe finished with issues" summary appears below the stepper only after `run-end`.

---

## 6. Skills tab

### 6.1 Browse skills

1. Tap **Skills** in the bottom nav.
2. Verify the header shows "Skills" and a ⚙ icon top-right.
3. Skills are grouped by cartridge (header: cartridge name, right-aligned `N skills · learned N` subtitle, **✎** Teach button, and the skills beneath).
4. Scroll down — the feed should be long (171 cartridges × varying skill counts).

**Pass**
- [ ] At least `cooking`, `demo`, and a few others are visible with skills beneath them.
- [ ] Tapping a skill's header chevron (`▾` / `▸`) toggles the runnable form.
- [ ] Cartridges with teachings show a "learned N" chip in accent color.

### 6.2 Run a pure-JS skill (no provider needed)

The seeded `demo` cartridge ships `calculate-hash` — a deterministic JS skill that takes `{text: "..."}` and returns a SHA-1 hash. Perfect for testing without any API key.

1. Find **calculate-hash** (under `demo` cartridge) and expand it.
2. Enter: `{"text": "hello world"}`
3. Tap **▶ Run**.

**Pass**
- [ ] A result panel appears below the form.
- [ ] The result reads something like `2aae6c35c94fcfb415dbe95f408b9ce91ee846ed`.
- [ ] A **ProvenanceBadge** appears above the result: **⚡ Local · deterministic JS · <N>ms**.

**Common failures**
- *"Skill failed: invalid skill payload"* → you entered raw text instead of JSON. Try `{"text": "hi"}` (valid JSON).

### 6.3 Run a skill that uses the LLM

Some seeded skills call `__skillos.llm.chat` internally. Before running one, configure the global skills provider:

1. Skills tab → tap **⚙** top-right → ProviderSettingsSheet opens (this writes to `_skills`, the global skills provider slot — separate from per-project config).
2. Configure a cloud provider with a real API key.
3. Save.

Now run a skill that uses the LLM. Good candidates from the seed: `mood-music`, `restaurant-roulette`, `kitchen-adventure`.

4. Expand **mood-music** (or similar).
5. Fill the input (often a mood string like `"melancholy"`).
6. Tap **▶ Run**.

**Pass**
- [ ] Result text contains a coherent LLM response.
- [ ] ProvenanceBadge reads **☁ Cloud · `<providerId>` · `<model>` · `<Xms>` · 1 LLM call** (or more calls). Color tint is warm/amber.
- [ ] The Brain tab now has an entry for this run (see §8).

### 6.4 Typed-input form

Typed fields render when a skill's `SKILL.md` frontmatter includes `metadata.input_schema`. No seeded skills have this yet — the feature is there for new skills created via Promote-to-Skill, forge ceremony, or hand-authored.

To confirm the renderer works without writing a new skill: use the **Library** tab (authoring mode) → open any skill → edit `SKILL.md` → add an `input_schema` under `metadata:`.

**Pass**
- [ ] Field renders with a title, description, and the right input type.
- [ ] Required fields show a `*` marker.
- [ ] Running the skill passes the typed values as `data.text` etc.

---

## 7. Typed Done-card renderers

Done-lane cards now render their payload through a **type-detecting registry**. The raw JSON view is preserved as a fallback and opt-in.

### 7.1 Detection

Expand any done card. The `choice.kind` used for rendering depends on payload shape:

| Renderer | Trigger |
|---|---|
| `table` | Array of ≥2 homogeneous objects (e.g. invoice line items, search results) |
| `schedule` | Array of objects carrying a date-ish field (date/day/when/at/timestamp/start) — weekly menus, itineraries, calendars |
| `reader` | Strings ≥40 chars, or objects with a `body`/`content`/`text`/`markdown`/`summary`/`result`/`article` field |
| `json` | Fallback when nothing structurally matches |

The `schema_ref` on the card can hint the choice — names matching `invoice`/`menu`/`report` bias toward `table`/`schedule`/`reader` respectively.

### 7.2 Verification

1. Run the `cooking` cartridge (§3.3) so it produces a `weekly_menu` document card.
2. Expand the done card. It should render as a **schedule** (day-grouped list) — not a JSON pre.
3. Tap **Raw JSON** at the bottom of the rich view to flip to the old pre dump.
4. Tap **Typed view** to flip back.

**Pass**
- [ ] Weekly menu renders as grouped-by-day list with meal titles + detail captions.
- [ ] Table-shaped data (e.g. invoice items) renders as a mobile-friendly table with up to 5 columns and a `+N more columns in raw` footer.
- [ ] Long text outputs render as a reader-view with code blocks fenced in `<pre>`.
- [ ] Raw JSON toggle round-trips without data loss.

---

## 8. Brain tab

### 8.1 Mode switch

The Brain header now shows a **Runs | Recipes** toggle under the sub-line.

- **Runs** mode (default): the old recency-grouped list (Today/Yesterday/This week/Earlier). Unchanged from pre-reframe.
- **Recipes** mode: per-cartridge clusters, each showing teachings + recent runs.

### 8.2 Runs view

After running at least one project (§3.3) and one skill (§6.2):

1. Tap **Brain**, keep mode = **Runs**.
2. Verify the **totals strip** (4 stats): `runs`, `success %`, `cloud spend`, `runtime`.
3. Verify the **local/cloud mix bar**: green (local) vs amber (cloud) segments + legend.
4. Records are grouped by recency with outcome icons, project chip, timestamp, duration, optional cost chip.

**Pass**
- [ ] Skill-tab runs appear under project `skills:<cartridge>`.
- [ ] Cartridge flow runs appear under the project's actual name.
- [ ] Records sort most-recent-first within each bucket.

### 8.3 Recipes view (bidirectional clusters)

1. Tap **Recipes** mode.
2. Each cluster shows:
   - Cartridge name
   - Meta chips: `learned N` (accent) when teachings exist, `N runs` (muted) when runs exist
   - **✎** inline Teach button
   - "What this recipe has learned about you" — editable teachings list (tap × to delete)
   - "Recent runs" — up to 5 recent experience records from that cartridge; + "… and N more in Runs" if more

**Pass**
- [ ] Clusters with teachings sort before clusters without.
- [ ] Deleting a teaching from the cluster removes it from Home patina and from §4 list.
- [ ] Tapping ✎ opens the same TeachRecipeSheet as from Runs/Skills tabs.

### 8.4 Honest scope

What the Brain tab does **not** do today:
- No extracted facts like "user is vegetarian" — only structured records.
- Clusters aren't a node-graph (no SVG edges). The reverse-lookup property holds because teachings belong to their recipe by primary key.
- `cost_estimate_usd` is almost always 0 in Runs mode because token usage isn't plumbed from LLM responses yet.

---

## 9. Offline banner

### 9.1 Test

1. With the app open on any tab, disable wifi / turn on airplane mode / block `localhost:5173` in DevTools **Network** → throttling (select "Offline").
2. Wait a beat.
3. A green-tinted banner should appear at the top of the screen: **⚡ Offline — local recipes still run. Cloud synthesis paused.**
4. Re-enable network → banner disappears within one network event.

**Pass**
- [ ] Banner is visible over every tab (Home/Runs/Skills/Brain/Library).
- [ ] Banner does not block clicks — content underneath is still interactive.
- [ ] Copy emphasizes that local runs still work (inverted-expectation tone).

### 9.2 Known scope

The banner only reflects `navigator.onLine`. It does not test actual reachability of configured providers. A misconfigured cloud provider or a blocked host won't toggle the banner; the run itself will surface the error.

---

## 10. Promote to Skill (end-to-end)

This is the flow that converts a one-off successful run into a permanent reusable skill. (Note: this is the per-card "capture this specific output as a skill" flow; for "the whole goal needs a new recipe", use the Forge ceremony in §2.3.)

**Preconditions**
- A done-lane card in a project (from §3.3).
- A cloud provider configured under `_skills` (from §6.3) — synthesis is LLM-driven.
- A cartridge that declares `skills_source:` (most seeded ones do; `demo` is safest).

### Steps

1. Runs tab → open the project with your done card.
2. Expand the done card (`▸`).
3. You should see a green **✨ Save as Skill** button alongside the lane-move buttons.
4. Tap it → **PromoteToSkillSheet** slides up.
5. Review the context block (card title, subtitle, project name, project cartridge).
6. **Skill name** is pre-filled. Edit if you want.
7. **Target cartridge** picker: select `demo` (or any host-capable cartridge).
8. If no provider is configured, a yellow banner tells you. Fix it via Skills tab ⚙, come back.
9. Tap **✨ Synthesize**. On completion:
   - `SKILL.md` textarea populates with frontmatter + body.
   - `scripts/index.js` textarea populates.
10. Review the generated code. Save if reasonable, regenerate or hand-edit if not.
11. Sheet closes. Toast: **"Saved \"<skill-name>\" to <cartridge>"**.

### Verify the skill exists

1. **Skills** tab → scroll to the target cartridge → your new skill appears.
2. Run it to verify the generated JS actually works.

**Pass**
- [ ] Synthesis completes without throwing.
- [ ] Saved skill appears in Skills tab without a reload.
- [ ] Running the skill returns a non-error result.

---

## 11. Provenance badges — what each state means

Every skill run (success or failure) attaches a `provenance` block to the result, surfaced via the `ProvenanceBadge` component.

| State | Icon | Border color | Meaning |
|---|---|---|---|
| Local deterministic | ⚡ | green | Skill ran pure JS, zero LLM calls |
| Cloud LLM | ☁ | amber | Skill made ≥1 `__skillos.llm.chat` call routed to a cloud provider |
| On-device LLM | 🦙 | accent | Same but the provider was wllama or litert |

Every badge also shows:
- Duration in ms / s
- LLM call count (only if > 0)

> **Note on cost**: per-run cost rendering was intentionally removed from the badge — the `⚡ Local` label already carries the "this was free" message without anchoring users in a cost frame. The underlying `costUsd` field on `SkillResultProvenance` is still populated and is reserved for a counterfactual-savings surface on Recipe tiles ("$0.37 saved vs cloud") in a future pass.

### Testing the color / classification logic

1. Run `calculate-hash` → expect green ⚡.
2. Run an LLM-using skill (§6.3) with a cloud provider → expect amber ☁.
3. Download an on-device model (§13) and set `_skills` to the local provider → rerun → expect accent 🦙.
4. Run a skill with no provider configured and no LLM calls → still green ⚡.
5. Run a skill with no provider but **does** call the LLM internally → result fails with `llm proxy not configured`; badge shows ☁ with 1 LLM call.

**Pass**
- [ ] All four states render distinct colors.
- [ ] Duration matches real wall-clock time.
- [ ] `1 LLM call` correctly pluralizes for larger counts.

---

## 12. Library tab (authoring mode)

Authoring mode unlocks the Library tab and lets you edit cartridges / agents / schemas / skills in the app.

### 12.1 Enable authoring mode

1. Runs tab header → tap **SkillOS** brand → SettingsSheet opens.
2. Toggle **Authoring mode** on.
3. Close the sheet.
4. Bottom nav now has a **fifth** tab: **Library**.

**Pass**
- [ ] Library tab visible.
- [ ] Toggling off removes the tab (if you were on Library, you auto-bounce to Home).

### 12.2 Browse / clone / edit

Same flows as before the reframe. See previous versions of this guide for detailed steps — nothing changed in authoring.

Quick check:
- [ ] Clone a cartridge → rename → save → appears in list.
- [ ] Edit an agent → change persists across reload.
- [ ] Edit a JS skill → Test panel returns result.
- [ ] Create a new cartridge via the wizard → appears in list with stub files.

---

## 13. On-device models (wllama)

Unchanged by the reframe. See [`tutorial-mobile.md §3`](./tutorial-mobile.md#3-on-device-llm-wllama-wasm) for the full flow.

Quick confirm that the on-device path works:

1. SettingsSheet → toggle **On-device LLMs** on.
2. Open Model Manager → pick a small Qwen — download.
3. Skills tab ⚙ → set `_skills` provider to `wllama-local` + the installed model.
4. Run any LLM-using skill (§6.3).
5. Expect **🦙 On-device · wllama-local · <model> · <duration>**.

---

## 14. Settings sheet

1. Runs tab → tap **SkillOS** brand.
2. Verify toggles:
   - **Authoring mode** (§12)
   - **On-device LLMs** (§13)
   - **Export to Files** (Capacitor-only; disabled in browser — greyed out)
3. Verify the **Reset** section lets you clear IndexedDB (useful for a fresh test).

**Pass**
- [ ] Each toggle persists across reload.
- [ ] Reset returns you to the first-boot seed flow.

---

## 15. Known caveats — don't report these as bugs

These are intentional limitations of the current build:

| What | Why |
|---|---|
| Teachings stored + displayed but not injected into agent prompts yet | Prompt-preamble plumbing into `cartridge/runner.ts` is a follow-up. The capture/display UX loop works end-to-end regardless. |
| Forge ceremony synthesizes a single skill, not a full multi-agent composition | V1 reuses `skill_synth.ts`. A `ProposedPlan` data model with `existing \| synthesize` per step is the next scope. |
| Per-run cost chip removed from ProvenanceBadge | Intentional — see §11 note. Counterfactual savings on Recipe tiles is the successor surface. |
| DB upgrade v3 → v4 on existing installs | Additive — new `teachings` store only. No existing data is touched. |
| `cost_estimate_usd` in Brain Runs view is ~always $0 | Token counts aren't plumbed from LLM responses to memory records yet. Mix bar is the meaningful signal. |
| Brain Runs mix bar labels on-device LLM runs as "cloud" | Chip branches on "has LLM call?" not "where did the LLM live?". Pre-existing. |
| Home tile activation creates at most one project per cartridge | Intentional — avoids per-recipe project sprawl. Use the Runs tab `+` to create explicit per-goal projects. |
| Freeform textarea instead of typed fields for most seeded skills | Seeded skills don't yet declare `input_schema`. Edit in Library to add it. |
| iOS Capacitor build untested on real hardware | Out of scope for browser tests. See `tutorial-mobile.md §10`. |

---

## 16. Reporting a real bug

When something genuinely breaks:

1. Open DevTools → **Console** → copy any red errors.
2. Open **Application** → IndexedDB → `skillos` → screenshot the affected store (`projects`, `memory`, `files`, `teachings`, `secrets`, `meta`).
3. Note which tab / flow was active and the last three actions.
4. Check `git status` and `git log -1` in `mobile/` — note the commit you were on.
5. Reproduce once with a fresh browser profile (§1) to rule out dirty IndexedDB state.

A good bug report has: exact steps, expected vs actual, console output, and the commit SHA.

---

## 17. End-to-end smoke test (7 minutes)

Quickest path that touches every new surface:

1. Fresh browser → wait for seed → land on **Home** (grid of recipe tiles). (§1)
2. Skills tab → ⚙ → add OpenRouter key → save. (§6.3)
3. Home → tap a `cooking` tile → lands on Runs → provider prompt (reuse `_skills`) → ▶ run. (§2.1, §3.3)
4. Watch the **composition stepper** cycle through steps; once done, tap **Details** to confirm raw log still works. (§5)
5. Expand a done card → verify it renders with a **typed renderer** (table/schedule/reader), not raw JSON. Flip to Raw JSON and back. (§7)
6. Tap the **✎** in the project header → type a teaching → save → verify toast + patina. (§4)
7. Tap **Brain** → flip to **Recipes** mode → verify your cartridge cluster shows the teaching you just saved and the run you just did. (§8.3)
8. Simulate offline (DevTools Network → Offline) → verify banner appears. Restore online. (§9)
9. Back to Home → tap the dashed **Teach a Recipe** tile → enter an unmatched goal → go through the Forge ceremony end to end → see the **NEW RECIPE ACQUIRED** ribbon. (§2.3)
10. Skills tab → verify the newly-forged skill is in the list under the host cartridge. Run it. (§2.3)

If all ten steps pass, the recipe-framing surfaces are working.
