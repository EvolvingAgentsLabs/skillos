"""End-to-end forge executor tests with a mocked Claude bridge.

Exercises the full gap-to-skill loop described in
``scenarios/Forge_Gap_To_Skill.md`` without touching Ollama or the network:

  router gap  →  ForgeExecutor.run  →  MockClaudeBridge
                                       artifact parsing (forge.artifacts)
                                       budget charge (forge.budget)
                                       journal append (forge.journal)

These are deliberately scoped below the AgentRuntime so that test failures
point at the forge package itself.  An AgentRuntime-level smoke test lives
in ``test_agent_runtime_route.py``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from forge.budget import BudgetLedger  # noqa: E402
from forge.claude_bridge import (  # noqa: E402
    ForgeResponse,
    MockClaudeBridge,
    PromptTemplate,
)
from forge.executor import ForgeExecutor, ForgeJobSpec  # noqa: E402
from forge.journal import ForgeJournal  # noqa: E402
from forge.router import RouteKind  # noqa: E402


# --- fixtures -------------------------------------------------------

def _scripted_generate_response() -> str:
    """A plausible Claude response for the forge-generate prompt.

    Mirrors the semver-sort example from the demo scenario.  Exact bytes
    matter because tests assert on file contents.
    """
    return """\
====FILE manifest.md====
---
skill_id: utility/semver/semver-sort
name: semver-sort
type: tool
domain: utility
family: semver
extends: utility/base
target_model: gemma4:e2b
produced_by: forge/generate/forge-generate-agent
forge_job_id: job-test-1
---
====FILE skill.md====
# semver-sort

Sort a list of SemVer 2.0 strings.  Delegate parsing to skill.js.
====FILE skill.js====
function compareSemver(a, b) {
  // minimal — real impl in production
  return a.localeCompare(b, undefined, { numeric: true });
}
function ai_edge_gallery_get_result(data /*, secret */) {
  const input = JSON.parse(data);
  const versions = Array.isArray(input.versions) ? input.versions : [];
  return JSON.stringify({ sorted: [...versions].sort(compareSemver) });
}
====FILE tests/cases.yaml====
- id: happy
  input: { versions: ["1.0.0", "0.9.0", "1.0.0-beta"] }
  expected: { sorted: ["0.9.0", "1.0.0-beta", "1.0.0"] }
  match: exact
- id: edge_empty
  input: { versions: [] }
  expected: { sorted: [] }
  match: exact
- id: adversarial_malformed
  input: { versions: ["1.0", "not-a-version", "1.0.0"] }
  expected_error: graceful-partial
====FILE forge_meta.yaml====
rationale: deterministic sort is pure JS; no LLM in hot path
token_estimate: 900
tools_requested: []
"""


def _bridge_with_response(text: str, *, input_tokens: int = 1200,
                          output_tokens: int = 600) -> MockClaudeBridge:
    bridge = MockClaudeBridge()
    bridge.push(ForgeResponse(
        text=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    ))
    return bridge


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """Create the project directory skeleton a real run would have."""
    p = tmp_path / "Project_semver_sort"
    (p / "forge").mkdir(parents=True)
    return p


# --- generate flow --------------------------------------------------

def test_generate_flow_writes_expected_artifacts(project):
    bridge = _bridge_with_response(_scripted_generate_response())
    executor = ForgeExecutor(bridge=bridge, template_root=ROOT / "system" / "skills" / "forge")
    spec = ForgeJobSpec(
        goal="sort SemVer strings with SemVer 2.0 ordering",
        project_path=project,
        kind=RouteKind.GENERATE,
        job_id="job-test-1",
    )

    result = executor.run(spec)

    assert result.outcome == "pass"
    assert result.candidates_path == project / "forge" / "candidates" / "job-test-1"
    expected = {
        "manifest.md", "skill.md", "skill.js",
        "tests/cases.yaml", "forge_meta.yaml",
    }
    actual = {str(p.relative_to(result.candidates_path)) for p in result.artifacts}
    assert actual == expected

    # skill.js must round-trip content faithfully.
    js = (result.candidates_path / "skill.js").read_text(encoding="utf-8")
    assert "ai_edge_gallery_get_result" in js


def test_generate_flow_charges_budget_and_writes_journal(project):
    bridge = _bridge_with_response(
        _scripted_generate_response(),
        input_tokens=1200, output_tokens=600,
    )
    executor = ForgeExecutor(
        bridge=bridge,
        template_root=ROOT / "system" / "skills" / "forge",
    )
    spec = ForgeJobSpec(
        goal="sort semver strings",
        project_path=project,
        kind=RouteKind.GENERATE,
        job_id="job-test-2",
    )

    result = executor.run(spec)
    assert result.outcome == "pass"
    assert result.tokens == 1800

    ledger = BudgetLedger.for_project(project)
    snap = ledger.snapshot()
    assert snap["usage"]["today_tokens"] == 1800
    assert snap["usage"]["today_usd"] > 0.0

    journal = ForgeJournal(project)
    records = journal.read_all()
    assert len(records) == 1
    assert records[0].job_id == "job-test-2"
    assert records[0].outcome == "pass"
    assert records[0].claude_tokens_used == 1800


def test_parse_error_dumps_raw_and_fails_cleanly(project):
    """Malformed response leaves forensics behind and records ``fail``.

    The executor must not explode on a bad response — it must record
    ``outcome: fail`` and preserve the raw text so an operator can
    diagnose the issue.
    """
    bridge = _bridge_with_response(
        "Here is a skill: not actually a bundle.",
        input_tokens=100, output_tokens=50,
    )
    executor = ForgeExecutor(
        bridge=bridge,
        template_root=ROOT / "system" / "skills" / "forge",
    )
    spec = ForgeJobSpec(
        goal="x",
        project_path=project,
        kind=RouteKind.GENERATE,
        job_id="job-bad",
    )

    result = executor.run(spec)
    assert result.outcome == "fail"
    # Executor charges even on parse failure — cloud call was real.
    snap = BudgetLedger.for_project(project).snapshot()
    assert snap["usage"]["today_tokens"] == 150
    # Raw response preserved for forensics.
    raw_dump = project / "forge" / "candidates" / "job-bad" / "raw_response.txt"
    assert raw_dump.exists()


def test_per_job_budget_cap_blocks_before_bridge_call(project):
    # Pre-set a tiny per-job cap.
    ledger = BudgetLedger.for_project(
        project, caps={"max_claude_tokens_per_job": 100},
    )
    ledger.save()

    bridge = _bridge_with_response(_scripted_generate_response())
    executor = ForgeExecutor(
        bridge=bridge,
        template_root=ROOT / "system" / "skills" / "forge",
    )
    spec = ForgeJobSpec(
        goal="x",
        project_path=project,
        kind=RouteKind.GENERATE,
        job_id="job-blocked",
        max_skill_tokens=2500,  # will exceed the per-job cap
    )

    result = executor.run(spec)
    assert result.outcome == "budget_exceeded"
    # Bridge must not have been called.
    assert bridge.calls == []


# --- evolve flow ----------------------------------------------------

def _scripted_evolve_response() -> str:
    return """\
