"""Gemma-compat attestation parsing and validation.

Attestations are written by ``forge/validate/forge-validate-agent`` into the
frontmatter of a skill's ``.manifest.md``.  No skill may enter the hot path
without one.  This module exposes a single source of truth for parsing,
validating freshness, and judging strength.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


class AttestationStrength(str, Enum):
    STRONG = "strong"
    WEAK = "weak"
    NONE = "none"


PASS_RATE_STRONG = 0.95
PASS_RATE_WEAK = 0.80
# Default freshness: attestations older than this are treated as stale and
# must be re-validated (cheap — no regen, just tests).
DEFAULT_FRESHNESS = timedelta(days=30)


@dataclass
class GemmaCompat:
    model: str
    validated_at: datetime
    pass_rate: float
    cases_total: int
    cases_passed: int
    max_tokens_observed: int
    median_latency_ms: int
    validator_version: str = "1.0.0"
    attestation_strength: AttestationStrength = AttestationStrength.NONE
    raw: dict[str, Any] | None = None

    @property
    def is_strong(self) -> bool:
        return self.attestation_strength == AttestationStrength.STRONG

    def is_stale(self, now: datetime | None = None,
                 max_age: timedelta = DEFAULT_FRESHNESS) -> bool:
        now = now or datetime.now(timezone.utc)
        return (now - self.validated_at) > max_age

    def matches_model(self, model: str) -> bool:
        """Exact tag match.  ``gemma4:e2b`` does not satisfy ``gemma4:e4b``."""
        return self.model.strip() == model.strip()


_FRONTMATTER_RE = re.compile(r"^---\n(.*?\n)---", re.DOTALL)


def _parse_frontmatter(text: str) -> dict[str, Any]:
    m = _FRONTMATTER_RE.match(text)
    if not m or yaml is None:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def _coerce_datetime(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str):
        # Tolerate both ``...Z`` and ``+00:00`` suffixes.
        s = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    raise ValueError(f"validated_at must be str|datetime, got {type(raw).__name__}")


def _strength_from_rate(rate: float) -> AttestationStrength:
    if rate >= PASS_RATE_STRONG:
        return AttestationStrength.STRONG
    if rate >= PASS_RATE_WEAK:
        return AttestationStrength.WEAK
    return AttestationStrength.NONE


def parse_gemma_compat(source: str | Path | dict[str, Any]) -> GemmaCompat | None:
    """Parse a ``gemma_compat`` block.

    ``source`` may be:
      * a ``Path`` to a ``.manifest.md`` file,
      * the raw manifest text,
      * an already-parsed frontmatter dict.
    Returns ``None`` when no attestation is present or required fields are
    missing — callers treat that as "not attested".
    """
    if isinstance(source, Path):
        data = _parse_frontmatter(source.read_text(encoding="utf-8"))
    elif isinstance(source, str):
        data = _parse_frontmatter(source)
    elif isinstance(source, dict):
        data = source
    else:
        raise TypeError(f"unsupported source type: {type(source).__name__}")

    raw = data.get("gemma_compat") or data
    if not isinstance(raw, dict):
        return None

    required = ("model", "validated_at", "pass_rate",
                "cases_total", "cases_passed")
    if not all(k in raw for k in required):
        return None

    try:
        pass_rate = float(raw["pass_rate"])
    except (TypeError, ValueError):
        return None

    declared = raw.get("attestation_strength")
    if declared in {"strong", "weak", "none"}:
        strength = AttestationStrength(declared)
    else:
        strength = _strength_from_rate(pass_rate)

    try:
        return GemmaCompat(
            model=str(raw["model"]),
            validated_at=_coerce_datetime(raw["validated_at"]),
            pass_rate=pass_rate,
            cases_total=int(raw["cases_total"]),
            cases_passed=int(raw["cases_passed"]),
            max_tokens_observed=int(raw.get("max_tokens_observed", 0)),
            median_latency_ms=int(raw.get("median_latency_ms", 0)),
            validator_version=str(raw.get("validator_version", "1.0.0")),
            attestation_strength=strength,
            raw=dict(raw),
        )
    except (ValueError, TypeError):
        return None


def attestation_ok(compat: GemmaCompat | None, *,
                   model: str,
                   now: datetime | None = None,
                   max_age: timedelta = DEFAULT_FRESHNESS) -> bool:
    """Return True iff the attestation is present, fresh, matches the target
    model tag, and meets at least the WEAK pass-rate threshold.

    ``max_age`` is a timedelta; override when a project pins skills to older
    snapshots (e.g. reproducibility mode).
    """
    if compat is None:
        return False
    if compat.attestation_strength == AttestationStrength.NONE:
        return False
    if not compat.matches_model(model):
        return False
    if compat.is_stale(now=now, max_age=max_age):
        return False
    return True
