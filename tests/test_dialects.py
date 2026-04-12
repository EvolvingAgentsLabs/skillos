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
    "formal-proof",
    "system-dynamics",
    "boolean-logic",
    "data-flow",
    "smiles-chem",
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

    def test_total_skills_at_least_25(self):
        fm = _parse_frontmatter_from_file(self.SKILL_INDEX_PATH)
        assert fm["total_skills"] >= 25, (
            f"total_skills is {fm['total_skills']}, expected >= 25"
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
        "system/skills/orchestration/ingress",
        "system/skills/orchestration/egress",
    ])
    def expected_dir(self, request):
        return os.path.join(SKILLOS_ROOT, request.param)

    def test_directory_exists(self, expected_dir):
        assert os.path.isdir(expected_dir), f"Directory missing: {expected_dir}"


# ---------------------------------------------------------------------------
# 12. TestIntentCompilerManifest
# ---------------------------------------------------------------------------
class TestIntentCompilerManifest:
    MANIFEST_PATH = os.path.join(
        SKILLS_DIR, "orchestration", "ingress", "intent-compiler-agent.manifest.md"
    )

    def test_manifest_exists(self):
        assert os.path.isfile(self.MANIFEST_PATH)

    def test_manifest_fields(self):
        fm = _parse_frontmatter_from_file(self.MANIFEST_PATH)
        assert fm["domain"] == "orchestration"
        assert fm["family"] == "ingress"
        assert fm["extends"] == "orchestration/base"
        assert fm["type"] == "agent"
        assert "full_spec" in fm
        assert fm["full_spec"].endswith("intent-compiler-agent.md")

    def test_manifest_subagent_type(self):
        fm = _parse_frontmatter_from_file(self.MANIFEST_PATH)
        assert fm["subagent_type"] == "intent-compiler-agent"


