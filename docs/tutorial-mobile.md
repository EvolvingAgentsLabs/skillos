# Tutorial — Testing SkillOS Mobile

End-to-end walkthrough for exercising the `mobile/` app locally: dev server in a browser, real cartridge run with a cloud provider, Capacitor Android build with LAN Ollama, and round-trip file sync back to the desktop Python runtime.

Estimated time: 20 min for the browser path, 90 min including the first Capacitor build.

---

## Prerequisites

| What | Version | Notes |
|---|---|---|
| Node.js | 18 LTS or 20 LTS | Needed to build the web bundle and run tests |
| Python (optional) | 3.11+ | Only for the round-trip-to-desktop section |
| Ollama (optional) | latest | Only for the LAN-LLM section. `ollama pull gemma2:2b` works on most laptops |
| Android Studio (optional) | latest | For the Capacitor APK build |
| Xcode (optional) | latest | For the iOS build |
| OpenRouter or Gemini API key | — | Easiest provider for the pure-PWA path |

You do not need Android Studio / Xcode to complete the browser tests — they are only required for packaging to a real phone.

---

## 1. Install + build

```bash
git clone https://github.com/EvolvingAgentsLabs/skillos.git
cd skillos/mobile
npm install              # ~1 min
```

### Smoke check

```bash
npm test                 # runs 76 tests across 13 spec files
```

Expected output: `Test Files 13 passed · Tests 76 passed`.

### Production build

```bash
npm run build
```

This runs three things in sequence:

1. `scripts/seed-build.mjs` — walks `../cartridges`, `../projects/Project_aorta`, `../system/SmartMemory.md` and writes `public/seed/` + `manifest.json`. Expect "wrote 180 files (8.08 MB)".
2. `svelte-check` — type-checks every `.ts` / `.svelte` file. Expect `0 ERRORS 0 WARNINGS`.
3. `vite build` — emits `dist/index.html` + one JS + one CSS chunk.

Bundle size should be around 300 KB JS (97 KB gzipped) + 15 KB CSS (3 KB gzipped).

### Optional: all cartridges + all projects in the seed

By default the seed includes every cartridge but only `Project_aorta` as an example project (to keep the download small). To include every project folder:

```bash
node scripts/seed-build.mjs --all-projects
```

Or whitelist specific ones:

```bash
node scripts/seed-build.mjs --projects=Project_aorta,Project_echo_q
```

---

## 2. Browser test — pure PWA + cloud provider

The fastest way to see the app running against a real LLM. Works on any laptop browser; no phone required.

```bash
cd skillos/mobile
npm run dev              # Vite dev server on http://localhost:5173
```

1. Open `http://localhost:5173` in Chrome (or open DevTools → Toggle device toolbar to emulate a phone).
2. Watch the splash: *"Seeding 180 / 180 files…"*. Takes ~2s on a laptop.
3. Swiper lands empty. Top-left is the **SkillOS** brand button (tap for app settings), top-right is **+** (new project). Three dots in the middle are the pager indicator.
4. Tap **+**. In the bottom sheet:
    - *Name*: `Sunday menu`
    - *Cartridge*: `cooking`
    - *Initial goal*: `Plan weekly meals for 2 adults, vegetarian`
    - **Create**
5. A full-screen project column appears with a 🎯 **Goal** card in the **Planned** lane.
6. Tap the ⚙ in the column header. The provider bottom sheet opens:
    - *Provider*: `OpenRouter · Qwen` (or `Google · Gemini`)
    - *API key*: paste your key
    - *Model*: leave blank to use the default (`qwen/qwen3.6-plus:free`)
    - **Save**
7. Tap **▶ run**.

What you should see:

- The 🎯 Goal card slides to **In Execution**.
- A 🤖 **menu-planner** card appears in **In Execution** with subtitle "running…".
- The **Run log drawer** at the bottom streams LLM tokens live.
- After menu-planner finishes, a 📄 **weekly_menu** card lands in **Done** (if the schema validated) and the menu-planner card moves to **Done**.
- Same sequence for 🤖 **shopping-list-builder** → 📄 **shopping_list**, then 🤖 **recipe-writer** → 📄 **recipes**.
- When the run ends: both cooking validators fire (`menu_complete.py`, `shopping_list_sane.py`) and report `ok [...]:`.
- The 🎯 Goal card finally moves to **Done**.

