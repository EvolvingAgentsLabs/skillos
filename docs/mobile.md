# SkillOS Mobile — Pure-JS Port

**Status**: v1 — experiment
**Module**: `mobile/` (Vite + Svelte 5 + TypeScript + Capacitor)
**Requires**: Node.js 18+ for building. Runs as a PWA in any modern browser; wraps for iOS/Android via Capacitor.

---

## What this is

SkillOS Mobile is a full-stack port of the SkillOS runtime to the browser. Every component that used to run on Python on a developer's workstation — Blackboard, CartridgeRegistry, CartridgeRunner, agent runtime, tool-call parser, Gallery skill executor, SmartMemory — now runs on the phone. The Python repo becomes an **authoring environment** for cartridges, schemas, validators, and skills; the mobile app is a **runtime** that executes them.

The "markdown is the program" principle is preserved intact. Every `cartridges/**/*.{md,yaml,schema.json}` file and `system/SmartMemory.md` ships verbatim as a static asset, seeds into IndexedDB on first boot, and is parsed at runtime by the same ajv / js-yaml / gray-matter-equivalent path that the desktop runtime uses.

---

## Why this matters

Three things a mobile port buys that the Python runtime cannot:

1. **On-device privacy.** Ollama over LAN from the user's laptop, or any OpenAI-compatible provider keyed per project. Prompts and outputs never touch a SkillOS server because there is no SkillOS server.
2. **Billions of devices.** Capacitor packages the same Svelte bundle as a native iOS / Android app with one command. The app stores its entire state (projects, blackboards, memory, secrets, seeded cartridges) in IndexedDB — works offline after the first launch.
3. **A visual representation of autonomous agent work.** The desktop runtime surfaces agent activity as streaming terminal text. On mobile the same runtime drives a three-lane Kanban per project — cards appear in *Planned*, slide into *In Execution*, land in *Done* as each agent's `<produces>{…}</produces>` validates. The user can see what the system is doing without reading log output.

---

## Architecture

```
Phone (self-contained after first boot)
├── Svelte 5 app (Vite-built PWA, Capacitor-wrapped for native)
│   ├── ProjectSwiper  → ProjectColumn → Lane → Card
│   ├── GoalComposer · ProviderSettingsSheet · SettingsSheet
│   ├── EvalsScreen · Onboarding · RunLogDrawer
│   └── Hidden sandboxed iframe (Gallery skill runtime)
│
├── IndexedDB  (via idb — schema v1)
│   ├── files        seeded markdown + user edits
│   ├── projects     per-project state snapshots
│   ├── blackboards  cartridge run outputs
│   ├── memory       SmartMemory experience log
│   └── secrets      provider keys + per-skill secrets
│
└── LLM client → OpenRouter · Gemini · Ollama (LAN, Capacitor only)
```

Below the UI layer the codebase mirrors the Python runtime one-for-one:

| Python module | TS port | Role |
|---|---|---|
| `cartridge_runtime.py:47-190` (Blackboard) | `mobile/src/lib/cartridge/blackboard.ts` | Typed KV store with pluggable validator |
| `cartridge_runtime.py:192-452` (Registry, frontmatter, flow parser) | `mobile/src/lib/cartridge/registry.ts` + `types.ts` | Loads cartridges from IndexedDB `files` |
| `cartridge_runtime.py:480-1274` (CartridgeRunner) | `mobile/src/lib/cartridge/runner.ts` | Standard / agentic / js-skills flows |
| `cartridges/cooking/validators/*.py` | `mobile/src/lib/cartridge/validators_builtin.ts` | TS siblings, registered by filename |
| `agent_runtime.py:68-108` (PROVIDER_CONFIGS) | `mobile/src/lib/llm/providers.ts` | OpenRouter / Gemini / Ollama configs |
| `agent_runtime.py:1055-1086` (_parse_tool_calls) | `mobile/src/lib/llm/tool_parser.ts` | All 5 dialects + repair + JSON extractor |
| `agent_runtime.py:1088-1235` (run_goal) | `mobile/src/lib/llm/run_goal.ts` | Multi-turn loop with FIFO compaction |
| `experiments/gemma4-skills/skill_loader.py` | `mobile/src/lib/skills/skill_loader.ts` | SKILL.md frontmatter parser |
| `experiments/gemma4-skills/runner.js` (Node) | `mobile/public/iframe/skill-host.js` | Browser-side: polyfills dropped, `__skillos` kept |
| `experiments/gemma4-skills/js_executor.py` (SkillResult) | `mobile/src/lib/skills/skill_result.ts` | Type + helpers |
| `system/SmartMemory.md` | `mobile/src/lib/memory/smart_memory.ts` | Append-only log with markdown round-trip |

The important thing: **no cartridge is rewritten**. The YAML manifests, agent markdown, JSON Schemas, and Gallery SKILL.md files that the Python runtime consumes are the same bytes the mobile app reads.

---

