"""
Tests for the SkillOS Dialects domain — validates all dialect definitions,
skill tree files, manifests, specs, and SkillIndex integration.
"""

import os
import re
import pytest
import yaml

# Root of the skillos project
SKILLOS_ROOT = os.path.join(os.path.dirname(__file__), "..")

DIALECTS_DIR = os.path.join(SKILLOS_ROOT, "system", "dialects")
SKILLS_DIR = os.path.join(SKILLOS_ROOT, "system", "skills")
DIALECTS_SKILLS_DIR = os.path.join(SKILLS_DIR, "dialects")

# All built-in dialect IDs
DIALECT_IDS = [
    "roclaw-bytecode",
    "caveman-prose",
    "strategy-pointer",
    "trace-log",
    "memory-xp",
    "constraint-dsl",
    "exec-plan",
    "strict-patch",
    "dom-nav",
]

VALID_COMPRESSION_TYPES = {"structural", "lexical", "symbolic"}

# Required sections in every .dialect.md file
REQUIRED_DIALECT_SECTIONS = [
    "Purpose",
    "Domain Scope",
    "Compression Rules",
    "Preservation Rules",
    "Grammar / Syntax",
    "Examples",
    "Expansion Protocol",
    "Metrics",
]


def _read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from a markdown file."""
    match = re.match(r"^---\n(.*?\n)---", content, re.DOTALL)
    assert match, f"No YAML frontmatter found"
    return yaml.safe_load(match.group(1))


def _parse_frontmatter_from_file(path: str) -> dict:
    return _parse_frontmatter(_read_file(path))


# ---------------------------------------------------------------------------
# 1. TestDialectRegistryIndex
# ---------------------------------------------------------------------------
class TestDialectRegistryIndex:
    """Validate system/dialects/_index.md."""

    INDEX_PATH = os.path.join(DIALECTS_DIR, "_index.md")

    def test_index_exists(self):
        assert os.path.isfile(self.INDEX_PATH), "_index.md missing from system/dialects/"

    def test_index_has_dialect_count(self):
        fm = _parse_frontmatter_from_file(self.INDEX_PATH)
        assert "dialect_count" in fm
        assert fm["dialect_count"] == len(DIALECT_IDS)

    def test_index_lists_all_dialects(self):
        content = _read_file(self.INDEX_PATH)
        for dialect_id in DIALECT_IDS:
            assert dialect_id in content, f"Dialect '{dialect_id}' not listed in _index.md"

    def test_index_type_field(self):
        fm = _parse_frontmatter_from_file(self.INDEX_PATH)
        assert fm.get("type") == "dialect-registry"


# ---------------------------------------------------------------------------
# 2. TestDialectDefinitions (parametrized over 3 dialects)
# ---------------------------------------------------------------------------
class TestDialectDefinitions:
    """Validate each .dialect.md file."""

    @pytest.fixture(params=DIALECT_IDS)
    def dialect_id(self, request):
        return request.param

    def _dialect_path(self, dialect_id: str) -> str:
        return os.path.join(DIALECTS_DIR, f"{dialect_id}.dialect.md")

    def test_dialect_file_exists(self, dialect_id):
        path = self._dialect_path(dialect_id)
        assert os.path.isfile(path), f"{dialect_id}.dialect.md not found"

    def test_dialect_frontmatter_fields(self, dialect_id):
        fm = _parse_frontmatter_from_file(self._dialect_path(dialect_id))
        required_fields = [
            "dialect_id",
            "name",
            "version",
            "domain_scope",
            "compression_type",
            "compression_ratio",
            "reversible",
            "input_format",
            "output_format",
        ]
        for field in required_fields:
            assert field in fm, f"Missing frontmatter field '{field}' in {dialect_id}"

    def test_dialect_id_matches_filename(self, dialect_id):
        fm = _parse_frontmatter_from_file(self._dialect_path(dialect_id))
        assert fm["dialect_id"] == dialect_id, (
            f"dialect_id '{fm['dialect_id']}' does not match filename '{dialect_id}'"
        )

    def test_valid_compression_type(self, dialect_id):
        fm = _parse_frontmatter_from_file(self._dialect_path(dialect_id))
        assert fm["compression_type"] in VALID_COMPRESSION_TYPES, (
            f"Invalid compression_type '{fm['compression_type']}' in {dialect_id}"
        )

    def test_domain_scope_is_list(self, dialect_id):
        fm = _parse_frontmatter_from_file(self._dialect_path(dialect_id))
        assert isinstance(fm["domain_scope"], list), "domain_scope must be a list"
        assert len(fm["domain_scope"]) > 0, "domain_scope must not be empty"

    def test_reversible_is_boolean(self, dialect_id):
        fm = _parse_frontmatter_from_file(self._dialect_path(dialect_id))
        assert isinstance(fm["reversible"], bool), "reversible must be a boolean"

    def test_required_sections_present(self, dialect_id):
        content = _read_file(self._dialect_path(dialect_id))
        for section in REQUIRED_DIALECT_SECTIONS:
            assert f"## {section}" in content, (
                f"Missing required section '## {section}' in {dialect_id}.dialect.md"
            )

    def test_minimum_examples(self, dialect_id):
        content = _read_file(self._dialect_path(dialect_id))
        # Count ### Example N patterns
        examples = re.findall(r"### Example \d+", content)
        assert len(examples) >= 3, (
            f"Expected at least 3 examples in {dialect_id}, found {len(examples)}"
        )

    def test_version_is_semver(self, dialect_id):
        fm = _parse_frontmatter_from_file(self._dialect_path(dialect_id))
        assert re.match(r"^\d+\.\d+\.\d+$", fm["version"]), (
            f"Version '{fm['version']}' is not valid semver"
        )


# ---------------------------------------------------------------------------
# 3. TestDialectsSkillDomain
# ---------------------------------------------------------------------------
class TestDialectsSkillDomain:
    """Validate base.md and index.md for the dialects skill domain."""

    def test_base_exists(self):
        path = os.path.join(DIALECTS_SKILLS_DIR, "base.md")
        assert os.path.isfile(path), "dialects/base.md missing"

    def test_base_frontmatter(self):
        fm = _parse_frontmatter_from_file(os.path.join(DIALECTS_SKILLS_DIR, "base.md"))
        assert fm.get("skill_domain") == "dialects"
        assert fm.get("type") == "base-template"

    def test_index_exists(self):
        path = os.path.join(DIALECTS_SKILLS_DIR, "index.md")
        assert os.path.isfile(path), "dialects/index.md missing"

    def test_index_frontmatter(self):
        fm = _parse_frontmatter_from_file(os.path.join(DIALECTS_SKILLS_DIR, "index.md"))
        assert fm.get("domain") == "dialects"
        assert fm.get("skill_count") == 3

    def test_index_lists_all_skills(self):
        content = _read_file(os.path.join(DIALECTS_SKILLS_DIR, "index.md"))
        assert "dialect-compiler-agent" in content
        assert "dialect-expander-agent" in content
        assert "dialect-registry-tool" in content


# ---------------------------------------------------------------------------
# 4. TestDialectCompilerManifest
# ---------------------------------------------------------------------------
class TestDialectCompilerManifest:
    MANIFEST_PATH = os.path.join(
        DIALECTS_SKILLS_DIR, "compiler", "dialect-compiler-agent.manifest.md"
    )

    def test_manifest_exists(self):
        assert os.path.isfile(self.MANIFEST_PATH)

    def test_manifest_fields(self):
        fm = _parse_frontmatter_from_file(self.MANIFEST_PATH)
        assert fm["domain"] == "dialects"
        assert fm["family"] == "compiler"
        assert fm["extends"] == "dialects/base"
        assert fm["type"] == "agent"
        assert "full_spec" in fm
        assert fm["full_spec"].endswith("dialect-compiler-agent.md")

    def test_manifest_subagent_type(self):
        fm = _parse_frontmatter_from_file(self.MANIFEST_PATH)
        assert fm["subagent_type"] == "dialect-compiler-agent"


# ---------------------------------------------------------------------------
# 5. TestDialectCompilerSpec
# ---------------------------------------------------------------------------
class TestDialectCompilerSpec:
    SPEC_PATH = os.path.join(
        DIALECTS_SKILLS_DIR, "compiler", "dialect-compiler-agent.md"
    )

    def test_spec_exists(self):
        assert os.path.isfile(self.SPEC_PATH)

    def test_spec_has_input_output_sections(self):
        content = _read_file(self.SPEC_PATH)
        assert "## Input Specification" in content
        assert "## Output Specification" in content
        assert "## Execution Logic" in content

    def test_spec_extends_base(self):
        fm = _parse_frontmatter_from_file(self.SPEC_PATH)
        assert fm.get("extends") == "dialects/base"

    def test_spec_references_dialect_definitions(self):
        content = _read_file(self.SPEC_PATH)
        assert "system/dialects/" in content


# ---------------------------------------------------------------------------
# 6. TestDialectExpanderManifest
# ---------------------------------------------------------------------------
class TestDialectExpanderManifest:
    MANIFEST_PATH = os.path.join(
        DIALECTS_SKILLS_DIR, "expander", "dialect-expander-agent.manifest.md"
    )

    def test_manifest_exists(self):
        assert os.path.isfile(self.MANIFEST_PATH)

    def test_manifest_fields(self):
        fm = _parse_frontmatter_from_file(self.MANIFEST_PATH)
        assert fm["domain"] == "dialects"
        assert fm["family"] == "expander"
        assert fm["extends"] == "dialects/base"
        assert fm["type"] == "agent"
        assert fm["full_spec"].endswith("dialect-expander-agent.md")

    def test_manifest_subagent_type(self):
        fm = _parse_frontmatter_from_file(self.MANIFEST_PATH)
        assert fm["subagent_type"] == "dialect-expander-agent"


# ---------------------------------------------------------------------------
# 7. TestDialectExpanderSpec
# ---------------------------------------------------------------------------
class TestDialectExpanderSpec:
    SPEC_PATH = os.path.join(
        DIALECTS_SKILLS_DIR, "expander", "dialect-expander-agent.md"
    )

    def test_spec_exists(self):
        assert os.path.isfile(self.SPEC_PATH)

    def test_spec_references_expansion_protocol(self):
        content = _read_file(self.SPEC_PATH)
        assert "Expansion Protocol" in content

    def test_spec_handles_irreversible(self):
        content = _read_file(self.SPEC_PATH)
        assert "irreversible" in content.lower()
        assert "information_loss" in content

    def test_spec_extends_base(self):
        fm = _parse_frontmatter_from_file(self.SPEC_PATH)
        assert fm.get("extends") == "dialects/base"


# ---------------------------------------------------------------------------
# 8. TestDialectRegistryManifest
# ---------------------------------------------------------------------------
class TestDialectRegistryManifest:
    MANIFEST_PATH = os.path.join(
        DIALECTS_SKILLS_DIR, "registry", "dialect-registry-tool.manifest.md"
    )

    def test_manifest_exists(self):
        assert os.path.isfile(self.MANIFEST_PATH)

    def test_manifest_type_is_tool(self):
        fm = _parse_frontmatter_from_file(self.MANIFEST_PATH)
        assert fm["type"] == "tool"

    def test_manifest_subagent_type_is_null(self):
        fm = _parse_frontmatter_from_file(self.MANIFEST_PATH)
        assert fm["subagent_type"] is None


# ---------------------------------------------------------------------------
# 9. TestDialectRegistrySpec
# ---------------------------------------------------------------------------
class TestDialectRegistrySpec:
    SPEC_PATH = os.path.join(
        DIALECTS_SKILLS_DIR, "registry", "dialect-registry-tool.md"
    )

    def test_spec_exists(self):
        assert os.path.isfile(self.SPEC_PATH)

    def test_spec_references_index(self):
        content = _read_file(self.SPEC_PATH)
        assert "system/dialects/_index.md" in content

    def test_spec_has_list_match_actions(self):
        content = _read_file(self.SPEC_PATH)
        assert '"list"' in content or "`list`" in content
        assert '"match"' in content or "`match`" in content
        assert '"describe"' in content or "`describe`" in content


# ---------------------------------------------------------------------------
# 10. TestSkillIndexUpdated
# ---------------------------------------------------------------------------
class TestSkillIndexUpdated:
    SKILL_INDEX_PATH = os.path.join(SKILLS_DIR, "SkillIndex.md")

    def test_dialects_domain_in_domain_table(self):
        content = _read_file(self.SKILL_INDEX_PATH)
        assert "| dialects" in content, "dialects domain not in Domain Table"

    def test_dialect_skills_in_quick_lookup(self):
        content = _read_file(self.SKILL_INDEX_PATH)
        assert "dialect-compiler-agent" in content
        assert "dialect-expander-agent" in content
        assert "dialect-registry-tool" in content

    def test_total_skills_at_least_23(self):
        fm = _parse_frontmatter_from_file(self.SKILL_INDEX_PATH)
        assert fm["total_skills"] >= 23, (
            f"total_skills is {fm['total_skills']}, expected >= 23"
        )

    def test_dialects_index_path_correct(self):
        content = _read_file(self.SKILL_INDEX_PATH)
        assert "system/skills/dialects/index.md" in content


# ---------------------------------------------------------------------------
# 11. TestDialectsDirectoryStructure
# ---------------------------------------------------------------------------
class TestDialectsDirectoryStructure:
    """Verify all expected directories exist."""

    EXPECTED_DIRS = [
        os.path.join(SKILLOS_ROOT, "system", "dialects"),
        os.path.join(SKILLOS_ROOT, "system", "skills", "dialects"),
        os.path.join(SKILLOS_ROOT, "system", "skills", "dialects", "compiler"),
        os.path.join(SKILLOS_ROOT, "system", "skills", "dialects", "expander"),
        os.path.join(SKILLOS_ROOT, "system", "skills", "dialects", "registry"),
    ]

    @pytest.fixture(params=[
        "system/dialects",
        "system/skills/dialects",
        "system/skills/dialects/compiler",
        "system/skills/dialects/expander",
        "system/skills/dialects/registry",
    ])
    def expected_dir(self, request):
        return os.path.join(SKILLOS_ROOT, request.param)

    def test_directory_exists(self, expected_dir):
        assert os.path.isdir(expected_dir), f"Directory missing: {expected_dir}"
