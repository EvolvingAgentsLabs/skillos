# Experiment: gemma4-skills

## Goal

Bridge Google AI Edge Gallery's JavaScript skills with SkillOS's agent runtime,
enabling Gemma 4 (via Ollama `gemma4:e2b`) to discover, load, and execute
Gallery-format JS skills from Python — without requiring the Android app.

Introduce a new cartridge type — **JS Skill Cartridge** — that bundles Gallery
JS skills by domain, starting with a `demo` cartridge that includes all
available Gallery skills.

---

## Model: Gemma 4 e2b via Ollama

**Model**: `gemma4:e2b` — 12B parameter Q2 quantization  
**Source**: https://ollama.com/library/gemma4:e2b  
**VRAM**: ~7.2 GB — fits on free Google Colab T4 (16 GB) or any modern GPU  
**Provider config** (already in `agent_runtime.py`):

```python
"gemma": {
    "base_url": "http://localhost:11434/v1",
    "base_url_env": "OLLAMA_BASE_URL",
    "api_key_default": "ollama",
    "model": "gemma4",         # override with GEMMA_MODEL=gemma4:e2b
    "manifest": "GEMINI.md",
}
```

**Usage**:
```bash
ollama pull gemma4:e2b
GEMMA_MODEL=gemma4:e2b python agent_runtime.py --provider gemma interactive
```

**Why e2b**: Smallest quantization that runs anywhere. The JS skill execution
is deterministic (Node.js), so the LLM only needs to: (1) pick the right skill,
(2) extract parameters from natural language, (3) format a JSON call. These are
simple slot-filling tasks well within e2b's capabilities, especially inside the
cartridge's guardrailed structure.

**Tier**: `mid` → `cognitive_pipeline` strategy (recursive context isolation).

---

## Architecture Analysis

### Gallery Side (Source)

**Skill format** — each skill is a self-contained directory:

```
skill-name/
├── SKILL.md              # YAML frontmatter (name, description, metadata) + LLM instructions
├── scripts/
│   ├── index.html        # Minimal HTML wrapper that loads index.js
│   └── index.js          # JS implementation
└── assets/               # Optional UI files
```

**JS contract** — every skill exports one global function:

```javascript
window['ai_edge_gallery_get_result'] = async (dataStr, secret) => {
  // dataStr: JSON string with skill-specific parameters
  // secret: optional API key string
  // Returns: JSON string with { result?, error?, webview?, image? }
}
```

**Return schema**:
| Field | Type | Purpose |
|-------|------|---------|
| `result` | string | Text result returned to the LLM |
| `error` | string | Error message on failure |
| `webview` | `{url, iframe?, aspectRatio?}` | Embedded UI (Android-only) |
| `image` | `{base64}` | Image response |

**Available skills** (11 total):
- **Built-in**: calculate-hash, interactive-map, kitchen-adventure, mood-tracker, qr-code, query-wikipedia, send-email, text-spinner
- **Featured**: mood-music, restaurant-roulette, virtual-piano

**Android execution path**:
1. LLM calls `loadSkill(name)` tool → returns SKILL.md instructions
2. LLM calls `runJs(skillName, scriptName, data)` tool
3. Android loads `index.html` in a hidden WebView
4. Polls for `ai_edge_gallery_get_result` function (max 10s)
5. Calls it with `(data, secret)` → captures result via JS-to-Kotlin bridge
6. Returns result to LLM or renders webview/image

### SkillOS Side (Target)

**Runtime**: `agent_runtime.py` — provider-agnostic LLM engine supporting Gemma 4.

**Tool system**: Tools are defined in markdown manifests (GEMINI.md) as shell scripts
wrapped in XML `<tool_call>` tags. The runtime:
1. Parses `<tool_call name="...">` from LLM output
2. Dispatches to registered Python functions (`self.tools` dict)
3. Built-in tools: `write_file`, `read_file`, `list_files`, `web_fetch`, `google_search`, etc.

**Agent delegation**: `_handle_delegate_to_agent()` runs a mini agentic loop with
full tool access for sub-agents.

**Gemma 4 strategy**: `cognitive_pipeline` — recursive context isolation where each
step gets a fresh context window, bounded tool loop, and `<produces>` output contract.

