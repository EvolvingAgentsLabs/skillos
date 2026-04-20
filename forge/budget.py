"""Per-project forge budget ledger.

Backed by ``projects/[P]/forge/budget.yaml``.  Enforced at every forge entry
point — a hit returns ``BudgetExceeded`` immediately, before any cloud call is
made.  The ledger is deliberately simple (YAML, not SQLite) so a human can
inspect or edit it in an emergency.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


DEFAULT_CAPS = {
    "max_claude_tokens_per_job": 200_000,
    "max_claude_tokens_per_day": 2_000_000,
    "max_claude_usd_per_day": 10.00,
}


class BudgetExceeded(RuntimeError):
    """Raised when a forge call would exceed a configured cap.

    Kept separate from ValueError so callers can distinguish budget-trip from
    malformed-input errors.
    """

    def __init__(self, cap_name: str, limit: float, observed: float):
        self.cap_name = cap_name
        self.limit = limit
        self.observed = observed
        super().__init__(
            f"forge budget exceeded: {cap_name} = {observed} > {limit}"
        )


@dataclass
class BudgetUsage:
    today_date: str = ""
    today_tokens: int = 0
    today_usd: float = 0.0
    all_time_tokens: int = 0
    all_time_usd: float = 0.0


@dataclass
class BudgetLedger:
    """YAML-backed ledger.  Read-modify-write on every charge.

    The coarse locking strategy (read, mutate, write) is intentional.  Forge
    calls are minutes-apart events; contention is not a concern.  If it ever
    becomes one, swap the backing store without touching callers.
    """

    project_path: Path
    caps: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_CAPS))
    usage: BudgetUsage = field(default_factory=BudgetUsage)

    # --- construction ------------------------------------------------

    @classmethod
    def for_project(cls, project_path: str | Path,
                    *, caps: dict[str, float] | None = None) -> "BudgetLedger":
        p = Path(project_path)
        ledger_file = p / "forge" / "budget.yaml"
        if ledger_file.exists() and yaml is not None:
            data = yaml.safe_load(ledger_file.read_text(encoding="utf-8")) or {}
            resolved_caps = {**DEFAULT_CAPS, **(data.get("caps") or {}),
                             **(caps or {})}
            usage_data = data.get("usage") or {}
            usage = BudgetUsage(
                today_date=str(usage_data.get("today_date", "")),
                today_tokens=int(usage_data.get("today_tokens", 0)),
                today_usd=float(usage_data.get("today_usd", 0.0)),
                all_time_tokens=int(usage_data.get("all_time_tokens", 0)),
                all_time_usd=float(usage_data.get("all_time_usd", 0.0)),
            )
        else:
            resolved_caps = {**DEFAULT_CAPS, **(caps or {})}
            usage = BudgetUsage()
        return cls(project_path=p, caps=resolved_caps, usage=usage)

    # --- daily rollover ----------------------------------------------

    def _roll_if_new_day(self) -> None:
        today = date.today().isoformat()
        if self.usage.today_date != today:
            self.usage.today_date = today
            self.usage.today_tokens = 0
            self.usage.today_usd = 0.0

    # --- enforcement -------------------------------------------------

    def check_can_spend(self, *, tokens: int = 0, usd: float = 0.0,
                        is_job_start: bool = False) -> None:
        """Raise ``BudgetExceeded`` if a projected spend would trip any cap.

        Call this BEFORE invoking Claude Code.  ``is_job_start`` additionally
        enforces the per-job cap against ``tokens`` alone.
        """
        self._roll_if_new_day()
        if is_job_start:
            limit = float(self.caps["max_claude_tokens_per_job"])
            if tokens > limit:
                raise BudgetExceeded("max_claude_tokens_per_job", limit, tokens)

        token_total = self.usage.today_tokens + max(0, tokens)
        usd_total = self.usage.today_usd + max(0.0, usd)

        if token_total > self.caps["max_claude_tokens_per_day"]:
            raise BudgetExceeded(
                "max_claude_tokens_per_day",
                self.caps["max_claude_tokens_per_day"],
                token_total,
            )
        if usd_total > self.caps["max_claude_usd_per_day"]:
            raise BudgetExceeded(
                "max_claude_usd_per_day",
                self.caps["max_claude_usd_per_day"],
                usd_total,
            )

    # --- charging ----------------------------------------------------

    def charge(self, *, tokens: int, usd: float) -> None:
        """Record a completed spend.  Callers should have already called
        ``check_can_spend`` with the projected values, but ``charge`` is
        tolerant of an overrun (e.g. a cloud call that used more than
        estimated) — it records the true number and subsequent checks will
        refuse further work until the next daily rollover.
        """
        self._roll_if_new_day()
        self.usage.today_tokens += max(0, tokens)
        self.usage.today_usd += max(0.0, usd)
        self.usage.all_time_tokens += max(0, tokens)
        self.usage.all_time_usd += max(0.0, usd)
        self.save()

    # --- persistence -------------------------------------------------

    def save(self) -> None:
        if yaml is None:
            return
        target = self.project_path / "forge" / "budget.yaml"
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "project": self.project_path.name,
            "caps": dict(self.caps),
            "usage": {
                "today_date": self.usage.today_date,
                "today_tokens": self.usage.today_tokens,
                "today_usd": round(self.usage.today_usd, 4),
                "all_time_tokens": self.usage.all_time_tokens,
                "all_time_usd": round(self.usage.all_time_usd, 4),
            },
        }
        tmp = target.with_suffix(".yaml.tmp")
        tmp.write_text(yaml.safe_dump(payload, sort_keys=False),
                       encoding="utf-8")
        os.replace(tmp, target)

    def snapshot(self) -> dict[str, Any]:
        self._roll_if_new_day()
        return {
            "caps": dict(self.caps),
            "usage": {
                "today_date": self.usage.today_date,
                "today_tokens": self.usage.today_tokens,
                "today_usd": round(self.usage.today_usd, 4),
                "all_time_tokens": self.usage.all_time_tokens,
                "all_time_usd": round(self.usage.all_time_usd, 4),
            },
        }
