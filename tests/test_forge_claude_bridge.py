"""Unit tests for forge.claude_bridge.

These are narrow: bridge plumbing (request shape, response plumbing,
template rendering, factory selection) rather than round-trip with a real
LLM.  The executor E2E test covers the glue.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from forge.claude_bridge import (  # noqa: E402
    AnthropicAPIBridge,
    ClaudeCLIBridge,
    ForgeRequest,
    ForgeResponse,
    MockClaudeBridge,
    PromptTemplate,
    get_claude_bridge,
)


# --- mock bridge ----------------------------------------------------

def test_mock_bridge_returns_scripted_response():
    bridge = MockClaudeBridge(scripted=[
        ForgeResponse(text="hello", input_tokens=10, output_tokens=2),
    ])
    resp = bridge.invoke(ForgeRequest(prompt="hi"))
    assert resp.text == "hello"
    assert resp.backend == "mock"
    assert resp.total_tokens == 12


def test_mock_bridge_raises_when_empty():
    bridge = MockClaudeBridge()
    with pytest.raises(RuntimeError, match="no scripted response"):
        bridge.invoke(ForgeRequest(prompt="hi"))


def test_mock_bridge_records_calls():
    bridge = MockClaudeBridge(scripted=[ForgeResponse(text="x")])
    req = ForgeRequest(prompt="p", system="s", max_tokens=100)
    bridge.invoke(req)
    assert len(bridge.calls) == 1
    assert bridge.calls[0] is req


# --- Anthropic SDK bridge -------------------------------------------

def test_anthropic_bridge_refuses_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    bridge = AnthropicAPIBridge()
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY not set"):
        bridge.invoke(ForgeRequest(prompt="x"))


def test_anthropic_bridge_invokes_sdk(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    class FakeUsage:
        input_tokens = 10
        output_tokens = 5

    class FakeBlock:
        def __init__(self, text):
            self.text = text

    class FakeMessage:
        content = [FakeBlock("hello")]
        usage = FakeUsage()
        stop_reason = "end_turn"

    class FakeMessages:
        def create(self, **kwargs):
            self.last_kwargs = kwargs
            return FakeMessage()

    class FakeClient:
        def __init__(self, **kw):
            self.messages = FakeMessages()

    fake_anthropic = type(sys)("anthropic")
    fake_anthropic.Anthropic = FakeClient  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "anthropic", fake_anthropic)

    bridge = AnthropicAPIBridge()
    resp = bridge.invoke(ForgeRequest(prompt="hi", system="sys", max_tokens=50))
    assert resp.text == "hello"
    assert resp.input_tokens == 10
    assert resp.output_tokens == 5
    assert resp.finish_reason == "end_turn"
    assert resp.backend == "anthropic-api"


# --- Claude CLI bridge ----------------------------------------------

def test_cli_bridge_subprocess_failure():
    bridge = ClaudeCLIBridge(binary="false")  # always exits 1
    with pytest.raises(RuntimeError, match="exited"):
        bridge.invoke(ForgeRequest(prompt="hi"))


def test_cli_bridge_missing_binary():
    bridge = ClaudeCLIBridge(binary="/nonexistent/path/claude-xyz")
    with pytest.raises(RuntimeError, match="not found"):
        bridge.invoke(ForgeRequest(prompt="hi"))


# --- factory --------------------------------------------------------

def test_factory_respects_backend_env(monkeypatch):
    monkeypatch.setenv("FORGE_CLAUDE_BACKEND", "mock")
    bridge = get_claude_bridge()
    assert isinstance(bridge, MockClaudeBridge)


def test_factory_picks_api_when_key_present(monkeypatch):
    monkeypatch.delenv("FORGE_CLAUDE_BACKEND", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    bridge = get_claude_bridge()
    assert isinstance(bridge, AnthropicAPIBridge)


def test_factory_falls_back_to_mock(monkeypatch):
    monkeypatch.delenv("FORGE_CLAUDE_BACKEND", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with patch("forge.claude_bridge._has_claude_cli", return_value=False):
        bridge = get_claude_bridge()
    assert isinstance(bridge, MockClaudeBridge)


# --- prompt templates -----------------------------------------------

def test_prompt_template_substitutes_known_keys():
    tmpl = PromptTemplate("Hello {name} — goal: {goal}")
    assert tmpl.render(name="World", goal="x") == "Hello World — goal: x"


def test_prompt_template_leaves_unknown_placeholders_intact():
    tmpl = PromptTemplate("A={a} B={b}")
    assert tmpl.render(a="1") == "A=1 B={b}"


def test_prompt_template_handles_json_dict_values():
    tmpl = PromptTemplate("Data: {payload}")
    out = tmpl.render(payload={"k": 1})
    assert '"k": 1' in out


def test_prompt_template_load_reads_disk(tmp_path):
    root = tmp_path / "forge"
    (root / "fam" / "prompts").mkdir(parents=True)
    (root / "fam" / "prompts" / "p.md").write_text(
        "Hello {name}", encoding="utf-8",
    )
    tmpl = PromptTemplate.load("fam", "p", root=root)
    assert tmpl.render(name="X") == "Hello X"


def test_prompt_template_load_raises_on_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        PromptTemplate.load("missing", "p", root=tmp_path)
