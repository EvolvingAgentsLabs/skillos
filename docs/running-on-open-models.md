# Running SkillOS on Open Models (Gemma 4 / Gemini) via an Anthropic Proxy

This guide shows how to run **the full SkillOS Claude Code runtime** — every agent, tool,
and the markdown-OS orchestration — against **non-Anthropic models** such as **Gemma 4**
or **Gemini**, at little or no cost.

> **How this differs from Runtime 2 (`agent_runtime.py`).**
> Runtime 2 is a *separate* provider-agnostic interpreter. This approach instead keeps
> **Runtime 1 (Claude Code)** exactly as-is and only swaps the model *behind* it, using a
> local proxy that speaks the Anthropic API on the front and translates to OpenAI/Gemini on
> the back. You keep Claude Code's native tool execution and `.claude/agents/` discovery —
> you just change which LLM is answering.

## Why it works with zero SkillOS changes

`skillos.py` never talks to a model directly — it shells out to the `claude` CLI
(`claude -p --output-format text`). Point the `claude` CLI at a proxy via
`ANTHROPIC_BASE_URL`, and **all of SkillOS** follows. No SkillOS logic changes.

```
SkillOS REPL (skillos.py)
   └─ claude -p ...                     (Claude Code CLI)
        └─ ANTHROPIC_BASE_URL → http://127.0.0.1:8082
             └─ claude-code-proxy       (Anthropic → OpenAI/Gemini, LiteLLM)
                  └─ OpenRouter / Google Gemini API → Gemma 4 / Gemini
```

---

## 1. The proxy

Use [`ariangibson/claude-code-proxy`](https://github.com/ariangibson/claude-code-proxy)
(a maintained LiteLLM-based Anthropic→OpenAI/Gemini bridge). Run it **from source** so the
two patches below apply and so you avoid the bundled compose file's external-network setup.

```bash
git clone https://github.com/ariangibson/claude-code-proxy ~/claude-code-proxy
cd ~/claude-code-proxy
cp .env.example .env          # configured per backend below
```

### Two required patches to `server.py`

These are **not** in upstream and are required for Claude Code's tool schemas to work:

1. **Model whitelist** (~line 113, `GEMINI_MODELS`): add the model IDs you intend to map to,
   e.g. `gemma-4-31b-it`, `gemma-4-26b-a4b-it`, `gemini-3.5-flash`. The proxy only remaps
   `haiku`/`sonnet` → `gemini/<model>` when the target is in this list; otherwise routing
   silently no-ops.

2. **Schema sanitizer** (`clean_gemini_schema`): the **Gemini** function-declaration schema
   rejects JSON-Schema unions and several keywords that Claude Code's tool definitions use.
   Extend the sanitizer to:
   - flatten `anyOf` / `oneOf` / `allOf` and list-valued `type` (Gemini error:
     *"Type Unions are not supported"*);
   - strip / convert unsupported keywords: `propertyNames`, `exclusiveMinimum/Maximum`,
     `const` → `enum`, `$ref`, `patternProperties`, `multipleOf`, … (Gemini error:
     *400 "Unknown name …"*).

   > This patch is only needed on the **Gemini** path. The **OpenRouter** path (below) uses
   > OpenAI-format tool schemas and needs no schema surgery.

Start it (installs deps on first run via `uv`):

```bash
set -a; . ./.env; set +a; unset VIRTUAL_ENV
.venv/bin/uvicorn server:app --host 127.0.0.1 --port 8082
```

---

## 2. Pick a backend

### Option A — Gemma 4 31B via OpenRouter ✅ recommended

Best results: real Gemma 4, generous limits, 262k context, supports `tools`/`tool_choice`,
no schema patch needed, ~\$0.12 / \$0.35 per 1M input/output tokens.

`~/claude-code-proxy/.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-...            # from https://openrouter.ai/keys
PREFERRED_PROVIDER="openai"
OPENAI_BASE_URL="https://openrouter.ai/api/v1"
OPENAI_API_KEY="${OPENROUTER_API_KEY}"
BIG_MODEL="google/gemma-4-31b-it"
SMALL_MODEL="google/gemma-4-31b-it"
```

### Option B — Gemini (e.g. gemini-3.5-flash) via Google AI

High throughput, good for exercising the whole stack. Requires the schema patch.

```env
GEMINI_API_KEY=...                         # from https://aistudio.google.com/apikey
PREFERRED_PROVIDER="google"
BIG_MODEL="gemini-3.5-flash"
SMALL_MODEL="gemini-3.5-flash"
```

### Option C — Gemma 4 via the Google Gemini API ⚠️ quota-limited

`gemma-4-31b-it` / `gemma-4-26b-a4b-it` work and support function calling, **but** the
Gemini API's Gemma quota is only ~**16k input tokens/min/model** — smaller than Claude
Code's single request (system prompt + ~28 tool schemas), so it returns
`429 RESOURCE_EXHAUSTED` even on the first call. Use only after requesting a quota increase;
otherwise prefer Option A.

```env
GEMINI_API_KEY=...
PREFERRED_PROVIDER="google"
BIG_MODEL="gemma-4-31b-it"
SMALL_MODEL="gemma-4-26b-a4b-it"
```

---

## 3. Point SkillOS at the proxy

Copy the template and keep it as your **local** (gitignored) settings — this avoids
committing machine-specific routing that would hijack other users' `claude`:

```bash
cp .claude/settings.local.json.example .claude/settings.local.json
```

It sets `ANTHROPIC_BASE_URL` to the proxy, forces `ANTHROPIC_MODEL`/
`ANTHROPIC_SMALL_FAST_MODEL` to the `sonnet`/`haiku` names the proxy maps, and pre-allows
the tools SkillOS needs (its `claude -p` calls can't answer permission prompts).

---

## 4. Run it

```bash
./skillos.sh
# then enter a goal, e.g.:
skillos$ Immediately write a Python rock-paper-scissors terminal game to projects/Project_rps/output/game.py — skip planning, use the Write tool now
```

### Verified end-to-end
- **OpenRouter Gemma 4 31B**: SkillOS booted, orchestrated, and wrote + ran a working
  Rock-Paper-Scissors game; a direct Claude Code goal wrote + ran a working Tic-Tac-Toe.
- **gemini-3.5-flash**: same, full SkillOS interactive run produced a working game.

---

## Caveats

- **Open models are weaker agents than Claude.** Open-ended SkillOS goals can get lost in
  the framework's meta-work (reading manifests, checking git) and exhaust Claude Code's turn
  budget without finishing. **Directive goals** ("write the file *now*, skip planning")
  converge reliably. This is a model-capability limit, not a setup issue.
- **Boot is slower.** `boot_skillos()` loads the full markdown OS; the default boot timeout
  was raised to 300s to accommodate slower models.
- **Gemma chain-of-thought leakage.** Gemma 4 emits reasoning inline (`"thought"` parts /
  "Plan:" preambles) that can surface in output — cosmetic.
- **Secrets.** API keys live in the proxy's `.env` (a different repo). Never commit real
  keys. SkillOS's `.claude/settings.local.json` is gitignored by design. Rotate any key that
  has been exposed.
```
