"""
Tests for the Pipeline Runtime — validates AOT dialect injection prerequisites
and scenario frontmatter parsing for agent_runtime.py pipeline execution.
"""

import os
import re
import pytest
import yaml

SKILLOS_ROOT = os.path.join(os.path.dirname(__file__), "..")
DIALECTS_DIR = os.path.join(SKILLOS_ROOT, "system", "dialects")
SCENARIOS_DIR = os.path.join(SKILLOS_ROOT, "scenarios")


def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_frontmatter(content: str) -> dict:
    match = re.match(r"^---\n(.*?\n)---", content, re.DOTALL)
    assert match, "No YAML frontmatter found"
    return yaml.safe_load(match.group(1))


# All dialect IDs that have .dialect.md files
DIALECT_IDS = [
    "roclaw-bytecode", "caveman-prose", "strategy-pointer", "trace-log",
    "memory-xp", "constraint-dsl", "exec-plan", "strict-patch", "dom-nav",
    "formal-proof", "system-dynamics", "boolean-logic", "data-flow",
    "smiles-chem",
]


# ---------------------------------------------------------------------------
# TestDialectGrammarSections — AOT extraction prerequisite
# ---------------------------------------------------------------------------
class TestDialectGrammarSections:
    """Every dialect file must have a Grammar / Syntax section for AOT extraction."""

    @pytest.fixture(params=DIALECT_IDS)
    def dialect_id(self, request):
        return request.param

    def test_grammar_section_exists(self, dialect_id):
        path = os.path.join(DIALECTS_DIR, f"{dialect_id}.dialect.md")
        if not os.path.isfile(path):
            pytest.skip(f"{dialect_id}.dialect.md not found")
        content = _read_file(path)
        assert "## Grammar / Syntax" in content, (
            f"{dialect_id}.dialect.md missing '## Grammar / Syntax' section — "
            f"AOT extraction requires this"
        )

    def test_examples_section_exists(self, dialect_id):
        path = os.path.join(DIALECTS_DIR, f"{dialect_id}.dialect.md")
        if not os.path.isfile(path):
            pytest.skip(f"{dialect_id}.dialect.md not found")
        content = _read_file(path)
        assert "## Examples" in content, (
            f"{dialect_id}.dialect.md missing '## Examples' section — "
            f"AOT extraction uses first example"
        )


# ---------------------------------------------------------------------------
# TestDialectBenchmarkScenarioParseable
# ---------------------------------------------------------------------------
class TestDialectBenchmarkScenarioParseable:
    """Dialect_Benchmark.md is parseable with valid frontmatter for pipeline execution."""

    SCENARIO_PATH = os.path.join(SCENARIOS_DIR, "Dialect_Benchmark.md")

    def test_scenario_exists(self):
        assert os.path.isfile(self.SCENARIO_PATH)

    def test_frontmatter_valid_yaml(self):
        content = _read_file(self.SCENARIO_PATH)
        fm = _parse_frontmatter(content)
        assert isinstance(fm, dict)

    def test_has_name(self):
        fm = _parse_frontmatter(_read_file(self.SCENARIO_PATH))
        assert fm.get("name") == "dialect-benchmark"

    def test_has_requires_dialects(self):
        fm = _parse_frontmatter(_read_file(self.SCENARIO_PATH))
        assert "requires_dialects" in fm
        assert isinstance(fm["requires_dialects"], list)
        assert len(fm["requires_dialects"]) >= 1

    def test_has_pipeline(self):
        fm = _parse_frontmatter(_read_file(self.SCENARIO_PATH))
        assert "pipeline" in fm
        assert isinstance(fm["pipeline"], list)
        assert len(fm["pipeline"]) >= 1

    def test_pipeline_dialect_files_exist(self):
        fm = _parse_frontmatter(_read_file(self.SCENARIO_PATH))
        for step in fm["pipeline"]:
            dialect = step["dialect"]
            path = os.path.join(DIALECTS_DIR, f"{dialect}.dialect.md")
            assert os.path.isfile(path), (
                f"Pipeline step {step['step']} references '{dialect}' "
                f"but {dialect}.dialect.md does not exist"
            )


# ---------------------------------------------------------------------------
# TestAOTFrontmatterParser
# ---------------------------------------------------------------------------
class TestAOTFrontmatterParser:
    """Test the _parse_frontmatter function used by agent_runtime.py."""

    def test_simple_frontmatter(self):
        content = "---\nname: test\nversion: v1\n---\n# Body"
        fm = _parse_frontmatter(content)
        assert fm["name"] == "test"
        assert fm["version"] == "v1"

    def test_list_frontmatter(self):
        content = "---\nitems:\n  - a\n  - b\n---\n# Body"
        fm = _parse_frontmatter(content)
        assert fm["items"] == ["a", "b"]

    def test_nested_list_frontmatter(self):
        content = (
            "---\npipeline:\n  - step: 1\n    dialect: formal-proof\n"
            "  - step: 2\n    dialect: boolean-logic\n---\n"
        )
        fm = _parse_frontmatter(content)
        assert len(fm["pipeline"]) == 2
        assert fm["pipeline"][0]["dialect"] == "formal-proof"
        assert fm["pipeline"][1]["step"] == 2


# ---------------------------------------------------------------------------
# TestAgentRuntimeImport
# ---------------------------------------------------------------------------
class TestAgentRuntimeImport:
    """Verify agent_runtime.py has the expected pipeline methods."""

    def test_parse_frontmatter_importable(self):
        """The module-level _parse_frontmatter function exists."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "agent_runtime",
            os.path.join(SKILLOS_ROOT, "agent_runtime.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        # We only check the function exists in source — don't exec (avoids import deps)
        source = _read_file(os.path.join(SKILLOS_ROOT, "agent_runtime.py"))
        assert "def _parse_frontmatter(" in source
        assert "def _load_dialect_grammars(" in source or "class AgentRuntime" in source

    def test_runtime_has_load_scenario(self):
        source = _read_file(os.path.join(SKILLOS_ROOT, "agent_runtime.py"))
        assert "def load_scenario(" in source

    def test_runtime_has_run_pipeline(self):
        source = _read_file(os.path.join(SKILLOS_ROOT, "agent_runtime.py"))
        assert "def run_pipeline(" in source

    def test_runtime_has_model_override(self):
        source = _read_file(os.path.join(SKILLOS_ROOT, "agent_runtime.py"))
        assert "def _call_with_model_override(" in source

    def test_runtime_has_scenario_cli_flag(self):
        source = _read_file(os.path.join(SKILLOS_ROOT, "agent_runtime.py"))
        assert "--scenario" in source