**Cartridge system**: Domain-sealed agent bundles (cooking, electrical) with
deterministic routing + JSON Schema validation. Already proven with Gemma 4 26B.

---

## Cartridge Compatibility Analysis

### Existing Cartridge Architecture

```
cartridges/<name>/
├── cartridge.yaml          # manifest: entry_intents, flows, blackboard_schema, validators
├── router.md               # closed-set intent classifier (LLM picks flow)
├── agents/*.md             # narrow system prompts with needs/produces contracts
├── flows/*.flow.md         # ordered agent sequences
├── schemas/*.schema.json   # JSON Schemas for blackboard entries
├── validators/*.py         # deterministic post-flow Python checks
└── evals/cases.yaml        # regression test cases
```

**Execution flow**:
1. `CartridgeRegistry.match_intent(goal)` → keyword overlap router (no LLM)
2. `CartridgeRunner._select_flow(manifest, goal)` → LLM classifier or keyword fallback
3. For each agent in flow: delegate via `_handle_delegate_to_agent()` (LLM fills slots)
4. Agent output extracted via `<produces>{...}</produces>` → validated against JSON Schema
5. Result stored on Blackboard → next agent reads it
6. Post-flow: Python validators run deterministically

**Key insight**: In existing cartridges, **every step is an LLM call**. The LLM
generates structured output (JSON inside `<produces>` tags) that gets validated.

### JS Skill Cartridge: A Natural Extension

A JS Skill Cartridge is **simpler** than a regular cartridge because execution
is deterministic — the LLM only does parameter extraction, not content generation.

**Two-step flow per skill invocation**:

```
Step 1 (LLM):  user_goal → parameter-extractor agent → extracted_params
Step 2 (Node.js): extracted_params → JS executor → skill_result
```

Compare with regular cartridge:
```
Step 1 (LLM):  user_goal → agent-1 → structured_output_1
Step 2 (LLM):  structured_output_1 → agent-2 → structured_output_2
Step 3 (LLM):  structured_output_2 → agent-3 → structured_output_3
```

**The JS executor replaces the second LLM call** with a deterministic subprocess.
This is cheaper, faster, and more reliable than having Gemma generate the answer.

### Proposed JS Skill Cartridge Structure

```
cartridges/<name>/
├── cartridge.yaml          # manifest — SAME format, new `type: js-skills` field
├── router.md               # intent classifier → which skill to use
├── skills/                 # *** NEW: replaces agents/ for JS skills ***
│   ├── calculate-hash/     # Gallery skill directories (copied or symlinked)
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       ├── index.html
│   │       └── index.js
│   ├── query-wikipedia/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── index.html
│   └── ...
├── agents/                 # parameter-extractor agents (one per skill or shared)
│   └── param-extractor.md  # Generic: reads SKILL.md instructions, extracts params
├── flows/*.flow.md         # Two-step: extract-params → run-js
├── schemas/
│   ├── skill_params.schema.json    # { skill_name, data, secret? }
│   └── skill_result.schema.json   # { result?, error?, webview?, image? }
├── validators/
│   └── result_valid.py     # Checks result has no error field
└── evals/cases.yaml
```

### cartridge.yaml for the `demo` cartridge

```yaml
name: demo
type: js-skills                    # ← NEW: tells CartridgeRunner to use JS executor
description: >
  All Gallery JS skills bundled as a demo cartridge.
  Gemma 4 extracts parameters, Node.js executes deterministically.

skills_source: ../../gallery/skills  # path to Gallery skills (built-in + featured)

entry_intents:
  - calculate hash
  - hash of text
  - search wikipedia
  - query wikipedia
  - spin text
  - text spinner
  - mood tracker
  - track mood
  - restaurant roulette
  - find restaurant
  - qr code
  - generate qr

flows:
  run-skill:                       # Single universal flow
    - param-extractor              # LLM: reads SKILL.md, extracts JSON params
    - js-executor                  # Deterministic: Node.js runs the skill

default_flow: run-skill

blackboard_schema:
  skill_params: skill_params.schema.json
  skill_result: skill_result.schema.json

validators:
  - result_valid.py

max_turns_per_agent: 2             # param extraction is simple
```

