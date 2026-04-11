# Tutorial: Running SkillOS with Gemma 4 on a Free Colab GPU

A step-by-step guide to running SkillOS with Google's Gemma 4 model via Ollama — locally or on a free Colab T4 GPU tunneled to your machine with a Cloudflare tunnel.

---

## Why Gemma 4?

| | Claude Code | Qwen/Gemini | Gemma 4 (Ollama) |
|---|---|---|---|
| Cost | Claude pricing | Free tier limits | Completely free |
| Offline | No | No | Yes (local) |
| Privacy | Cloud | Cloud | 100% local or your own Colab |
| Context | Large | Provider-dependent | 128K–256K |
| GPU needed | No | No | Yes (or Colab free tier) |

Gemma 4 slots into SkillOS's existing multi-provider runtime. It reuses the same `GEMINI.md` manifest (same `<tool_call>/<final_answer>` wire format) so all agents, tools, and scenarios work unchanged.

---

## Option A: Local Ollama (if you have a GPU)

### Prerequisites

- A GPU with >= 8 GB VRAM (for `gemma4:e2b`) or >= 10 GB (for `gemma4`)
- macOS, Linux, or WSL2

### Step 1: Install Ollama

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

Or on macOS: download from [ollama.com](https://ollama.com).

### Step 2: Pull Gemma 4

```bash
# Default 12B Q4 quantization (~9.6 GB)
ollama pull gemma4

# Or the smaller Q2 quantization (~7.2 GB) — fits more GPUs
ollama pull gemma4:e2b
```

### Step 3: Test connectivity

```bash
cd skillos
python agent_runtime.py --provider gemma test
```

You should see:

```
✅ Agent Runtime Initialized (provider=gemma, model=gemma4, manifest=GEMINI.md).
Running quick test...
```

### Step 4: Run SkillOS

```bash
# Single goal
python agent_runtime.py --provider gemma "List the files in workspace/"

# Interactive mode
python agent_runtime.py --provider gemma interactive
```

### Using a different model variant

```bash
# Override via environment variable
GEMMA_MODEL=gemma4:e2b python agent_runtime.py --provider gemma interactive
```

---

## Option B: Free Colab T4 GPU + Cloudflare Tunnel

No local GPU? No problem. Google Colab gives you a free T4 (15 GB VRAM) and a Cloudflare tunnel exposes the Ollama API back to your machine over HTTPS — no signup required.

### Architecture

```
┌──────────────────────────────────────────────────┐
│  Google Colab (free T4 GPU)                      │
│                                                  │
│  Ollama server (:11434)                          │
│       │  OLLAMA_ORIGINS=*                        │
│       │  OLLAMA_HOST=0.0.0.0:11434               │
│       │                                          │
│       └── cloudflared tunnel ──────────────────┐ │
│                                                │ │
└────────────────────────────────────────────────┘ │
                                                   │
            Internet (HTTPS)                       │
                                                   │
┌──────────────────────────────────────────────────┐
│  Your local machine                              │
│                                                  │
│  OLLAMA_BASE_URL=https://xxx.trycloudflare.com   │
│       │                                          │
│       └── agent_runtime.py --provider gemma      │
│              │                                   │
│              └── SkillOS agents & tools           │
└──────────────────────────────────────────────────┘
```

### Step 1: Open the Colab notebook

Open `notebooks/skillos_gemma4_colab.ipynb` in Google Colab:

1. Go to [colab.research.google.com](https://colab.research.google.com)
2. File > Upload notebook > select `skillos/notebooks/skillos_gemma4_colab.ipynb`
3. Runtime > Change runtime type > **T4 GPU**

### Step 2: Run the notebook cells

Run all cells in order:

| Cell | What it does | Time |
|------|-------------|------|
| 1 | (Markdown) Overview and instructions | — |
| 2 | Install zstd + Ollama, start server with `OLLAMA_ORIGINS=*` | ~30s |
| 3 | Pull `gemma4` model (Q4 quantization) | ~2 min |
| 4 | Quick test via `/v1/chat/completions` | ~5s |
| 5 | Install `cloudflared`, start tunnel, print URL | ~10s |
| 6 | (Markdown) Model variants and tips | — |

After Cell 5, you'll see output like:

```
============================================================
Tunnel URL: https://something-something.trycloudflare.com

Use on your local machine:
  OLLAMA_BASE_URL=https://something-something.trycloudflare.com/v1 python agent_runtime.py --provider gemma "Say hello"
============================================================
```

### Step 3: Install dependencies and set the tunnel URL

```bash
cd skillos

# One-time setup
python3 -m venv .venv
.venv/bin/pip install openai python-dotenv

# Set the tunnel URL
export OLLAMA_BASE_URL=https://something-something.trycloudflare.com/v1

# Test connectivity
.venv/bin/python agent_runtime.py --provider gemma test

# Interactive mode
.venv/bin/python agent_runtime.py --provider gemma interactive
```

Or use a `.env` file:

```bash
# Add to skillos/.env
OLLAMA_BASE_URL=https://something-something.trycloudflare.com/v1
```

Then just run:

```bash
.venv/bin/python agent_runtime.py --provider gemma interactive
```

### Step 4: Run a multi-agent scenario

The runtime supports full agent delegation — Gemma 4 can discover and delegate to specialized agents in `components/agents/`:

```bash
# Multi-agent content creation (ResearchAgent → WriterAgent → file write)
.venv/bin/python agent_runtime.py --provider gemma --permission-policy autonomous --max-turns 15 \
  "Write a short guide explaining what large language models are. Save the article to projects/Project_llm_guide/output/article.md"

# Research task
.venv/bin/python agent_runtime.py --provider gemma --max-turns 15 \
  "Research the latest developments in robotics and create a summary"

# Code analysis
.venv/bin/python agent_runtime.py --provider gemma --max-turns 15 \
  "Analyze the files in components/agents/ and describe each agent's purpose"
```

**Tested end-to-end workflow:**
1. Gemma 4 plans the task and discovers available agents via `list_files`
2. Delegates research to `ResearchAgent` (produces structured notes)
3. Delegates writing to `WriterAgent` (produces polished article)
4. Calls `write_file` to save the output
5. Returns a `<final_answer>` summary

---

## Model Variants

| Tag | Params | Quant | VRAM | Context | Colab T4? |
|-----|--------|-------|------|---------|-----------|
| `gemma4:e2b` | 12B | Q2 | ~7.2 GB | 128K | Yes |
| `gemma4` | 12B | Q4 | ~9.6 GB | 128K | Yes |
| `gemma4:e4b` | 12B | Q4 | ~9.6 GB | 128K | Yes |
| `gemma4:26b` | 27B | Q4 | ~18 GB | 256K | No (A100) |
| `gemma4:31b` | 27B | Q8 | ~20 GB | 256K | No (A100) |

**Recommendation**: Use `gemma4` (Q4) for both Colab and local — it fits in the T4's 15 GB VRAM and produces significantly better instruction-following than the Q2 variant. Only use `gemma4:e2b` if you're very tight on VRAM.

To switch variants:

```bash
# Pull the variant
ollama pull gemma4:26b

# Set via env var
GEMMA_MODEL=gemma4:26b python agent_runtime.py --provider gemma interactive
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama API endpoint. Set for remote tunnel. |
| `OLLAMA_API_KEY` | `ollama` | Ollama ignores auth, but the OpenAI client needs a non-empty string. |
| `GEMMA_MODEL` | `gemma4` | Override the default model tag. |

---

## Troubleshooting

### "Connection refused" when running with `--provider gemma`

Ollama isn't running. Start it:

```bash
# macOS (if installed via .app)
open -a Ollama

# Linux
ollama serve &
```

### "Model not found: gemma4"

Pull the model first:

```bash
ollama pull gemma4
```

### Cloudflare tunnel URL expired / 524 timeout

Cloudflare quick tunnels have no uptime guarantee. If you see a 524 timeout error, the Colab session likely expired. Re-run Cell 5 (or all cells from Cell 2 if the runtime was recycled) to get a fresh URL. Update your `OLLAMA_BASE_URL` accordingly.

### Colab disconnected

Colab free tier disconnects after ~90 minutes of inactivity. Keep the browser tab active, or re-run all cells from Cell 2 onward.

For longer sessions, consider:
- A named Cloudflare tunnel with a [Cloudflare account](https://dash.cloudflare.com) for persistent URLs
- Running Ollama on a cloud VM (any provider with a T4/L4 GPU)

### Ollama returns 403 through the tunnel

Ollama rejects requests with non-localhost `Origin` headers by default. The Colab notebook sets `OLLAMA_ORIGINS=*` and `OLLAMA_HOST=0.0.0.0:11434` to fix this. If you're running Ollama manually:

```bash
OLLAMA_ORIGINS='*' OLLAMA_HOST='0.0.0.0:11434' ollama serve
```

### Slow responses

Gemma 4 on a T4 generates ~20-40 tokens/sec. Add network latency for the Cloudflare tunnel. For faster responses:
- Use local Ollama (no tunnel overhead)
- Use `gemma4:e2b` (smaller, faster, but worse instruction following)
- Use `--no-stream` flag to skip streaming (slightly faster for short responses)

### Agent produces malformed tool calls

Gemma 4 uses the same `<tool_call>/<final_answer>` format as Gemini via the `GEMINI.md` manifest. The runtime handles five different tool call formats that Gemma may produce (named tags, unnamed tags, JSON arrays, unclosed tags) and includes automatic JSON repair for unescaped quotes inside string values. If tool calls still fail:
- Use `gemma4` (Q4) instead of `gemma4:e2b` (Q2) — higher quantization = better instruction following
- Add `--max-turns 15` to give the agent more attempts
- Use `--no-stream` for debugging (full response visible at once)
- Add `--permission-policy autonomous` if the agent needs write access

---

## How It Works Under the Hood

The `--provider gemma` flag selects this config from `agent_runtime.py`:

```python
"gemma": {
    "base_url": "http://localhost:11434/v1",
    "base_url_env": "OLLAMA_BASE_URL",
    "api_key_env": "OLLAMA_API_KEY",
    "api_key_default": "ollama",
    "model": "gemma4",
    "model_env": "GEMMA_MODEL",
    "manifest": "GEMINI.md",
    "cache_headers": {"Bypass-Tunnel-Reminder": "true"},
}
```

Key design decisions:
- **Reuses `GEMINI.md` manifest** — Gemma 4 follows the same `<tool_call>/<final_answer>` wire format, so no new manifest needed
- **`base_url_env`/`model_env`** — env var overrides for tunnel URL and model variants, without touching code
- **`api_key_default: "ollama"`** — Ollama ignores auth, but the OpenAI Python client requires a non-empty API key
- **OpenAI-compatible API** — Ollama exposes `/v1/chat/completions` that the existing OpenAI client speaks natively
- **`Bypass-Tunnel-Reminder` header** — prevents tunnel intermediaries from injecting HTML into API responses
- **Tool name aliasing** — `run_agent` (what Gemma often generates) is automatically resolved to `delegate_to_agent`
- **Multi-format tool call parsing** — handles 5 different XML/JSON formats Gemma may produce
- **JSON repair** — automatic fallback for malformed JSON with unescaped quotes in string values

Context compaction (`compactor.py`) is also configured for Gemma 4's context windows (128K for 12B variants, 256K for 27B variants).

---

## What's Next

Once you have Gemma 4 running:

1. **Try the research scenario**: `python agent_runtime.py --provider gemma "Run the RealWorld_Research_Task scenario"`
2. **Run agent delegation**: Goals that require multiple agents work the same way — the runtime delegates via `delegate_to_agent`
3. **Compare providers**: Run the same goal with `--provider qwen`, `--provider gemini`, and `--provider gemma` to compare outputs
4. **Go offline**: With local Ollama, SkillOS works with zero internet — useful for air-gapped environments or privacy-sensitive tasks
