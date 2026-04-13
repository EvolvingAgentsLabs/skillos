"""
Tests for examples/ and scenarios/ — the SkillOS sample library.

Covers:
  - All 9 numbered examples are present and well-formed
  - All 9 scenarios are present and well-formed
  - Each markdown file has a title, non-trivial body, and no broken structure
  - Project structure convention is followed in existing projects/
"""

import re
from typing import Optional

import pytest
from pathlib import Path
from conftest import ROOT


EXAMPLES_DIR = ROOT / "examples"
SCENARIOS_DIR = ROOT / "scenarios"
PROJECTS_DIR = ROOT / "projects"


# ── Helpers ───────────────────────────────────────────────────────

def md_title(text: str) -> Optional[str]:
    m = re.search(r"^#\s+(.+)", text, re.MULTILINE)
    return m.group(1).strip() if m else None


# ── Examples ──────────────────────────────────────────────────────

EXPECTED_EXAMPLES = [
    "01_hello_world.md",
    "02_web_research.md",
    "03_code_review.md",
    "04_parallel_research.md",
    "05_data_pipeline.md",
    "06_reflective_loop.md",
    "07_memory_driven.md",
    "08_custom_agent_creation.md",
    "09_autoresearch.md",
]


class TestExamplesDirectory:
    def test_examples_dir_exists(self):
        assert EXAMPLES_DIR.exists(), "examples/ directory not found"

    def test_examples_readme_exists(self):
        assert (EXAMPLES_DIR / "README.md").exists(), (
            "examples/README.md not found"
        )

    @pytest.mark.parametrize("filename", EXPECTED_EXAMPLES)
    def test_example_file_exists(self, filename):
        assert (EXAMPLES_DIR / filename).exists(), (
            f"examples/{filename} is missing"
        )

    @pytest.mark.parametrize("filename", EXPECTED_EXAMPLES)
    def test_example_has_h1_title(self, filename):
        text = (EXAMPLES_DIR / filename).read_text(encoding="utf-8")
        assert md_title(text) is not None, (
            f"examples/{filename}: missing # Title heading"
        )

    @pytest.mark.parametrize("filename", EXPECTED_EXAMPLES)
    def test_example_has_sufficient_content(self, filename):
        text = (EXAMPLES_DIR / filename).read_text(encoding="utf-8")
        assert len(text.strip()) > 100, (
            f"examples/{filename}: content is too short"
        )

    @pytest.mark.parametrize("filename", EXPECTED_EXAMPLES)
    def test_example_is_valid_markdown(self, filename):
        text = (EXAMPLES_DIR / filename).read_text(encoding="utf-8")
        # Basic check: no unclosed fenced code blocks
        fence_count = len(re.findall(r"^```", text, re.MULTILINE))
        assert fence_count % 2 == 0, (
            f"examples/{filename}: odd number of ``` fences — possible unclosed block"
        )

    def test_examples_are_numbered_sequentially(self):
        nums = sorted(
            int(f.name[:2])
            for f in EXAMPLES_DIR.glob("[0-9]*.md")
        )
        assert nums == list(range(1, len(nums) + 1)), (
            "Example files should be numbered sequentially from 01"
        )


# ── Scenarios ─────────────────────────────────────────────────────

EXPECTED_SCENARIOS = [
    "RealWorld_Research_Task.md",
    "CodeAnalysis_Task.md",
    "ContentCreation_Task.md",
    "DataAnalysis_Task.md",
    "GitRepoAudit_Task.md",
    "KnowledgeSynthesis_Task.md",
    "AutoResearch_Task.md",
    "ProjectAortaScenario.md",
    "RoClaw_Integration.md",
]


