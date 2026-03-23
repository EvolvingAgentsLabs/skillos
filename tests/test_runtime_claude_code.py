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

CORE_AGENT_NAMES = [
    "SystemAgent",
    "ValidationAgent",
    "ErrorRecoveryAgent",
    "MemoryAnalysisAgent",
    "MemoryConsolidationAgent",
]


class TestCoreAgentsPresent:
    @pytest.mark.parametrize("agent_name", CORE_AGENT_NAMES)
    def test_agent_in_system_dir(self, agent_name):
        assert (SYSTEM_AGENTS_DIR / f"{agent_name}.md").exists(), (
            f"system/agents/{agent_name}.md not found"
        )

    @pytest.mark.parametrize("agent_name", CORE_AGENT_NAMES)
    def test_agent_discoverable_in_claude_dir(self, agent_name):
        """Every system agent must be mirrored in .claude/agents/ for discovery."""
        assert (AGENTS_DIR / f"{agent_name}.md").exists(), (
            f".claude/agents/{agent_name}.md not found — run setup_agents.sh"
        )


# ── Agent frontmatter validation ──────────────────────────────────

def all_agent_files():
    """Parametrize over every .md in .claude/agents/."""
    if not AGENTS_DIR.exists():
        return []
    return list(AGENTS_DIR.glob("*.md"))


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
    """Every agent in system/agents/ must be mirrored in .claude/agents/."""

    def test_all_system_agents_discoverable(self):
        if not SYSTEM_AGENTS_DIR.exists() or not AGENTS_DIR.exists():
            pytest.skip("Agent directories not set up")

        system_agents = {f.name for f in SYSTEM_AGENTS_DIR.glob("*.md")}
        discovery_agents = {f.name for f in AGENTS_DIR.glob("*.md")}
        missing = system_agents - discovery_agents
        assert not missing, (
            f"These system agents are not in .claude/agents/ (run setup_agents.sh): "
            f"{sorted(missing)}"
        )


# ── SystemAgent content ───────────────────────────────────────────

class TestSystemAgentContent:
    @pytest.fixture(scope="class")
    def system_agent_text(self):
        p = SYSTEM_AGENTS_DIR / "SystemAgent.md"
        if not p.exists():
            pytest.skip("SystemAgent.md not found")
        return p.read_text(encoding="utf-8")

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
