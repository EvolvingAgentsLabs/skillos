"""JS Executor — runs Gallery JS skills via Node.js subprocess.

Replaces the Android WebView execution path with a Node.js runner.
Each skill invocation is a fresh subprocess for isolation.
"""

from __future__ import annotations

import json
import subprocess
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

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


def run_skill(skill: SkillDefinition, data: str, secret: str = "",
              *, timeout: int = DEFAULT_TIMEOUT) -> SkillResult:
    """Execute a Gallery JS skill via Node.js.

    Args:
        skill: Loaded skill definition.
        data: JSON string with skill parameters.
        secret: Optional API key/secret.
        timeout: Max execution time in seconds.

    Returns:
        SkillResult with the parsed output.
    """
    js_path = skill.js_path or skill.script_path
    if not js_path:
        return SkillResult.from_error(f"No JS file found for skill '{skill.name}'")

    if not os.path.exists(js_path):
        return SkillResult.from_error(f"JS file not found: {js_path}")

    cmd = ["node", RUNNER_JS, js_path, data]
    if secret:
        cmd.append(secret)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=skill.skill_dir,  # run from skill dir so relative paths work
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
        # Non-JSON output — treat as plain text result
        return SkillResult(ok=True, result=stdout, raw={"result": stdout})


def run_skill_by_name(registry: SkillRegistry, skill_name: str,
                      data: str, secret: str = "",
                      *, timeout: int = DEFAULT_TIMEOUT) -> SkillResult:
    """Look up a skill by name in the registry and execute it."""
    skill = registry.get(skill_name)
    if skill is None:
        available = ", ".join(registry.names())
        return SkillResult.from_error(
            f"Skill '{skill_name}' not found. Available: {available}")
    return run_skill(skill, data, secret, timeout=timeout)


if __name__ == "__main__":
    import sys
    # Quick test: python js_executor.py calculate-hash '{"text":"hello world"}'
    # Resolve relative to this file: experiments/gemma4-skills/ → skillos/ → evolvingagents/
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