class TestScenariosDirectory:
    def test_scenarios_dir_exists(self):
        assert SCENARIOS_DIR.exists(), "scenarios/ directory not found"

    @pytest.mark.parametrize("filename", EXPECTED_SCENARIOS)
    def test_scenario_file_exists(self, filename):
        assert (SCENARIOS_DIR / filename).exists(), (
            f"scenarios/{filename} is missing"
        )

    @pytest.mark.parametrize("filename", EXPECTED_SCENARIOS)
    def test_scenario_has_h1_title(self, filename):
        text = (SCENARIOS_DIR / filename).read_text(encoding="utf-8")
        assert md_title(text) is not None, (
            f"scenarios/{filename}: missing # Title heading"
        )

    @pytest.mark.parametrize("filename", EXPECTED_SCENARIOS)
    def test_scenario_has_sufficient_content(self, filename):
        text = (SCENARIOS_DIR / filename).read_text(encoding="utf-8")
        assert len(text.strip()) > 200, (
            f"scenarios/{filename}: content is too short"
        )

    @pytest.mark.parametrize("filename", EXPECTED_SCENARIOS)
    def test_scenario_is_valid_markdown(self, filename):
        text = (SCENARIOS_DIR / filename).read_text(encoding="utf-8")
        fence_count = len(re.findall(r"^```", text, re.MULTILINE))
        assert fence_count % 2 == 0, (
            f"scenarios/{filename}: odd number of ``` fences"
        )

    @pytest.mark.parametrize("filename", EXPECTED_SCENARIOS)
    def test_scenario_describes_goal(self, filename):
        text = (SCENARIOS_DIR / filename).read_text(encoding="utf-8")
        keywords = ["goal", "objective", "task", "execute", "scenario", "agent"]
        assert any(kw in text.lower() for kw in keywords), (
            f"scenarios/{filename}: should describe a goal or task"
        )


# ── Project structure convention ──────────────────────────────────

class TestProjectsDirectory:
    def test_projects_dir_exists(self):
        assert PROJECTS_DIR.exists(), "projects/ directory not found"

    @pytest.mark.parametrize("subdir", [
        "components", "input", "output", "memory", "state"
    ])
    def test_hello_world_project_has_required_dirs(self, subdir):
        """The sample project must follow the canonical structure."""
        project = PROJECTS_DIR / "Project_hello_world"
        if not project.exists():
            pytest.skip("Project_hello_world not found — skipping structure check")
        assert (project / subdir).exists(), (
            f"Project_hello_world/{subdir}/ is missing"
        )

    def test_hello_world_memory_has_short_and_long_term(self):
        project = PROJECTS_DIR / "Project_hello_world"
        if not project.exists():
            pytest.skip("Project_hello_world not found")
        assert (project / "memory" / "short_term").exists()
        assert (project / "memory" / "long_term").exists()

    def test_hello_world_components_has_agents_and_tools(self):
        project = PROJECTS_DIR / "Project_hello_world"
        if not project.exists():
            pytest.skip("Project_hello_world not found")
        assert (project / "components" / "agents").exists()
        assert (project / "components" / "tools").exists()


# ── System core files ─────────────────────────────────────────────

class TestSystemCoreFiles:
    REQUIRED_SYSTEM_FILES = [
        "system/SmartLibrary.md",
        "system/SmartMemory.md",
        "system/sources.list",
        "system/packages.lock",
    ]

    @pytest.mark.parametrize("rel_path", REQUIRED_SYSTEM_FILES)
    def test_system_file_exists(self, root, rel_path):
        assert (root / rel_path).exists(), (
            f"Required system file not found: {rel_path}"
        )

    def test_smart_library_has_content(self, root):
        text = (root / "system" / "SmartLibrary.md").read_text(encoding="utf-8")
        assert len(text.strip()) > 50

    def test_smart_memory_has_content(self, root):
        text = (root / "system" / "SmartMemory.md").read_text(encoding="utf-8")
        assert len(text.strip()) > 0

    def test_setup_scripts_exist(self, root):
        assert (root / "setup_agents.sh").exists(), "setup_agents.sh not found"
        assert (root / "setup_agents.ps1").exists(), "setup_agents.ps1 not found"

    def test_setup_sh_is_executable_or_has_shebang(self, root):
        text = (root / "setup_agents.sh").read_text(encoding="utf-8")
        assert text.startswith("#!"), "setup_agents.sh should have a shebang"
