"""Tests for cartridge_runtime.py.

These tests use a ``FakeRuntime`` so they never hit a real LLM, exercise
all three primary classes (Blackboard, CartridgeRegistry, CartridgeRunner),
and validate the packaged reference cartridges' structure.

Run directly:
    pytest tests/test_cartridge_runtime.py -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# Skip the whole module if PyYAML is unavailable — cartridges rely on it.
yaml = pytest.importorskip("yaml")

import cartridge_runtime as cr  # noqa: E402


# ═══════════════════════════════════════════════════════════════════
# Blackboard
# ═══════════════════════════════════════════════════════════════════

class TestBlackboard:
    def test_put_and_get_roundtrip(self):
        bb = cr.Blackboard()
        bb.put("user_goal", "cook pasta", produced_by="user",
               description="what to cook")
        entry = bb.get("user_goal")
        assert entry is not None
        assert entry.value == "cook pasta"
        assert entry.produced_by == "user"
        assert entry.description == "what to cook"

    def test_value_helper_and_default(self):
        bb = cr.Blackboard()
        assert bb.value("missing", default="fallback") == "fallback"
        bb.put("k", 42)
        assert bb.value("k") == 42

    def test_has_and_keys(self):
        bb = cr.Blackboard()
        assert not bb.has("x")
        bb.put("x", 1)
        bb.put("y", 2)
        assert bb.has("x") and bb.has("y")
        assert set(bb.keys()) == {"x", "y"}

    def test_bundle_subset(self):
        bb = cr.Blackboard()
        bb.put("a", 1)
        bb.put("b", 2)
        bb.put("c", 3)
        assert bb.bundle(["a", "c"]) == {"a": 1, "c": 3}
        assert bb.bundle(["missing"]) == {}

    def test_describe_renders_markdown(self):
        bb = cr.Blackboard()
        bb.put("weekly_menu", {"days": []},
               produced_by="menu-planner",
               description="7-day menu with 3 meals")
        out = bb.describe(["weekly_menu"])
        assert "`weekly_menu`" in out
        assert "menu-planner" in out
        assert "7-day menu" in out

    def test_snapshot_shape(self):
        bb = cr.Blackboard()
        bb.put("k", [1, 2, 3], produced_by="agent-x", description="list")
        snap = bb.snapshot()
        assert set(snap["k"]) >= {"value", "schema_ref", "produced_by",
                                  "description", "created_at"}
        assert snap["k"]["value"] == [1, 2, 3]

    def test_schema_validation_minimal_fallback(self, tmp_path):
        # Write a simple schema to disk
        schema = {"type": "object", "required": ["x"]}
        (tmp_path / "thing.schema.json").write_text(json.dumps(schema))
        bb = cr.Blackboard(schemas_dir=tmp_path)
        ok_bad, _ = bb.put("a", {"not_x": 1},
                           schema_ref="thing.schema.json")
        ok_good, _ = bb.put("b", {"x": 123},
                            schema_ref="thing.schema.json")
        assert ok_good is True
        # jsonschema OR minimal check should reject the missing-required case
        assert ok_bad is False

    def test_schema_missing_file_is_not_fatal(self, tmp_path):
        bb = cr.Blackboard(schemas_dir=tmp_path)
        ok, msg = bb.put("k", 1, schema_ref="nonexistent.schema.json")
        assert ok is True
        assert "missing" in msg


class TestMinimalSchemaCheck:
    def test_object_missing_required(self):
        ok, msg = cr._minimal_schema_check(
            {"a": 1}, {"type": "object", "required": ["b"]}
        )
        assert not ok and "missing required" in msg

    def test_array_type_mismatch(self):
        ok, _ = cr._minimal_schema_check("not a list", {"type": "array"})
        assert not ok

    def test_scalar_types(self):
        assert cr._minimal_schema_check("abc", {"type": "string"})[0]
        assert cr._minimal_schema_check(1, {"type": "integer"})[0]
        assert cr._minimal_schema_check(1.5, {"type": "number"})[0]
        assert cr._minimal_schema_check(True, {"type": "boolean"})[0]
        assert not cr._minimal_schema_check("x", {"type": "integer"})[0]


# ═══════════════════════════════════════════════════════════════════
# JSON extraction helpers
# ═══════════════════════════════════════════════════════════════════

class TestJSONHelpers:
    def test_extract_first_json_object(self):
        txt = 'foo {"a": 1, "b": [2, 3]} bar'
        assert cr._extract_first_json_object(txt) == '{"a": 1, "b": [2, 3]}'

    def test_extract_respects_strings(self):
        txt = '{"a": "has } inside"}'
        assert cr._extract_first_json_object(txt) == '{"a": "has } inside"}'

    def test_extract_none_if_unbalanced(self):
        assert cr._extract_first_json_object("no braces here") is None

    def test_split_frontmatter(self):
        text = "---\nname: x\nneeds: [a]\n---\nbody here"
        fm, body = cr._split_frontmatter(text)
        assert fm["name"] == "x"
        assert fm["needs"] == ["a"]
        assert body == "body here"

    def test_split_frontmatter_no_match(self):
        fm, body = cr._split_frontmatter("just body")
        assert fm == {}
        assert body == "just body"


# ═══════════════════════════════════════════════════════════════════
# Registry (against the real cartridges in this repo)
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def registry():
    return cr.CartridgeRegistry(ROOT / "cartridges")


class TestCartridgeRegistry:
    def test_discovers_reference_cartridges(self, registry):
        names = registry.names()
        assert "cooking" in names
        assert "residential-electrical" in names

    def test_get_manifest_fields(self, registry):
        m = registry.get("cooking")
        assert m is not None
        assert m.name == "cooking"
        assert "plan-weekly-menu" in m.flows
        assert m.blackboard_schema.get("weekly_menu") == \
               "weekly_menu.schema.json"
        assert m.max_turns_per_agent >= 1

    def test_load_agent_parses_frontmatter(self, registry):
        spec = registry.load_agent("cooking", "menu-planner")
        assert spec is not None
        assert spec.name == "menu-planner"
        assert "user_goal" in spec.needs
        assert "weekly_menu" in spec.produces
        assert spec.produces_schema == "weekly_menu.schema.json"
        assert "Menu Planner" in spec.body

    def test_agent_not_found(self, registry):
        assert registry.load_agent("cooking", "nope-agent") is None

    def test_match_intent_cooking(self, registry):
        name, score = registry.match_intent(
            "plan weekly menu for 2 vegetarians"
        )
        assert name == "cooking"
        assert score >= 2

    def test_match_intent_electrical(self, registry):
        name, score = registry.match_intent(
            "design electrical installation for a 3-bedroom house"
        )
        assert name == "residential-electrical"
        assert score >= 2

    def test_match_intent_no_match_for_garbage(self, registry):
        name, _ = registry.match_intent("xyzzy plugh frobnicate")
        assert name is None


# ═══════════════════════════════════════════════════════════════════
# CartridgeRunner with a FakeRuntime
# ═══════════════════════════════════════════════════════════════════

class FakeRuntime:
    """Stand-in for AgentRuntime — returns pre-programmed responses per
    (agent_name) so we can deterministically exercise the full flow."""

    def __init__(self, scripted_responses: dict[str, str]):
        self.scripted = scripted_responses
        self.calls: list[tuple[str, str, dict, int]] = []

    def _handle_delegate_to_agent(self, agent_name, task_description,
                                    input_data=None, max_turns=3,
                                    project_dir=""):
        self.calls.append((agent_name, task_description,
                            dict(input_data or {}), max_turns))
        if agent_name not in self.scripted:
            return "<produces>{}</produces>"
        return self.scripted[agent_name]

    def _call_llm(self, messages, **kwargs):
        # Router fallback: always pick the first flow
        return "plan-weekly-menu"


def _fake_menu():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"]
    return {
        "weekly_menu": {
            "household_size": 2,
            "dietary_notes": "vegetarian",
            "days": [
                {"day": d, "meals": [
                    {"slot": "breakfast", "name": "Yogurt", "protein": "yogurt", "prep_minutes": 5},
                    {"slot": "lunch", "name": "Salad", "protein": "chickpeas", "prep_minutes": 15},
                    {"slot": "dinner", "name": "Pasta", "protein": "parmesan", "prep_minutes": 30},
                ]} for d in days
            ],
        }
    }


def _fake_shopping_list():
    return {
        "shopping_list": {
            "household_size": 2,
            "aisles": {
                "produce": [{"item": "tomatoes", "quantity": "1 kg"}],
                "dairy":   [{"item": "yogurt", "quantity": "500 g"},
                            {"item": "parmesan", "quantity": "200 g"}],
                "pantry":  [{"item": "pasta", "quantity": "500 g"}],
                "protein": [{"item": "chickpeas", "quantity": "400 g"}],
                "other":   [],
            }
        }
    }


def _fake_recipes():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday"]
    return {
        "recipes": [
            {
                "name": f"Pasta {d}", "day": d, "servings": 2,
                "total_minutes": 30,
                "ingredients": [
                    {"item": "pasta", "quantity": "200 g"},
                    {"item": "parmesan", "quantity": "50 g"},
                ],
                "steps": ["Boil water.", "Cook pasta.", "Add cheese."],
            }
            for d in days
        ]
    }


def _wrap(payload: dict) -> str:
    return f"Reasoning done.\n<produces>\n{json.dumps(payload)}\n</produces>"


class TestCartridgeRunner:
    def test_end_to_end_cooking_happy_path(self, registry):
        rt = FakeRuntime({
            "menu-planner":          _wrap(_fake_menu()),
            "shopping-list-builder": _wrap(_fake_shopping_list()),
            "recipe-writer":         _wrap(_fake_recipes()),
        })
        runner = cr.CartridgeRunner(rt, registry, verbose=False,
                                     max_retries_per_step=0)
        result = runner.run(
            "cooking",
            "plan weekly menu for 2 vegetarians",
            flow="plan-weekly-menu",
        )
        assert result.flow == "plan-weekly-menu"
        assert len(result.steps) == 3
        assert all(s.validated for s in result.steps)
        assert result.ok is True
        assert "weekly_menu" in result.blackboard
        assert "shopping_list" in result.blackboard
        assert "recipes" in result.blackboard
        # FakeRuntime got the expected chained inputs
        call_agents = [c[0] for c in rt.calls]
        assert call_agents == ["menu-planner", "shopping-list-builder",
                                "recipe-writer"]
        # shopping-list-builder received weekly_menu on its input_data
        assert "weekly_menu" in rt.calls[1][2]

    def test_missing_produces_tag_causes_failure(self, registry):
        rt = FakeRuntime({
            "menu-planner": "No tag here, just prose.",
        })
        runner = cr.CartridgeRunner(rt, registry, verbose=False,
                                     max_retries_per_step=0)
        result = runner.run("cooking", "plan weekly menu",
                            flow="quick-shopping-list")
        menu_step = result.steps[0]
        assert not menu_step.validated
        assert "produces" in menu_step.message.lower()

    def test_retry_on_schema_failure(self, registry):
        # First attempt: missing 'days'. Second attempt: valid.
        responses = iter([
            _wrap({"weekly_menu": {"household_size": 2}}),  # invalid
            _wrap(_fake_menu()),                            # valid
        ])

        class RetryingFake(FakeRuntime):
            def _handle_delegate_to_agent(self, agent_name,
                                          task_description,
                                          input_data=None, max_turns=3,
                                          project_dir=""):
                self.calls.append((agent_name, task_description,
                                    dict(input_data or {}), max_turns))
                if agent_name == "menu-planner":
                    return next(responses)
                if agent_name == "shopping-list-builder":
                    return _wrap(_fake_shopping_list())
                return "<produces>{}</produces>"

        rt = RetryingFake({})
        runner = cr.CartridgeRunner(rt, registry, verbose=False,
                                     max_retries_per_step=1)
        result = runner.run("cooking", "plan weekly menu",
                            flow="quick-shopping-list")
        # Runner must have called menu-planner twice total
        planner_calls = [c for c in rt.calls if c[0] == "menu-planner"]
        assert len(planner_calls) == 2
        # Final step for menu-planner must be validated
        menu_step = next(s for s in result.steps if s.agent == "menu-planner")
        assert menu_step.validated is True

    def test_deterministic_validator_runs(self, registry):
        rt = FakeRuntime({
            "menu-planner":          _wrap(_fake_menu()),
            "shopping-list-builder": _wrap(_fake_shopping_list()),
            "recipe-writer":         _wrap(_fake_recipes()),
        })
        runner = cr.CartridgeRunner(rt, registry, verbose=False,
                                     max_retries_per_step=0)
        result = runner.run("cooking", "plan weekly menu")
        # menu_complete.py + shopping_list_sane.py should both pass
        assert result.ok is True

    def test_unknown_cartridge_raises(self, registry):
        rt = FakeRuntime({})
        runner = cr.CartridgeRunner(rt, registry, verbose=False)
        with pytest.raises(KeyError):
            runner.run("nonexistent", "goal")

    def test_unknown_flow_raises(self, registry):
        rt = FakeRuntime({})
        runner = cr.CartridgeRunner(rt, registry, verbose=False)
        with pytest.raises(KeyError):
            runner.run("cooking", "goal", flow="no-such-flow")


# ═══════════════════════════════════════════════════════════════════
# Reference cartridge structural integrity
# ═══════════════════════════════════════════════════════════════════

class TestReferenceCartridges:
    def test_cooking_has_expected_files(self):
        base = ROOT / "cartridges" / "cooking"
        assert (base / "cartridge.yaml").is_file()
        assert (base / "router.md").is_file()
        for agent in ("menu-planner", "shopping-list-builder",
                       "recipe-writer"):
            assert (base / "agents" / f"{agent}.md").is_file()
        for schema in ("weekly_menu", "shopping_list", "recipes"):
            assert (base / "schemas" / f"{schema}.schema.json").is_file()
        for val in ("menu_complete.py", "shopping_list_sane.py"):
            assert (base / "validators" / val).is_file()
        assert (base / "evals" / "cases.yaml").is_file()

    def test_electrical_has_expected_files(self):
        base = ROOT / "cartridges" / "residential-electrical"
        assert (base / "cartridge.yaml").is_file()
        for agent in ("load-calculator", "circuit-designer"):
            assert (base / "agents" / f"{agent}.md").is_file()
        for schema in ("load_profile", "circuits"):
            assert (base / "schemas" / f"{schema}.schema.json").is_file()
        assert (base / "validators" / "compliance_checker.py").is_file()

    def test_electrical_compliance_checker_catches_wet_room_without_rcd(self):
        """Regression: the validator must flag wet-room circuits missing RCD."""
        import importlib.util
        path = ROOT / "cartridges" / "residential-electrical" / \
               "validators" / "compliance_checker.py"
        spec = importlib.util.spec_from_file_location("cc", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        snapshot = {
            "load_profile": {"value": {
                "voltage_v": 230,
                "rooms": [{"name": "kitchen",
                            "loads": [{"appliance": "refrigerator",
                                        "watts": 250,
                                        "circuit_type": "dedicated"}]}],
            }},
            "circuits": {"value": [{
                "id": "C1", "label": "Kitchen fridge",
                "type": "dedicated", "breaker_a": 16, "wire_mm2": 2.5,
                "rcd": False,  # ← violation
                "loads": ["kitchen/refrigerator"],
            }]},
        }
        ok, msg = mod.validate(snapshot)
        assert not ok
        assert "wet room" in msg.lower() or "rcd" in msg.lower()

    def test_electrical_compliance_checker_passes_valid_design(self):
        import importlib.util
        path = ROOT / "cartridges" / "residential-electrical" / \
               "validators" / "compliance_checker.py"
        spec = importlib.util.spec_from_file_location("cc2", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        snapshot = {
            "load_profile": {"value": {
                "voltage_v": 230,
                "rooms": [{"name": "livingroom",
                            "loads": [{"appliance": "lighting",
                                        "watts": 200,
                                        "circuit_type": "lighting"}]}],
            }},
            "circuits": {"value": [{
                "id": "C1", "label": "Living room lights",
                "type": "lighting", "breaker_a": 10, "wire_mm2": 1.5,
                "rcd": False,
                "loads": ["livingroom/lighting"],
            }]},
        }
        ok, msg = mod.validate(snapshot)
        assert ok, f"expected clean design to pass, got: {msg}"

    def test_cooking_menu_validator(self):
        import importlib.util
        path = ROOT / "cartridges" / "cooking" / \
               "validators" / "menu_complete.py"
        spec = importlib.util.spec_from_file_location("mc", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Truncated menu (only 3 days) should fail
        bad = {"weekly_menu": {"value": {"days": [
            {"day": "Monday", "meals": []},
        ] * 3}}}
        ok, _ = mod.validate(bad)
        assert not ok

        # 7-day well-formed menu should pass
        days = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]
        good = {"weekly_menu": {"value": {"days": [
            {"day": d, "meals": [
                {"slot": "breakfast"},
                {"slot": "lunch"},
                {"slot": "dinner"},
            ]} for d in days
        ]}}}
        ok, _ = mod.validate(good)
        assert ok
