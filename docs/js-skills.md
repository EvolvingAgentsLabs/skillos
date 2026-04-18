# JS Skill Cartridges: Gallery Skills as Subagents

**Status**: v1 — experiment  
**Module**: `experiments/gemma4-skills/` + `cartridge_runtime.py`  
**Cartridge**: `cartridges/demo/`  
**Requires**: Node.js 18+, Python 3.11+

---

## What this is

JS Skill Cartridges let SkillOS run [Google AI Edge Gallery](https://github.com/google-ai-edge/gallery) JavaScript skills natively. Gallery skills are self-contained JS modules designed for on-device execution with Gemma 4 on Android. This bridge runs them via Node.js instead of an Android WebView, and extends them with capabilities Gallery doesn't have: persistent state, LLM sub-calls, skill chaining, and multi-flow modes.

A new cartridge type (`type: js-skills`) integrates with the existing CartridgeRunner infrastructure: Blackboard, JSON Schema validation, validators, evals, and intent routing all work identically.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  SkillOS REPL (skillos.py)                                   │
│                                                               │
│  skillos$ skill calculate-hash '{"text":"hello"}'   (direct) │
│  skillos$ cartridge demo "hash of hello"            (via LLM)│
└──────────────────────┬───────────────────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │  CartridgeRunner        │
          │  ┌──────────────────┐   │
          │  │  Blackboard      │   │
          │  │  user_goal ──────│───┼─→ param-extractor (LLM)
          │  │  skill_params ───│───┼─→ js-executor (Node.js)
          │  │  skill_result ◄──│───┼── validated result
          │  └──────────────────┘   │
          └─────────────────────────┘
                       │
          ┌────────────▼────────────┐
          │  Node.js runner.js      │
          │  ┌──────────────────┐   │
          │  │ Web API polyfills│   │  crypto.subtle, fetch,
          │  │ localStorage    │   │  localStorage (→ disk),
          │  │ __skillos.llm   │   │  btoa/atob, window/document
          │  └──────────────────┘   │
          │  eval(index.js)         │
          │  → ai_edge_gallery_get_result(data, secret)
          │  → JSON result to stdout│
          └─────────────────────────┘
```

---

## Skill format (Gallery standard)

Each skill is a directory:

```
skill-name/
├── SKILL.md              # YAML frontmatter + LLM instructions
├── scripts/
│   ├── index.html        # HTML entry point (loads index.js)
│   └── index.js          # JS implementation
└── assets/               # Optional: webview HTML, images, data
```

### SKILL.md

```yaml
---
name: calculate-hash
description: Calculate the hash of a given text.
metadata:
  require-secret: false          # true if skill needs an API key
  runtime: node                  # "node" (default) or "browser" (Playwright)
---

# Calculate hash
## Instructions
Call the `run_js` tool with:
- data: A JSON string with field `text`
```

### JS contract

Every skill exports one function:

```javascript
window['ai_edge_gallery_get_result'] = async (dataStr, secret) => {
  const input = JSON.parse(dataStr);
  // ... do work ...
  return JSON.stringify({ result: "the answer" });
};
```

**Return schema**: `{ result?, error?, webview?, image? }`

---

## Three flow modes

### 1. Deterministic (`run-skill`) — for small models

```yaml
flows:
  run-skill:
    - param-extractor    # LLM reads SKILL.md, extracts JSON params
    - js-executor        # Node.js runs the skill (no LLM)
```

The CartridgeRunner pre-selects the skill via keyword/LLM routing, injects SKILL.md instructions onto the Blackboard, and the param-extractor agent produces `skill_params`. The js-executor step runs deterministically.

**Best for**: `gemma4:e2b` and other small models that struggle with tool use.

### 2. Agentic (`agentic`) — for capable models

```yaml
flows:
  agentic:
    mode: agentic
```

The LLM gets `load_skill` and `run_js` as tools and decides autonomously which skill to use (or whether to skip skills entirely). Mirrors Gallery's Android implementation.

**Best for**: `gemma4:26b`, Gemini, Claude — models that handle multi-turn tool use.

### 3. Skill chaining (`research-pipeline`) — multi-step pipelines

```yaml
flows:
  research-pipeline:
    - skill: query-wikipedia
      needs: [user_goal]
      produces: [wiki_data]
    - skill: calculate-hash
      needs: [wiki_data]
      produces: [content_hash]
```

Each step is a JS skill with explicit `needs`/`produces`. The Blackboard passes data between steps. No LLM call needed — skills execute deterministically in sequence.

**Best for**: Composing multiple skills into pipelines. Gallery has no equivalent.

---

## `__skillos` runtime API

Every JS skill has access to `__skillos`, a runtime helper injected by `runner.js`:

### `__skillos.llm.chat(prompt, options?)`

Call the orchestrating Gemma 4 (or any configured LLM) for sub-reasoning:

```javascript
window['ai_edge_gallery_get_result'] = async (dataStr) => {
  const { topic } = JSON.parse(dataStr);

  // Fetch raw data
  const resp = await fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${topic}`);
  const wiki = await resp.json();

  // Ask Gemma 4 to analyze it
  const analysis = await __skillos.llm.chat(
    `Analyze this text and identify 3 key insights:\n\n${wiki.extract}`
  );

  return JSON.stringify({ result: analysis });
};
```

**Options**: `{ system, temperature, max_tokens }`

### `__skillos.llm.chatJSON(prompt, schema?)`

Like `chat()` but parses the response as JSON:

```javascript
const entities = await __skillos.llm.chatJSON(
  `Extract named entities from: "${text}"`,
  { type: "array", items: { type: "string" } }
);
```

### `__skillos.state.save(key, value)` / `__skillos.state.load(key)`

Persistent state separate from localStorage:

```javascript
__skillos.state.save("last_query", { topic, timestamp: Date.now() });
const prev = __skillos.state.load("last_query");
```

### `__skillos.runtime` / `__skillos.skillName`

Metadata: `"node"` or `"browser"`, and the current skill name.

---

## Persistent localStorage

When `SKILL_STATE_DIR` is set, localStorage persists to disk as `{skill-name}.json`. The CartridgeRunner sets this automatically to `cartridges/demo/state/`.

```
# First call
skillos$ skill mood-tracker '{"action":"log_mood","score":8}'
→ "Logged mood of 8/10 for 2026-04-18"

# Second call (new process) — state persists
skillos$ skill mood-tracker '{"action":"get_mood","date":"today"}'
→ "Your mood on 2026-04-18 was 8/10"
```

---

## REPL commands

```
skillos$ skills                                          # List all skills
skillos$ skill <name> '<json>'                           # Run directly (no LLM)
skillos$ skill calculate-hash '{"text":"hello world"}'
skillos$ skill mood-tracker '{"action":"get_history"}'

skillos$ cartridge demo "hash of hello world"            # Via LLM (deterministic)
skillos$ cartridge demo --flow agentic "hash of hello"   # Via LLM (agentic)
```

---

## Authoring a new JS skill

1. Create a directory under `cartridges/demo/skills/your-skill/`
2. Write `SKILL.md` with YAML frontmatter and LLM instructions
3. Create `scripts/index.html` (HTML wrapper) and `scripts/index.js`
4. Export `window['ai_edge_gallery_get_result']`
5. Test: `skillos$ skill your-skill '{"param":"value"}'`

Skills are compatible with Gallery's Android app — the same skill directory works in both environments.

### Using `__skillos.llm` to create a subagent skill

```javascript
// skills/summarizer/scripts/index.js
window['ai_edge_gallery_get_result'] = async (dataStr) => {
  const { url } = JSON.parse(dataStr);

  // Fetch content
  const resp = await fetch(url);
  const html = await resp.text();

  // Ask Gemma 4 to summarize
  const summary = await __skillos.llm.chat(
    `Summarize this webpage in 3 bullet points:\n\n${html.substring(0, 5000)}`,
    { temperature: 0.3, max_tokens: 500 }
  );

  return JSON.stringify({ result: summary });
};
```

This skill is a **subagent**: it fetches, reasons (via Gemma 4), and returns a synthesized result.

---

## Creating domain-specific skill cartridges

The `demo` cartridge bundles all 11 Gallery skills. For production, create focused domain cartridges:

```yaml
# cartridges/research/cartridge.yaml
name: research
type: js-skills
skills_source: skills    # local skills/ directory

entry_intents:
  - research topic
  - look up
  - summarize

flows:
  quick-lookup:
    - skill: query-wikipedia
      needs: [user_goal]
      produces: [wiki_data]
  
  deep-research:
    - skill: query-wikipedia
      needs: [user_goal]
      produces: [wiki_data]
    - skill: summarizer         # custom skill using __skillos.llm
      needs: [wiki_data]
      produces: [analysis]
```

Tighter `entry_intents` and fewer skills improve routing accuracy for small models.

---

## Compatibility with Gallery Android

| Feature | Gallery (Android) | SkillOS (Node.js) |
|---|---|---|
| Skill format | Same SKILL.md + scripts/ | Same |
| JS contract | `ai_edge_gallery_get_result` | Same |
| Web APIs | Full WebView | Polyfills (crypto, fetch, localStorage, btoa) |
| Canvas/WebAudio | Native | Playwright (optional) |
| UI rendering | Inline in chat | Opens in browser |
| State persistence | WebView-scoped | Disk-backed (survives restarts) |
| LLM sub-calls | Cloud API only | Local Ollama via `__skillos.llm` |
| Skill chaining | None | Blackboard pipelines |

Skills authored for one platform work on the other. SkillOS-specific features (`__skillos.llm`, persistent state, chaining) are additive — Gallery ignores them.

---

## File layout

```
experiments/gemma4-skills/
├── skill_loader.py         # SKILL.md parser + SkillRegistry
├── js_executor.py          # Python → Node.js bridge + RuntimeConfig
├── runner.js               # Node.js executor with polyfills + __skillos
├── test_skills.py          # 26 integration tests
├── ANALYSIS.md             # Architecture analysis
└── ANALYSIS_IMPROVEMENTS.md # Upgrade design document

cartridges/demo/
├── cartridge.yaml          # type: js-skills, 3 flow modes
├── router.md               # Skill classifier prompt
├── agents/
│   └── param-extractor.md  # Parameter extraction agent
├── flows/
│   └── run-skill.flow.md   # Flow documentation
├── skills/                 # 11 Gallery JS skills (self-contained)
│   ├── calculate-hash/
│   ├── query-wikipedia/
│   ├── mood-tracker/
│   └── ...
├── schemas/                # JSON Schemas for Blackboard
├── validators/             # Post-flow Python checks
├── evals/                  # Regression test cases
└── state/                  # Persistent skill state (localStorage)
```
