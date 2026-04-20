"""Two-tier provider router.

Mirrors the decision table in
``system/skills/orchestration/provider-router.md``.  The markdown file is the
human-readable contract; this module is the enforced implementation.  When the
two disagree, the markdown wins — update this file to match.

Design notes
------------

* **Policy lives in code, not in prompts.**  Tier selection is deterministic
  so we can unit-test it and reason about incidents.  The markdown policy is a
  spec the agents read to keep their delegation in line.
* **Gemma never sees forge-only artifacts.**  A skill without a valid
  ``gemma_compat`` block is treated as forge-only until validated.
* **Fail closed.**  If we cannot reach Ollama or load skill metadata, the
  router refuses with ``NO_ROUTE`` rather than silently falling through to
  Claude.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable

from forge.attestation import (
    GemmaCompat,
    attestation_ok,
    parse_gemma_compat,
)
from forge.budget import BudgetLedger, BudgetExceeded
from forge.journal import ForgeJournal


class Tier(str, Enum):
    HOT = "hot"          # Gemma local, default tag
    WARM = "warm"        # Gemma local, larger tag (e.g. E4B)
    FORGE = "forge"      # Claude Code, meta-work only
    ESCALATE = "escalate"  # Surface to user — no route


class RouteKind(str, Enum):
    CARTRIDGE = "cartridge"
    SKILL = "skill"
    GENERATE = "generate"
    EVOLVE = "evolve"
    VALIDATE = "validate"
    NO_ROUTE = "no_route"
    FORGE_DISABLED = "forge_disabled"
    FORGE_LOOP = "forge_loop"
    BUDGET_EXCEEDED = "budget_exceeded"


# --- thresholds ------------------------------------------------------

DEGRADATION_PASS_RATE = 0.80          # below this -> evolve
DEGRADATION_MIN_SAMPLES = 10          # need at least N recent invocations
FORGE_LOOP_THRESHOLD = 3              # same signature -> halt
FORGE_LOOP_WINDOW_H = 24.0


# --- input / output types --------------------------------------------

@dataclass
class RouteRequest:
    """Everything the router needs to decide.

    The caller assembles this from its own context (``system-agent`` does so
    from SkillIndex, memory, and project state).  Keeping it a dumb dataclass
    means tests can construct realistic scenarios without spinning up the
    whole runtime.
    """

    goal: str
    project_path: Path | None = None
    target_model: str = "gemma4:e2b"
    fallback_model: str = "gemma4:e4b"

    # Optional: skill/cartridge candidates already located by the caller.
    candidate_cartridge: str | None = None
    candidate_skill_manifest: Path | None = None

    # Historical signal from memory-analysis-agent (may be empty).
    recent_pass_rate: float | None = None
    recent_sample_size: int = 0

    # User-supplied requests.
    user_requested_forge: bool = False
    user_requested_skill_id: str | None = None

    # Environment snapshots (injected for testability).
    env: dict[str, str] = field(default_factory=lambda: dict(os.environ))


@dataclass
class RouteDecision:
    tier: Tier
    kind: RouteKind
    target: str                    # cartridge name / skill path / "generate"
    model: str | None = None       # which Ollama tag, when applicable
    rationale: str = ""
    attestation: GemmaCompat | None = None

    @property
    def is_actionable(self) -> bool:
        return self.kind not in {
            RouteKind.NO_ROUTE,
            RouteKind.FORGE_DISABLED,
            RouteKind.FORGE_LOOP,
            RouteKind.BUDGET_EXCEEDED,
        }


# --- router ----------------------------------------------------------

class ProviderRouter:
    """Decides the tier for each incoming goal or skill invocation.

    The router is stateless except for an optional ``BudgetLedger`` and a
    ``ForgeJournal`` reader — both scoped to the active project.  That means
    the same instance can route across different projects as long as each
    ``RouteRequest.project_path`` is supplied.
    """

    def __init__(self, *,
                 degradation_pass_rate: float = DEGRADATION_PASS_RATE,
                 degradation_min_samples: int = DEGRADATION_MIN_SAMPLES,
                 forge_loop_threshold: int = FORGE_LOOP_THRESHOLD,
                 forge_loop_window_h: float = FORGE_LOOP_WINDOW_H):
        self.degradation_pass_rate = degradation_pass_rate
        self.degradation_min_samples = degradation_min_samples
        self.forge_loop_threshold = forge_loop_threshold
        self.forge_loop_window_h = forge_loop_window_h

    # --- entry point -------------------------------------------------

    def route(self, req: RouteRequest) -> RouteDecision:
        # 1. Hard offline gate first — nothing reaches Claude in this mode.
        offline = _truthy(req.env.get("SKILLOS_FORGE_OFFLINE"))

        # 2. Explicit user request for forge wins over matching skills.
        if req.user_requested_forge:
            return self._route_user_forge(req, offline)

        # 3. Existing cartridge is the fastest path — Gemma-native.
        if req.candidate_cartridge:
            return RouteDecision(
                tier=Tier.HOT,
                kind=RouteKind.CARTRIDGE,
                target=req.candidate_cartridge,
                model=req.target_model,
                rationale="cartridge match — hot tier",
            )

        # 4. Existing skill: gate on attestation.
        if req.candidate_skill_manifest is not None:
            return self._route_existing_skill(req, offline)

        # 5. No candidate skill/cartridge: generate one (forge tier).
        return self._route_generate(req, offline)

    # --- sub-routes --------------------------------------------------

    def _route_user_forge(self, req: RouteRequest, offline: bool) -> RouteDecision:
        if offline:
            return RouteDecision(
                tier=Tier.ESCALATE,
                kind=RouteKind.FORGE_DISABLED,
                target="generate",
                rationale="SKILLOS_FORGE_OFFLINE set; user-requested forge refused",
            )
        guard = self._check_forge_preconditions(req, signature=req.goal)
        if guard is not None:
            return guard
        return RouteDecision(
            tier=Tier.FORGE,
            kind=RouteKind.GENERATE,
            target="forge/generate/forge-generate-agent",
            rationale="user explicitly requested forge",
        )

    def _route_existing_skill(self, req: RouteRequest,
                              offline: bool) -> RouteDecision:
        manifest_path = req.candidate_skill_manifest
        assert manifest_path is not None
        compat = parse_gemma_compat(manifest_path) if manifest_path.exists() \
            else None

        # No attestation at all — must validate before hot-path use.
        if compat is None:
            if offline:
                return RouteDecision(
                    tier=Tier.ESCALATE,
                    kind=RouteKind.FORGE_DISABLED,
                    target=str(manifest_path),
                    rationale="skill lacks attestation; forge disabled",
                    attestation=None,
                )
            guard = self._check_forge_preconditions(
                req, signature=f"validate:{manifest_path}"
            )
            if guard is not None:
                return guard
            return RouteDecision(
                tier=Tier.FORGE,
                kind=RouteKind.VALIDATE,
                target="forge/validate/forge-validate-agent",
                rationale="no gemma_compat attestation present",
            )

        # Attestation exists but is stale or model mismatch — re-validate.
        if not attestation_ok(compat, model=req.target_model):
            if offline:
                return RouteDecision(
                    tier=Tier.ESCALATE,
                    kind=RouteKind.FORGE_DISABLED,
                    target=str(manifest_path),
                    rationale="stale attestation; forge disabled",
                    attestation=compat,
                )
            guard = self._check_forge_preconditions(
                req, signature=f"validate:{manifest_path}"
            )
            if guard is not None:
                return guard
            return RouteDecision(
                tier=Tier.FORGE,
                kind=RouteKind.VALIDATE,
                target="forge/validate/forge-validate-agent",
                rationale="attestation stale or target_model changed",
                attestation=compat,
            )

        # Degradation check — kick to evolve if pass-rate has slipped.
        if self._is_degraded(req):
            if offline:
                return RouteDecision(
                    tier=Tier.HOT if compat.is_strong else Tier.WARM,
                    kind=RouteKind.SKILL,
                    target=str(manifest_path),
                    model=req.target_model if compat.is_strong
                          else req.fallback_model,
                    rationale="degraded; forge offline so running as-is",
                    attestation=compat,
                )
            guard = self._check_forge_preconditions(
                req, signature=f"evolve:{manifest_path}"
            )
            if guard is not None:
                return guard
            return RouteDecision(
                tier=Tier.FORGE,
                kind=RouteKind.EVOLVE,
                target="forge/evolve/forge-evolve-agent",
                rationale="SmartMemory pass-rate below threshold",
                attestation=compat,
            )

        # Happy path: strong -> HOT, weak -> WARM.
        if compat.is_strong:
            return RouteDecision(
                tier=Tier.HOT,
                kind=RouteKind.SKILL,
                target=str(manifest_path),
                model=req.target_model,
                rationale="strong attestation",
                attestation=compat,
            )
        return RouteDecision(
            tier=Tier.WARM,
            kind=RouteKind.SKILL,
            target=str(manifest_path),
            model=req.fallback_model,
            rationale="weak attestation — warm tier",
            attestation=compat,
        )

    def _route_generate(self, req: RouteRequest, offline: bool) -> RouteDecision:
        if offline:
            return RouteDecision(
                tier=Tier.ESCALATE,
                kind=RouteKind.FORGE_DISABLED,
                target="generate",
                rationale="no skill matches; forge disabled",
            )
        guard = self._check_forge_preconditions(req, signature=req.goal)
        if guard is not None:
            return guard
        return RouteDecision(
            tier=Tier.FORGE,
            kind=RouteKind.GENERATE,
            target="forge/generate/forge-generate-agent",
            rationale="no cartridge/skill matches goal",
        )

    # --- guards ------------------------------------------------------

    def _is_degraded(self, req: RouteRequest) -> bool:
        if req.recent_pass_rate is None:
            return False
        if req.recent_sample_size < self.degradation_min_samples:
            return False
        return req.recent_pass_rate < self.degradation_pass_rate

    def _check_forge_preconditions(self, req: RouteRequest,
                                   *, signature: str) -> RouteDecision | None:
        """Run the budget and loop-detector checks shared by every forge
        route.  Returns a ``RouteDecision`` if a precondition refuses the
        call, ``None`` if the call may proceed.
        """
        if req.project_path is None:
            return None  # tests often omit; production callers always supply

        # Forge-loop detector.
        try:
            journal = ForgeJournal(req.project_path)
            hits = journal.count_recent_by_signature(
                signature, within_hours=self.forge_loop_window_h,
            )
        except Exception:
            hits = 0
        if hits >= self.forge_loop_threshold:
            return RouteDecision(
                tier=Tier.ESCALATE,
                kind=RouteKind.FORGE_LOOP,
                target=signature,
                rationale=f"{hits} forge jobs matched signature within "
                          f"{self.forge_loop_window_h}h "
                          f"(threshold {self.forge_loop_threshold})",
            )

        # Budget preflight — cap-only check, actual spend recorded after.
        try:
            ledger = BudgetLedger.for_project(req.project_path)
            ledger.check_can_spend(tokens=0, usd=0.0)
        except BudgetExceeded as exc:
            return RouteDecision(
                tier=Tier.ESCALATE,
                kind=RouteKind.BUDGET_EXCEEDED,
                target=exc.cap_name,
                rationale=str(exc),
            )
        except Exception:
            # Missing ledger file is not a reason to refuse — the forge
            # tier will create one on first charge.
            pass

        return None


# --- helpers ---------------------------------------------------------

def _truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def route_goal(goal: str, *,
               project_path: str | Path | None = None,
               candidate_cartridge: str | None = None,
               candidate_skill_manifest: str | Path | None = None,
               recent_pass_rate: float | None = None,
               recent_sample_size: int = 0,
               user_requested_forge: bool = False,
               target_model: str | None = None,
               fallback_model: str | None = None) -> RouteDecision:
    """Convenience one-shot wrapper for callers that don't want to hold a
    ``ProviderRouter`` instance."""
    req = RouteRequest(
        goal=goal,
        project_path=Path(project_path) if project_path else None,
        candidate_cartridge=candidate_cartridge,
        candidate_skill_manifest=(
            Path(candidate_skill_manifest) if candidate_skill_manifest else None
        ),
        recent_pass_rate=recent_pass_rate,
        recent_sample_size=recent_sample_size,
        user_requested_forge=user_requested_forge,
        target_model=target_model or os.environ.get("GEMMA_MODEL", "gemma4:e2b"),
        fallback_model=fallback_model
            or os.environ.get("GEMMA_FALLBACK_MODEL", "gemma4:e4b"),
    )
    return ProviderRouter().route(req)