====FILE manifest.md====
---
skill_id: memory/analysis/memory-analysis-agent
target_model: gemma4:e2b
gemma_compat:
  model: gemma4:e2b
  validated_at: "2026-04-20T00:00:00Z"
  pass_rate: 0.92
  cases_total: 10
  cases_passed: 9
---
====FILE skill.md====
# Memory Analysis (evolved)

Use near-duplicate detection before clustering.  Reject entries with
identical normalized titles.
====FILE diff.patch====
--- a/memory-analysis.md
+++ b/memory-analysis.md
@@ -1 +1,2 @@
-Cluster by title.
+Reject duplicate normalized titles before clustering.
====FILE tests/cases.yaml====
- id: dedup_happy
  input: { entries: ["Foo", "FOO", "foo"] }
  expected: { clusters: 1 }
====FILE rationale.md====
Dominant cluster: missing-few-shot + logic-bug (no normalization step).
Fix: add normalization before clustering.
====FILE forge_meta.yaml====
rollback_hint: Revert the normalization step if dedupe over-merges distinct titles.
"""


def test_evolve_flow_materializes_diff(project):
    bridge = _bridge_with_response(_scripted_evolve_response())
    executor = ForgeExecutor(
        bridge=bridge,
        template_root=ROOT / "system" / "skills" / "forge",
    )
    spec = ForgeJobSpec(
        goal="improve memory dedupe",
        project_path=project,
        kind=RouteKind.EVOLVE,
        trigger="evolve",
        target_skill_id="memory/analysis/memory-analysis-agent",
        signal="degradation",
        evidence="trace-1, trace-2, trace-3",
        current_skill="# Memory Analysis\nCluster by title.",
        job_id="job-evolve-1",
    )

    result = executor.run(spec)
    assert result.outcome == "pass"
    names = {p.name for p in result.artifacts}
    assert "diff.patch" in names
    assert "rationale.md" in names


# --- prompt templates -----------------------------------------------

def test_generate_template_renders_all_placeholders(tmp_path):
    tmpl = PromptTemplate.load(
        "generate", "generate_skill",
        root=ROOT / "system" / "skills" / "forge",
    )
    rendered = tmpl.render(
        job_id="j1",
        goal="x",
        project_path="p",
        target_model="gemma4:e2b",
        max_skill_tokens=2500,
        allow_js="true",
        allow_new_tools="false",
        tool_allow_list="Read, Write",
    )
    # No unresolved placeholders of the form {word}.
    import re
    leftovers = re.findall(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", rendered)
    # Known curly-brace uses inside JSON/schema examples are not placeholders,
    # but templates should have no unresolved single-word ones.
    assert leftovers == []
