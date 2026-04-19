"""JS Executor — runs Gallery JS skills via Node.js subprocess.

Replaces the Android WebView execution path with a Node.js runner.
Each skill invocation is a fresh subprocess for isolation.

Supports:
- Persistent localStorage via SKILL_STATE_DIR (Upgrade 1)
- LLM sub-calls via __skillos.llm.chat() (Upgrade 3)
- Headless browser fallback via Playwright (Upgrade 5)
"""

from __future__ import annotations

import json
import subprocess
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from skill_loader import SkillDefinition, SkillRegistry

RUNNER_JS = str(Path(__file__).resolve().parent / "runner.js")

# Timeout for skill execution (seconds)
DEFAULT_TIMEOUT = 30


@dataclass
class SkillResult:
    """Result of a Gallery JS skill execution."""
    ok: bool
    result: Optional[str] = None       # text result for LLM
    error: Optional[str] = None        # error message
    webview: Optional[dict] = None     # {url, iframe?, aspectRatio?}
    image: Optional[dict] = None       # {base64}
    raw: Optional[dict] = None         # full parsed JSON

    @staticmethod
    def from_json(data: dict) -> "SkillResult":
        return SkillResult(
            ok="error" not in data or not data["error"],
            result=data.get("result"),
            error=data.get("error"),
            webview=data.get("webview"),
            image=data.get("image"),
            raw=data,
        )

    @staticmethod
    def from_error(msg: str) -> "SkillResult":
        return SkillResult(ok=False, error=msg, raw={"error": msg})

    def to_llm_string(self) -> str:
        """Format result for returning to the LLM."""
        if self.error:
            return f"Error: {self.error}"
        if self.result:
            return self.result
        if self.webview:
            return f"[Webview generated: {self.webview.get('url', 'unknown')}]"
        if self.image:
            return "[Image generated]"
        return json.dumps(self.raw or {})


@dataclass
class RuntimeConfig:
    """Runtime configuration passed to the JS runner via environment."""
    state_dir: str = ""                # SKILL_STATE_DIR: persist localStorage
    llm_api_url: str = ""              # LLM_API_URL: Ollama/OpenRouter endpoint
    llm_model: str = "gemma4:e2b"      # LLM_MODEL: model name
    llm_api_key: str = "ollama"        # LLM_API_KEY: API key
    shared_state_name: str = ""        # Override SKILL_NAME so all skills share state

    def to_env(self, skill_name: str = "") -> dict[str, str]:
        """Build env dict for subprocess."""
        env = os.environ.copy()
        if self.state_dir:
            env["SKILL_STATE_DIR"] = self.state_dir
        name = self.shared_state_name or skill_name
        if name:
            env["SKILL_NAME"] = name
        if self.llm_api_url:
            env["LLM_API_URL"] = self.llm_api_url
            env["LLM_MODEL"] = self.llm_model
            env["LLM_API_KEY"] = self.llm_api_key
        return env


# Default config (no state persistence, no LLM)
_default_config = RuntimeConfig()


def run_skill(skill: SkillDefinition, data: str, secret: str = "",
              *, timeout: int = DEFAULT_TIMEOUT,
              config: RuntimeConfig | None = None) -> SkillResult:
    """Execute a Gallery JS skill via Node.js.

    Args:
        skill: Loaded skill definition.
        data: JSON string with skill parameters.
        secret: Optional API key/secret.
        timeout: Max execution time in seconds.
        config: Runtime config (state dir, LLM endpoint).

    Returns:
        SkillResult with the parsed output.
    """
    cfg = config or _default_config

    # Upgrade 5: Check if skill needs browser runtime
    if _needs_browser(skill):
        return _run_in_playwright(skill, data, secret, timeout=timeout, config=cfg)

    return _run_in_node(skill, data, secret, timeout=timeout, config=cfg)


def _run_in_node(skill: SkillDefinition, data: str, secret: str = "",
                 *, timeout: int = DEFAULT_TIMEOUT,
                 config: RuntimeConfig | None = None) -> SkillResult:
    """Execute skill in Node.js subprocess."""
    cfg = config or _default_config
    js_path = skill.js_path or skill.script_path
    if not js_path:
        return SkillResult.from_error(f"No JS file found for skill '{skill.name}'")

    if not os.path.exists(js_path):
        return SkillResult.from_error(f"JS file not found: {js_path}")

    cmd = ["node", RUNNER_JS, js_path, data]
    if secret:
        cmd.append(secret)

    env = cfg.to_env(skill.name)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=skill.skill_dir,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return SkillResult.from_error(
            f"Skill '{skill.name}' timed out after {timeout}s")
    except FileNotFoundError:
        return SkillResult.from_error(
            "Node.js not found. Install Node.js 18+ to run Gallery JS skills.")

    if proc.returncode != 0 and not proc.stdout.strip():
        stderr = proc.stderr.strip()[:500] if proc.stderr else "unknown error"
        return SkillResult.from_error(f"Node.js error: {stderr}")

    stdout = proc.stdout.strip()
    if not stdout:
        return SkillResult.from_error("Skill returned empty output")

    try:
        parsed = json.loads(stdout)
        return SkillResult.from_json(parsed)
    except json.JSONDecodeError:
        return SkillResult(ok=True, result=stdout, raw={"result": stdout})