### How It Extends CartridgeRunner

The `CartridgeRunner._run_agent()` method currently always calls
`_handle_delegate_to_agent()` (LLM). For JS skill cartridges, we add a
check: if the agent name is `js-executor`, call the Node.js runner instead.

```python
def _run_agent(self, manifest, agent_name, bb, *, retry_feedback=""):
    if manifest.type == "js-skills" and agent_name == "js-executor":
        return self._run_js_skill(manifest, bb)  # ← NEW deterministic path
    # ... existing LLM delegation path ...
```

This is a **minimal, backward-compatible extension**:
- Existing cartridges work exactly as before
- Only `type: js-skills` cartridges use the JS executor
- The JS executor step reuses the Blackboard and validation infrastructure
- Validators, schemas, evals — all work identically

### Why This Is Better Than Standalone Tools

| Approach | Pros | Cons |
|---|---|---|
| **Standalone tools** (`load_skill` + `run_js` in agent_runtime) | Simple, works with any provider | LLM must discover skills + format params in open-ended context. Gemma e2b may struggle |
| **JS Skill Cartridge** | Sealed routing, guardrailed params, schema validation, deterministic JS execution, reusable evals | Slightly more setup |

For Gemma 4 e2b specifically, the cartridge approach is superior because:
1. **Closed-set routing**: keyword router picks the skill — no LLM creativity needed
2. **Bounded param extraction**: SKILL.md instructions tell the LLM exactly what JSON to produce
3. **Schema validation + retry**: if Gemma misformats the JSON, it gets one structured retry
4. **Zero LLM calls for execution**: Node.js runs deterministically
5. **Eval regression**: `cases.yaml` catches regressions across model versions

---

## Integration Design

### Option A: Node.js Skill Runner (Recommended)

Replace the Android WebView execution with a Node.js runtime that:
1. Reads `SKILL.md` → parses YAML frontmatter → extracts instructions
2. Loads `scripts/index.js` in a Node.js context
3. Provides a minimal browser-like environment (`window`, `crypto`, `fetch`, `localStorage`)
4. Calls `ai_edge_gallery_get_result(data, secret)` and captures the JSON result
5. Integrates as a cartridge step OR standalone tools

**Why Node.js**: Gallery skills use Web APIs (crypto.subtle, fetch, localStorage, TextEncoder).
Node.js 18+ has native `fetch` and `crypto.subtle` via `globalThis.crypto`. A thin
polyfill layer covers `window`, `localStorage`, and `document` stubs.

### Option B: Python-only with Playwright/Pyppeteer

Run skills in a headless Chromium browser. Full Web API compatibility but heavy
dependency. Overkill for most skills.

### Option C: Deno Runtime

Full Web API compatibility out of the box. Lighter than Playwright but requires
Deno installation. Good alternative if Node.js polyfill becomes unwieldy.

---

## Implementation Plan

### Phase 1: Skill Loader (`skill_loader.py`)

```
Gallery skills dir ──► parse SKILL.md ──► SkillDefinition dataclass
                                           - name, description
                                           - instructions (for LLM)
                                           - require_secret, homepage
                                           - script_path (index.html/index.js)
                                           - assets_dir
```

- Scan a configured gallery skills directory
- Parse YAML frontmatter from SKILL.md
- Build a registry of available skills (like CartridgeRegistry)
- Provide `list_skills()` and `get_skill(name)` methods

### Phase 2: JS Executor (`js_executor.py` + `runner.js`)

```
SkillDefinition + data JSON + secret ──► Node.js subprocess ──► parsed result
```

- Create a Node.js wrapper script (`runner.js`) that:
  - Sets up `window`, `globalThis`, `crypto`, `fetch`, `localStorage` polyfills
  - Loads the skill's `index.js` via `require()` or dynamic import
  - Calls `ai_edge_gallery_get_result(data, secret)`
  - Prints JSON result to stdout
- Python side: `subprocess.run(["node", "runner.js", skill_path, data_json, secret])`
- Parse stdout JSON → `SkillResult` dataclass

### Phase 3: Demo Cartridge (`cartridges/demo/`)

Create the first JS Skill Cartridge:

