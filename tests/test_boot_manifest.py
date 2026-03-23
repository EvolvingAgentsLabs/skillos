"""
Tests for Boot.md — the universal SkillOS boot manifest.

Every runtime (skillos.py, QWEN, Claude Code agents, Codex) must be able
to read Boot.md and find a well-formed banner, checklist, protocol, and
invariants section.
"""

import re
import pytest
from pathlib import Path
from conftest import has_section, extract_section, parse_frontmatter, ROOT


# ── Existence & Frontmatter ───────────────────────────────────────

class TestBootManifestExists:
    def test_boot_md_at_root(self, root):
        assert (root / "Boot.md").exists(), "Boot.md must exist at project root"

    def test_boot_md_not_empty(self, boot_text):
        assert len(boot_text.strip()) > 100

    def test_frontmatter_present(self, boot_text):
        assert boot_text.startswith("---"), "Boot.md must have YAML frontmatter"


class TestBootManifestFrontmatter:
    REQUIRED_FIELDS = ["name", "type", "priority", "description", "runtimes"]

    def test_has_name_field(self, boot_frontmatter):
        assert "name" in boot_frontmatter
        assert boot_frontmatter["name"] == "boot"

    def test_has_type_field(self, boot_frontmatter):
        assert "type" in boot_frontmatter
        assert boot_frontmatter["type"] == "skill"

    def test_priority_is_zero(self, boot_frontmatter):
        assert "priority" in boot_frontmatter
        assert boot_frontmatter["priority"] == "0", (
            "priority must be 0 — Boot.md is always loaded first"
        )

    def test_has_description(self, boot_frontmatter):
        assert "description" in boot_frontmatter
        assert len(boot_frontmatter["description"]) > 10

    def test_runtimes_field_present(self, boot_text):
        # runtimes is a list in YAML, so check raw text
        assert "runtimes:" in boot_text

    def test_runtimes_includes_claude_code(self, boot_text):
        assert "claude-code" in boot_text

    def test_runtimes_includes_qwen(self, boot_text):
        assert "qwen" in boot_text

    def test_runtimes_includes_codex(self, boot_text):
        assert "codex" in boot_text


# ── Required Sections ─────────────────────────────────────────────

class TestBootManifestSections:
    REQUIRED_SECTIONS = [
        "Banner",
        "Boot Checklist",
        "Boot Protocol by Runtime",
        "System Invariants",
        "Quick Reference",
        "File Locations",
    ]

    @pytest.mark.parametrize("section", REQUIRED_SECTIONS)
    def test_section_exists(self, boot_text, section):
        assert has_section(boot_text, section), (
            f"Boot.md is missing required section: ## {section}"
        )


# ── Banner ────────────────────────────────────────────────────────

class TestBootBanner:
    def test_banner_has_code_block(self, boot_text):
        """Banner must be inside a fenced code block so any runtime can extract it."""
        section = extract_section(boot_text, "Banner")
        assert "```" in section, "Banner section must contain a fenced code block"

    def test_banner_contains_ascii_art(self, boot_text):
        """The banner code block must contain multi-line ASCII art."""
        m = re.search(r"## Banner\s*```\s*(.*?)```", boot_text, re.DOTALL)
        assert m, "Could not find Banner code block"
        art = m.group(1)
        lines = [l for l in art.splitlines() if l.strip()]
        assert len(lines) >= 5, "ASCII art should have at least 5 non-empty lines"

    def test_banner_extraction_regex(self, boot_text):
        """Regex used by skillos.py show_banner() must extract art correctly."""
        m = re.search(r"## Banner\s*```\s*(.*?)```", boot_text, re.DOTALL)
        assert m is not None
        art_lines = [l for l in m.group(1).rstrip().splitlines() if l.strip()]
        assert len(art_lines) >= 2, "Should have art lines + subtitle lines"

    def test_banner_has_version_subtitle(self, boot_text):
        assert "v1.0" in boot_text or "v2" in boot_text, (
            "Banner should include a version string"
        )


# ── Boot Checklist ────────────────────────────────────────────────

class TestBootChecklist:
    def test_checklist_has_six_steps(self, boot_text):
        section = extract_section(boot_text, "Boot Checklist")
        steps = re.findall(r"^\d+\.", section, re.MULTILINE)
        assert len(steps) == 6, f"Expected 6 checklist steps, got {len(steps)}"

    def test_checklist_step1_reads_boot_md(self, boot_text):
        section = extract_section(boot_text, "Boot Checklist")
        assert "Boot.md" in section

    def test_checklist_step3_loads_smart_library(self, boot_text):
        section = extract_section(boot_text, "Boot Checklist")
        assert "SmartLibrary" in section

    def test_checklist_step4_checks_agents(self, boot_text):
        section = extract_section(boot_text, "Boot Checklist")
        assert ".claude/agents" in section or "agent discovery" in section.lower()

    def test_checklist_step5_initializes_projects(self, boot_text):
        section = extract_section(boot_text, "Boot Checklist")
        assert "projects/" in section or "project structure" in section.lower()


# ── Boot Protocol by Runtime ──────────────────────────────────────

class TestBootProtocol:
    EXPECTED_RUNTIMES = [
        "Claude Code",
        "QWEN Runtime",
        "Claude Code Agents",
        "Any LLM Runtime",
    ]

    @pytest.mark.parametrize("runtime", EXPECTED_RUNTIMES)
    def test_protocol_covers_runtime(self, boot_text, runtime):
        section = extract_section(boot_text, "Boot Protocol by Runtime")
        assert runtime in section, (
            f"Boot Protocol section missing instructions for: {runtime}"
        )

    def test_skillos_protocol_mentions_scheduler(self, boot_text):
        assert "scheduler" in boot_text.lower()

    def test_qwen_protocol_mentions_read_file(self, boot_text):
        section = extract_section(boot_text, "Boot Protocol by Runtime")
        assert "read_file" in section, (
            "QWEN protocol must instruct runtime to use read_file tool"
        )

    def test_qwen_protocol_mentions_session_booted(self, boot_text):
        section = extract_section(boot_text, "Boot Protocol by Runtime")
        assert "session_booted" in section


# ── System Invariants ─────────────────────────────────────────────

class TestSystemInvariants:
    EXPECTED_INVARIANTS = [
        "markdown",
        "hardcoded",
        "isolated",
        "memory",
        "compose",
    ]

    @pytest.mark.parametrize("keyword", EXPECTED_INVARIANTS)
    def test_invariant_present(self, boot_text, keyword):
        section = extract_section(boot_text, "System Invariants")
        assert keyword in section.lower(), (
            f"System Invariants section missing keyword: '{keyword}'"
        )


# ── File Locations Table ──────────────────────────────────────────

class TestFileLocations:
    EXPECTED_PATHS = [
        "Boot.md",
        "system/SmartLibrary.md",
        "system/SmartMemory.md",
        "system/agents/",
        "system/tools/",
        "projects/",
        ".claude/agents/",
    ]

    @pytest.mark.parametrize("path", EXPECTED_PATHS)
    def test_path_listed_in_boot_md(self, boot_text, path):
        section = extract_section(boot_text, "File Locations")
        assert path in section, (
            f"File Locations table should list: {path}"
        )

    @pytest.mark.parametrize("path", EXPECTED_PATHS)
    def test_listed_path_actually_exists(self, root, path):
        # Paths ending in / are directories; others are files
        full = root / path
        assert full.exists(), (
            f"Boot.md lists '{path}' but it does not exist on disk"
        )
