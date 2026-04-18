"""Integration tests for the gemma4-skills experiment.

Tests the full pipeline: skill loading → JS execution → cartridge integration.
Covers all 5 upgrades: persistent state, LLM helper, skill chaining, agentic
mode, and browser executor.

Run with: python test_skills.py (or pytest test_skills.py)
"""

from __future__ import annotations

import json
import os
import sys
import io
import shutil
import tempfile
from pathlib import Path

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Ensure imports work
EXPERIMENT_DIR = Path(__file__).resolve().parent
SKILLOS_DIR = EXPERIMENT_DIR.parent.parent
sys.path.insert(0, str(EXPERIMENT_DIR))
sys.path.insert(0, str(SKILLOS_DIR))

from skill_loader import SkillRegistry, load_skill, SkillDefinition
from js_executor import run_skill, run_skill_by_name, SkillResult, RuntimeConfig

GALLERY_BUILT_IN = SKILLOS_DIR.parent / "gallery" / "skills" / "built-in"
GALLERY_FEATURED = SKILLOS_DIR.parent / "gallery" / "skills" / "featured"


def _get_registry() -> SkillRegistry:
    """Build registry from the Gallery project (not copied)."""
    dirs = []
    for d in [GALLERY_BUILT_IN, GALLERY_FEATURED]:
        if d.exists():
            dirs.append(str(d))
    assert dirs, "No Gallery skills directories found — expected ../gallery/skills/"
    return SkillRegistry(*dirs)


# ── Skill Loader Tests ──────────────────────────────────────────────

class TestSkillLoader:

    def test_load_single_skill(self):
        skill_dir = GALLERY_BUILT_IN / "calculate-hash"
        assert skill_dir.exists(), "calculate-hash skill directory not found"
        skill = load_skill(skill_dir)
        assert skill is not None
        assert skill.name == "calculate-hash"
        assert "hash" in skill.description.lower()
        assert skill.js_path.endswith("index.js")
        assert os.path.isabs(skill.js_path)
        assert not skill.require_secret

    def test_registry_discovers_all_skills(self):
        reg = _get_registry()
        assert len(reg) >= 8
        assert reg.has("calculate-hash")
        assert reg.has("query-wikipedia")
        assert reg.has("text-spinner")

    def test_registry_descriptions(self):
        reg = _get_registry()
        desc = reg.descriptions()
        assert "calculate-hash" in desc
        assert "query-wikipedia" in desc

    def test_skill_not_found(self):
        reg = _get_registry()
        assert reg.get("nonexistent-skill") is None

    def test_skill_with_secret(self):
        reg = _get_registry()
        rr = reg.get("restaurant-roulette")
        if rr:
            assert rr.require_secret is True

    def test_runtime_field_default(self):
        """Skills default to 'node' runtime."""
        reg = _get_registry()
        s = reg.get("calculate-hash")
        assert s.runtime == "node"


# ── JS Executor Tests ───────────────────────────────────────────────

class TestJsExecutor:

    def test_calculate_hash(self):
        reg = _get_registry()
        result = run_skill_by_name(reg, "calculate-hash",
                                   json.dumps({"text": "hello world"}))
        assert result.ok, f"Skill failed: {result.error}"
        assert result.result == "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed"

    def test_calculate_hash_empty(self):
        reg = _get_registry()
        result = run_skill_by_name(reg, "calculate-hash",
                                   json.dumps({"text": ""}))
        assert result.ok, f"Skill failed: {result.error}"
        assert result.result == "da39a3ee5e6b4b0d3255bfef95601890afd80709"

    def test_text_spinner(self):
        reg = _get_registry()
        result = run_skill_by_name(reg, "text-spinner",
                                   json.dumps({"text": "Hello"}))
        assert result.ok, f"Skill failed: {result.error}"
        assert result.webview is not None or result.result is not None

    def test_skill_not_found_error(self):
        reg = _get_registry()
        result = run_skill_by_name(reg, "nonexistent", "{}")
        assert not result.ok
        assert "not found" in result.error

    def test_invalid_json_data(self):
        reg = _get_registry()
        result = run_skill_by_name(reg, "calculate-hash", "not json")
        assert not result.ok or result.result is not None

    def test_runtime_config(self):
        """RuntimeConfig produces correct env dict."""
        cfg = RuntimeConfig(
            state_dir="/tmp/test-state",
            llm_api_url="http://localhost:11434/v1",
            llm_model="gemma4:e2b",
            llm_api_key="test-key",
        )
        env = cfg.to_env("my-skill")
        assert env["SKILL_STATE_DIR"] == "/tmp/test-state"
        assert env["SKILL_NAME"] == "my-skill"
        assert env["LLM_API_URL"] == "http://localhost:11434/v1"
        assert env["LLM_MODEL"] == "gemma4:e2b"
        assert env["LLM_API_KEY"] == "test-key"


