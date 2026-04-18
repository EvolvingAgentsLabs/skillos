"""Integration tests for the gemma4-skills experiment.

Tests the full pipeline: skill loading → JS execution → cartridge integration.
Run with: python test_skills.py (or pytest test_skills.py)
"""

from __future__ import annotations

import json
import os
import sys
import io
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
from js_executor import run_skill, run_skill_by_name, SkillResult

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
        """Load a single skill from its directory."""
        skill_dir = None
        for d in [GALLERY_BUILT_IN]:
            candidate = d / "calculate-hash"
            if candidate.exists():
                skill_dir = candidate
                break
        assert skill_dir, "calculate-hash skill directory not found"
        skill = load_skill(skill_dir)
        assert skill is not None
        assert skill.name == "calculate-hash"
        assert "hash" in skill.description.lower()
        assert skill.js_path.endswith("index.js")
        assert os.path.isabs(skill.js_path)
        assert not skill.require_secret

    def test_registry_discovers_all_skills(self):
        """Registry finds all 11 Gallery skills."""
        reg = _get_registry()
        assert len(reg) >= 8  # at minimum the built-in ones
        assert reg.has("calculate-hash")
        assert reg.has("query-wikipedia")
        assert reg.has("text-spinner")

    def test_registry_descriptions(self):
        """Descriptions formatted for LLM context."""
        reg = _get_registry()
        desc = reg.descriptions()
        assert "calculate-hash" in desc
        assert "query-wikipedia" in desc

    def test_skill_not_found(self):
        """Nonexistent skill returns None."""
        reg = _get_registry()
        assert reg.get("nonexistent-skill") is None

    def test_skill_with_secret(self):
        """Skills requiring a secret are flagged."""
        reg = _get_registry()
        rr = reg.get("restaurant-roulette")
        if rr:
            assert rr.require_secret is True


# ── JS Executor Tests ───────────────────────────────────────────────

class TestJsExecutor:

    def test_calculate_hash(self):
        """calculate-hash returns correct SHA-1."""
        reg = _get_registry()
        result = run_skill_by_name(reg, "calculate-hash",
                                   json.dumps({"text": "hello world"}))
        assert result.ok, f"Skill failed: {result.error}"
        assert result.result == "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed"

    def test_calculate_hash_empty(self):
        """SHA-1 of empty string."""
        reg = _get_registry()
        result = run_skill_by_name(reg, "calculate-hash",
                                   json.dumps({"text": ""}))
        assert result.ok, f"Skill failed: {result.error}"
        assert result.result == "da39a3ee5e6b4b0d3255bfef95601890afd80709"

    def test_text_spinner(self):
        """text-spinner returns a webview."""
        reg = _get_registry()
        result = run_skill_by_name(reg, "text-spinner",
                                   json.dumps({"text": "Hello"}))
        assert result.ok, f"Skill failed: {result.error}"
        # text-spinner returns a webview, not a text result
        assert result.webview is not None or result.result is not None

    def test_skill_not_found_error(self):
        """Executing nonexistent skill returns error."""
        reg = _get_registry()
        result = run_skill_by_name(reg, "nonexistent", "{}")
        assert not result.ok
        assert "not found" in result.error

    def test_invalid_json_data(self):
        """Skill handles invalid JSON data gracefully."""
        reg = _get_registry()
        result = run_skill_by_name(reg, "calculate-hash", "not json")
        # Should fail gracefully, not crash
        assert not result.ok or result.result is not None


# ── Cartridge Integration Tests ─────────────────────────────────────

class TestCartridgeIntegration:

    def test_demo_cartridge_discovered(self):
        """Demo cartridge appears in the registry."""
        from cartridge_runtime import CartridgeRegistry
        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))
        manifest = reg.get("demo")
        assert manifest is not None
        assert manifest.type == "js-skills"
        assert "run-skill" in manifest.flows

    def test_demo_cartridge_skills_loaded(self):
        """CartridgeRunner can load JS skills for demo cartridge."""
        from cartridge_runtime import CartridgeRegistry, CartridgeRunner

        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))

        class MockRuntime:
            def _call_llm(self, messages):
                return ""

        runner = CartridgeRunner(MockRuntime(), reg, verbose=False)
        manifest = reg.get("demo")
        skill_reg = runner._get_skill_registry(manifest)
        assert len(skill_reg) >= 8

    def test_keyword_routing(self):
        """Keyword router selects correct skills."""
        from cartridge_runtime import CartridgeRegistry, CartridgeRunner

        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))

        class MockRuntime:
            def _call_llm(self, messages):
                return ""

        runner = CartridgeRunner(MockRuntime(), reg, verbose=False)
        manifest = reg.get("demo")
        skill_reg = runner._get_skill_registry(manifest)

        assert runner._route_to_skill(manifest, "calculate hash of test", skill_reg) == "calculate-hash"
        assert runner._route_to_skill(manifest, "wikipedia Albert Einstein", skill_reg) == "query-wikipedia"
        assert runner._route_to_skill(manifest, "log my mood", skill_reg) == "mood-tracker"
        assert runner._route_to_skill(manifest, "generate qr code", skill_reg) == "qr-code"

    def test_js_executor_step(self):
        """Full js-executor step through CartridgeRunner."""
        from cartridge_runtime import CartridgeRegistry, CartridgeRunner, Blackboard

        reg = CartridgeRegistry(str(SKILLOS_DIR / "cartridges"))

        class MockRuntime:
            def _call_llm(self, messages):
                return ""

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


# ── Runner ──────────────────────────────────────────────────────────

def run_tests():
    """Simple test runner without pytest dependency."""
    passed = 0
    failed = 0
    errors = []

    test_classes = [TestSkillLoader, TestJsExecutor, TestCartridgeIntegration]

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
