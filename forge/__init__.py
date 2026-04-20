"""Forge — meta-layer runtime for SkillOS.

The ``forge/`` Python package implements the execution-side of the forge domain
declared under ``system/skills/forge/``.  The markdown specs describe *what*
each forge skill does; this package enforces *how* SkillOS routes between the
local Gemma hot path and the Claude Code forge path.

Public entry points
-------------------

``forge.router.ProviderRouter``
    Decides which tier (Hot / Warm / Forge) handles a given goal or a given
    skill invocation.  Reads the decision table from
    ``system/skills/orchestration/provider-router.md`` (best-effort; falls
    back to hard-coded defaults so the router is usable before the policy
    file is loaded).

``forge.budget.BudgetLedger``
    Per-project token and USD ledger backed by
    ``projects/[P]/forge/budget.yaml``.  Hard-stops forge invocations that
    would exceed configured caps.

``forge.attestation``
    Parses and validates ``gemma_compat`` frontmatter blocks.

``forge.journal``
    Append-only log writer + reader for ``projects/[P]/forge/journal.md``.
"""

from forge.router import ProviderRouter, RouteDecision, RouteKind, RouteRequest, Tier
from forge.budget import BudgetLedger, BudgetExceeded
from forge.attestation import (
    GemmaCompat,
    AttestationStrength,
    parse_gemma_compat,
    attestation_ok,
)
from forge.journal import ForgeJournal, ForgeJobRecord

__all__ = [
    "ProviderRouter",
    "RouteDecision",
    "RouteKind",
    "RouteRequest",
    "Tier",
    "BudgetLedger",
    "BudgetExceeded",
    "GemmaCompat",
    "AttestationStrength",
    "parse_gemma_compat",
    "attestation_ok",
    "ForgeJournal",
    "ForgeJobRecord",
]
