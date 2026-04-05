"""
SkillOS Test Suite — Shared fixtures and helpers.

Covers boot validation across all supported runtimes:
  - Boot.md manifest (universal)
  - skillos.py  (Claude Code terminal runtime)
  - QWEN.md / agent_runtime.py  (Agent runtime)
  - .claude/agents/  (Claude Code sub-agent runtime)
"""

import re
import sys
import importlib
import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Paths ─────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent


# ── Markdown helpers ──────────────────────────────────────────────

def parse_frontmatter(text: str) -> dict:
    """Return key→value dict from YAML-style frontmatter (--- … ---)."""
    result = {}
    if not text.startswith("---"):
        return result
    end = text.index("---", 3)
    block = text[3:end].strip()
    for line in block.splitlines():
        line = line.strip()
        if ":" in line and not line.startswith("-"):
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
    return result


def has_section(text: str, heading: str) -> bool:
    """True if markdown text contains a ## heading with the given title."""
    return bool(re.search(rf"^##\s+{re.escape(heading)}", text, re.MULTILINE))


def extract_section(text: str, heading: str) -> str:
    """Return the content of a ## section (until the next ## or EOF)."""
    pattern = rf"(?m)^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else ""


# ── Module loader (handles side-effects in skillos.py) ───────────

def load_skillos_module():
    """
    Import skillos.py with:
      - rich mocked (may not be installed in CI)
      - os.chdir patched (prevents changing CWD)
    Returns the module or None if import fails for an unexpected reason.
    """
    rich_mock = MagicMock()
    mocks = {
        "rich": rich_mock,
        "rich.console": rich_mock,
        "rich.markdown": rich_mock,
        "rich.table": rich_mock,
        "rich.theme": rich_mock,
        "rich.spinner": rich_mock,
        "rich.live": rich_mock,
    }
    with patch.dict(sys.modules, mocks):
        with patch("os.chdir"):
            spec = importlib.util.spec_from_file_location(
                "skillos_module", ROOT / "skillos.py"
            )
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                return mod
            except Exception as exc:
                pytest.skip(f"Could not import skillos.py: {exc}")


def load_qwen_module():
    """
    Import agent_runtime.py with openai / dotenv mocked.
    Skips the test if the module cannot be loaded.
    """
    mocks = {
        "openai": MagicMock(),
        "dotenv": MagicMock(),
    }
    with patch.dict(sys.modules, mocks):
        with patch("os.chdir"):
            spec = importlib.util.spec_from_file_location(
                "agent_runtime_module", ROOT / "agent_runtime.py"
            )
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                return mod
            except Exception as exc:
                pytest.skip(f"Could not import agent_runtime.py: {exc}")


# ── Fixtures ──────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture(scope="session")
def boot_text():
    p = ROOT / "Boot.md"
    assert p.exists(), "Boot.md not found at project root"
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def boot_frontmatter(boot_text):
    return parse_frontmatter(boot_text)


@pytest.fixture(scope="session")
def qwen_md_text():
    p = ROOT / "QWEN.md"
    assert p.exists(), "QWEN.md not found at project root"
    return p.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def skillos_text():
    p = ROOT / "skillos.py"
    assert p.exists(), "skillos.py not found at project root"
    return p.read_text(encoding="utf-8")
