"""Claude Code bridge for the forge tier.

The router sends forge-tier calls here.  Three backends are available:

* :class:`AnthropicAPIBridge` — uses the ``anthropic`` SDK directly.  Lowest
  friction in CI and scriptable runs.  Requires ``ANTHROPIC_API_KEY``.
* :class:`ClaudeCLIBridge` — shells out to the ``claude`` CLI.  Matches the
  "Claude Code is the forge" framing and reuses the user's existing CLI auth.
* :class:`MockClaudeBridge` — scripted responses, no network.  Used by
  tests and by ``--dry-run``.

All bridges implement the same :class:`ClaudeBridge` protocol.  The factory
``get_claude_bridge()`` picks the right one based on environment.

The bridge is deliberately thin.  It takes a structured ``ForgeRequest``
(prompt + constraints), returns a structured ``ForgeResponse`` (text plus
token accounting), and leaves artifact writing to the caller.  Prompt
templates live under ``system/skills/forge/<family>/prompts/`` as markdown
so they are reviewable and editable without touching code.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# --- types -----------------------------------------------------------

@dataclass
class ForgeRequest:
    """Everything a forge-tier call needs.

    ``prompt`` is fully-rendered — the caller applies its own templating.
    ``max_tokens`` is an upper bound for the bridge backend; the budget
    ledger enforces harder caps outside.
    """

    prompt: str
    system: str = ""
    max_tokens: int = 4096
    temperature: float = 0.2
    stop: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ForgeResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    wall_clock_s: float = 0.0
    finish_reason: str = "stop"
    backend: str = ""

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


# --- protocol --------------------------------------------------------

class ClaudeBridge(ABC):
    """Common interface for every forge backend."""

    name: str = "abstract"

    @abstractmethod
    def invoke(self, request: ForgeRequest) -> ForgeResponse:  # pragma: no cover
        ...


# --- Anthropic SDK backend ------------------------------------------

class AnthropicAPIBridge(ClaudeBridge):
    """Direct anthropic-python-sdk backend.

    Imports the SDK lazily so the package can be imported in environments
    without ``anthropic`` installed (e.g. Ollama-only boxes).
    """

    name = "anthropic-api"

    def __init__(self, *, model: str | None = None,
                 api_key: str | None = None):
        self.model = model or os.environ.get("FORGE_CLAUDE_MODEL",
                                              "claude-sonnet-4-6")
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self._client = None  # lazy

    def _client_or_raise(self):
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set; cannot use AnthropicAPIBridge. "
                "Set SKILLOS_FORGE_OFFLINE=1 to disable forge entirely."
            )
        try:
            import anthropic  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "anthropic package not installed; "
                "`pip install anthropic` or use ClaudeCLIBridge"
            ) from exc
        self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def invoke(self, request: ForgeRequest) -> ForgeResponse:
        import time
        client = self._client_or_raise()
        started = time.monotonic()
        kwargs: dict[str, Any] = dict(
            model=self.model,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            messages=[{"role": "user", "content": request.prompt}],
        )
        if request.system:
            kwargs["system"] = request.system
        if request.stop:
            kwargs["stop_sequences"] = request.stop
        msg = client.messages.create(**kwargs)
        wall = time.monotonic() - started
        text = "".join(
            getattr(block, "text", "") for block in (msg.content or [])
        )
        usage = getattr(msg, "usage", None)
        return ForgeResponse(
            text=text,
            input_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
            output_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
            wall_clock_s=wall,
            finish_reason=str(getattr(msg, "stop_reason", "stop")),
            backend=self.name,
        )


# --- Claude CLI backend ---------------------------------------------

class ClaudeCLIBridge(ClaudeBridge):
    """Shells out to the ``claude`` CLI.

    Useful when the user already has Claude Code installed and authenticated;
    no separate API key management.  The CLI does not report token counts,
    so we approximate them with a 1 token ≈ 4 bytes heuristic — good enough
    for budget enforcement, not good enough for billing reconciliation.
    """

    name = "claude-cli"
    APPROX_CHARS_PER_TOKEN = 4

    def __init__(self, *, binary: str = "claude",
                 extra_args: list[str] | None = None,
                 timeout_s: int = 600):
        self.binary = binary
        self.extra_args = list(extra_args or [])
        self.timeout_s = timeout_s

    def invoke(self, request: ForgeRequest) -> ForgeResponse:
        import time
        args = [self.binary, *self.extra_args,
                "--dangerously-skip-permissions",
                "-p", request.prompt]
        started = time.monotonic()
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=self.timeout_s,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"claude CLI not found (looked for {shlex.quote(self.binary)}); "
                f"install it or switch to AnthropicAPIBridge"
            ) from exc
        wall = time.monotonic() - started
        if result.returncode != 0:
            raise RuntimeError(
                f"claude CLI exited {result.returncode}: {result.stderr[:500]}"
            )
        text = result.stdout
        in_tokens = len(request.prompt) // self.APPROX_CHARS_PER_TOKEN
        out_tokens = len(text) // self.APPROX_CHARS_PER_TOKEN
        return ForgeResponse(
            text=text,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            wall_clock_s=wall,
            finish_reason="stop",
            backend=self.name,
        )


# --- Mock backend (tests + --dry-run) --------------------------------

class MockClaudeBridge(ClaudeBridge):
    """Scripted responses.  Preload with ``push()`` before each call."""

    name = "mock"

    def __init__(self, *, scripted: list[ForgeResponse] | None = None):
        self._queue: list[ForgeResponse] = list(scripted or [])
        self.calls: list[ForgeRequest] = []

    def push(self, response: ForgeResponse) -> None:
        self._queue.append(response)

    def invoke(self, request: ForgeRequest) -> ForgeResponse:
        self.calls.append(request)
        if not self._queue:
            raise RuntimeError(
                "MockClaudeBridge: no scripted response available "
                "— call push(...) before invoke(...)"
            )
        resp = self._queue.pop(0)
        if not resp.backend:
            resp.backend = self.name
        return resp


# --- factory ---------------------------------------------------------

def get_claude_bridge() -> ClaudeBridge:
    """Select a bridge based on environment.

    Resolution order:
      1. ``FORGE_CLAUDE_BACKEND`` env var (``mock`` | ``cli`` | ``api``)
      2. ``ANTHROPIC_API_KEY`` present → API
      3. ``claude`` binary on PATH → CLI
      4. Fall back to Mock (raises on first call, making failure visible)
    """
    backend = os.environ.get("FORGE_CLAUDE_BACKEND", "").strip().lower()
    if backend == "mock":
        return MockClaudeBridge()
    if backend == "api":
        return AnthropicAPIBridge()
    if backend == "cli":
        return ClaudeCLIBridge()
    if os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicAPIBridge()
    if _has_claude_cli():
        return ClaudeCLIBridge()
    return MockClaudeBridge()


def _has_claude_cli() -> bool:
    from shutil import which
    return which("claude") is not None


# --- prompt templates ------------------------------------------------

TEMPLATE_ROOT = Path("system/skills/forge")


class PromptTemplate:
    """Very small templating helper: ``{placeholder}`` substitution only.

    We deliberately avoid Jinja or str.format (which chokes on ``{`` in
    markdown fences).  Substitution is tied to a regex for ``{word}`` so
    code samples inside the template survive.
    """

    _PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

    def __init__(self, text: str):
        self.text = text

    @classmethod
    def load(cls, family: str, name: str,
             *, root: Path | str | None = None) -> "PromptTemplate":
        base = Path(root) if root else TEMPLATE_ROOT
        path = base / family / "prompts" / f"{name}.md"
        if not path.exists():
            raise FileNotFoundError(
                f"prompt template not found: {path}  "
                f"(expected under {base}/{family}/prompts/)"
            )
        return cls(path.read_text(encoding="utf-8"))

    def render(self, **context: Any) -> str:
        def _sub(m: re.Match[str]) -> str:
            key = m.group(1)
            if key in context:
                value = context[key]
                if not isinstance(value, str):
                    value = json.dumps(value, indent=2, sort_keys=True)
                return value
            return m.group(0)  # leave unknown placeholders intact
        return self._PLACEHOLDER_RE.sub(_sub, self.text)
