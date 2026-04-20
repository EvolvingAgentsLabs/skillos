"""Run a forge job end-to-end.

Composition root for the forge tier.  The executor is deliberately small —
each responsibility (bridge, templates, artifact writing, budget, journal)
lives in its own module.  This file just orchestrates:

1. preflight (budget, loop detector already handled by the router; the
   executor re-checks in case the caller skipped the router)
2. render the right prompt template
3. invoke the Claude bridge
4. parse and materialize the artifact bundle
5. charge the budget
6. append a journal entry
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from forge.artifacts import ArtifactError, materialize
from forge.budget import BudgetExceeded, BudgetLedger
from forge.claude_bridge import (
    ClaudeBridge,
    ForgeRequest,
    ForgeResponse,
    PromptTemplate,
    get_claude_bridge,
)
from forge.journal import ForgeJobRecord, ForgeJournal
from forge.router import RouteKind


DEFAULT_ESTIMATED_USD_PER_1K = 0.003  # input/output blended; rough.


@dataclass
class ForgeJobSpec:
    """Input to :class:`ForgeExecutor.run`.

    Matches the YAML shape written by system-agent into
    ``projects/[P]/forge/jobs/<job_id>.yaml``, so a spec loaded from disk
    and a spec built in-memory use the same dataclass.
    """

    goal: str
    project_path: Path
    kind: RouteKind                       # GENERATE | EVOLVE | VALIDATE
    trigger: str = "gap"                  # gap | evolve | user_request | ...
    target_model: str = "gemma4:e2b"
    max_skill_tokens: int = 2500
    allow_js: bool = True
    allow_new_tools: bool = False
    tool_allow_list: list[str] = field(default_factory=lambda: [
        "Read", "Write", "Grep", "Glob",
    ])

    # Evolve-only fields.
    target_skill_id: str = ""
    signal: str = ""
    evidence: str = ""
    current_skill: str = ""

    # Metadata carried through to the journal.
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


@dataclass
class ForgeJobResult:
    job_id: str
    outcome: str                          # pass | fail | rolled_back | blocked | budget_exceeded
    candidates_path: Path | None = None
    artifacts: list[Path] = field(default_factory=list)
    tokens: int = 0
    usd: float = 0.0
    wall_clock_s: float = 0.0
    notes: str = ""
    response_text: str = ""


class ForgeExecutor:
    """Orchestrates a single forge job.

    Create one instance per process (or per project) — bridges may cache
    expensive state (HTTP clients).  Injecting the bridge keeps the
    executor testable without env-dependent factory runs.
    """

    def __init__(self, *, bridge: ClaudeBridge | None = None,
                 template_root: Path | str | None = None):
        self.bridge = bridge or get_claude_bridge()
        self.template_root = Path(template_root) if template_root else None

    # --- entry point ------------------------------------------------

    def run(self, spec: ForgeJobSpec) -> ForgeJobResult:
        started_at = datetime.now(timezone.utc).isoformat()
        t0 = time.monotonic()
        ledger = BudgetLedger.for_project(spec.project_path)
        journal = ForgeJournal(spec.project_path)

        # Preflight budget (per-job cap).
        try:
            ledger.check_can_spend(
                tokens=spec.max_skill_tokens,
                is_job_start=True,
            )
        except BudgetExceeded as exc:
            return self._record_and_return(
                spec, journal, started_at, t0,
                outcome="budget_exceeded",
                notes=str(exc),
            )

        # Render the prompt.
        try:
            prompt = self._render_prompt(spec)
        except FileNotFoundError as exc:
            return self._record_and_return(
                spec, journal, started_at, t0,
                outcome="blocked",
                notes=f"prompt template missing: {exc}",
            )

        # Call Claude.
        try:
            response = self.bridge.invoke(ForgeRequest(
                prompt=prompt,
                system=_system_prompt(spec),
                max_tokens=8192,
                temperature=0.2,
            ))
        except Exception as exc:
            return self._record_and_return(
                spec, journal, started_at, t0,
                outcome="fail",
                notes=f"bridge error: {exc}",
            )

        # Charge budget immediately on success — even if artifact parsing
        # fails, the cloud call was real.
        usd = _estimate_usd(response)
        ledger.charge(tokens=response.total_tokens, usd=usd)

        # Materialize artifacts.
        candidates_dir = spec.project_path / "forge" / "candidates" / spec.job_id
        try:
            written = materialize(
                response.text,
                destination=candidates_dir,
                kind=None,  # spec may not know the kind; prompt may choose
            )
        except ArtifactError as exc:
            # Keep the raw response for forensics even on parse failure.
            _dump_raw(candidates_dir, response.text, exc)
            return self._record_and_return(
                spec, journal, started_at, t0,
                outcome="fail",
                candidates_path=candidates_dir,
                tokens=response.total_tokens,
                usd=usd,
                notes=f"artifact parse error: {exc}",
                response_text=response.text,
            )

        return self._record_and_return(
            spec, journal, started_at, t0,
            outcome="pass",
            candidates_path=candidates_dir,
            artifacts=written,
            tokens=response.total_tokens,
            usd=usd,
            response_text=response.text,
        )

    # --- helpers ----------------------------------------------------

    def _render_prompt(self, spec: ForgeJobSpec) -> str:
        if spec.kind is RouteKind.GENERATE:
            tmpl = PromptTemplate.load(
                "generate", "generate_skill", root=self.template_root,
            )
            return tmpl.render(
                job_id=spec.job_id,
                goal=spec.goal,
                project_path=str(spec.project_path),
                target_model=spec.target_model,
                max_skill_tokens=spec.max_skill_tokens,
                allow_js=str(spec.allow_js).lower(),
                allow_new_tools=str(spec.allow_new_tools).lower(),
                tool_allow_list=", ".join(spec.tool_allow_list),
            )
        if spec.kind is RouteKind.EVOLVE:
            tmpl = PromptTemplate.load(
                "evolve", "evolve_skill", root=self.template_root,
            )
            return tmpl.render(
                job_id=spec.job_id,
                target_skill_id=spec.target_skill_id,
                signal=spec.signal or "degradation",
                target_model=spec.target_model,
                project_path=str(spec.project_path),
                evidence=spec.evidence or "(none supplied)",
                current_skill=spec.current_skill or "(not embedded)",
            )
        raise ValueError(
            f"unsupported forge kind for executor: {spec.kind.value}"
        )

    def _record_and_return(self,
                           spec: ForgeJobSpec,
                           journal: ForgeJournal,
                           started_at: str,
                           t0: float,
                           *,
                           outcome: str,
                           candidates_path: Path | None = None,
                           artifacts: list[Path] | None = None,
                           tokens: int = 0,
                           usd: float = 0.0,
                           notes: str = "",
                           response_text: str = "") -> ForgeJobResult:
        wall = time.monotonic() - t0
        record = ForgeJobRecord(
            job_id=spec.job_id,
            trigger=spec.trigger,
            goal=spec.goal,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc).isoformat(),
            outcome=outcome,
            artifacts_produced=[str(p) for p in (artifacts or [])],
            claude_tokens_used=tokens,
            claude_usd_used=usd,
            wall_clock_s=wall,
            notes=notes,
        )
        try:
            journal.append(record)
        except Exception as exc:
            # Never let journal failure mask the job outcome.
            notes = (notes + f" [journal write failed: {exc}]").strip()

        return ForgeJobResult(
            job_id=spec.job_id,
            outcome=outcome,
            candidates_path=candidates_path,
            artifacts=artifacts or [],
            tokens=tokens,
            usd=usd,
            wall_clock_s=wall,
            notes=notes,
            response_text=response_text,
        )


# --- utilities -------------------------------------------------------

def _system_prompt(spec: ForgeJobSpec) -> str:
    return (
        "You are the SkillOS Forge.  You never execute user goals.  You "
        "produce artifact bundles that a smaller local model "
        f"({spec.target_model}) will run.  Emit only the fenced file "
        "blocks described in the user message.  No prose outside those."
    )


def _estimate_usd(response: ForgeResponse) -> float:
    # Intentionally rough — real-world pricing varies by model, caching,
    # discounting.  Exact accounting happens outside SkillOS.
    return round(
        (response.total_tokens / 1000.0) * DEFAULT_ESTIMATED_USD_PER_1K, 4
    )


def _dump_raw(candidates_dir: Path, text: str, exc: Exception) -> None:
    try:
        candidates_dir.mkdir(parents=True, exist_ok=True)
        (candidates_dir / "raw_response.txt").write_text(text, encoding="utf-8")
        (candidates_dir / "parse_error.txt").write_text(
            str(exc), encoding="utf-8",
        )
    except Exception:
        pass  # best effort