# ---------------------------------------------------------------------------
# 13. TestIntentCompilerSpec
# ---------------------------------------------------------------------------
class TestIntentCompilerSpec:
    SPEC_PATH = os.path.join(
        SKILLS_DIR, "orchestration", "ingress", "intent-compiler-agent.md"
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
        assert fm.get("extends") == "orchestration/base"

    def test_spec_references_dialect_compiler(self):
        content = _read_file(self.SPEC_PATH)
        assert "dialect-compiler-agent" in content


# ---------------------------------------------------------------------------
# 14. TestHumanRendererManifest
# ---------------------------------------------------------------------------
class TestHumanRendererManifest:
    MANIFEST_PATH = os.path.join(
        SKILLS_DIR, "orchestration", "egress", "human-renderer-agent.manifest.md"
    )

    def test_manifest_exists(self):
        assert os.path.isfile(self.MANIFEST_PATH)

    def test_manifest_fields(self):
        fm = _parse_frontmatter_from_file(self.MANIFEST_PATH)
        assert fm["domain"] == "orchestration"
        assert fm["family"] == "egress"
        assert fm["extends"] == "orchestration/base"
        assert fm["type"] == "agent"
        assert fm["full_spec"].endswith("human-renderer-agent.md")

    def test_manifest_subagent_type(self):
        fm = _parse_frontmatter_from_file(self.MANIFEST_PATH)
        assert fm["subagent_type"] == "human-renderer-agent"


# ---------------------------------------------------------------------------
# 15. TestHumanRendererSpec
# ---------------------------------------------------------------------------
class TestHumanRendererSpec:
    SPEC_PATH = os.path.join(
        SKILLS_DIR, "orchestration", "egress", "human-renderer-agent.md"
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
        assert fm.get("extends") == "orchestration/base"

    def test_spec_references_dialect_expander(self):
        content = _read_file(self.SPEC_PATH)
        assert "dialect-expander-agent" in content


# ---------------------------------------------------------------------------
# 16. TestOrchestrationFacadeSkills
# ---------------------------------------------------------------------------
ORCHESTRATION_SKILLS_DIR = os.path.join(SKILLS_DIR, "orchestration")


class TestOrchestrationFacadeSkills:
    """Verify orchestration/index.md lists facade agents."""

    def test_orchestration_index_skill_count(self):
        fm = _parse_frontmatter_from_file(
            os.path.join(ORCHESTRATION_SKILLS_DIR, "index.md")
        )
        assert fm.get("skill_count") == 3

    def test_orchestration_index_lists_intent_compiler(self):
        content = _read_file(os.path.join(ORCHESTRATION_SKILLS_DIR, "index.md"))
        assert "intent-compiler-agent" in content

    def test_orchestration_index_lists_human_renderer(self):
        content = _read_file(os.path.join(ORCHESTRATION_SKILLS_DIR, "index.md"))
        assert "human-renderer-agent" in content


# ---------------------------------------------------------------------------
# 17. TestIntentCompilerDialectRouting
# ---------------------------------------------------------------------------
class TestIntentCompilerDialectRouting:
    """Verify intent-compiler-agent routes to correct dialect for each domain.

    The intent-compiler defines a mapping table (Intent Pattern → Preferred Dialect)
    and a domain classification table. These tests validate completeness and
    consistency without invoking an LLM.
    """

    SPEC_PATH = os.path.join(
        SKILLS_DIR, "orchestration", "ingress", "intent-compiler-agent.md"
    )

    # The expected routing table from the intent-compiler spec
    EXPECTED_ROUTES = {
        "exec-plan": "Execution plan, multi-step goal",
        "formal-proof": "Logical argument, causal chain",
        "boolean-logic": "Conditions, rules, gating logic",
        "data-flow": "Pipeline, data processing flow",
        "system-dynamics": "System behavior, feedback loops",
        "roclaw-bytecode": "Robot motor commands",
        "strategy-pointer": "Strategy reference",
        "constraint-dsl": "Constraints or requirements",
        "caveman-prose": "Prose for storage",
        "smiles-chem": "Molecular structure",
    }

    # Domain classification signal words expected in the spec
    EXPECTED_DOMAINS = {
        "robot": ["navigate", "move", "RoClaw"],
        "memory": ["remember", "trace", "dream"],
        "knowledge": ["wiki", "research", "explain"],
        "orchestration": ["plan", "execute", "workflow"],
        "reasoning": ["prove", "therefore", "implies"],
    }

    @pytest.fixture(autouse=True)
    def _load_spec(self):
        self._content = _read_file(self.SPEC_PATH)

    def test_every_routed_dialect_exists_as_definition(self):
        """Every dialect referenced in the routing table must have a .dialect.md file."""
        for dialect_id in self.EXPECTED_ROUTES:
            path = os.path.join(DIALECTS_DIR, f"{dialect_id}.dialect.md")
            assert os.path.isfile(path), (
                f"Intent compiler routes to '{dialect_id}' but "
                f"{dialect_id}.dialect.md does not exist"
            )

    def test_every_routed_dialect_in_registry_index(self):
        """Every dialect in the routing table must appear in _index.md."""
        index_content = _read_file(os.path.join(DIALECTS_DIR, "_index.md"))
        for dialect_id in self.EXPECTED_ROUTES:
            assert dialect_id in index_content, (
                f"Intent compiler routes to '{dialect_id}' but it's missing from _index.md"
            )

    @pytest.fixture(params=list(EXPECTED_ROUTES.keys()))
    def routed_dialect(self, request):
        return request.param

    def test_routing_table_contains_dialect(self, routed_dialect):
        """Each expected dialect must appear in the intent-compiler spec."""
        assert routed_dialect in self._content, (
            f"Dialect '{routed_dialect}' missing from intent-compiler routing table"
        )

    def test_domain_classification_table_present(self):
        """The spec must contain signal words for all 5 domains."""
        for domain, keywords in self.EXPECTED_DOMAINS.items():
            assert domain in self._content, (
                f"Domain '{domain}' missing from intent-compiler classification"
            )
            for kw in keywords:
                assert kw in self._content, (
                    f"Signal word '{kw}' for domain '{domain}' missing"
                )

    def test_fallback_dialect_defined(self):
        """The spec must define caveman-prose as the fallback dialect."""
        assert "caveman-prose" in self._content
        assert "confidence" in self._content.lower()

    def test_strict_patch_not_in_routing_table(self):
        """strict-patch is a code-editing dialect, not an intent-compilation target.

        It should NOT appear in the intent-compiler's routing table (it's invoked
        directly by the benchmark/tool, not via intent classification).
        """
        # strict-patch may be mentioned elsewhere in the spec for reference,
        # but should not be in the "Preferred Dialect" column of the routing table.
        # We check it's NOT listed as a route destination.
        lines = self._content.split("\n")
        routing_lines = [
            ln for ln in lines
            if "Preferred Dialect" not in ln  # skip header
            and "|" in ln
            and "strict-patch" in ln
            and any(kw in ln for kw in ["Intent Pattern", "plan", "argument", "conditions"])
        ]
        # strict-patch shouldn't be an intent route (it's a tool-level dialect)
        # This is a soft check — if strict-patch IS added later, update this test.
        assert len(routing_lines) == 0, (
            "strict-patch found in intent routing table — it should be invoked "
            "directly by tools, not via intent classification"
        )


# ---------------------------------------------------------------------------
# 18. TestHumanRendererDialectExpansion
# ---------------------------------------------------------------------------
class TestHumanRendererDialectExpansion:
    """Verify human-renderer-agent can detect and expand each dialect back to prose.

    The human-renderer defines a detection table (Content Pattern → Detected Dialect)
    and delegates to dialect-expander-agent. These tests validate completeness.
    """

    SPEC_PATH = os.path.join(
        SKILLS_DIR, "orchestration", "egress", "human-renderer-agent.md"
    )

    # The expected detection patterns from the renderer spec
    EXPECTED_DETECTIONS = {
        "exec-plan": "@plan[",
        "formal-proof": "GIVEN:",
        "system-dynamics": "[STOCK]",
        "boolean-logic": "∧",
        "data-flow": "[SRC]",
        "smiles-chem": "SMILES",
        "roclaw-bytecode": "hex frames",
        "strategy-pointer": "@w[",
        "memory-xp": "[XP]",
        "constraint-dsl": "[HARD]",
    }

    @pytest.fixture(autouse=True)
    def _load_spec(self):
        self._content = _read_file(self.SPEC_PATH)

    @pytest.fixture(params=list(EXPECTED_DETECTIONS.keys()))
    def detected_dialect(self, request):
        return request.param

    def test_detection_pattern_present(self, detected_dialect):
        """Each dialect must have a detection pattern in the renderer spec."""
        assert detected_dialect in self._content, (
            f"Dialect '{detected_dialect}' missing from human-renderer detection table"
        )

    def test_detection_signature_present(self, detected_dialect):
        """The signature token for each dialect must appear in the spec."""
        signature = self.EXPECTED_DETECTIONS[detected_dialect]
        assert signature in self._content, (
            f"Detection signature '{signature}' for '{detected_dialect}' "
            f"missing from human-renderer spec"
        )

    def test_every_detected_dialect_has_definition(self, detected_dialect):
        """Every dialect the renderer can detect must have a .dialect.md file."""
        path = os.path.join(DIALECTS_DIR, f"{detected_dialect}.dialect.md")
        assert os.path.isfile(path), (
            f"Renderer detects '{detected_dialect}' but "
            f"{detected_dialect}.dialect.md does not exist"
        )

    def test_fallback_for_unknown_dialect(self):
        """The spec must define fallback behavior for unrecognized output."""
        assert "fallback" in self._content.lower()
        assert "caveman-prose" in self._content

    def test_irreversible_dialect_handling(self):
        """The spec must handle irreversible dialects (e.g., roclaw-bytecode)."""
        assert "irreversible" in self._content.lower()
        assert "information_notes" in self._content


# ---------------------------------------------------------------------------
# 19. TestLanguageFacadeBidirectional
# ---------------------------------------------------------------------------
class TestLanguageFacadeBidirectional:
    """Verify bidirectional coverage: every dialect the intent-compiler can
    route TO must be detectable and expandable BY the human-renderer.

    This validates the Language Facade round-trip guarantee.
    """

    COMPILER_PATH = os.path.join(
        SKILLS_DIR, "orchestration", "ingress", "intent-compiler-agent.md"
    )
    RENDERER_PATH = os.path.join(
        SKILLS_DIR, "orchestration", "egress", "human-renderer-agent.md"
    )

    # Dialects that the intent-compiler can route to
    COMPILER_DIALECTS = [
        "exec-plan", "formal-proof", "boolean-logic", "data-flow",
        "system-dynamics", "roclaw-bytecode", "strategy-pointer",
        "constraint-dsl", "caveman-prose", "smiles-chem",
    ]

    @pytest.fixture(params=COMPILER_DIALECTS)
    def dialect_id(self, request):
        return request.param

    def test_compiler_dialect_detectable_by_renderer(self, dialect_id):
        """Every dialect the compiler routes to must be in the renderer's detection table."""
        renderer_content = _read_file(self.RENDERER_PATH)
        # caveman-prose is the fallback, not detected by pattern
        if dialect_id == "caveman-prose":
            assert "caveman-prose" in renderer_content
            return
        assert dialect_id in renderer_content, (
            f"Intent-compiler routes to '{dialect_id}' but human-renderer "
            f"cannot detect it — Language Facade has a gap"
        )

    def test_dialect_has_expansion_protocol(self, dialect_id):
        """Every routed dialect must define an Expansion Protocol in its .dialect.md."""
        path = os.path.join(DIALECTS_DIR, f"{dialect_id}.dialect.md")
        if not os.path.isfile(path):
            pytest.skip(f"{dialect_id}.dialect.md not found")
        content = _read_file(path)
        assert "## Expansion Protocol" in content, (
            f"Dialect '{dialect_id}' has no Expansion Protocol section — "
            f"human-renderer cannot expand it"
        )


# ---------------------------------------------------------------------------
# 20. TestScenarioDialectDeclarations
# ---------------------------------------------------------------------------
class TestScenarioDialectDeclarations:
    """Validate requires_dialects and pipeline fields in Dialect_Benchmark.md."""

    SCENARIO_PATH = os.path.join(
        SKILLOS_ROOT, "scenarios", "Dialect_Benchmark.md"
    )

    @pytest.fixture(autouse=True)
    def _load_scenario(self):
        self._content = _read_file(self.SCENARIO_PATH)
        self._fm = _parse_frontmatter(self._content)

    def test_requires_dialects_present(self):
        assert "requires_dialects" in self._fm, (
            "Scenario missing requires_dialects field"
        )

    def test_requires_dialects_are_valid(self):
        for dialect_id in self._fm["requires_dialects"]:
            path = os.path.join(DIALECTS_DIR, f"{dialect_id}.dialect.md")
            assert os.path.isfile(path), (
                f"requires_dialects lists '{dialect_id}' but "
                f"{dialect_id}.dialect.md does not exist"
            )

    def test_pipeline_present(self):
        assert "pipeline" in self._fm, "Scenario missing pipeline field"

    def test_pipeline_steps_sequential(self):
        steps = self._fm["pipeline"]
        for i, step in enumerate(steps, start=1):
            assert step["step"] == i, (
                f"Pipeline step {i} has step number {step['step']}"
            )

    def test_pipeline_steps_have_required_fields(self):
        for step in self._fm["pipeline"]:
            assert "step" in step, "Pipeline step missing 'step' field"
            assert "deliverable" in step, "Pipeline step missing 'deliverable' field"
            assert "dialect" in step, "Pipeline step missing 'dialect' field"

    def test_pipeline_dialects_subset_of_requires(self):
        required = set(self._fm["requires_dialects"])
        for step in self._fm["pipeline"]:
            assert step["dialect"] in required, (
                f"Pipeline step dialect '{step['dialect']}' not in requires_dialects"
            )


# ---------------------------------------------------------------------------
# 21. TestSystemAgentInlineGrammars
# ---------------------------------------------------------------------------
class TestSystemAgentInlineGrammars:
    """Validate Quick Grammar Reference and Pipeline Execution Mode in system-agent.md."""

    SPEC_PATH = os.path.join(
        SKILLS_DIR, "orchestration", "core", "system-agent.md"
    )

    @pytest.fixture(autouse=True)
    def _load_spec(self):
        self._content = _read_file(self.SPEC_PATH)

    def test_quick_grammar_reference_exists(self):
        assert "### Quick Grammar Reference" in self._content

    def test_pipeline_execution_mode_exists(self):
        assert "### Pipeline Execution Mode" in self._content

    INLINED_DIALECTS = [
        "formal-proof",
        "system-dynamics",
        "boolean-logic",
        "constraint-dsl",
        "exec-plan",
        "data-flow",
    ]

    @pytest.fixture(params=INLINED_DIALECTS)
    def inlined_dialect(self, request):
        return request.param

    def test_dialect_inlined(self, inlined_dialect):
        assert f"**{inlined_dialect}**" in self._content, (
            f"Dialect '{inlined_dialect}' not inlined in Quick Grammar Reference"
        )

    # Verify key tokens from each dialect's grammar match what's in the actual files
    KEY_TOKENS = {
        "formal-proof": "GIVEN:",
        "system-dynamics": "[STOCK]",
        "boolean-logic": "parenthesization",
        "constraint-dsl": "C[N]",
        "exec-plan": "@plan[",
        "data-flow": "[SRC]",
    }

    def test_key_tokens_present(self, inlined_dialect):
        token = self.KEY_TOKENS[inlined_dialect]
        assert token in self._content, (
            f"Key token '{token}' for '{inlined_dialect}' missing from "
            f"Quick Grammar Reference"
        )