## Cross-cutting design decisions

### 1. The tool-call dialect is preserved

`agent_runtime.py`'s `_parse_tool_calls` recognizes five on-wire forms: `<tool_call name="x">{…}</tool_call>`, unclosed variants terminated at the next tag, bare `<tool_call>` with name inferred from keys, `<tool_call>\nname\n{…}\n</tool_call>`, and JSON arrays inside ```json fences. Every cartridge agent was authored against this dialect; Gemma and Qwen don't reliably emit OpenAI-style `tool_calls`. The TS port is verbatim so every cartridge runs unchanged.

### 2. Ollama over LAN is Capacitor-only

A PWA served over `https://` cannot `fetch()` `http://192.168.x.y:11434` — browsers block mixed content without override. Capacitor's native WebView exposes `android:usesCleartextTraffic="true"` plus a `network_security_config.xml` that permits cleartext only to RFC-1918 ranges; iOS takes `NSAppTransportSecurity.NSAllowsArbitraryLoadsInWebContent`. In pure-PWA mode the provider picker greys out *Ollama (LAN)* and surfaces only OpenRouter + Gemini. The shipped config fragments under `mobile/capacitor-resources/` are pre-written; the install step is "copy them into the native project after `cap add`."

### 3. Gallery skills run in a null-origin iframe

One long-lived hidden `<iframe>` at `mobile/public/iframe/skill-host.html`, sandboxed with `sandbox="allow-scripts"` **without** `allow-same-origin`. The iframe therefore has a null origin: it cannot read the app's IndexedDB, its localStorage, or its secrets.

The host loads the skill's JavaScript into the iframe via a Blob URL `<script>` tag — no `'unsafe-eval'` required, CSP `script-src 'self' blob:` is enough. The skill calls `window.ai_edge_gallery_get_result(data, secret)` exactly as on Gallery's Android app. LLM sub-calls from the skill (`__skillos.llm.chat/chatJSON`) proxy back to the host over `postMessage`, so the iframe never sees the real API key.

State persistence (`__skillos.state.save/load`) is replaced with a postMessage RPC to the host, which writes to IndexedDB under `skill-state/<name>`.

### 4. Live UI via Svelte 5 runes

`CartridgeRunner` takes an `onEvent(e)` callback; a single `run_events.svelte.ts` rune store pushes events (`run-start`, `step-start`, `llm-turn`, `tool-call`, `tool-result`, `blackboard-put`, `step-end`, `validator`, `run-end`). Components read `$derived` slices. Card lane transitions happen as side-effects of each event — no generators, no event-bus library, no Redux-shaped plumbing.

### 5. Validators port to TypeScript

The Python runtime can import `.py` files at runtime. Mobile cannot. The ~50 LOC of `cartridges/cooking/validators/*.py` are ported 1:1 to TS and registered by filename in `validators_builtin.ts`. When `manifest.validators` declares `menu_complete.py`, the TS runner resolves it to the TS implementation; the Python runner keeps using the `.py`. Both coexist; determinism is preserved on both sides.

### 6. Compaction is deferred

Full LLM-powered compaction (Python `compactor.py`) didn't make the first cut. The TS runner uses a tiny FIFO rule: when the conversation grows past 40 messages, drop the oldest `Tool '…' returned:` entries until back under. Good enough for single-run cartridge flows; insufficient for long-running agentic loops. Post-v1 work.

---

## Visual UX — the idea-storm made real

The original feature request observed that the Python runtime "has zero real visual representation of workflows" and proposed "horizontal project swiping combined with vertical lifecycle feeds." The mobile app implements exactly that:

```
┌─────────────────────────────────────────┐
│ SkillOS          · · ·             + │   ← app bar + page dots + new project
├─────────────────────────────────────────┤
│ Project: cooking-demo            ⚙ ▶  │   ← per-project header + run/settings
│ cooking                               +│
├──────────────────────────────────────── │
│ PLANNED                                 │
│   🎯 plan weekly meals                  │   ← Goal card
├──────────────────────────────────────── │
│ IN EXECUTION                            │
│   🤖 menu-planner   running…            │   ← Agent card (moves Planned→Exec on step-start)
│   🤖 shopping-list-builder  running…    │
├──────────────────────────────────────── │
│ DONE                                    │
│   📄 weekly_menu   menu-planner · 7s ago │  ← Document card (appears on blackboard-put ok)
│   📄 shopping_list shopping-list · 3s ago│
│   📄 recipes       recipe-writer · just │
├─────────────────────────────────────────┤
│ ● Running…   [streaming LLM log]       │   ← RunLogDrawer (sticky bottom)
└─────────────────────────────────────────┘
     ← swipe left/right for other projects →
```

Cards are polymorphic: 🎯 Goal, 🤖 Agent, 🧩 Skill, 📄 Document. Their colored left border encodes `kind`; lane position encodes lifecycle state; subtitle encodes origin + schema ref. Tap a card to expand; see the raw `<produces>` payload.

