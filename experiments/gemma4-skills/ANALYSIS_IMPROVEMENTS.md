# Analysis: Improving SkillOS to Match Gallery's Power + JS Subagents

## What Gallery Actually Does That SkillOS Doesn't

After reading every skill implementation, the Gallery skill system is more
powerful than it appears on the surface. Three patterns stand out:

### 1. Skills That Call LLMs (restaurant-roulette)

```javascript
// restaurant-roulette/scripts/index.js — calls Gemini from JS
const response = await fetch(
  `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${API_KEY}`,
  { method: 'POST', body: JSON.stringify({
      contents: [{parts: [{text: prompt}]}],
      generationConfig: {
        responseMimeType: 'application/json',
        responseSchema: {type: 'ARRAY', items: {type: 'STRING'}}
      }
  })}
);
```

**This is a JS skill acting as a subagent** — it doesn't just compute, it reasons.
The skill constructs a prompt, calls an LLM, and post-processes the structured result.
The on-device Gemma 4 never sees this — the skill autonomously invoked a cloud LLM.

### 2. Skills With State (mood-tracker)

```javascript
// mood-tracker — persists data across calls via localStorage
const STORAGE_KEY = 'mood_tracker_data';
localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
// Next invocation reads the same data
const data = JSON.parse(localStorage.getItem(STORAGE_KEY));
```

Skills maintain memory between invocations. This is agent-like behavior —
the skill remembers what happened before and acts differently based on history.

### 3. Multi-Step Skills (mood-music)

```
LLM → run_js("mood-music", "get_genres.html", {})     → list of valid genres
LLM → (picks best genre from list)
LLM → run_js("mood-music", "index.html", {genre, ...}) → generated music track
```

The LLM orchestrates multiple calls to the same skill. The skill has two
entry points and the LLM must reason about intermediate results. This is
**LLM-orchestrated multi-step tool use** — a primitive form of subagent behavior.

### 4. Gallery's System Prompt Is a Skill Router

```kotlin
// AgentChatTaskModule.kt — the system prompt IS the skill framework
"""
For EVERY new task, you MUST execute these steps:
1. Find the most relevant skill from: ___SKILLS___
2. Use load_skill to read its instructions
3. Follow the skill's instructions exactly
"""
```

The LLM has full autonomy to decide WHICH skill to use and WHETHER to use one.
SkillOS's cartridge approach pre-decides this, which helps small models but
removes the LLM's ability to reason about skill selection.

---

## The Core Insight: JS Skills ARE Subagents

Gallery proves that a JS skill can:
- **Reason**: Call an LLM API and process the response (restaurant-roulette)
- **Remember**: Persist state across invocations (mood-tracker)
- **Multi-step**: Expose multiple entry points the LLM orchestrates (mood-music)
- **Fetch**: Call external APIs and synthesize results (query-wikipedia)

These are the four capabilities of an agent. The only thing Gallery skills
CAN'T do is call back to the host LLM (Gemma 4 on-device). But with Ollama
exposing Gemma 4 via HTTP API, **a JS skill running in SkillOS CAN call the
same Gemma 4 that's orchestrating it**.

This creates a recursive architecture:

```
Gemma 4 (orchestrator)
  → calls JS skill (subagent)
    → JS skill calls Gemma 4 via Ollama API (sub-reasoning)
    → JS skill processes response
    → JS skill returns structured result
  → Gemma 4 uses result to continue
```

---

## Improvement Plan: 5 Upgrades

### Upgrade 1: Persistent Skill State (localStorage)

**Problem**: SkillOS's runner.js creates a fresh `_storage = {}` per invocation.
Mood-tracker loses all data between calls.

**Solution**: Persist localStorage to disk, scoped per skill.

```javascript
// runner.js — load/save localStorage from a JSON file
const STATE_DIR = process.env.SKILL_STATE_DIR || '/tmp/skillos-skill-state';
const stateFile = path.join(STATE_DIR, `${skillName}.json`);

// On startup: load persisted state
if (fs.existsSync(stateFile)) {
  Object.assign(_storage, JSON.parse(fs.readFileSync(stateFile)));
}

// On exit: persist state
process.on('beforeExit', () => {
  fs.mkdirSync(STATE_DIR, { recursive: true });
  fs.writeFileSync(stateFile, JSON.stringify(_storage));
});
```

**Cartridge integration**: State dir lives under `cartridges/demo/state/` or
`projects/[Project]/state/skill-state/`. The CartridgeRunner passes it via env var.

