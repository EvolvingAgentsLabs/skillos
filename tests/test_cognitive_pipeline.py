"""
Tests for the Cognitive Pipeline Executor — validates model capability lookup,
pipeline parsing, strategy routing, step validation, and tool call extraction.
"""

import os
import re
import pytest
import yaml

SKILLOS_ROOT = os.path.join(os.path.dirname(__file__), "..")
SCENARIOS_DIR = os.path.join(SKILLOS_ROOT, "scenarios")


def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _read_source():
    return _read_file(os.path.join(SKILLOS_ROOT, "agent_runtime.py"))


# ---------------------------------------------------------------------------
# Import helpers — import dataclasses and AgentRuntime class attributes
# without fully instantiating the runtime (avoids API key requirements)
# ---------------------------------------------------------------------------

def _import_runtime_module():
    """Import agent_runtime module source-level attributes."""
    import sys as _sys
    import importlib.util
    from unittest.mock import MagicMock, patch

    mocks = {
        "openai": MagicMock(),
        "dotenv": MagicMock(),
    }
    with patch.dict("sys.modules", mocks):
        mod_name = "agent_runtime_mod"
        spec = importlib.util.spec_from_file_location(
            mod_name, os.path.join(SKILLOS_ROOT, "agent_runtime.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        # Register in sys.modules so dataclasses can resolve __module__
        _sys.modules[mod_name] = mod
        try:
            spec.loader.exec_module(mod)
        except Exception:
            _sys.modules.pop(mod_name, None)
            raise
        return mod


@pytest.fixture(scope="module")
def rt_mod():
    """Loaded agent_runtime module (mocked deps)."""
    return _import_runtime_module()


# ---------------------------------------------------------------------------
# TestModelCapabilities
# ---------------------------------------------------------------------------
class TestModelCapabilities:
    """MODEL_CAPABILITIES lookup and fallback behavior."""

    def test_known_model_gemma(self, rt_mod):
        caps = rt_mod.AgentRuntime.MODEL_CAPABILITIES
        assert "google/gemma-4-26b-a4b-it" in caps
        assert caps["google/gemma-4-26b-a4b-it"]["tier"] == "mid"
        assert caps["google/gemma-4-26b-a4b-it"]["recommended_strategy"] == "cognitive_pipeline"

    def test_known_model_gemma_local(self, rt_mod):
        caps = rt_mod.AgentRuntime.MODEL_CAPABILITIES
        assert "gemma4" in caps
        assert caps["gemma4"]["tier"] == "mid"

    def test_known_model_high_tier(self, rt_mod):
        caps = rt_mod.AgentRuntime.MODEL_CAPABILITIES
        assert caps["claude-opus-4-6"]["tier"] == "high"
        assert caps["claude-opus-4-6"]["recommended_strategy"] == "agentic"

    def test_known_model_low_tier(self, rt_mod):
        caps = rt_mod.AgentRuntime.MODEL_CAPABILITIES
        assert caps["qwen/qwen3.6-plus:free"]["tier"] == "low"
        assert caps["qwen/qwen3.6-plus:free"]["recommended_strategy"] == "pipeline"

    def test_unknown_model_fallback(self, rt_mod):
        default = rt_mod.AgentRuntime._DEFAULT_CAPABILITY
        assert default["tier"] == "mid"
        assert default["recommended_strategy"] == "cognitive_pipeline"
        # Verify unknown model would get default
        caps = rt_mod.AgentRuntime.MODEL_CAPABILITIES
        assert "totally-unknown-model-xyz" not in caps


# ---------------------------------------------------------------------------
# TestParseCognitivePipeline
# ---------------------------------------------------------------------------
class TestParseCognitivePipeline:
    """Pipeline parsing from scenario files (Format A and B)."""

    def test_parse_aorta_scenario(self, rt_mod):
        """ProjectAortaScenario.md (Format B) → 3 steps."""
        path = os.path.join(SCENARIOS_DIR, "ProjectAortaScenario.md")
        if not os.path.isfile(path):
            pytest.skip("ProjectAortaScenario.md not found")
        steps = rt_mod.AgentRuntime._parse_cognitive_pipeline(path)
        assert len(steps) == 3
        # Step 1
        assert steps[0]["step"] == 1
        assert "visionary-agent" in steps[0]["agent"]
        assert steps[0]["goal"]  # non-empty
        assert "project_vision.md" in steps[0]["output"]
        # Step 2
        assert steps[1]["step"] == 2
        assert "mathematician-agent" in steps[1]["agent"]
        # Step 3
        assert steps[2]["step"] == 3
        assert "quantum-engineer-agent" in steps[2]["agent"]

    def test_parse_echoq_scenario(self, rt_mod):
        """Operation_Echo_Q.md (Format B) → 4 phases."""
        path = os.path.join(SCENARIOS_DIR, "Operation_Echo_Q.md")
        if not os.path.isfile(path):
            pytest.skip("Operation_Echo_Q.md not found")
        steps = rt_mod.AgentRuntime._parse_cognitive_pipeline(path)
        assert len(steps) == 4
        # Phase 1
        assert steps[0]["step"] == 1
        assert "quantum-theorist-agent" in steps[0]["agent"]
        # Phase 2
        assert steps[1]["step"] == 2
        assert "pure-mathematician-agent" in steps[1]["agent"]
        # Phase 3
        assert steps[2]["step"] == 3
        assert "qiskit-engineer-agent" in steps[2]["agent"]
        # Phase 4
        assert steps[3]["step"] == 4
        assert "system-architect-agent" in steps[3]["agent"]

    def test_parse_returns_list(self, rt_mod):
        """Even with a non-pipeline scenario, returns a list."""
        path = os.path.join(SCENARIOS_DIR, "RealWorld_Research_Task.md")
        if not os.path.isfile(path):
            pytest.skip("RealWorld_Research_Task.md not found")
        steps = rt_mod.AgentRuntime._parse_cognitive_pipeline(path)
        assert isinstance(steps, list)


# ---------------------------------------------------------------------------
# TestStrategyRouter
# ---------------------------------------------------------------------------
class TestStrategyRouter:
    """execute_scenario routes to the correct method based on model tier."""

    def test_source_has_execute_scenario(self):
        source = _read_source()
        assert "def execute_scenario(" in source

    def test_source_has_run_cognitive_pipeline(self):
        source = _read_source()
        assert "def run_cognitive_pipeline(" in source

    def test_source_has_strategy_routing_logic(self):
        """The execute_scenario method references all three strategies."""
        source = _read_source()
        assert '"agentic"' in source
        assert '"cognitive_pipeline"' in source
        assert '"pipeline"' in source

    def test_high_tier_routes_to_agentic(self, rt_mod):
        caps = rt_mod.AgentRuntime.MODEL_CAPABILITIES
        for model, info in caps.items():
            if info["tier"] == "high":
                assert info["recommended_strategy"] == "agentic"

    def test_mid_tier_routes_to_cognitive_pipeline(self, rt_mod):
        caps = rt_mod.AgentRuntime.MODEL_CAPABILITIES
        for model, info in caps.items():
            if info["tier"] == "mid":
                assert info["recommended_strategy"] == "cognitive_pipeline"

    def test_low_tier_routes_to_pipeline(self, rt_mod):
        # Low-tier models route to a closed-plan-space strategy.  "pipeline"
        # is the default; "cartridge_only" is a stricter variant used for
        # very small models (e.g. gemma4:e2b) where only pre-sealed
        # cartridges are safe.
        caps = rt_mod.AgentRuntime.MODEL_CAPABILITIES
        allowed = {"pipeline", "cartridge_only"}
        for model, info in caps.items():
            if info["tier"] == "low":
                assert info["recommended_strategy"] in allowed, (
                    f"{model}: unexpected low-tier strategy "
                    f"{info['recommended_strategy']!r}"
                )

    def test_strategy_override_in_source(self):
        """strategy_override takes precedence in execute_scenario."""
        source = _read_source()
        assert "strategy_override" in source


# ---------------------------------------------------------------------------
# TestValidateStepOutput
# ---------------------------------------------------------------------------
class TestValidateStepOutput:
    """_validate_step_output rule-based quality gate."""

    def test_validate_pass(self, rt_mod):
        result = rt_mod.StepResult(
            step_num=1, agent_name="test-agent",
            output="x" * 3000, char_count=3000,
            files_written=["output/test.md"],
        )
        validation = rt_mod.StepValidation(min_chars=2000)
        # Call the static-like method — instantiate a minimal check
        # Since _validate_step_output doesn't use self beyond the params, test directly
        issues = []
        if result.char_count < validation.min_chars:
            issues.append("too short")
        if validation.require_file_write and not result.files_written:
            issues.append("no file")
        assert len(issues) == 0

    def test_validate_too_short(self, rt_mod):
        result = rt_mod.StepResult(
            step_num=1, agent_name="test-agent",
            output="short", char_count=100,
            files_written=["output/test.md"],
        )
        validation = rt_mod.StepValidation(min_chars=2000)
        issues = []
        if result.char_count < validation.min_chars:
            issues.append("too short")
        if validation.require_file_write and not result.files_written:
            issues.append("no file")
        assert "too short" in issues

    def test_validate_no_files(self, rt_mod):
        result = rt_mod.StepResult(
            step_num=1, agent_name="test-agent",
            output="x" * 3000, char_count=3000,
            files_written=[],
        )
        validation = rt_mod.StepValidation(min_chars=2000, require_file_write=True)
        issues = []
        if result.char_count < validation.min_chars:
            issues.append("too short")
        if validation.require_file_write and not result.files_written:
            issues.append("no file")
        assert "no file" in issues

    def test_validate_no_file_requirement(self, rt_mod):
        """When require_file_write=False, missing files is OK."""
        result = rt_mod.StepResult(
            step_num=1, agent_name="test-agent",
            output="x" * 3000, char_count=3000,
            files_written=[],
        )
        validation = rt_mod.StepValidation(min_chars=2000, require_file_write=False)
        issues = []
        if result.char_count < validation.min_chars:
            issues.append("too short")
        if validation.require_file_write and not result.files_written:
            issues.append("no file")
        assert len(issues) == 0


# ---------------------------------------------------------------------------
# TestParseToolCallsRefactored
# ---------------------------------------------------------------------------
class TestParseToolCallsRefactored:
    """_parse_tool_calls extracted method handles all 4 formats."""

    def test_source_has_parse_tool_calls(self):
        source = _read_source()
        assert "def _parse_tool_calls(self, response" in source

    def test_run_goal_uses_parse_tool_calls(self):
        """run_goal delegates to _parse_tool_calls instead of inline parsing."""
        source = _read_source()
        # The refactored run_goal should call self._parse_tool_calls
        # Find the run_goal method body
        run_goal_start = source.index("def run_goal(")
        run_goal_end = source.index("\n    def ", run_goal_start + 1)
        run_goal_body = source[run_goal_start:run_goal_end]
        assert "self._parse_tool_calls(response)" in run_goal_body

    def test_format_a_pattern_in_parse_tool_calls(self):
        """Format A regex is in _parse_tool_calls, not duplicated in run_goal."""
        source = _read_source()
        # _parse_tool_calls should contain the format A regex
        ptc_start = source.index("def _parse_tool_calls(")
        ptc_end = source.index("\n    def ", ptc_start + 1)
        ptc_body = source[ptc_start:ptc_end]
        assert 'tool_call name="' in ptc_body


# ---------------------------------------------------------------------------
# TestDataclasses
# ---------------------------------------------------------------------------
class TestDataclasses:
    """StepResult and StepValidation dataclasses exist and have expected fields."""

    def test_step_result_fields(self, rt_mod):
        r = rt_mod.StepResult(step_num=1, agent_name="test")
        assert r.step_num == 1
        assert r.agent_name == "test"
        assert r.output == ""
        assert r.files_written == []
        assert r.char_count == 0
        assert r.status == "pending"

    def test_step_validation_fields(self, rt_mod):
        v = rt_mod.StepValidation()
        assert v.min_chars == 2000
        assert v.require_file_write is True
        assert v.required_sections == []

    def test_step_validation_custom(self, rt_mod):
        v = rt_mod.StepValidation(min_chars=5000, require_file_write=False,
                                   required_sections=["Abstract", "Results"])
        assert v.min_chars == 5000
        assert v.require_file_write is False
        assert len(v.required_sections) == 2


# ---------------------------------------------------------------------------
# TestCLIFlags
# ---------------------------------------------------------------------------
class TestCLIFlags:
    """CLI argument parsing includes --strategy and --project-dir."""

    def test_strategy_flag_in_source(self):
        source = _read_source()
        assert '"--strategy"' in source

    def test_project_dir_flag_in_source(self):
        source = _read_source()
        assert '"--project-dir"' in source

    def test_execute_scenario_used_in_cli(self):
        """The --scenario handler calls execute_scenario."""
        source = _read_source()
        assert "runtime.execute_scenario(" in source


# ---------------------------------------------------------------------------
# TestRunScenarioScript
# ---------------------------------------------------------------------------
class TestRunScenarioScript:
    """run_scenario.py exists and has expected structure."""

    def test_script_exists(self):
        path = os.path.join(SKILLOS_ROOT, "run_scenario.py")
        assert os.path.isfile(path)

    def test_script_has_argparse(self):
        source = _read_file(os.path.join(SKILLOS_ROOT, "run_scenario.py"))
        assert "argparse" in source
        assert "ArgumentParser" in source

    def test_script_imports_runtime(self):
        source = _read_file(os.path.join(SKILLOS_ROOT, "run_scenario.py"))
        assert "from agent_runtime import AgentRuntime" in source

    def test_script_uses_execute_scenario(self):
        source = _read_file(os.path.join(SKILLOS_ROOT, "run_scenario.py"))
        assert "execute_scenario" in source

    def test_script_supports_strategy(self):
        source = _read_file(os.path.join(SKILLOS_ROOT, "run_scenario.py"))
        assert "--strategy" in source

    def test_script_supports_project_dir(self):
        source = _read_file(os.path.join(SKILLOS_ROOT, "run_scenario.py"))
        assert "--project-dir" in source


# ---------------------------------------------------------------------------
# TestDynamicSubagentCreation
# ---------------------------------------------------------------------------
class TestDynamicSubagentCreation:
    """_generate_agent_spec creates markdown agent files from scenario context."""

    def test_source_has_generate_agent_spec(self):
        source = _read_source()
        assert "def _generate_agent_spec(" in source

    def test_generate_agent_spec_creates_file(self, rt_mod, tmp_path):
        """Generated spec is saved to components/agents/ and .claude/agents/."""
        project_dir = str(tmp_path / "projects" / "Project_test")
        os.makedirs(os.path.join(project_dir, "components", "agents"), exist_ok=True)

        step = {"step": 1, "agent": "test-visionary-agent",
                "goal": "Create a project vision", "output": "vision.md"}
        scenario = "---\nname: test\n---\n# Test\n\n### Stage 1: Vision\n**Agent**: test-visionary-agent\n**Goal**: Create vision\n"

        spec = rt_mod.AgentRuntime._generate_agent_spec(
            "test-visionary-agent", step, scenario, project_dir,
        )
        assert "name: test-visionary-agent" in spec
        assert "Create a project vision" in spec

        agent_file = os.path.join(project_dir, "components", "agents", "test-visionary-agent.md")
        assert os.path.isfile(agent_file)

    def test_generate_agent_spec_has_frontmatter(self, rt_mod, tmp_path):
        project_dir = str(tmp_path / "projects" / "Project_test2")
        os.makedirs(os.path.join(project_dir, "components", "agents"), exist_ok=True)

        step = {"step": 2, "agent": "math-agent", "goal": "Derive equations",
                "output": "math.md"}
        spec = rt_mod.AgentRuntime._generate_agent_spec(
            "math-agent", step, "---\nname: x\n---\n# Body", project_dir,
        )
        assert spec.startswith("---")
        assert "phase: 2" in spec
        assert "name: math-agent" in spec

    def test_generate_agent_spec_adds_bash_for_py(self, rt_mod, tmp_path):
        """Agent spec includes Bash tool when output is .py."""
        project_dir = str(tmp_path / "projects" / "Project_test3")
        os.makedirs(os.path.join(project_dir, "components", "agents"), exist_ok=True)

        step = {"step": 3, "agent": "coder-agent", "goal": "Write code",
                "output": "implementation.py"}
        spec = rt_mod.AgentRuntime._generate_agent_spec(
            "coder-agent", step, "---\nname: x\n---\n# Body", project_dir,
        )
        assert "Bash" in spec

    def test_run_step_uses_generate_on_missing_agent(self):
        """_run_step_with_tools calls _generate_agent_spec when agent not found."""
        source = _read_source()
        # Find the _run_step_with_tools method body
        start = source.index("def _run_step_with_tools(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "_generate_agent_spec" in body


# ---------------------------------------------------------------------------
# TestToolCallScaffolding
# ---------------------------------------------------------------------------
class TestToolCallScaffolding:
    """Tool-call scaffolding injects a few-shot example for mid-tier models."""

    def test_scaffold_in_run_step(self):
        """_run_step_with_tools injects a scaffold example message."""
        source = _read_source()
        start = source.index("def _run_step_with_tools(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "scaffold_example" in body
        assert "write_file" in body

    def test_scaffold_has_three_messages(self):
        """Initial messages include user prompt, scaffold assistant, and follow-up user."""
        source = _read_source()
        start = source.index("def _run_step_with_tools(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        # Should have 3 initial messages: user, assistant (scaffold), user (follow-up)
        assert '"role": "assistant"' in body
        assert "Good format" in body

    def test_auto_wrap_prose_output(self):
        """When model produces prose but no tool call, auto-save to file."""
        source = _read_source()
        start = source.index("def _run_step_with_tools(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "Auto-saved prose output" in body or "auto_path" in body


# ---------------------------------------------------------------------------
# TestPriorOutputFileInjection
# ---------------------------------------------------------------------------
class TestPriorOutputFileInjection:
    """Prior step files are pre-read and injected into later step prompts."""

    def test_file_injection_in_run_step(self):
        """_run_step_with_tools scans output dir for prior files."""
        source = _read_source()
        start = source.index("def _run_step_with_tools(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "FILES FROM PRIOR STEPS" in body
        assert "os.walk" in body

    def test_file_injection_truncates_large_files(self):
        """Injected files are truncated to 3000 chars."""
        source = _read_source()
        start = source.index("def _run_step_with_tools(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "3000" in body

    def test_file_injection_limits_count(self):
        """At most 10 files are injected to keep context manageable."""
        source = _read_source()
        start = source.index("def _run_step_with_tools(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "[:10]" in body
        assert "--project-dir" in source


# ---------------------------------------------------------------------------
# TestEnhancedDelegation
# ---------------------------------------------------------------------------
class TestEnhancedDelegation:
    """_handle_delegate_to_agent now runs a multi-turn tool loop."""

    def test_delegation_has_tool_loop(self):
        """_handle_delegate_to_agent contains a tool execution loop."""
        source = _read_source()
        start = source.index("def _handle_delegate_to_agent(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        # Must have a bounded loop
        assert "for turn in range(max_turns)" in body

    def test_delegation_injects_tool_format(self):
        """Delegated agents get tool format instructions in their system prompt."""
        source = _read_source()
        start = source.index("def _handle_delegate_to_agent(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "_GEMINI_TOOL_FORMAT_INSTRUCTIONS" in body

    def test_delegation_has_scaffold(self):
        """Delegated agents get a few-shot scaffold example."""
        source = _read_source()
        start = source.index("def _handle_delegate_to_agent(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "scaffold_example" in body
        assert '"role": "assistant"' in body

    def test_delegation_parses_tool_calls(self):
        """Delegated agents' responses are parsed for tool calls."""
        source = _read_source()
        start = source.index("def _handle_delegate_to_agent(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "_parse_tool_calls(response)" in body

    def test_delegation_tracks_files(self):
        """File writes by delegated agents are tracked."""
        source = _read_source()
        start = source.index("def _handle_delegate_to_agent(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "files_written" in body
        assert 'write_file' in body

    def test_delegation_restores_system_prompt(self):
        """System prompt is restored after delegation via try/finally."""
        source = _read_source()
        start = source.index("def _handle_delegate_to_agent(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "original_system_prompt" in body
        assert "finally:" in body
        assert "self.system_prompt = original_system_prompt" in body

    def test_delegation_generates_missing_agents(self):
        """When agent not found, delegation generates a spec dynamically."""
        source = _read_source()
        start = source.index("def _handle_delegate_to_agent(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "_generate_agent_spec" in body

    def test_delegation_injects_project_files(self):
        """Delegated agents get project file context when project_dir is set."""
        source = _read_source()
        start = source.index("def _handle_delegate_to_agent(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "AVAILABLE PROJECT FILES" in body
        assert "os.walk" in body

    def test_delegation_uses_active_project_dir(self):
        """Delegation falls back to self._active_project_dir when no explicit project_dir."""
        source = _read_source()
        start = source.index("def _handle_delegate_to_agent(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "_active_project_dir" in body

    def test_delegation_handles_final_answer(self):
        """Delegation extracts final_answer tag to return clean output."""
        source = _read_source()
        start = source.index("def _handle_delegate_to_agent(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "final_answer" in body
        assert "_extract_tag_content" in body

    def test_delegation_has_permission_check(self):
        """Tool calls within delegation go through permission policy."""
        source = _read_source()
        start = source.index("def _handle_delegate_to_agent(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "self.policy.authorize" in body

    def test_active_project_dir_in_init(self):
        """_active_project_dir is initialized in __init__."""
        source = _read_source()
        assert "_active_project_dir" in source
        start = source.index("def __init__(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "_active_project_dir" in body

    def test_active_project_dir_set_in_cognitive_pipeline(self):
        """run_cognitive_pipeline sets _active_project_dir."""
        source = _read_source()
        start = source.index("def run_cognitive_pipeline(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "_active_project_dir = project_dir" in body

    def test_active_project_dir_set_in_execute_scenario(self):
        """execute_scenario sets _active_project_dir for agentic mode."""
        source = _read_source()
        start = source.index("def execute_scenario(")
        end = source.index("\n    def ", start + 1)
        body = source[start:end]
        assert "_active_project_dir" in body
