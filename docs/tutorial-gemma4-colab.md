# Tutorial: Running SkillOS with Gemma 4 on a Free Colab GPU

A step-by-step guide to running SkillOS with Google's Gemma 4 model via Ollama — locally or on a free Colab T4 GPU tunneled to your machine with Pinggy.

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

## Option B: Free Colab T4 GPU + Pinggy Tunnel

No local GPU? No problem. Google Colab gives you a free T4 (15 GB VRAM) and Pinggy tunnels the Ollama API back to your machine over SSH.

### Architecture

```
┌─────────────────────────────────────────────┐
│  Google Colab (free T4 GPU)                 │
│                                             │
│  Ollama server (:11434)                     │
│       │                                     │
│       └── Pinggy SSH tunnel ──────────────┐ │
│                                           │ │
└───────────────────────────────────────────┘ │
                                              │
            Internet (HTTPS)                  │
                                              │
┌─────────────────────────────────────────────┐
│  Your local machine                         │
│                                             │
│  OLLAMA_BASE_URL=https://xxx.a.pinggy.link  │
│       │                                     │
│       └── agent_runtime.py --provider gemma │
│              │                              │
│              └── SkillOS agents & tools     │
└─────────────────────────────────────────────┘
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
| 2 | Install Ollama, start server | ~30s |
| 3 | Pull `gemma4:e2b` model | ~2 min |
| 4 | Quick test via `/v1/chat/completions` | ~5s |
| 5 | Start Pinggy SSH tunnel, print URL | ~10s |
| 6 | (Markdown) Model variants and tips | — |

After Cell 5, you'll see output like:

```
============================================================
Tunnel URL: https://rnxyz-abc-123.a.pinggy.link

Use on your local machine:
  OLLAMA_BASE_URL=https://rnxyz-abc-123.a.pinggy.link/v1 python agent_runtime.py --provider gemma "Say hello"
============================================================
```

### Step 3: Copy the tunnel URL to your local machine

```bash
cd skillos

# Set the tunnel URL and run
export OLLAMA_BASE_URL=https://rnxyz-abc-123.a.pinggy.link/v1

# Test
python agent_runtime.py --provider gemma test

# Interactive mode
python agent_runtime.py --provider gemma interactive

# Single goal
python agent_runtime.py --provider gemma "Create a Python script that prints the Fibonacci sequence"
```

Or use a `.env` file:

```bash
# Add to skillos/.env
OLLAMA_BASE_URL=https://rnxyz-abc-123.a.pinggy.link/v1
```

Then just run:

```bash
python agent_runtime.py --provider gemma interactive
```

### Step 4: Run a full scenario

```bash
# Research task
python agent_runtime.py --provider gemma "Research the latest developments in robotics and create a summary"

# Agent delegation
python agent_runtime.py --provider gemma "Create a tutorial on Python decorators with code examples"

# With more turns for complex tasks
python agent_runtime.py --provider gemma --max-turns 15 "Build a REST API specification for a todo app"
```

---

## Model Variants

| Tag | Params | Quant | VRAM | Context | Colab T4? |
|-----|--------|-------|------|---------|-----------|
| `gemma4:e2b` | 12B | Q2 | ~7.2 GB | 128K | Yes |
| `gemma4` | 12B | Q4 | ~9.6 GB | 128K | Yes |
| `gemma4:e4b` | 12B | Q4 | ~9.6 GB | 128K | Yes |
| `gemma4:26b` | 27B | Q4 | ~18 GB | 256K | No (A100) |
| `gemma4:31b` | 27B | Q8 | ~20 GB | 256K | No (A100) |

**Recommendation**: Use `gemma4:e2b` for Colab (fits comfortably in T4's 15 GB). Use `gemma4` locally if you have >= 10 GB VRAM.

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

### Pinggy tunnel URL expired

Free Pinggy tunnels last ~60 minutes. Re-run Cell 5 in the Colab notebook to get a new URL. Update your `OLLAMA_BASE_URL` accordingly.

### Colab disconnected

Colab free tier disconnects after ~90 minutes of inactivity. Keep the browser tab active, or re-run all cells from Cell 2 onward.

For longer sessions, consider:
- [Pinggy Pro](https://pinggy.io) for persistent subdomains
- Running Ollama on a cloud VM (any provider with a T4/L4 GPU)

### Slow responses

Gemma 4 on a T4 generates ~20-40 tokens/sec (Q2 quant). Add network latency for the Pinggy tunnel. For faster responses:
- Use local Ollama (no tunnel overhead)
- Use `gemma4:e2b` (smaller, faster)
- Use `--no-stream` flag to skip streaming (slightly faster for short responses)

### Agent produces malformed tool calls

Gemma 4 uses the same `<tool_call>/<final_answer>` format as Gemini via the `GEMINI.md` manifest. If tool calls are malformed:
- Try `gemma4` (Q4) instead of `gemma4:e2b` (Q2) — higher quantization = better instruction following
- Add `--max-turns 15` to give the agent more attempts
- Use `--no-stream` for debugging (full response visible at once)

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
    "cache_headers": {},
}
```

Key design decisions:
- **Reuses `GEMINI.md` manifest** — Gemma 4 follows the same `<tool_call>/<final_answer>` wire format, so no new manifest needed
- **`base_url_env`/`model_env`** — env var overrides for tunnel URL and model variants, without touching code
- **`api_key_default: "ollama"`** — Ollama ignores auth, but the OpenAI Python client requires a non-empty API key
- **OpenAI-compatible API** — Ollama exposes `/v1/chat/completions` that the existing OpenAI client speaks natively

Context compaction (`compactor.py`) is also configured for Gemma 4's context windows (128K for 12B variants, 256K for 27B variants).

---

## What's Next

Once you have Gemma 4 running:

1. **Try the research scenario**: `python agent_runtime.py --provider gemma "Run the RealWorld_Research_Task scenario"`
2. **Run agent delegation**: Goals that require multiple agents work the same way — the runtime delegates via `delegate_to_agent`
3. **Compare providers**: Run the same goal with `--provider qwen`, `--provider gemini`, and `--provider gemma` to compare outputs
4. **Go offline**: With local Ollama, SkillOS works with zero internet — useful for air-gapped environments or privacy-sensitive tasks
