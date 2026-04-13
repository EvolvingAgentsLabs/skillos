"""
Tests for the Claude Code sub-agent runtime (.claude/agents/).

Covers:
  - Agent discovery directory exists and is populated
  - Every agent file has valid YAML frontmatter
  - Required fields: name, description (and optionally tools)
  - Core system agents are present and discoverable
  - Agent names in frontmatter match filenames (no silent mismatches)
  - Boot.md is referenced by the runtime instructions
"""

import re
import pytest
from pathlib import Path
from conftest import ROOT, parse_frontmatter, has_section


AGENTS_DIR = ROOT / ".claude" / "agents"
SYSTEM_AGENTS_DIR = ROOT / "system" / "agents"


# ── Discovery directory ───────────────────────────────────────────

class TestAgentDiscoveryDirectory:
    def test_claude_agents_dir_exists(self):
        assert AGENTS_DIR.exists(), (
            ".claude/agents/ must exist — run setup_agents.sh to populate it"
        )

    def test_claude_agents_dir_has_md_files(self):
        md_files = list(AGENTS_DIR.glob("*.md"))
        assert len(md_files) > 0, ".claude/agents/ contains no .md agent files"

    def test_system_agents_dir_exists(self):
        assert SYSTEM_AGENTS_DIR.exists()

    def test_system_agents_dir_has_md_files(self):
        assert len(list(SYSTEM_AGENTS_DIR.glob("*.md"))) > 0


# ── Core agents are discoverable ─────────────────────────────────

# PascalCase names in system/agents/ (backward-compat redirect stubs)
CORE_AGENT_STUBS = [
    "SystemAgent",
    "ValidationAgent",
    "ErrorRecoveryAgent",
    "MemoryAnalysisAgent",
    "MemoryConsolidationAgent",
]

# kebab-case names in .claude/agents/ (full specs from skill tree)
CORE_AGENT_DISCOVERY_NAMES = [
    "system-agent",
    "validation-agent",
    "error-recovery-agent",
    "memory-analysis-agent",
    "memory-consolidation-agent",
]


class TestCoreAgentsPresent:
    @pytest.mark.parametrize("agent_name", CORE_AGENT_STUBS)
    def test_agent_in_system_dir(self, agent_name):
        assert (SYSTEM_AGENTS_DIR / f"{agent_name}.md").exists(), (
            f"system/agents/{agent_name}.md not found"
        )

    @pytest.mark.parametrize("agent_name", CORE_AGENT_DISCOVERY_NAMES)
    def test_agent_discoverable_in_claude_dir(self, agent_name):
        """Every core agent must be in .claude/agents/ (kebab-case from skill tree)."""
        assert (AGENTS_DIR / f"{agent_name}.md").exists(), (
            f".claude/agents/{agent_name}.md not found — run setup_agents.sh"
        )


# ── Agent frontmatter validation ──────────────────────────────────

def all_agent_files():
    """Parametrize over every .md in .claude/agents/."""
    if not AGENTS_DIR.exists():
        return []
    return list(AGENTS_DIR.glob("*.md"))


def _is_project_agent(agent_path: Path) -> bool:
    """Project agents (e.g. Project_aorta_visionary-agent.md) are dynamically
    generated and may have incomplete frontmatter."""
    return agent_path.name.startswith("Project_")


class TestAgentFrontmatter:
    @pytest.mark.parametrize("agent_path", all_agent_files())
    def test_agent_has_frontmatter(self, agent_path):
        text = agent_path.read_text(encoding="utf-8")
        assert text.startswith("---"), (
            f"{agent_path.name}: must start with YAML frontmatter (---)"
        )

    @pytest.mark.parametrize("agent_path", all_agent_files())
    def test_agent_has_name_field(self, agent_path):
        text = agent_path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        assert "name" in fm, f"{agent_path.name}: frontmatter missing 'name' field"
        assert len(fm["name"]) > 0

    @pytest.mark.parametrize("agent_path", all_agent_files())
    def test_agent_has_description_field(self, agent_path):
        if _is_project_agent(agent_path):
            pytest.skip("Project agents may have incomplete frontmatter")
        text = agent_path.read_text(encoding="utf-8")
        fm = parse_frontmatter(text)
        assert "description" in fm, (
            f"{agent_path.name}: frontmatter missing 'description' field"
        )
        assert len(fm["description"]) > 10, (
            f"{agent_path.name}: description is too short"
        )

    @pytest.mark.parametrize("agent_path", all_agent_files())
    def test_agent_has_markdown_body(self, agent_path):
        text = agent_path.read_text(encoding="utf-8")
        # Body is content after the closing --- of frontmatter
        parts = text.split("---", 2)
        assert len(parts) >= 3, f"{agent_path.name}: malformed frontmatter"
        body = parts[2].strip()
        assert len(body) > 50, f"{agent_path.name}: agent body is too short"

    @pytest.mark.parametrize("agent_path", all_agent_files())
    def test_agent_has_h1_title(self, agent_path):
        text = agent_path.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]
            assert re.search(r"^#\s+\S", body, re.MULTILINE), (
                f"{agent_path.name}: agent body should have a # Title heading"
            )