**Impact**: mood-tracker, kitchen-adventure (if stateful) work correctly.
Future skills can maintain context across conversations.

---

### Upgrade 2: Agentic Skill Mode (LLM Decides)

**Problem**: SkillOS's cartridge rigidly pre-routes to a skill. The LLM never
gets to decide "this doesn't need a skill, I'll answer directly" or "I need
two skills for this".

**Solution**: Add an `agentic` flow mode alongside the cartridge flow.

```yaml
# cartridge.yaml
flows:
  run-skill:                  # Existing: deterministic 2-step
    - param-extractor
    - js-executor
  agentic:                    # NEW: LLM-driven skill selection
    mode: agentic             # Flag: LLM has full control
    tools:
      - load_skill            # LLM can load any skill's instructions
      - run_js                # LLM can execute any skill
      - direct_answer         # LLM can skip skills entirely

default_flow: agentic         # Use agentic by default with capable models
fallback_flow: run-skill      # Fall back to deterministic for e2b
```

**How it works**:
- For `tier: mid+` models (Gemma 4 26B, Gemini): use `agentic` flow.
  The LLM gets `load_skill` and `run_js` as tools (like Gallery's Android implementation)
  and decides autonomously.
- For `tier: low` models (Gemma 4 e2b): fall back to `run-skill` deterministic flow
  with pre-routing and cartridge guardrails.

**System prompt** (mirrors Gallery's approach):
```markdown
You have access to these skills:
- calculate-hash: Calculate the hash of a given text
- query-wikipedia: Query summary from Wikipedia
- ...

For each request:
1. Decide if a skill is needed
2. If yes, call load_skill to read its instructions
3. Follow the instructions to call run_js
4. Present the result to the user
```

**Impact**: SkillOS gains Gallery's agentic freedom for capable models while
keeping the guardrailed path for small models. Best of both worlds.

---

### Upgrade 3: JS Skills as LLM-Calling Subagents

**Problem**: Current skills are deterministic functions. Restaurant-roulette
calls the Gemini cloud API, but SkillOS skills can't call the LOCAL Gemma 4.

**Solution**: Inject the Ollama API URL into the JS runtime so skills can
call the same Gemma 4 that's orchestrating them.

```javascript
// runner.js — inject LLM endpoint as environment
const LLM_API_URL = process.env.LLM_API_URL || 'http://localhost:11434/v1';
const LLM_MODEL = process.env.LLM_MODEL || 'gemma4:e2b';
const LLM_API_KEY = process.env.LLM_API_KEY || 'ollama';

// Make available to skills
globalThis.__skillos = {
  llm: {
    url: LLM_API_URL,
    model: LLM_MODEL,
    apiKey: LLM_API_KEY,
    // Convenience function
    async chat(prompt, options = {}) {
      const resp = await fetch(`${LLM_API_URL}/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${LLM_API_KEY}`,
        },
        body: JSON.stringify({
          model: LLM_MODEL,
          messages: [{ role: 'user', content: prompt }],
          ...options,
        }),
      });
      const data = await resp.json();
      return data.choices[0].message.content;
    },
  },
};
```

**Example: A "research" skill that reasons**:

```javascript
// skills/deep-research/scripts/index.js
window['ai_edge_gallery_get_result'] = async (dataStr) => {
  const { topic } = JSON.parse(dataStr);

  // Step 1: Fetch from Wikipedia
  const wikiResp = await fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${topic}`);
  const wiki = await wikiResp.json();

  // Step 2: Ask Gemma 4 to analyze the content
  const analysis = await __skillos.llm.chat(
    `Analyze this Wikipedia extract about "${topic}" and identify 3 key insights:\n\n${wiki.extract}`
  );

  // Step 3: Return structured result
  return JSON.stringify({
    result: analysis,
    source: wiki.content_urls?.desktop?.page || '',
  });
};
```

**This JS skill IS a subagent**: it fetches data, reasons about it via Gemma 4,
and returns a synthesized result. The orchestrating Gemma 4 sees only the final
output — it doesn't know that another Gemma 4 call happened inside.

**Cartridge integration**: The `js-executor` step in CartridgeRunner passes
the Ollama config as environment variables:

```python
# In _run_js_skill():
env = {
    "LLM_API_URL": self.rt.client.base_url,
    "LLM_MODEL": self.rt.model,
    "LLM_API_KEY": self.rt.api_key,
    "SKILL_STATE_DIR": str(Path(manifest.path) / "state"),
}
result = exec_js(skill_def, data, secret, timeout=timeout, env=env)
```

**Impact**: Any Gallery-format skill can now call Gemma 4. This enables
skills that research, summarize, translate, classify — not just compute.
Skills become true subagents with reasoning capability.

---

### Upgrade 4: Skill Chaining via Blackboard

**Problem**: Gallery has zero skill-to-skill communication. Each skill runs
in isolation. SkillOS has the Blackboard but only uses it for the rigid
param-extractor → js-executor two-step flow.

**Solution**: Allow JS skills to read from and write to the Blackboard,
enabling multi-skill flows where one skill's output feeds the next.

**New cartridge flow type**: multi-skill pipeline.

```yaml
# cartridges/research/cartridge.yaml
name: research
type: js-skills

