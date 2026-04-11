"""Tests for the skill-security-scan-agent — validates spec files exist and are well-formed."""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ROOT = Path(__file__).resolve().parent.parent


# ── Helpers ──────────────────────────────────────────────────────

def _parse_frontmatter(text: str) -> dict:
    """Return key->value dict from YAML-style frontmatter."""
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


# ── Manifest tests ───────────────────────────────────────────────

class TestSecurityScannerManifest:
    MANIFEST_PATH = ROOT / "system/skills/validation/security/skill-security-scan-agent.manifest.md"

    def test_manifest_exists(self):
        assert self.MANIFEST_PATH.exists()

    def test_manifest_has_required_frontmatter(self):
        fm = _parse_frontmatter(self.MANIFEST_PATH.read_text())
        for key in ("skill_id", "name", "type", "domain", "family", "version",
                     "description", "full_spec"):
            assert key in fm, f"Missing frontmatter key: {key}"

    def test_manifest_domain_is_validation(self):
        fm = _parse_frontmatter(self.MANIFEST_PATH.read_text())
        assert fm["domain"] == "validation"

    def test_manifest_family_is_security(self):
        fm = _parse_frontmatter(self.MANIFEST_PATH.read_text())
        assert fm["family"] == "security"

    def test_manifest_extends_validation_base(self):
        fm = _parse_frontmatter(self.MANIFEST_PATH.read_text())
        assert fm.get("extends") == "validation/base"


# ── Full spec tests ──────────────────────────────────────────────

class TestSecurityScannerSpec:
    SPEC_PATH = ROOT / "system/skills/validation/security/skill-security-scan-agent.md"

    def test_spec_exists(self):
        assert self.SPEC_PATH.exists()

    def test_spec_references_all_8_checks(self):
        text = self.SPEC_PATH.read_text()
        for i in range(1, 9):
            check_id = f"CHECK-{i:02d}"
            assert check_id in text, f"{check_id} not found in spec"

    def test_spec_has_safe_verdict(self):
        text = self.SPEC_PATH.read_text()
        assert "SAFE" in text

    def test_spec_has_warning_verdict(self):
        text = self.SPEC_PATH.read_text()
        assert "WARNING" in text

    def test_spec_has_blocked_verdict(self):
        text = self.SPEC_PATH.read_text()
        assert "BLOCKED" in text

    def test_spec_extends_validation_base(self):
        fm = _parse_frontmatter(self.SPEC_PATH.read_text())
        assert fm.get("extends") == "validation/base"

    def test_spec_has_report_template(self):
        text = self.SPEC_PATH.read_text()
        assert "## Report Template" in text or "## Check Results" in text


# ── Supporting infrastructure ────────────────────────────────────

class TestSecurityInfrastructure:

    def test_blocklist_exists(self):
        assert (ROOT / "system/security/blocklist.md").exists()

    def test_scan_reports_dir_exists(self):
        assert (ROOT / "system/security/scan_reports").is_dir()

    def test_scan_index_exists(self):
        assert (ROOT / "system/security/scan_index.md").exists()

    def test_scan_index_has_table_header(self):
        text = (ROOT / "system/security/scan_index.md").read_text()
        assert "scan_id" in text
        assert "verdict" in text


# ── Validation index updated ─────────────────────────────────────

class TestValidationIndexUpdated:
    INDEX_PATH = ROOT / "system/skills/validation/index.md"

    def test_index_lists_security_scanner(self):
        text = self.INDEX_PATH.read_text()
        assert "skill-security-scan-agent" in text

    def test_index_skill_count_updated(self):
        fm = _parse_frontmatter(self.INDEX_PATH.read_text())
        count = int(fm.get("skill_count", "0"))
        assert count >= 2