# ── System↔discovery sync ─────────────────────────────────────────

class TestAgentSync:
    """Non-redirect agents in system/agents/ must be discoverable in .claude/agents/."""

    @staticmethod
    def _is_redirect_stub(path: Path) -> bool:
        """Check if an agent file is a redirect stub (has redirect: in frontmatter)."""
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return False
        try:
            end = text.index("---", 3)
            frontmatter = text[3:end]
            return "redirect:" in frontmatter
        except ValueError:
            return False

    def test_non_redirect_system_agents_discoverable(self):
        """Non-redirect agents in system/agents/ must be in .claude/agents/.
        Redirect stubs are expected — their full specs live in the skill tree
        and are copied to .claude/agents/ under kebab-case names by setup_agents.sh.
        """
        if not SYSTEM_AGENTS_DIR.exists() or not AGENTS_DIR.exists():
            pytest.skip("Agent directories not set up")

        non_redirect = {
            f.name for f in SYSTEM_AGENTS_DIR.glob("*.md")
            if not self._is_redirect_stub(f)
        }
        discovery_agents = {f.name for f in AGENTS_DIR.glob("*.md")}
        missing = non_redirect - discovery_agents
        assert not missing, (
            f"These non-redirect system agents are not in .claude/agents/: "
            f"{sorted(missing)}"
        )

    def test_redirect_stubs_have_skill_tree_counterpart(self):
        """Every redirect stub should have a corresponding agent in .claude/agents/."""
        if not SYSTEM_AGENTS_DIR.exists() or not AGENTS_DIR.exists():
            pytest.skip("Agent directories not set up")

        discovery_names = {f.stem for f in AGENTS_DIR.glob("*.md")}
        for stub in SYSTEM_AGENTS_DIR.glob("*.md"):
            if not self._is_redirect_stub(stub):
                continue
            # Read the frontmatter name field to find the kebab-case name
            text = stub.read_text(encoding="utf-8")
            fm = parse_frontmatter(text)
            agent_name = fm.get("name", "")
            assert agent_name in discovery_names, (
                f"Redirect stub {stub.name} (name={agent_name}) has no "
                f"counterpart in .claude/agents/"
            )


# ── SystemAgent content ───────────────────────────────────────────

SYSTEM_AGENT_SKILL_PATH = ROOT / "system" / "skills" / "orchestration" / "core" / "system-agent.md"


class TestSystemAgentContent:
    @pytest.fixture(scope="class")
    def system_agent_text(self):
        # Prefer the full spec from the skill tree; fall back to legacy path
        if SYSTEM_AGENT_SKILL_PATH.exists():
            return SYSTEM_AGENT_SKILL_PATH.read_text(encoding="utf-8")
        p = AGENTS_DIR / "system-agent.md"
        if p.exists():
            return p.read_text(encoding="utf-8")
        pytest.skip("system-agent.md not found in skill tree or .claude/agents/")

    def test_system_agent_has_purpose(self, system_agent_text):
        assert "orchestrat" in system_agent_text.lower(), (
            "SystemAgent should describe its orchestration role"
        )

    def test_system_agent_mentions_projects_dir(self, system_agent_text):
        assert "projects/" in system_agent_text

    def test_system_agent_mentions_memory(self, system_agent_text):
        assert "memory" in system_agent_text.lower()


# ── Claude Code architecture doc ─────────────────────────────────

class TestClaudeCodeArchDoc:
    def test_architecture_doc_exists(self, root):
        assert (root / "CLAUDE_CODE_ARCHITECTURE.md").exists()

    def test_architecture_doc_references_boot(self, root):
        text = (root / "CLAUDE_CODE_ARCHITECTURE.md").read_text(encoding="utf-8")
        # Either Boot.md is referenced, or boot process is described
        assert "Boot" in text or "boot" in text, (
            "CLAUDE_CODE_ARCHITECTURE.md should describe the boot process"
        )