flows:
  deep-research:
    - skill: query-wikipedia      # JS skill: fetch data
      needs: [user_goal]
      produces: [wiki_extract]
    - skill: analyze              # JS skill: call Gemma 4 to analyze
      needs: [wiki_extract]
      produces: [analysis]
    - skill: format-report        # JS skill: format final output
      needs: [wiki_extract, analysis]
      produces: [report]
```

**How it works**: CartridgeRunner already has the Blackboard and the
needs/produces contract. The only change is that instead of a single
`param-extractor → js-executor` flow, we support N JS skill steps,
each reading from and writing to the Blackboard.

For each step:
1. CartridgeRunner bundles `needs` keys from Blackboard
2. Passes them as `data` to the JS skill
3. JS skill returns result
4. CartridgeRunner stores result under `produces` key on Blackboard
5. Next skill reads it

**No LLM call needed for routing** — the flow is declared in YAML.
The JS skills are deterministic (or call Gemma 4 internally as subagents).

**Impact**: SkillOS gains multi-skill pipelines that Gallery can't do.
A research cartridge could: fetch → analyze → summarize → format,
with each step being a JS skill that may or may not call Gemma 4.

---

### Upgrade 5: Headless Browser Option (Full Web API)

**Problem**: 5 of 11 Gallery skills require DOM/Canvas/WebAudio that
Node.js polyfills can't provide. UI-heavy skills simply don't work.

**Solution**: Optional Playwright-based executor for skills that need
full browser APIs.

```python
# js_executor.py — dual executor
def run_skill(skill, data, secret, *, timeout=30, env=None):
    if skill.requires_browser:
        return _run_in_playwright(skill, data, secret, timeout, env)
    else:
        return _run_in_node(skill, data, secret, timeout, env)
```

**Skill metadata extension**:
```yaml
# SKILL.md frontmatter
---
name: qr-code
description: Generate QR code
metadata:
  runtime: browser    # "node" (default) or "browser"
---
```

**For terminal output**: Even with Playwright, webview/image results need
rendering. Options:
- Save webview HTML to `output/` and print the path
- Convert images to terminal-compatible formats (sixel, kitty protocol)
- Save images as PNG files and print path
- Generate ASCII art fallback for simple visualizations

**Impact**: All 11 Gallery skills work. Skills like qr-code, interactive-map,
and virtual-piano produce file outputs. Playwright is optional — only
installed when browser-dependent skills are used.

---

## Can Gemma 4 e2b Support This?

### What e2b Needs To Do Per Upgrade

| Upgrade | e2b Role | Difficulty for e2b |
|---|---|---|
| 1. Persistent State | Nothing — state handled by runner.js | N/A (no LLM) |
| 2. Agentic Mode | Select skill + call load_skill + call run_js | Hard — falls back to deterministic |
| 3. JS Subagents | Nothing — JS skill calls Ollama directly | N/A (JS does it) |
| 4. Skill Chaining | Nothing — CartridgeRunner orchestrates | N/A (declarative) |
| 5. Headless Browser | Nothing — Playwright handles it | N/A (no LLM) |

**Key insight**: Upgrades 1, 3, 4, 5 require ZERO additional LLM capability.
They're infrastructure improvements that work identically on e2b and 26B.

Only Upgrade 2 (agentic mode) requires a capable model. For e2b, the fallback
to the deterministic cartridge flow is automatic.

**But Upgrade 3 is the game-changer**: When a JS skill calls Gemma 4 e2b
via Ollama, each sub-call is a fresh, single-turn prompt — exactly what e2b
is good at. The JS skill constructs a focused prompt like "Analyze this text
and return 3 insights" — no tool calling, no multi-turn reasoning, just
single-shot completion. e2b handles this reliably.

The pattern is:
```
Gemma 4 e2b (orchestrator) — needs cartridge guardrails, struggles with tools
  → JS skill (subagent framework) — deterministic orchestration in JS
    → Gemma 4 e2b (worker) — single-turn focused prompt, no tools needed
    → Gemma 4 e2b (worker) — another focused prompt
    → JS aggregates results
  → Structured result back to orchestrator