# ── Upgrade 5: Playwright-based browser executor ─────────────────────

def _needs_browser(skill: SkillDefinition) -> bool:
    """Check if a skill requires a full browser (Canvas, WebAudio, etc.)."""
    return getattr(skill, "runtime", "node") == "browser"


def _run_in_playwright(skill: SkillDefinition, data: str, secret: str = "",
                       *, timeout: int = DEFAULT_TIMEOUT,
                       config: RuntimeConfig | None = None) -> SkillResult:
    """Execute skill in headless Chromium via Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return SkillResult.from_error(
            f"Skill '{skill.name}' requires a browser runtime. "
            f"Install Playwright: pip install playwright && playwright install chromium")

    script_path = skill.script_path or skill.js_path
    if not script_path or not os.path.exists(script_path):
        return SkillResult.from_error(f"Script not found: {script_path}")

    # Build file:// URL for the HTML entry point
    html_path = script_path
    if html_path.endswith(".js"):
        # Look for sibling index.html
        html_candidate = html_path.replace(".js", ".html")
        if os.path.exists(html_candidate):
            html_path = html_candidate
        else:
            return SkillResult.from_error(
                f"Browser runtime needs an HTML entry point, not .js: {html_path}")

    file_url = Path(html_path).as_uri()

    # Inject __skillos if LLM is configured
    cfg = config or _default_config
    skillos_inject = ""
    if cfg.llm_api_url:
        skillos_inject = f"""
        window.__skillos = {{
          runtime: 'browser',
          llm: {{
            available: true,
            url: '{cfg.llm_api_url}',
            model: '{cfg.llm_model}',
            async chat(prompt, options = {{}}) {{
              const messages = [];
              if (options.system) messages.push({{ role: 'system', content: options.system }});
              messages.push({{ role: 'user', content: prompt }});
              const resp = await fetch('{cfg.llm_api_url}/chat/completions', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json', 'Authorization': 'Bearer {cfg.llm_api_key}' }},
                body: JSON.stringify({{ model: '{cfg.llm_model}', messages, temperature: options.temperature || 0.7 }})
              }});
              const data = await resp.json();
              return data.choices[0].message.content;
            }}
          }}
        }};
        """

    safe_data = json.dumps(data)  # double-encode for JS injection
    safe_secret = json.dumps(secret)

    js_eval = f"""
    (async function() {{
      {skillos_inject}
      var startTs = Date.now();
      while(true) {{
        if (typeof ai_edge_gallery_get_result === 'function') break;
        if (typeof window.ai_edge_gallery_get_result === 'function') break;
        await new Promise(r => setTimeout(r, 100));
        if (Date.now() - startTs > 10000) break;
      }}
      var fn = window.ai_edge_gallery_get_result || globalThis.ai_edge_gallery_get_result;
      if (typeof fn !== 'function') return JSON.stringify({{error: 'function not found'}});
      var result = await fn({safe_data}, {safe_secret});
      return typeof result === 'string' ? result : JSON.stringify(result);
    }})()
    """

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(file_url, wait_until="networkidle", timeout=timeout * 1000)
            raw = page.evaluate(js_eval)
            browser.close()
    except Exception as e:
        return SkillResult.from_error(f"Playwright error: {e}")

    if not raw:
        return SkillResult.from_error("Browser returned empty result")

    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        return SkillResult.from_json(parsed)
    except (json.JSONDecodeError, TypeError):
        return SkillResult(ok=True, result=str(raw), raw={"result": str(raw)})


# ── Public helpers ───────────────────────────────────────────────────

def run_skill_by_name(registry: SkillRegistry, skill_name: str,
                      data: str, secret: str = "",
                      *, timeout: int = DEFAULT_TIMEOUT,
                      config: RuntimeConfig | None = None) -> SkillResult:
    """Look up a skill by name in the registry and execute it."""
    skill = registry.get(skill_name)
    if skill is None:
        available = ", ".join(registry.names())
        return SkillResult.from_error(
            f"Skill '{skill_name}' not found. Available: {available}")
    return run_skill(skill, data, secret, timeout=timeout, config=config)


if __name__ == "__main__":
    import sys
    gallery_root = Path(__file__).resolve().parent.parent.parent.parent / "gallery" / "skills"
    registry = SkillRegistry(gallery_root / "built-in", gallery_root / "featured")

    skill_name = sys.argv[1] if len(sys.argv) > 1 else "calculate-hash"
    data = sys.argv[2] if len(sys.argv) > 2 else '{"text": "hello world"}'
    secret = sys.argv[3] if len(sys.argv) > 3 else ""

    print(f"Running skill: {skill_name}")
    print(f"Data: {data}")
    result = run_skill_by_name(registry, skill_name, data, secret)
    print(f"OK: {result.ok}")
    print(f"Result: {result.to_llm_string()}")
