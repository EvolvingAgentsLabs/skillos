# SkillOS Desktop Shell

A Tauri-based desktop wrapper around the SkillOS forge runtime.  The shell
is deliberately thin: the Python process (`forge/server.py`) is the source
of truth for skills, cartridges, budget, journal, and forge execution; the
desktop app renders a UI on top of the HTTP API and starts/stops the
Python backend as a sidecar.

## Current status

**Scaffold only.**  The Rust shell launches the Python server, the web
assets show a working dashboard against the API, and the Tauri command
surface exposes the minimum needed for the next pass.  Packaging, signing,
auto-updates, and cartridge-cache UI are explicitly out of scope for this
milestone.

## Why Tauri (not Electron)

- Binary size: ~15 MB vs ~150 MB.  Matters when we ship Gemma GGUFs
  alongside (~3 GB) and need headroom in the installer.
- Rust host gives first-class subprocess + filesystem APIs, which we need
  for managing the Python sidecar and the cartridge cache.
- WebView renders the same HTML/JS we'd use for the web demo, so the
  frontend is reusable.

## Layout

```
desktop/
├── README.md                    # this file
├── Cargo.toml                   # Rust crate manifest (not yet usable until
│                                  tauri-cli is invoked)
├── tauri.conf.json              # Tauri app config
├── src-tauri/
│   └── src/
│       ├── main.rs              # Tauri entry + sidecar manager
│       ├── sidecar.rs           # Python forge server lifecycle
│       └── commands.rs          # #[tauri::command] wrappers over HTTP API
└── ui/
    ├── index.html               # Single-page dashboard
    └── app.js                   # Vanilla JS — no framework dependency
```

## Prerequisites to build

- Rust toolchain (`rustup default stable`)
- `cargo install tauri-cli` (v2.x)
- System deps per https://v2.tauri.app/start/prerequisites/
- A working Python 3.11+ with `pip install openai pyyaml python-dotenv`
  (the sidecar uses the SkillOS forge package from the repo root)

## Build + run (dev)

```bash
# from repo root
cd desktop
cargo tauri dev
```

The dev script launches the Python sidecar on port 8765 and the Tauri
window pointed at `ui/index.html`.  The UI talks to `127.0.0.1:8765`.

## Production build

```bash
cd desktop
cargo tauri build
```

Produces signed-or-unsigned installers under
`desktop/src-tauri/target/release/bundle/`.

## Sidecar management

The Rust host starts the Python server on app launch and terminates it on
app shutdown.  The `FORGE_API_TOKEN` is generated at start, exported to
the sidecar, and injected into every UI fetch so the API is not open to
arbitrary localhost clients.

## Next steps

- [ ] Implement `src-tauri/src/sidecar.rs`  — subprocess spawn, health-wait
  loop, graceful shutdown.
- [ ] Implement `src-tauri/src/commands.rs` — `tauri::command` wrappers
  over HTTP API so the frontend can use `invoke()` instead of `fetch()`
  (matters for sandboxed environments).
- [ ] Build the Board view (Multica-style task list).
- [ ] Cartridge cache browser: LRU, size, swap latency.
- [ ] Settings: model tag, Ollama URL, Anthropic API key, budget caps.
- [ ] Packaging: bundle Ollama + default Gemma4:e2b model for one-click
  install.
