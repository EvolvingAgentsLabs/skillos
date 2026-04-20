"""Append-only journal of forge jobs per project.

Backing file: ``projects/[P]/forge/journal.md`` — human-readable markdown with
YAML fenced blocks per entry so both humans and scripts can read it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None


VALID_TRIGGERS = {"gap", "evolve", "user_request", "model_upgrade", "scheduled"}
VALID_OUTCOMES = {"pass", "fail", "rolled_back", "blocked", "budget_exceeded"}


@dataclass
class ForgeJobRecord:
    job_id: str
    trigger: str
    goal: str
    started_at: str
    finished_at: str = ""
    outcome: str = "pass"
    artifacts_produced: list[str] = field(default_factory=list)
    claude_tokens_used: int = 0
    claude_usd_used: float = 0.0
    wall_clock_s: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "trigger": self.trigger,
            "goal": self.goal,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "outcome": self.outcome,
            "artifacts_produced": list(self.artifacts_produced),
            "claude_tokens_used": self.claude_tokens_used,
            "claude_usd_used": round(self.claude_usd_used, 4),
            "wall_clock_s": round(self.wall_clock_s, 3),
            "notes": self.notes,
        }


_ENTRY_RE = re.compile(r"```yaml\n(.*?)\n```", re.DOTALL)


class ForgeJournal:
    HEADER = (
        "# Forge Journal\n\n"
        "Append-only log of forge jobs for this project.  Each entry is a YAML\n"
        "fenced block.  Do not edit past entries — use `skillos forge rollback`\n"
        "to record a reversal as a new entry.\n\n"
    )

    def __init__(self, project_path: str | Path):
        self.project_path = Path(project_path)
        self.journal_file = self.project_path / "forge" / "journal.md"

    def append(self, record: ForgeJobRecord) -> None:
        if record.trigger not in VALID_TRIGGERS:
            raise ValueError(
                f"invalid trigger '{record.trigger}'; "
                f"expected one of {sorted(VALID_TRIGGERS)}"
            )
        if record.outcome not in VALID_OUTCOMES:
            raise ValueError(
                f"invalid outcome '{record.outcome}'; "
                f"expected one of {sorted(VALID_OUTCOMES)}"
            )
        if yaml is None:
            raise RuntimeError("PyYAML required to write forge journal")

        self.journal_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.journal_file.exists():
            self.journal_file.write_text(self.HEADER, encoding="utf-8")

        block = "```yaml\n"
        block += yaml.safe_dump(record.to_dict(), sort_keys=False).strip()
        block += "\n```\n\n"
        with self.journal_file.open("a", encoding="utf-8") as fh:
            fh.write(block)

    def read_all(self) -> list[ForgeJobRecord]:
        if not self.journal_file.exists() or yaml is None:
            return []
        text = self.journal_file.read_text(encoding="utf-8")
        out: list[ForgeJobRecord] = []
        for match in _ENTRY_RE.finditer(text):
            try:
                data = yaml.safe_load(match.group(1)) or {}
            except Exception:
                continue
            if not isinstance(data, dict) or "job_id" not in data:
                continue
            out.append(ForgeJobRecord(
                job_id=str(data.get("job_id", "")),
                trigger=str(data.get("trigger", "")),
                goal=str(data.get("goal", "")),
                started_at=str(data.get("started_at", "")),
                finished_at=str(data.get("finished_at", "")),
                outcome=str(data.get("outcome", "")),
                artifacts_produced=list(data.get("artifacts_produced") or []),
                claude_tokens_used=int(data.get("claude_tokens_used", 0) or 0),
                claude_usd_used=float(data.get("claude_usd_used", 0.0) or 0.0),
                wall_clock_s=float(data.get("wall_clock_s", 0.0) or 0.0),
                notes=str(data.get("notes", "")),
            ))
        return out

    def recent(self, n: int = 20) -> list[ForgeJobRecord]:
        records = self.read_all()
        return records[-n:]

    # --- loop detector ----------------------------------------------

    def count_recent_by_signature(self, signature: str,
                                  within_hours: float = 24.0) -> int:
        """Count forge jobs within the last ``within_hours`` whose ``goal``
        matches ``signature`` (case-insensitive substring).  Used by the
        router's forge-loop detector.
        """
        if not signature:
            return 0
        records = self.read_all()
        cutoff = datetime.now(timezone.utc).timestamp() - within_hours * 3600
        needle = signature.lower()
        hits = 0
        for r in records:
            try:
                started = datetime.fromisoformat(
                    r.started_at.replace("Z", "+00:00")
                ).timestamp()
            except Exception:
                continue
            if started < cutoff:
                continue
            if needle in r.goal.lower():
                hits += 1
        return hits