Tap any 📄 card to expand — the full JSON produced by the agent is displayed inline. Tap a 🤖 card to see the full assistant transcript.

### If it fails

- **401 / 403 from the provider** — key invalid. Tap ⚙ and re-enter.
- **`no <produces>{...}</produces> JSON block found`** — the model returned prose instead of the structured contract. Free-tier Qwen sometimes does this; retry once, or switch to Gemini.
- **Schema violation** — the model produced well-formed JSON but it didn't satisfy `weekly_menu.schema.json` (e.g. missing `prep_minutes`). The runner's retry-with-feedback kicks in once; if both attempts fail, you'll see the ⚠️ lane marker and the validator fallback message.
- **Request blocked** — check the browser console. If it mentions CORS, your provider may require an `HTTP-Referer` header; the `openrouter-*` providers set this automatically.

### Optional: test a Gallery JS skill directly

Create a new project with cartridge `demo`, then run it with the goal `hash the word hello`. The demo cartridge's router picks `calculate-hash`, the param-extractor agent extracts `{"text": "hello"}`, and the iframe executes the skill deterministically. You should see a 📄 **skill_result** card in Done with `{"result": "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d", …}`.

---

## 3. Evals harness

Runs every cartridge's `cases.yaml` through the mobile runner end-to-end against your configured provider.

1. From any project, tap the **SkillOS** brand in the top-left.
2. *Settings → Run cartridge evals…*
3. **Run all**.

What you see: a row per case with ✓/✗, assertion diffs for failures, total pass count. A typical clean run on OpenRouter Qwen completes all cooking + electrical cases in about a minute.

---

## 4. Capacitor Android build (LAN Ollama)

This is the path that unlocks on-device Ollama. Requires Android Studio and a device on the same wifi as a laptop running `ollama serve`.

### 4.1 Add the Android platform (one time)

```bash
cd skillos/mobile
npm run build                                  # produces dist/
npx cap add android                            # scaffolds android/
```

### 4.2 Wire up cleartext for LAN

The config is pre-written under `capacitor-resources/`. Copy the files into the native project:

```bash
mkdir -p android/app/src/main/res/xml
cp capacitor-resources/android/network_security_config.xml \
   android/app/src/main/res/xml/
```

Open `android/app/src/main/AndroidManifest.xml` and add to the `<application …>` tag:

```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    android:usesCleartextTraffic="true"
    ... >
```

(The first is the whitelist for RFC-1918 ranges; the second enables cleartext globally in the WebView. `networkSecurityConfig` narrows it back down so only LAN traffic is cleartext.)

### 4.3 Push + run

```bash
npx cap sync android
npx cap open android            # opens Android Studio
```

In Android Studio: plug in the phone (USB debugging on), press ▶. The APK installs and launches.

### 4.4 Verify Ollama LAN reachability

On the laptop:

```bash
ollama serve                    # default port 11434
ollama pull gemma2:2b
```

Note the laptop's LAN IP (e.g. `192.168.1.42`). Also ensure Ollama accepts external connections:

```bash
# Linux / macOS
OLLAMA_HOST=0.0.0.0 OLLAMA_ORIGINS='*' ollama serve

# Windows (PowerShell)
$env:OLLAMA_HOST = "0.0.0.0"
$env:OLLAMA_ORIGINS = "*"
ollama serve
```

In the phone app:

