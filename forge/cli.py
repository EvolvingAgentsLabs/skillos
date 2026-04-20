"""Forge CLI — ``python -m forge <subcommand>``.

Subcommands
-----------

``log [--project PATH] [--tail N]``
    Print the forge journal.  Pretty-prints each entry in chronological
    order.

``budget [--project PATH]``
    Show the current budget ledger and today's usage.

``audit [--model TAG] [--strict]``
    Report gemma_compat status for every loaded cartridge.  Exit code is
    non-zero when any cartridge is ``missing``/``stale``/``model_mismatch``
    (or ``weak`` under ``--strict``).

``route GOAL [--project PATH] [--manifest PATH] [--cartridge NAME]``
    Print the route decision for a hypothetical goal.  Useful to sanity-check
    the policy without actually invoking an agent.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from forge.budget import BudgetLedger
from forge.journal import ForgeJournal
from forge.router import ProviderRouter, RouteRequest


def _default_project() -> Path:
    env = os.environ.get("SKILLOS_PROJECT")
    if env:
        return Path(env)
    return Path.cwd()


# --- log -------------------------------------------------------------

def cmd_log(args: argparse.Namespace) -> int:
    journal = ForgeJournal(args.project)
    records = journal.recent(args.tail) if args.tail else journal.read_all()
    if not records:
        print(f"(no forge journal entries under {args.project})")
        return 0
    for r in records:
        print(f"── {r.job_id}  [{r.trigger}]  {r.started_at}")
        print(f"   goal:        {r.goal}")
        print(f"   outcome:     {r.outcome}")
        if r.artifacts_produced:
            print(f"   artifacts:   {', '.join(r.artifacts_produced)}")
        if r.claude_tokens_used or r.claude_usd_used:
            print(f"   cost:        {r.claude_tokens_used} tokens / "
                  f"${r.claude_usd_used:.4f}")
        if r.wall_clock_s:
            print(f"   wall clock:  {r.wall_clock_s:.1f}s")
        if r.notes:
            print(f"   notes:       {r.notes}")
        print()
    return 0


# --- budget ----------------------------------------------------------

def cmd_budget(args: argparse.Namespace) -> int:
    ledger = BudgetLedger.for_project(args.project)
    snap = ledger.snapshot()
    if args.json:
        print(json.dumps(snap, indent=2))
        return 0
    print(f"Forge budget — {args.project}")
    print(f"  today_date:        {snap['usage']['today_date'] or '(not started)'}")
    print(f"  today_tokens:      {snap['usage']['today_tokens']:>10}  /  "
          f"{int(snap['caps']['max_claude_tokens_per_day']):>10}")
    print(f"  today_usd:         ${snap['usage']['today_usd']:>9.2f}  /  "
          f"${snap['caps']['max_claude_usd_per_day']:>9.2f}")
    print(f"  all_time_tokens:   {snap['usage']['all_time_tokens']:>10}")
    print(f"  all_time_usd:      ${snap['usage']['all_time_usd']:>9.2f}")
    print(f"  per-job cap:       {int(snap['caps']['max_claude_tokens_per_job']):>10} tokens")
    return 0


# --- audit -----------------------------------------------------------

def cmd_audit(args: argparse.Namespace) -> int:
    try:
        from cartridge_runtime import CartridgeRegistry
    except Exception as exc:
        print(f"error: could not import CartridgeRegistry: {exc}", file=sys.stderr)
        return 2
    registry = CartridgeRegistry(args.cartridges_root)
    status = registry.check_attestations(model=args.model, strict=args.strict)
    if not status:
        print(f"(no cartridges found under {args.cartridges_root})")
        return 0
    bad = {"missing", "stale", "model_mismatch"}
    if args.strict:
        bad = bad | {"weak"}
    width = max((len(n) for n in status), default=10)
    exit_code = 0
    for name in sorted(status):
        marker = " " if status[name] not in bad else "!"
        print(f" {marker} {name:<{width}}  {status[name]}")
        if status[name] in bad:
            exit_code = 1
    return exit_code


# --- route -----------------------------------------------------------

def cmd_route(args: argparse.Namespace) -> int:
    req = RouteRequest(
        goal=args.goal,
        project_path=args.project,
        target_model=args.model,
        fallback_model=args.fallback_model,
        candidate_cartridge=args.cartridge,
        candidate_skill_manifest=(Path(args.manifest) if args.manifest else None),
        user_requested_forge=args.force_forge,
        recent_pass_rate=args.pass_rate,
        recent_sample_size=args.samples,
    )
    decision = ProviderRouter().route(req)
    payload = {
        "tier": decision.tier.value,
        "kind": decision.kind.value,
        "target": decision.target,
        "model": decision.model,
        "rationale": decision.rationale,
        "actionable": decision.is_actionable,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"tier:       {payload['tier']}")
        print(f"kind:       {payload['kind']}")
        print(f"target:     {payload['target']}")
        print(f"model:      {payload['model']}")
        print(f"actionable: {payload['actionable']}")
        print(f"rationale:  {payload['rationale']}")
    return 0 if decision.is_actionable else 1


# --- entry point -----------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forge",
        description="SkillOS forge management (journal, budget, attestation, router).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_log = sub.add_parser("log", help="print the forge journal")
    p_log.add_argument("--project", type=Path, default=_default_project())
    p_log.add_argument("--tail", type=int, default=0,
                       help="show only the last N entries (0 = all)")
    p_log.set_defaults(func=cmd_log)

    p_budget = sub.add_parser("budget", help="show the budget ledger")
    p_budget.add_argument("--project", type=Path, default=_default_project())
    p_budget.add_argument("--json", action="store_true")
    p_budget.set_defaults(func=cmd_budget)

    p_audit = sub.add_parser("audit",
                             help="report gemma_compat status for every cartridge")
    p_audit.add_argument("--model",
                         default=os.environ.get("GEMMA_MODEL", "gemma4:e2b"))
    p_audit.add_argument("--cartridges-root", type=Path,
                         default=Path("cartridges"))
    p_audit.add_argument("--strict", action="store_true",
                         help="treat 'weak' as a warning")
    p_audit.set_defaults(func=cmd_audit)

    p_route = sub.add_parser("route",
                             help="compute the route decision for a goal")
    p_route.add_argument("goal")
    p_route.add_argument("--project", type=Path, default=_default_project())
    p_route.add_argument("--model",
                         default=os.environ.get("GEMMA_MODEL", "gemma4:e2b"))
    p_route.add_argument("--fallback-model",
                         default=os.environ.get("GEMMA_FALLBACK_MODEL",
                                                "gemma4:e4b"))
    p_route.add_argument("--cartridge")
    p_route.add_argument("--manifest")
    p_route.add_argument("--force-forge", action="store_true")
    p_route.add_argument("--pass-rate", type=float, default=None)
    p_route.add_argument("--samples", type=int, default=0)
    p_route.add_argument("--json", action="store_true")
    p_route.set_defaults(func=cmd_route)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
