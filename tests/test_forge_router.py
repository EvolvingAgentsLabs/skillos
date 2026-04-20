"""Tests for forge.router, forge.budget, forge.attestation, forge.journal.

These tests avoid any network or LLM call.  They operate entirely on in-
memory fixtures and tmp_path scratch dirs so they run in CI without needing
Ollama or an ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from forge.attestation import (  # noqa: E402
    AttestationStrength,
    attestation_ok,
    parse_gemma_compat,
)
from forge.budget import BudgetExceeded, BudgetLedger  # noqa: E402
from forge.journal import ForgeJobRecord, ForgeJournal  # noqa: E402
from forge.router import (  # noqa: E402
    ProviderRouter,
    RouteKind,
    RouteRequest,
    Tier,
)


# --- attestation fixtures -------------------------------------------

def _make_manifest(tmp_path: Path, *, model: str = "gemma4:e2b",
                   pass_rate: float = 0.97,
                   days_old: int = 1,
                   strength: str | None = None) -> Path:
    ts = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()
    strength_line = (
        f"  attestation_strength: {strength}\n" if strength else ""
    )
    content = f"""---
skill_id: utility/semver/semver-sort
name: semver-sort
target_model: {model}
gemma_compat:
  model: {model}
  validated_at: "{ts}"
  pass_rate: {pass_rate}
  cases_total: 10
  cases_passed: {int(pass_rate * 10)}
  max_tokens_observed: 1200
  median_latency_ms: 320
  validator_version: "1.0.0"
{strength_line}---
"""
    path = tmp_path / "semver-sort.manifest.md"
    path.write_text(content, encoding="utf-8")
    return path


# --- attestation ----------------------------------------------------

def test_parse_gemma_compat_returns_strong(tmp_path):
    manifest = _make_manifest(tmp_path, pass_rate=0.97)
    compat = parse_gemma_compat(manifest)
    assert compat is not None
    assert compat.attestation_strength == AttestationStrength.STRONG
    assert compat.model == "gemma4:e2b"
    assert compat.pass_rate == pytest.approx(0.97)


def test_parse_gemma_compat_weak_band(tmp_path):
    manifest = _make_manifest(tmp_path, pass_rate=0.85)
    compat = parse_gemma_compat(manifest)
    assert compat is not None
    assert compat.attestation_strength == AttestationStrength.WEAK


def test_parse_gemma_compat_below_weak_is_none(tmp_path):
    manifest = _make_manifest(tmp_path, pass_rate=0.50)
    compat = parse_gemma_compat(manifest)
    assert compat is not None
    assert compat.attestation_strength == AttestationStrength.NONE
    assert attestation_ok(compat, model="gemma4:e2b") is False


def test_attestation_ok_rejects_model_mismatch(tmp_path):
    manifest = _make_manifest(tmp_path, model="gemma4:e2b")
    compat = parse_gemma_compat(manifest)
    assert attestation_ok(compat, model="gemma4:e4b") is False


def test_attestation_ok_rejects_stale(tmp_path):
    manifest = _make_manifest(tmp_path, days_old=60)
    compat = parse_gemma_compat(manifest)
    assert attestation_ok(compat, model="gemma4:e2b") is False


def test_attestation_ok_accepts_fresh_strong(tmp_path):
    manifest = _make_manifest(tmp_path)
    compat = parse_gemma_compat(manifest)
    assert attestation_ok(compat, model="gemma4:e2b") is True


def test_parse_gemma_compat_returns_none_for_missing_block():
    compat = parse_gemma_compat("---\nname: x\n---\n")
    assert compat is None


# --- budget ---------------------------------------------------------

def test_budget_round_trip(tmp_path):
    ledger = BudgetLedger.for_project(tmp_path,
                                      caps={"max_claude_usd_per_day": 5.0})
    ledger.check_can_spend(tokens=1000, usd=0.02)
    ledger.charge(tokens=1000, usd=0.02)
    reopened = BudgetLedger.for_project(tmp_path)
    snap = reopened.snapshot()
    assert snap["usage"]["today_tokens"] == 1000
    assert snap["usage"]["all_time_tokens"] == 1000
    assert snap["caps"]["max_claude_usd_per_day"] == 5.0


def test_budget_refuses_overspend(tmp_path):
    ledger = BudgetLedger.for_project(
        tmp_path, caps={"max_claude_tokens_per_day": 1000}
    )
    ledger.charge(tokens=900, usd=0.0)
    with pytest.raises(BudgetExceeded) as exc:
        ledger.check_can_spend(tokens=200)
    assert exc.value.cap_name == "max_claude_tokens_per_day"


def test_budget_per_job_cap(tmp_path):
    ledger = BudgetLedger.for_project(
        tmp_path, caps={"max_claude_tokens_per_job": 500}
    )
    with pytest.raises(BudgetExceeded) as exc:
        ledger.check_can_spend(tokens=600, is_job_start=True)
    assert exc.value.cap_name == "max_claude_tokens_per_job"


# --- journal --------------------------------------------------------

def _record(job_id: str, *, goal: str = "sort semver",
            outcome: str = "pass", started_at: str | None = None):
    return ForgeJobRecord(
        job_id=job_id,
        trigger="gap",
        goal=goal,
        started_at=started_at or datetime.now(timezone.utc).isoformat(),
        outcome=outcome,
    )


def test_journal_append_and_read(tmp_path):
    journal = ForgeJournal(tmp_path)
    journal.append(_record("j1"))
    journal.append(_record("j2", goal="evolve memory skill"))
    records = journal.read_all()
    assert [r.job_id for r in records] == ["j1", "j2"]


def test_journal_rejects_invalid_trigger(tmp_path):
    journal = ForgeJournal(tmp_path)
    bad = _record("j1")
    bad.trigger = "bogus"
    with pytest.raises(ValueError):
        journal.append(bad)


def test_journal_loop_detector_counts_matches(tmp_path):
    journal = ForgeJournal(tmp_path)
    for i in range(4):
        journal.append(_record(f"j{i}", goal="sort semver list"))
    # unrelated entry to ensure we filter
    journal.append(_record("j99", goal="summarize arxiv paper"))
    assert journal.count_recent_by_signature("sort semver") == 4
    assert journal.count_recent_by_signature("nonexistent") == 0


# --- router ---------------------------------------------------------

def test_router_prefers_cartridge(tmp_path):
    decision = ProviderRouter().route(RouteRequest(
        goal="make breakfast",
        project_path=tmp_path,
        candidate_cartridge="cooking",
    ))
    assert decision.tier == Tier.HOT
    assert decision.kind == RouteKind.CARTRIDGE
    assert decision.target == "cooking"


def test_router_hot_tier_on_strong_attestation(tmp_path):
    manifest = _make_manifest(tmp_path)
    decision = ProviderRouter().route(RouteRequest(
        goal="sort semvers",
        project_path=tmp_path,
        candidate_skill_manifest=manifest,
    ))
    assert decision.tier == Tier.HOT
    assert decision.kind == RouteKind.SKILL
    assert decision.attestation is not None


def test_router_warm_tier_on_weak_attestation(tmp_path):
    manifest = _make_manifest(tmp_path, pass_rate=0.85)
    decision = ProviderRouter().route(RouteRequest(
        goal="sort semvers",
        project_path=tmp_path,
        candidate_skill_manifest=manifest,
    ))
    assert decision.tier == Tier.WARM
    assert decision.kind == RouteKind.SKILL
    assert decision.model == "gemma4:e4b"


def test_router_validate_on_missing_attestation(tmp_path):
    manifest = tmp_path / "bare.manifest.md"
    manifest.write_text("---\nname: bare\n---\n", encoding="utf-8")
    decision = ProviderRouter().route(RouteRequest(
        goal="run bare skill",
        project_path=tmp_path,
        candidate_skill_manifest=manifest,
    ))
    assert decision.tier == Tier.FORGE
    assert decision.kind == RouteKind.VALIDATE


def test_router_validate_on_model_mismatch(tmp_path):
    manifest = _make_manifest(tmp_path, model="gemma4:e4b")
    decision = ProviderRouter().route(RouteRequest(
        goal="x",
        project_path=tmp_path,
        candidate_skill_manifest=manifest,
        target_model="gemma4:e2b",
    ))
    assert decision.kind == RouteKind.VALIDATE


def test_router_evolve_on_degraded_pass_rate(tmp_path):
    manifest = _make_manifest(tmp_path, pass_rate=0.97)
    decision = ProviderRouter().route(RouteRequest(
        goal="x",
        project_path=tmp_path,
        candidate_skill_manifest=manifest,
        recent_pass_rate=0.50,
        recent_sample_size=15,
    ))
    assert decision.tier == Tier.FORGE
    assert decision.kind == RouteKind.EVOLVE


def test_router_no_degrade_below_min_samples(tmp_path):
    manifest = _make_manifest(tmp_path, pass_rate=0.97)
    decision = ProviderRouter().route(RouteRequest(
        goal="x",
        project_path=tmp_path,
        candidate_skill_manifest=manifest,
        recent_pass_rate=0.40,
        recent_sample_size=3,
    ))
    # Below min-samples, not enough signal to evolve.
    assert decision.tier == Tier.HOT


def test_router_generate_when_no_candidate(tmp_path):
    decision = ProviderRouter().route(RouteRequest(
        goal="invent a new thing",
        project_path=tmp_path,
    ))
    assert decision.tier == Tier.FORGE
    assert decision.kind == RouteKind.GENERATE


def test_router_offline_refuses_generate(tmp_path):
    decision = ProviderRouter().route(RouteRequest(
        goal="invent a new thing",
        project_path=tmp_path,
        env={"SKILLOS_FORGE_OFFLINE": "1"},
    ))
    assert decision.tier == Tier.ESCALATE
    assert decision.kind == RouteKind.FORGE_DISABLED


def test_router_offline_refuses_validate(tmp_path):
    manifest = tmp_path / "bare.manifest.md"
    manifest.write_text("---\nname: bare\n---\n", encoding="utf-8")
    decision = ProviderRouter().route(RouteRequest(
        goal="x",
        project_path=tmp_path,
        candidate_skill_manifest=manifest,
        env={"SKILLOS_FORGE_OFFLINE": "1"},
    ))
    assert decision.kind == RouteKind.FORGE_DISABLED


def test_router_loop_detector_trips(tmp_path):
    journal = ForgeJournal(tmp_path)
    for i in range(3):
        journal.append(_record(f"j{i}", goal="recurring signature"))
    decision = ProviderRouter().route(RouteRequest(
        goal="recurring signature",
        project_path=tmp_path,
    ))
    assert decision.tier == Tier.ESCALATE
    assert decision.kind == RouteKind.FORGE_LOOP


def test_router_budget_exceeded_refuses(tmp_path, monkeypatch):
    # Pre-fill a ledger at the cap so the next preflight trips.
    ledger = BudgetLedger.for_project(
        tmp_path, caps={"max_claude_tokens_per_day": 10}
    )
    ledger.charge(tokens=10, usd=0.0)
    # Force check_can_spend to reject even 0-token preflight by shrinking cap.
    monkeypatch.setattr(
        "forge.router.BudgetLedger.check_can_spend",
        lambda self, **kw: (_ for _ in ()).throw(
            BudgetExceeded("max_claude_tokens_per_day", 10, 11)
        ),
    )
    decision = ProviderRouter().route(RouteRequest(
        goal="new thing",
        project_path=tmp_path,
    ))
    assert decision.kind == RouteKind.BUDGET_EXCEEDED


def test_router_user_requested_forge_even_with_cartridge(tmp_path):
    decision = ProviderRouter().route(RouteRequest(
        goal="custom skill for my niche task",
        project_path=tmp_path,
        candidate_cartridge="cooking",
        user_requested_forge=True,
    ))
    assert decision.tier == Tier.FORGE
    assert decision.kind == RouteKind.GENERATE