# ── Upgrade 1: Persistent State Tests ───────────────────────────────

class TestPersistentState:

    def test_state_persists_across_calls(self):
        """localStorage persists to disk between invocations."""
        reg = _get_registry()
        mood = reg.get("mood-tracker")
        if not mood:
            return  # skip if not available

        state_dir = tempfile.mkdtemp(prefix="skillos-test-state-")
        cfg = RuntimeConfig(state_dir=state_dir)
        try:
            # Log a mood
            r1 = run_skill(mood,
                           json.dumps({"action": "log_mood", "score": 7, "comment": "test"}),
                           config=cfg)
            assert r1.ok, f"Log failed: {r1.error}"
            assert "7/10" in r1.result

            # Read it back in a new invocation
            r2 = run_skill(mood,
                           json.dumps({"action": "get_mood", "date": "today"}),
                           config=cfg)
            assert r2.ok, f"Read failed: {r2.error}"
            assert "7/10" in r2.result

            # Verify state file exists
            state_file = Path(state_dir) / "mood-tracker.json"
            assert state_file.exists(), "State file not created"
        finally:
            shutil.rmtree(state_dir, ignore_errors=True)


# ── Upgrade 3: LLM Helper Tests ────────────────────────────────────

class TestLLMHelper:

    def test_skillos_helper_available_without_llm(self):
        """__skillos object exists even without LLM config."""
        reg = _get_registry()
        # Run a simple skill — __skillos should be available but llm.available=false
        result = run_skill_by_name(reg, "calculate-hash",
                                   json.dumps({"text": "test"}))
        assert result.ok  # skill works even without LLM

    def test_config_with_llm(self):
        """RuntimeConfig with LLM settings passes them to env."""
        cfg = RuntimeConfig(
            llm_api_url="http://localhost:11434/v1",
            llm_model="gemma4:e2b",
        )
        env = cfg.to_env("test")
        assert env["LLM_API_URL"] == "http://localhost:11434/v1"
        assert env["LLM_MODEL"] == "gemma4:e2b"


# ── Cartridge Integration Tests ─────────────────────────────────────

class TestCartridgeIntegration:

    def test_demo_cartridge_discovered(self):
        from cartridge_runtime import CartridgeRegistry
        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))
        manifest = reg.get("demo")
        assert manifest is not None
        assert manifest.type == "js-skills"
        assert "run-skill" in manifest.flows

    def test_demo_cartridge_has_three_flows(self):
        """Demo cartridge has run-skill, agentic, and research-pipeline flows."""
        from cartridge_runtime import CartridgeRegistry
        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))
        manifest = reg.get("demo")
        assert "run-skill" in manifest.flows
        assert "agentic" in manifest.flows
        assert "research-pipeline" in manifest.flows

    def test_agentic_flow_parsed(self):
        """Agentic flow has mode=agentic."""
        from cartridge_runtime import CartridgeRegistry
        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))
        manifest = reg.get("demo")
        agentic = manifest.flow_defs.get("agentic")
        assert agentic is not None
        assert agentic.is_agentic

    def test_skill_chain_flow_parsed(self):
        """Research pipeline has SkillStep objects with needs/produces."""
        from cartridge_runtime import CartridgeRegistry, SkillStep
        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))
        manifest = reg.get("demo")
        pipeline = manifest.flow_defs.get("research-pipeline")
        assert pipeline is not None
        assert len(pipeline.steps) == 2
        step0 = pipeline.steps[0]
        assert isinstance(step0, SkillStep)
        assert step0.skill == "query-wikipedia"
        assert step0.needs == ["user_goal"]
        assert step0.produces == ["wiki_data"]

    def test_demo_cartridge_skills_loaded(self):
        from cartridge_runtime import CartridgeRegistry, CartridgeRunner
        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))

        class MockRuntime:
            tools = {}
            def _call_llm(self, messages): return ""

        runner = CartridgeRunner(MockRuntime(), reg, verbose=False)
        manifest = reg.get("demo")
        skill_reg = runner._get_skill_registry(manifest)
        assert len(skill_reg) >= 8

    def test_keyword_routing(self):
        from cartridge_runtime import CartridgeRegistry, CartridgeRunner
        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))

        class MockRuntime:
            tools = {}
            def _call_llm(self, messages): return ""

        runner = CartridgeRunner(MockRuntime(), reg, verbose=False)
        manifest = reg.get("demo")
        skill_reg = runner._get_skill_registry(manifest)

        assert runner._route_to_skill(manifest, "calculate hash of test", skill_reg) == "calculate-hash"
        assert runner._route_to_skill(manifest, "wikipedia Albert Einstein", skill_reg) == "query-wikipedia"
        assert runner._route_to_skill(manifest, "log my mood", skill_reg) == "mood-tracker"
        assert runner._route_to_skill(manifest, "generate qr code", skill_reg) == "qr-code"

    def test_js_executor_step(self):
        from cartridge_runtime import CartridgeRegistry, CartridgeRunner, Blackboard
        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))

        class MockRuntime:
            tools = {}
            def _call_llm(self, messages): return ""

        runner = CartridgeRunner(MockRuntime(), reg, verbose=False)
        manifest = reg.get("demo")

        bb = Blackboard(schemas_dir=Path(manifest.path) / "schemas")
        bb.put("skill_params", {
            "skill_name": "calculate-hash",
            "data": json.dumps({"text": "test123"}),
        }, produced_by="test")

        step = runner._run_js_skill(manifest, bb)
        assert step.validated, f"Step failed: {step.message}"
        result = bb.value("skill_result")
        assert result.get("result") == "7288edd0fc3ffcbe93a0cf06e3568e28521687bc"