1. Create a project (any cartridge).
2. ⚙ → *Provider*: `Ollama (LAN)`. (Greyed out on pure-PWA browsers — enabled here because you're in a Capacitor WebView.)
3. *Base URL*: `http://192.168.1.42:11434/v1`
4. *Model*: `gemma2:2b`
5. **Save → ▶ run**

You should see the same three-lane animation as in the browser test, but every token is generated on your laptop's GPU. Response latency is whatever Ollama reports locally — typically 1–3 tokens/sec on CPU-only, 20+ on GPU.

### 4.5 iOS build (sketch)

```bash
npx cap add ios
npx cap open ios                # Xcode opens ios/App/App.xcworkspace
```

In Xcode: open `Info.plist` and merge the keys from `capacitor-resources/ios/Info.plist.fragment`. Set the signing team, plug in an iPhone, press ▶.

ATS caveat: `NSAllowsArbitraryLoadsInWebContent = true` is dev-friendly but Apple may challenge it on App Store review. Dev-install via Xcode is the guaranteed path.

---

## 5. Round-trip to the desktop Python runtime

Works only from the Capacitor builds — pure-PWA browsers can't write to `Documents/`.

### Export

1. Run a cartridge end-to-end so you have a populated project + SmartMemory entries.
2. Top-left brand → **Settings → Export to Files…**.
3. The status line reports `exported N files → DOCUMENTS/SkillOS`.

On Android that's typically `/storage/emulated/0/Documents/SkillOS/`; on iOS it's the app's scoped Documents folder (accessible via the Files app).

### Inspect on desktop

Pull the folder over USB or cloud sync, drop it next to your `skillos/` checkout, and inspect:

```
Documents/SkillOS/
├── cartridges/**/       (every seeded cartridge file)
├── projects/
│   └── Sunday_menu/
│       ├── state/pipeline_state.md
│       └── cards/
│           ├── card_<id1>.md    (Goal)
│           ├── card_<id2>.md    (Agent)
│           └── …
└── system/SmartMemory.md
```

The `pipeline_state.md` frontmatter mirrors `projects/Project_aorta/state/pipeline_state.md`'s shape: `project`, `cartridge`, `status`, `stages: [{name, agent, status, output}, …]`.

The `SmartMemory.md` file is rendered with the same YAML frontmatter as the desktop runtime's log — `experience_id`, `timestamp`, `session_id`, `project`, `goal`, `outcome`, `components_used`, `quality_score`, `cost_estimate_usd`, `duration_seconds`, plus `## Output Summary` and `## Learnings` sections if present.

### Import

To sync desktop edits back onto the phone: place the modified files anywhere under `Documents/SkillOS/` on the device, then **Settings → Import from Files…**. The walker loads every `.md`/`.yaml`/`.json`/`.js` back into IndexedDB. (Projects stored in the `projects` object store are not overwritten — only the `files` store refreshes. To reset projects, delete them from the UI first.)

---

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Splash screen stalls at "Fetching seed manifest…" | `public/seed/manifest.json` missing | `npm run seed` and reload |
| Build fails with "Conversion of type 'Record<…>' to type 'SkillWebview'" | Stale local build | `rm -rf node_modules dist && npm install && npm run build` |
| `fake-indexeddb` not found in tests | Didn't run `npm install` after adding deps | `npm install` |
| LAN Ollama reachable from laptop browser but not from phone | `OLLAMA_HOST` not set to `0.0.0.0`, or phone on different wifi | see §4.4 |
| Skill iframe logs "script load failed" in console | iOS WKWebView + sandbox + Blob quirk | Rebuild with the `srcdoc=` fallback (toggle in `skill-host.js`) — filed as a future follow-up |
| `svelte-check` warns about `context="module"` | Using an older copy of `RunLogDrawer.svelte` | Pull latest — v1 uses the new `<script module>` attribute |
| Evals screen says "No provider configured" | Haven't visited any project's ⚙ yet | Open ⚙ on any project, save settings once |

### Logs and inspection

- **DevTools console** — every `console.warn`/`error` from the app, plus iframe `[skill:<name>] …` forwarded logs.
- **Run log drawer** — streaming LLM deltas, tool calls, validator results.
- **IndexedDB** — Chrome DevTools → Application → IndexedDB → `skillos` → `files` / `projects` / `memory`. Everything the app writes is inspectable.
- **Settings → Resync from bundle** — nukes `meta.seed_version` and re-pulls `/public/seed/**`. Useful after editing cartridge files in the repo.

---

## 7. What to test before shipping

A minimal pre-release checklist:

- [ ] `npm test` — 76/76 pass
- [ ] `npm run build` — `0 ERRORS 0 WARNINGS` from svelte-check
- [ ] Browser: create + run a `cooking` project end-to-end against OpenRouter
- [ ] Browser: run `demo` cartridge → `calculate-hash` produces the expected SHA-1
- [ ] Browser: *Settings → Run cartridge evals* → all cases for `cooking` pass (allow for flaky assistant turns — rerun if needed)
- [ ] Capacitor Android: install APK, reach LAN Ollama, run `cooking` successfully
- [ ] Capacitor Android: Export to Files → the markdown tree on `Documents/SkillOS/` matches the desktop layout
- [ ] App survives background / foreground cycling mid-run

That's the full circuit. File issues against the repo if any step diverges.