```

**JS becomes the reliable orchestration layer that compensates for e2b's
weakness at multi-turn tool use.** The JS skill can do what the LLM can't:
maintain state, chain API calls, validate intermediate results, retry on
failure — all deterministically. Each individual Gemma 4 call is simple
and focused.

---

## Architecture: JS Skill as Subagent (Full Pattern)

```
┌─────────────────────────────────────────────────────────┐
│  CartridgeRunner (Python)                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Blackboard                                      │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │    │
│  │  │user_goal │→ │wiki_data │→ │analysis  │→ ... │    │
│  │  └──────────┘  └──────────┘  └──────────┘      │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Flow: [query-wikipedia] → [analyze-skill] → [report]   │
│              │                    │                       │
│              ▼                    ▼                       │
│  ┌──────────────────┐  ┌───────────────────────┐        │
│  │  Node.js runner   │  │  Node.js runner        │       │
│  │  ┌──────────────┐ │  │  ┌─────────────────┐  │       │
│  │  │ fetch()      │ │  │  │ fetch(Ollama)    │  │       │
│  │  │ Wikipedia API│ │  │  │ Gemma 4 e2b     │  │       │
│  │  │ → extract    │ │  │  │ "Analyze this..." │  │      │
│  │  │ → return     │ │  │  │ → parse response │  │       │
│  │  └──────────────┘ │  │  │ → structured out │  │       │
│  │  result: {text}   │  │  └─────────────────┘  │       │
│  └──────────────────┘  │  result: {analysis}    │       │
│                         └───────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

**What each layer does**:
- **CartridgeRunner** (Python): Orchestration, Blackboard, schema validation, retry
- **JS Skill** (Node.js): Domain logic, API calls, LLM sub-calls, state
- **Gemma 4** (Ollama): Single-turn reasoning when the skill needs intelligence

**What Gallery can't do**: Chain skills through a Blackboard. Each Gallery
skill is isolated. SkillOS's Blackboard enables a research pipeline where
Wikipedia skill's output feeds into an analysis skill, which feeds into a
report skill — with schema validation at each step.

**What SkillOS couldn't do (before these upgrades)**: Let skills reason.
With Upgrade 3, any JS skill can call Gemma 4 for intelligent sub-tasks,
making it a true subagent rather than a deterministic function.

---

## Comparison After Upgrades

| Capability | Gallery | SkillOS (current) | SkillOS (with upgrades) |
|---|---|---|---|
| Full Web API | Yes (WebView) | No (polyfills) | Yes (Playwright option) |
| Persistent state | Yes (localStorage) | No | Yes (disk-backed) |
| LLM freedom | Yes (agentic) | No (pre-routed) | Yes (agentic mode + fallback) |
| Skills call LLM | Yes (cloud API) | No | Yes (local Ollama) |
| Skill chaining | No | No | Yes (Blackboard pipelines) |
| Schema validation | No | Yes | Yes |
| Retry on failure | No | Yes (1 retry) | Yes |
| Eval regression | No | Yes | Yes |
| Multi-provider | No (on-device only) | Yes | Yes |
| Subagent pattern | Accidental (cloud call) | No | First-class (JS + Ollama) |

**SkillOS with upgrades surpasses Gallery** in every dimension except
native mobile UI rendering (which is Android-specific and not a goal).

---

## Implementation Priority

| # | Upgrade | Effort | Impact | Why |
|---|---|---|---|---|
| 1 | Persistent State | Small (20 lines in runner.js) | Medium | Unlocks stateful skills |
| 3 | JS Skills as LLM Subagents | Medium (inject env + helper) | **Huge** | Skills become intelligent agents |
| 4 | Skill Chaining via Blackboard | Medium (extend cartridge flow) | **Huge** | Multi-skill pipelines |
| 2 | Agentic Mode | Medium (new flow type) | High | Gallery-style freedom |
| 5 | Headless Browser | Large (Playwright dep) | Low | Only for UI-heavy skills |

**Recommended order**: 1 → 3 → 4 → 2 → 5

Upgrades 1+3 are the foundation. Once skills can persist state AND call
Gemma 4, they become real subagents. Upgrade 4 then lets you chain them.
Upgrade 2 adds flexibility. Upgrade 5 is optional polish.