```
cartridges/demo/
├── cartridge.yaml              # type: js-skills, all Gallery skills
├── router.md                   # "Given these skills, pick one"
├── skills/                     # symlink or copy of Gallery skills
│   ├── calculate-hash/
│   ├── query-wikipedia/
│   ├── text-spinner/
│   ├── mood-tracker/
│   ├── qr-code/
│   ├── kitchen-adventure/
│   ├── mood-music/
│   ├── restaurant-roulette/
│   ├── send-email/
│   ├── interactive-map/
│   └── virtual-piano/
├── agents/
│   └── param-extractor.md      # Generic agent: reads SKILL.md → produces params
├── flows/
│   └── run-skill.flow.md       # param-extractor → js-executor
├── schemas/
│   ├── skill_params.schema.json
│   └── skill_result.schema.json
├── validators/
│   └── result_valid.py
└── evals/
    └── cases.yaml
```

### Phase 4: CartridgeRunner Extension

Extend `cartridge_runtime.py` to handle `type: js-skills`:

```python
# In CartridgeManifest dataclass:
type: str = "standard"           # "standard" (LLM agents) or "js-skills"
skills_source: str = ""          # path to Gallery skills directory

# In CartridgeRunner._run_agent():
if agent_name == "js-executor":
    params = bb.value("skill_params")
    result = js_executor.run(
        skill_name=params["skill_name"],
        data=params["data"],
        secret=params.get("secret", ""),
        skills_dir=manifest.skills_dir,
    )
    bb.put("skill_result", result, ...)
    return StepResult(validated=True, ...)
```

### Phase 5: Standalone Tools (Optional Fallback)

Also register `load_skill` and `run_js` as agent runtime tools for
open-ended use outside cartridges (with larger models like Gemma 26B or Gemini).

---

## End-to-End Flow: Demo Cartridge with gemma4:e2b

```
User: "What's the hash of hello world?"

1. skillos.py REPL receives goal
2. CartridgeRegistry.match_intent("hash of hello world")
   → matches "demo" cartridge (keyword: "hash")
3. CartridgeRunner._select_flow()
   → "run-skill" (only flow)
4. Step 1: param-extractor agent (LLM call)
   - System prompt: param-extractor.md
   - Injects: list of available skills with descriptions
   - Gemma 4 e2b reads skill descriptions, picks "calculate-hash"
   - Reads calculate-hash SKILL.md instructions
   - Produces: <produces>{"skill_name": "calculate-hash", "data": "{\"text\": \"hello world\"}"}</produces>
   - Validated against skill_params.schema.json
   - Stored on Blackboard as "skill_params"
5. Step 2: js-executor (deterministic — NO LLM call)
   - Reads skill_params from Blackboard
   - Calls: node runner.js calculate-hash/scripts/index.js '{"text":"hello world"}'
   - Node.js executes crypto.subtle.digest('SHA-1', ...)
   - Returns: {"result": "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed"}
   - Validated against skill_result.schema.json
   - Stored on Blackboard as "skill_result"
6. Validators: result_valid.py checks no "error" field
7. CartridgeRunner renders summary → returned to user

Output: "The SHA-1 hash of 'hello world' is 2aae6c35c94fcfb415dbe95f408b9ce91ee846ed"
```

**LLM calls**: 1 (param extraction only)  
**Cost**: ~$0.001 with Ollama (local) or ~$0.002 via OpenRouter  
**Reliability**: High — deterministic execution, schema-validated params  

---

## Domain Cartridge Examples (Future)

The `demo` cartridge bundles everything. Future cartridges can subset by domain:

| Cartridge | Skills | Use Case |
|---|---|---|
| `demo` | All 11 Gallery skills | Testing, showcase |
| `research` | query-wikipedia, calculate-hash | Knowledge tasks |
| `food` | restaurant-roulette, kitchen-adventure | Dining decisions |
| `productivity` | mood-tracker, send-email, qr-code | Personal tools |
| `creative` | text-spinner, mood-music, virtual-piano | Entertainment |

Each domain cartridge has tighter `entry_intents` and a more focused router,
which improves routing accuracy for smaller models like e2b.

---

## Compatibility Matrix