Horizontal swipe uses CSS `scroll-snap-type: x mandatory` + `scroll-snap-align: start`. One project per 100vw column. Overscroll is clipped with `overscroll-behavior: contain` so iOS rubber-band doesn't collide with snap.

---

## What the mobile port unlocks

### For the user
- **Run a real multi-agent cartridge from a phone.** Type "plan weekly meals for 2 adults, vegetarian" → swipe → watch three agents populate three lanes → end up with validated `weekly_menu` / `shopping_list` / `recipes` cards. The same flow that runs on the desktop, now reachable from anywhere with a browser.
- **Plug in your laptop's LLM.** Start `ollama serve` at home; install the Capacitor APK; point the app at `http://<laptop>:11434/v1`. Your phone becomes a frontend to whatever model fits in your GPU.
- **Stay entirely offline.** First launch seeds 8 MB of cartridges; every run after that needs only an LLM. With Ollama LAN, nothing leaves the house.
- **Export back to disk.** *Settings → Export to Files* writes the full state as markdown to `Documents/SkillOS/`; import rehydrates. Round-tripping between phone and desktop is a folder copy.

### For the project
- **Cartridges become a distribution format.** Ship a new cartridge (agents + schemas + validators + evals) and it runs identically on desktop Python and on mobile JS. No second implementation.
- **Gallery skills become first-class.** Google AI Edge Gallery's skill format is already the JS-skill contract the mobile app speaks. Any existing Gallery skill runs on SkillOS with no porting.
- **Evaluation is portable.** `cartridges/*/evals/cases.yaml` runs through the mobile evals screen against any configured provider. The same regression gate the desktop uses.
- **The skill sandbox story tightens.** Mobile's null-origin iframe + postMessage proxy is a harder boundary than anything the Python runtime can offer (pickles, dynamic imports, subprocess). The iframe pattern is a candidate to port *back* to desktop for defense-in-depth.

---

## Limitations (today)

- **No shell tools.** Mobile has no shell; any agent that needs `Bash`/`Read`/`Write` fails fast with a clear error. For cartridges that need filesystem access, author them as Gallery JS skills instead.
- **No `runtime: browser` (Playwright) skills.** The iframe is the browser runtime.
- **No LLM-powered compaction.** FIFO truncation only. Long agentic loops will eventually trim themselves in suboptimal ways.
- **Pure-PWA bundle size is ~100 KB gzipped.** Fine for a phone, but ajv + js-yaml dominate. A future pass could swap ajv for a smaller schema checker and tree-shake js-yaml.
- **iOS ATS.** `NSAllowsArbitraryLoadsInWebContent` is narrower than a global opt-out and accepted for dev-oriented apps, but App Store review may challenge it. Dev-install via Xcode is the guaranteed path.

---

## Potential

The interesting claim the implementation makes is that **SkillOS's domain layer (cartridges) can be framework- and runtime-agnostic**. Python runs them today; JavaScript runs the same bytes tomorrow. Swift or Kotlin could run them the day after. The cartridge manifests, schemas, and agent markdown are a neutral representation that multiple runtimes interpret.

That suggests a few directions worth exploring:

1. **Cartridge stores on the phone.** A small registry of community cartridges that a user installs by downloading the folder. No code review cycle for the OS itself — just for the cartridge.
2. **Peer-to-peer cartridge sharing.** `Settings → Export to Files` already emits the portable layout; a "share" button could zip a project + its cartridge and airdrop it. Another phone imports it and runs the same flow with its own provider.
3. **On-device-only small-model cartridges.** The Gemma cartridges (cooking, electrical, learn) are already designed for small models. Combined with Ollama, a single Capacitor build handles end-to-end execution with zero cloud calls. Latency becomes the only cost.
4. **Runtime as the product.** The Python runtime remains the authoring experience — claude-code, editor integration, shell tools. The mobile runtime is what end users install. The split is natural: authors use desktop; consumers use mobile.

The port is an experiment, not a replacement. But it validates a thesis the Python-only version couldn't: **the markdown-first architecture really does abstract over the runtime**.

---

## Verification

As of first merge:

- **76 passing tests** across 13 spec files (`seed`, `blackboard`, `registry` integration vs. real seeded cartridges, `project_store`, `tool_parser` all 5 dialects + repair, `llm_client` SSE streaming, `run_goal`, `skill_loader` integration vs. all 12 demo skills, `skill_host_bridge`, `validators_builtin`, `runner` full cooking flow end-to-end, `smart_memory`, `evals`).
- **`svelte-check` 0 errors on 363 files.**
- **Vite bundle 301 KB JS + 15 KB CSS** (gzipped 97 KB + 3 KB).
- **Seed pipeline 180 files / 8.08 MB** — 4 cartridges + Project_aorta + SmartMemory.md copied verbatim.

See [tutorial-mobile.md](tutorial-mobile.md) for the hands-on testing guide.