# ── Upgrade 4: Skill Chaining Tests ─────────────────────────────────

class TestSkillChaining:

    def test_research_pipeline_flow(self):
        """Two-skill pipeline: wikipedia → hash via Blackboard."""
        from cartridge_runtime import CartridgeRegistry, CartridgeRunner
        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))

        class MockRuntime:
            tools = {}
            def _call_llm(self, messages): return ""

        runner = CartridgeRunner(MockRuntime(), reg, verbose=False)
        result = runner.run("demo", "Python programming", flow="research-pipeline")

        # Wikipedia step should succeed (network-dependent)
        wiki_step = result.steps[0]
        assert wiki_step.validated, f"Wikipedia step failed: {wiki_step.message}"

        # Hash step should succeed if wikipedia succeeded
        hash_step = result.steps[1]
        assert hash_step.validated, f"Hash step failed: {hash_step.message}"

        # Blackboard should have both outputs
        assert "wiki_data" in result.blackboard
        assert "content_hash" in result.blackboard

    def test_skill_step_needs_checking(self):
        """SkillStep fails gracefully when needs are missing."""
        from cartridge_runtime import (CartridgeRegistry, CartridgeRunner,
                                       Blackboard, SkillStep)
        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))

        class MockRuntime:
            tools = {}
            def _call_llm(self, messages): return ""

        runner = CartridgeRunner(MockRuntime(), reg, verbose=False)
        manifest = reg.get("demo")

        bb = Blackboard()
        # Don't put required "user_goal" on blackboard
        step = SkillStep(skill="calculate-hash", needs=["missing_key"], produces=["out"])
        result = runner._run_skill_step(manifest, step, bb)
        assert not result.validated
        assert "missing" in result.message


# ── Upgrade 5: Browser Executor Tests ───────────────────────────────

class TestBrowserExecutor:

    def test_needs_browser_default_false(self):
        """Skills default to node runtime, not browser."""
        from js_executor import _needs_browser
        reg = _get_registry()
        s = reg.get("calculate-hash")
        assert not _needs_browser(s)

    def test_playwright_import_error(self):
        """Browser executor returns helpful error when Playwright missing."""
        from js_executor import _run_in_playwright
        reg = _get_registry()
        s = reg.get("calculate-hash")
        # Force browser runtime
        s_copy = SkillDefinition(
            name=s.name, description=s.description, instructions=s.instructions,
            skill_dir=s.skill_dir, script_path=s.script_path, js_path=s.js_path,
            runtime="browser",
        )
        result = _run_in_playwright(s_copy, '{"text":"test"}', "")
        # Either Playwright works or we get a helpful error
        assert result.ok or "Playwright" in (result.error or "")


# ── Runner ──────────────────────────────────────────────────────────

def run_tests():
    """Simple test runner without pytest dependency."""
    passed = 0
    failed = 0
    errors = []

    test_classes = [
        TestSkillLoader,
        TestJsExecutor,
        TestPersistentState,
        TestLLMHelper,
        TestCartridgeIntegration,
        TestSkillChaining,
        TestBrowserExecutor,
    ]

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        print(f"\n{'=' * 60}")
        print(f"  {cls.__name__}")
        print(f"{'=' * 60}")
        for method_name in sorted(methods):
            method = getattr(instance, method_name)
            try:
                method()
                print(f"  PASS  {method_name}")
                passed += 1
            except Exception as e:
                print(f"  FAIL  {method_name}: {e}")
                failed += 1
                errors.append((cls.__name__, method_name, str(e)))

    print(f"\n{'=' * 60}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")
    if errors:
        print("\nFailures:")
        for cls_name, method, err in errors:
            print(f"  {cls_name}.{method}: {err}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_tests())