| Gallery Skill | Web APIs Used | Node.js Compatible? | Notes |
|---|---|---|---|
| calculate-hash | crypto.subtle, TextEncoder | Yes (native) | Pure computation |
| query-wikipedia | fetch | Yes (native in Node 18+) | Network required |
| text-spinner | None (pure JS) | Yes | Pure computation |
| qr-code | Canvas? | Needs polyfill | May need `canvas` npm pkg |
| mood-tracker | localStorage | Needs polyfill | Stateful |
| send-email | URLScheme | N/A | Android-only (mailto:) |
| interactive-map | DOM/Leaflet | N/A | UI-only skill |
| kitchen-adventure | DOM? | TBD | May be UI-heavy |
| mood-music | Spotify API? | Likely yes | Network + secret |
| restaurant-roulette | fetch (Gemini API) | Yes | Network + secret |
| virtual-piano | Web Audio | N/A | UI-only skill |

**Viable for Phase 1**: calculate-hash, query-wikipedia, text-spinner, restaurant-roulette  
**Requires polyfills**: mood-tracker (localStorage), qr-code (canvas)  
**UI-only (result-only in terminal)**: interactive-map, virtual-piano, send-email  

---

## Success Criteria

1. `GEMMA_MODEL=gemma4:e2b python agent_runtime.py --provider gemma "Calculate the hash of 'hello world'"`
   routes through demo cartridge → param-extractor → js-executor → returns SHA-1 hash
2. `query-wikipedia` skill works end-to-end with Gemma 4 e2b
3. `cartridges` command in skillos REPL lists `demo` alongside `cooking` and `residential-electrical`
4. `cartridge demo "hash of test123"` works from the REPL
5. Demo cartridge passes eval regression suite (`evals/cases.yaml`)
6. No Android dependency — runs entirely in Python + Node.js + Ollama

---

## Files to Create

```
experiments/gemma4-skills/
├── ANALYSIS.md                     # This document
├── skill_loader.py                 # Gallery SKILL.md parser + registry
├── js_executor.py                  # Node.js skill runner (Python wrapper)
├── runner.js                       # Node.js script that executes Gallery JS skills
├── test_skills.py                  # Integration tests

cartridges/demo/                    # First JS Skill Cartridge
├── cartridge.yaml                  # type: js-skills manifest (skills_source points to gallery)
├── router.md                       # Skill classifier prompt
├── agents/
│   └── param-extractor.md          # Generic parameter extraction agent
├── flows/
│   └── run-skill.flow.md           # param-extractor → js-executor
├── schemas/
│   ├── skill_params.schema.json    # { skill_name, data, secret? }
│   └── skill_result.schema.json    # { result?, error?, webview?, image? }
├── validators/
│   └── result_valid.py             # Checks result has no error field
└── evals/
    └── cases.yaml                  # Regression tests
```

**Modified files**:
- `cartridge_runtime.py` — add `type` field to CartridgeManifest, JS executor path in `_run_agent()`
- `agent_runtime.py` — optional: register `load_skill`/`run_js` as standalone tools

---

## Key Insights

### 1. Gallery skills ARE tools, not agents

The Gallery skill format is a **tool contract**: the LLM gets instructions
(SKILL.md) telling it what parameters to pass, and the JS function is a
deterministic executor. This maps perfectly to the cartridge model where
the LLM fills structured slots and a deterministic step executes.

### 2. JS Skill Cartridges are simpler than regular cartridges

Regular cartridges: LLM → LLM → LLM (each agent is an LLM call)  
JS Skill Cartridges: LLM → Node.js (one LLM call + one deterministic call)

Fewer LLM calls = cheaper, faster, more reliable. The cartridge guardrails
(router, schema, validators) still apply, making even gemma4:e2b reliable.

### 3. The Blackboard is the bridge

The Blackboard typed KV store naturally carries `skill_params` from the
LLM step to the JS executor step, and `skill_result` back. No new
infrastructure needed — just a new step type.

### 4. Domain cartridges improve small-model accuracy

By subsetting skills into domain cartridges (research, food, productivity),
the router has fewer options to classify and the param-extractor has fewer
skill descriptions to scan. This directly improves accuracy for e2b.
