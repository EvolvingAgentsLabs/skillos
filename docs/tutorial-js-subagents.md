# Tutorial: Building JS Subagents with Gemma 4

This tutorial builds a **Research & Learn** system that demonstrates
everything SkillOS's JS skills can do that Gallery's Android implementation cannot.
By the end, you'll have a 4-skill pipeline where JavaScript skills fetch data,
call Gemma 4 for analysis, store knowledge persistently, and generate quizzes
— all chained through a typed Blackboard.

**What you'll build:**

```
"Learn about Albert Einstein"
    ↓
[1] query-wikipedia     → fetch Wikipedia article      (Gallery skill, no LLM)
    ↓
[2] insight-extractor   → Gemma 4 analyzes the text    (JS subagent, 1 LLM call)
    ↓
[3] knowledge-tracker   → stores insights to disk      (persistent state)
    ↓
"Quiz me on Einstein"
    ↓
[4] quiz-generator      → Gemma 4 creates questions    (reads stored knowledge + LLM)
```

**What Gallery cannot do** (and why this matters):

| Capability | Gallery | This tutorial |
|---|---|---|
| Skill calls local LLM | No | Steps 2 and 4 call Gemma 4 via Ollama |
| State persists across sessions | No | Step 3 saves to disk, step 4 reads it back |
| Skills chain through shared state | No | 4 skills connected via Blackboard |
| Cross-skill data sharing | No | quiz-generator reads knowledge-tracker's data |

---

## Prerequisites

```bash
# Node.js 18+ (for running JS skills)
node --version   # v18.x or higher

# Ollama with Gemma 4 (for LLM subagent calls)
ollama pull gemma4:e2b

# Python dependencies
pip install openai python-dotenv pyyaml rich
```

---

## Part 1: Run the Gallery skill standalone

First, verify the existing Gallery skill works in SkillOS:

```bash
cd skillos

# List available skills
python skillos.py
# Then type: skills

# Run calculate-hash directly (no LLM needed)
# Type: skill calculate-hash '{"text":"hello world"}'
# → 2aae6c35c94fcfb415dbe95f408b9ce91ee846ed

# Run query-wikipedia
# Type: skill query-wikipedia '{"topic":"Albert Einstein","lang":"en"}'
# → Einstein's Wikipedia summary
```

This is what Gallery can already do. Now let's go beyond.

---

## Part 2: Understand the learn cartridge

Open `cartridges/learn/cartridge.yaml`. The key structure:

```yaml
name: learn
type: js-skills        # ← enables JS skill execution via Node.js

flows:
  learn:               # Full pipeline: fetch → analyze → store
    - skill: query-wikipedia
      needs: [user_goal]
      produces: [wiki_data]

    - skill: insight-extractor
      needs: [wiki_data, user_goal]
      produces: [insights]

    - skill: knowledge-tracker
      needs: [user_goal, insights]
      produces: [store_result]
      data_map:                    # ← remap Blackboard keys to skill params
        topic: user_goal
        insights: insights
      defaults:                    # ← inject default values
        action: store
```

**Three things that are new vs Gallery:**

1. **`needs`/`produces`** — Each skill declares what Blackboard keys it reads and writes. The CartridgeRunner chains them automatically.

2. **`data_map`** — Remaps Blackboard key names to the parameter names the skill expects. `user_goal` on the Blackboard becomes `topic` in the skill's data JSON.

3. **`defaults`** — Injects constant values. `action: store` tells the knowledge-tracker to store data, not query it.

---

## Part 3: The subagent skill — insight-extractor

Open `cartridges/learn/skills/insight-extractor/scripts/index.js`:

```javascript
window['ai_edge_gallery_get_result'] = async (dataStr) => {
  const input = JSON.parse(dataStr);
  const text = input.text || input.wiki_data || '';
  const topic = input.topic || input.user_goal || 'this topic';

  // THIS IS THE KEY DIFFERENTIATOR
  // A Gallery skill can't do this — calling the LOCAL model
  const insights = await __skillos.llm.chatJSON(
    `Analyze this text about "${topic}" in depth. Extract:
     1. A one-paragraph summary
     2. Exactly 5 key facts
     3. 3 connections to related topics
     ...
     Text: ${text.substring(0, 4000)}`,
    null,
    { temperature: 0.2 }
  );

  return JSON.stringify({ result: JSON.stringify(insights) });
};
```

**`__skillos.llm.chatJSON()`** calls Gemma 4 e2b via the Ollama API. The JS
skill constructs a focused prompt, gets structured JSON back, and enriches it
with metadata. This is a **subagent** — it fetches, reasons, and synthesizes.

Gallery's restaurant-roulette does something similar with a cloud Gemini API call,
but it can't call the *on-device* model. SkillOS skills call the same Gemma 4
that's orchestrating them.

### Without LLM (graceful fallback)

If Ollama isn't running, the skill falls back to basic heuristic extraction:

```javascript
if (!__skillos || !__skillos.llm || !__skillos.llm.available) {
  return JSON.stringify({
    result: JSON.stringify({
      topic: topic,
      method: 'heuristic (no LLM available)',
      key_facts: extractBasicFacts(text),   // sentence extraction
    })
  });
}
```

The pipeline works either way — just with better insights when Gemma is available.

---

## Part 4: Persistent knowledge — knowledge-tracker

Open `cartridges/learn/skills/knowledge-tracker/scripts/index.js`:

```javascript
const KB_KEY = 'knowledge_tracker_db';

function loadKB() {
  // localStorage is persisted to disk by runner.js
  const raw = localStorage.getItem(KB_KEY);
  return raw ? JSON.parse(raw) : { topics: {}, meta: { created: new Date().toISOString() } };
}
```

