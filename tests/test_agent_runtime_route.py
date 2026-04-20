"""AgentRuntime.route_and_execute smoke tests.

Exercises the new router entry point at the AgentRuntime surface.  The
AgentRuntime itself is expensive to construct (it loads a manifest and
instantiates an OpenAI client), so these tests build a minimal runtime
with openai mocked out via the existing ``load_qwen_module`` helper.

The hot-tier branch is not exercised here (that would require a real or
stubbed Ollama endpoint); ``test_runtime_qwen.py`` covers it already.
We focus on the router dispatch table: offline gate, forge-tier
delegation, escalation, and the warm-tier model swap.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    import agent_runtime as _agent_runtime_mod  # noqa: E402
except Exception:  # pragma: no cover
    _agent_runtime_mod = None


@pytest.fixture
def rt(tmp_path):
    """Build an AgentRuntime with its constructor heavily stubbed.

    We bypass ``__init__`` entirely because it would try to open an Ollama
    endpoint, and swap in just the attributes ``route_and_execute`` reads.
    """
    if _agent_runtime_mod is None:
        pytest.skip("agent_runtime not importable in this environment")
    runtime = _agent_runtime_mod.AgentRuntime.__new__(
        _agent_runtime_mod.AgentRuntime
    )
    runtime.model = "gemma4:e2b"
    runtime.provider_name = "gemma"
    runtime.client = MagicMock()

    # Capture calls to run_goal so we can assert what the router dispatched.
    runtime._captured_goals = []

    def fake_run_goal(goal, **kw):
        runtime._captured_goals.append(goal)
        return f"ran: {goal}"

    runtime.run_goal = fake_run_goal  # type: ignore[method-assign]
    return runtime


def test_route_escalates_when_offline_and_no_skill(rt, tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLOS_FORGE_OFFLINE", "1")
    outcome = rt.route_and_execute(
        "build a thing that does not exist yet",
        project_path=tmp_path,
    )
    assert outcome["tier"] == "escalate"
    assert outcome["status"] == "blocked"
    assert outcome["kind"] == "forge_disabled"
    assert rt._captured_goals == []  # hot path never invoked


def test_route_hot_tier_runs_goal_with_cartridge(rt, tmp_path):
    outcome = rt.route_and_execute(
        "make breakfast",
        project_path=tmp_path,
        candidate_cartridge="cooking",
    )
    assert outcome["tier"] == "hot"
    assert outcome["kind"] == "cartridge"
    assert outcome["status"] == "executed"
    assert rt._captured_goals == ["make breakfast"]


def test_route_warm_tier_swaps_model_then_restores(rt, tmp_path, monkeypatch):
    # Stage a weak attestation so the router picks the warm tier.
    monkeypatch.setenv("GEMMA_FALLBACK_MODEL", "gemma4:e4b")
    manifest = tmp_path / "weak.manifest.md"
    manifest.write_text("""---
skill_id: x
gemma_compat:
  model: gemma4:e2b
  validated_at: "2026-04-15T00:00:00Z"
  pass_rate: 0.85
  cases_total: 10
  cases_passed: 8
---
""", encoding="utf-8")

    seen_models: list[str] = []

    def run_goal_capturing(goal, **kw):
        seen_models.append(rt.model)
        return "ok"

    rt.run_goal = run_goal_capturing  # type: ignore[method-assign]

    outcome = rt.route_and_execute(
        "do the weak thing",
        project_path=tmp_path,
        candidate_skill_manifest=manifest,
    )
    assert outcome["tier"] == "warm"
    assert seen_models == ["gemma4:e4b"]
    # Model is restored after the call.
    assert rt.model == "gemma4:e2b"


def test_route_forge_blocks_without_project_path(rt):
    # No project_path supplied — forge cannot run, must refuse gracefully.
    outcome = rt.route_and_execute(
        "invent a new skill",
        project_path=None,
    )
    # Router falls through to FORGE/generate but executor requires a path.
    # The runtime method rejects before touching the executor.
    assert outcome["status"] == "blocked"
    assert "project_path" in outcome["rationale"]


def test_route_forge_delegates_to_executor(rt, tmp_path, monkeypatch):
    """When the router picks FORGE/GENERATE, route_and_execute delegates
    to ForgeExecutor.  We stub the executor to avoid real bridge calls.
    """
    fake_result = MagicMock(
        outcome="pass", job_id="jx",
        candidates_path=tmp_path / "forge" / "candidates" / "jx",
        notes="ok",
    )
    with patch("forge.executor.ForgeExecutor.run",
               return_value=fake_result) as run_mock:
        outcome = rt.route_and_execute(
            "make a new skill",
            project_path=tmp_path,
        )
    assert outcome["tier"] == "forge"
    assert outcome["status"] == "forge_pass"
    assert outcome["job_id"] == "jx"
    run_mock.assert_called_once()