Gallery's mood-tracker also uses localStorage, but it dies when the WebView
is recycled. SkillOS's `runner.js` persists localStorage to
`cartridges/learn/state/knowledge-tracker.json` — it survives process restarts,
machine reboots, and even Git commits.

**The knowledge base compounds:**

```
Session 1: learn "Albert Einstein"  → 3 facts stored
Session 2: learn "Quantum Computing" → 3 more facts, 2 topics total
Session 3: learn "Albert Einstein"  → facts MERGED (visit_count: 2)
Session 4: quiz "Albert Einstein"   → questions generated from stored facts
```

---

## Part 5: Cross-skill state — quiz-generator

The most powerful pattern: `quiz-generator` reads data written by
`knowledge-tracker` in a *previous* pipeline run.

```javascript
// quiz-generator reads the knowledge base written by knowledge-tracker
const KB_KEY = 'knowledge_tracker_db';  // same key!
const kb = loadKB();
const topicData = kb.topics[topic];

// Then calls Gemma 4 to generate questions from stored knowledge
const quizData = await __skillos.llm.chatJSON(
  `Generate ${count} quiz questions about "${topic}".
   Base the questions ONLY on these facts:
   ${topicData.key_facts.map(f => '- ' + f).join('\n')}`
);
```

**This is impossible in Gallery** — two skills sharing persistent state
and one of them using an LLM to reason about the other's data.

---

## Part 6: Run it

### Without Ollama (heuristic fallback)

```bash
python skillos.py
```

```
skillos$ cartridges
# You'll see: cooking, demo, learn, residential-electrical

skillos$ cartridge learn "Albert Einstein"
# Pipeline runs: wikipedia → insight-extractor (heuristic) → knowledge-tracker
# → "Stored knowledge on 'albert einstein' (3 facts)"

skillos$ cartridge learn --flow review "albert einstein"
# → Shows stored knowledge with facts and summary

skillos$ cartridge learn --flow stats ""
# → "Topics: 1, Total Facts: 3"
```

### With Ollama (full subagent power)

```bash
# Terminal 1: start Ollama
ollama serve

# Terminal 2: run SkillOS with Gemma 4
GEMMA_MODEL=gemma4:e2b python agent_runtime.py --provider gemma interactive
```

```
skillos$ cartridge learn "Quantum Computing"
# Pipeline runs:
#   1. query-wikipedia → fetches QC article
#   2. insight-extractor → Gemma 4 extracts 5 key facts, 3 connections,
#      2 surprising insights, difficulty rating
#   3. knowledge-tracker → stores everything persistently

skillos$ cartridge learn "Albert Einstein"
# Knowledge base now has 2 topics

skillos$ cartridge learn --flow quiz "quantum computing"
# quiz-generator reads stored QC knowledge
# Gemma 4 generates 3 multiple-choice questions
# Questions are based ONLY on facts you've researched

skillos$ cartridge learn --flow connections ""
# Shows connections between Quantum Computing and Einstein
# (if the insight-extractor found cross-topic links)
```

---

## Part 7: What you've demonstrated

### The four Gallery-impossible patterns in one cartridge

```
┌─────────────────────────────────────────────────────────┐
│  learn cartridge                                         │
│                                                          │
│  [1] Gallery Skill Reuse                                │
│      query-wikipedia works identically to Android        │
│                                                          │
│  [2] LLM Subagent (insight-extractor, quiz-generator)   │
│      JS calls __skillos.llm.chatJSON() → Gemma 4 e2b   │
│      The skill REASONS, not just computes               │
│                                                          │
│  [3] Skill Chaining (Blackboard pipeline)               │
│      wikipedia → extractor → tracker: 3 skills chained  │
│      Each reads the previous skill's output              │
│                                                          │
│  [4] Persistent + Cross-Skill State                     │
│      knowledge-tracker writes to disk                    │
│      quiz-generator reads it in a different flow         │
│      Knowledge compounds across sessions                 │
│                                                          │
│  Combined: a LEARNING SYSTEM that Gallery can't build   │
└─────────────────────────────────────────────────────────┘
```

### Architecture comparison

```
Gallery Android:
  LLM → loadSkill → runJs → result
  (One skill, one call, no memory, no chaining)

SkillOS learn cartridge:
  CartridgeRunner
    → [wikipedia] fetch article                    (0 LLM calls)
    → [insight-extractor] __skillos.llm.chat()     (1 LLM call — subagent)
    → [knowledge-tracker] localStorage → disk      (0 LLM calls — persistent)
    → [quiz-generator] read KB + __skillos.llm     (1 LLM call — subagent)
  
  Total: 2 LLM calls, 4 skills, persistent knowledge, cross-skill state
```

### Cost on Gemma 4 e2b (local Ollama)

| Step | LLM calls | Cost |
|---|---|---|
| query-wikipedia | 0 | $0 (fetch) |
| insight-extractor | 1 | $0 (local) |
| knowledge-tracker | 0 | $0 (localStorage) |
| quiz-generator | 1 | $0 (local) |
| **Total** | **2** | **$0** |

Two focused single-turn Gemma 4 calls. No complex multi-turn tool use.
The JS skills handle the orchestration that e2b can't do reliably.

---

## Next steps

- **Add more skills**: Create a `summarizer` skill that condenses long articles
- **Add a `flashcard-generator`**: Generate Anki-style flashcards from knowledge
- **Build domain cartridges**: A `science` cartridge with wikipedia + insight + knowledge
- **Connect to the SkillOS wiki**: Feed insights into the Knowledge Wiki system
- **Share skills with Gallery**: Skills you create work on Android too (minus `__skillos.llm`)
