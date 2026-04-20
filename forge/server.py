"""HTTP API for the forge runtime.

Pure-stdlib ``http.server`` — deliberately no FastAPI/Flask dependency so
the desktop shell can ship without Python web frameworks.  This also keeps
the API surface explicit: every endpoint is one handler method.

Endpoints (all JSON in/out):

    GET  /health                              → {"status":"ok"}
    GET  /api/route?goal=...                  → route decision
    POST /api/route       {goal, project, ...} → route decision
    GET  /api/budget?project=...              → budget snapshot
    GET  /api/journal?project=...&tail=N       → recent journal entries
    GET  /api/audit?model=...                  → per-cartridge attestation status
    POST /api/forge/run   {goal, project,      → execute a forge job
                           kind: "generate"}      (generate or evolve)

All write endpoints refuse when ``SKILLOS_FORGE_OFFLINE=1`` unless the
route decision itself is non-forge.

Start with::

    python -m forge serve --host 127.0.0.1 --port 8765

Security: bind to loopback by default.  Bearer-token auth can be enabled
via ``FORGE_API_TOKEN``.  Do not expose on a public interface without it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from dataclasses import asdict, is_dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from forge.budget import BudgetLedger
from forge.journal import ForgeJournal
from forge.router import (
    ProviderRouter,
    RouteKind,
    RouteRequest,
    Tier,
)


# --- helpers ---------------------------------------------------------

def _json_default(obj: Any) -> Any:
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, Path):
        return str(obj)
    if hasattr(obj, "value"):        # Enum
        return obj.value
    raise TypeError(f"not JSON-serializable: {type(obj).__name__}")


def _dump(obj: Any) -> bytes:
    return json.dumps(obj, default=_json_default).encode("utf-8")


def _auth_required() -> str | None:
    return os.environ.get("FORGE_API_TOKEN") or None


# --- request handler ------------------------------------------------

class ForgeAPIHandler(BaseHTTPRequestHandler):
    server_version = "SkillOSForge/1.0"

    # Silence default noisy access logs — the desktop shell has its own.
    def log_message(self, fmt: str, *args: Any) -> None:
        return

    # --- dispatch ---------------------------------------------------

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        url = urlparse(self.path)
        try:
            if not self._check_auth():
                return
            if url.path == "/health":
                return self._respond(200, {"status": "ok"})
            if url.path == "/api/route":
                return self._route_get(url)
            if url.path == "/api/budget":
                return self._budget_get(url)
            if url.path == "/api/journal":
                return self._journal_get(url)
            if url.path == "/api/audit":
                return self._audit_get(url)
            return self._respond(404, {"error": "not found", "path": url.path})
        except Exception as exc:
            self._respond(500, {"error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        try:
            if not self._check_auth():
                return
            body = self._read_body()
            if url.path == "/api/route":
                return self._route_post(body)
            if url.path == "/api/forge/run":
                return self._forge_run_post(body)
            return self._respond(404, {"error": "not found", "path": url.path})
        except Exception as exc:
            self._respond(500, {"error": str(exc)})

    # --- auth -------------------------------------------------------

    def _check_auth(self) -> bool:
        required = _auth_required()
        if required is None:
            return True
        header = self.headers.get("Authorization", "")
        if header == f"Bearer {required}":
            return True
        self._respond(401, {"error": "unauthorized"})
        return False

    # --- body parsing ----------------------------------------------

    def _read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON body: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object")
        return data

    # --- routes ----------------------------------------------------

    def _route_get(self, url) -> None:
        q = parse_qs(url.query)
        self._route_common({
            "goal": (q.get("goal") or [""])[0],
            "project": (q.get("project") or [None])[0],
            "cartridge": (q.get("cartridge") or [None])[0],
            "manifest": (q.get("manifest") or [None])[0],
            "force_forge": _qbool(q.get("force_forge")),
        })

    def _route_post(self, body: dict[str, Any]) -> None:
        self._route_common(body)

    def _route_common(self, body: dict[str, Any]) -> None:
        goal = str(body.get("goal", "")).strip()
        if not goal:
            return self._respond(400, {"error": "goal required"})
        project = body.get("project")
        manifest = body.get("manifest")
        req = RouteRequest(
            goal=goal,
            project_path=Path(project) if project else None,
            candidate_cartridge=body.get("cartridge") or None,
            candidate_skill_manifest=Path(manifest) if manifest else None,
            recent_pass_rate=_as_float(body.get("recent_pass_rate")),
            recent_sample_size=int(body.get("recent_sample_size", 0) or 0),
            user_requested_forge=bool(body.get("force_forge", False)),
            target_model=str(body.get("target_model")
                              or os.environ.get("GEMMA_MODEL", "gemma4:e2b")),
            fallback_model=str(body.get("fallback_model")
                                or os.environ.get("GEMMA_FALLBACK_MODEL",
                                                  "gemma4:e4b")),
        )
        decision = ProviderRouter().route(req)
        self._respond(200, {
            "tier": decision.tier.value,
            "kind": decision.kind.value,
            "target": decision.target,
            "model": decision.model,
            "rationale": decision.rationale,
            "actionable": decision.is_actionable,
        })

    # --- budget ----------------------------------------------------

    def _budget_get(self, url) -> None:
        project = _project_from_query(url)
        ledger = BudgetLedger.for_project(project)
        self._respond(200, ledger.snapshot())

    # --- journal ---------------------------------------------------

    def _journal_get(self, url) -> None:
        q = parse_qs(url.query)
        project = _project_from_query(url)
        tail = int((q.get("tail") or [0])[0])
        journal = ForgeJournal(project)
        records = journal.recent(tail) if tail else journal.read_all()
        self._respond(200, {
            "project": str(project),
            "count": len(records),
            "records": [r.to_dict() for r in records],
        })

    # --- audit -----------------------------------------------------

    def _audit_get(self, url) -> None:
        q = parse_qs(url.query)
        model = (q.get("model") or [os.environ.get("GEMMA_MODEL", "gemma4:e2b")])[0]
        strict = _qbool(q.get("strict"))
        root = Path((q.get("cartridges_root") or ["cartridges"])[0])
        try:
            from cartridge_runtime import CartridgeRegistry
        except Exception as exc:
            return self._respond(500, {
                "error": f"cartridge_runtime import failed: {exc}",
            })
        registry = CartridgeRegistry(root)
        status = registry.check_attestations(model=model, strict=strict)
        self._respond(200, {"model": model, "status": status})

    # --- forge run --------------------------------------------------

    def _forge_run_post(self, body: dict[str, Any]) -> None:
        if os.environ.get("SKILLOS_FORGE_OFFLINE", "").strip().lower() in {
            "1", "true", "yes", "on"
        }:
            return self._respond(409, {
                "error": "SKILLOS_FORGE_OFFLINE set; forge is disabled",
            })
        goal = str(body.get("goal", "")).strip()
        project = body.get("project")
        kind_raw = str(body.get("kind", "generate")).lower()
        if not goal or not project:
            return self._respond(400, {"error": "goal and project required"})
        try:
            kind = RouteKind(kind_raw)
        except ValueError:
            return self._respond(400, {"error": f"unknown kind: {kind_raw}"})
        if kind not in {RouteKind.GENERATE, RouteKind.EVOLVE}:
            return self._respond(400, {
                "error": f"kind {kind.value} not supported via API",
            })

        # Lazy-import executor so HTTP server can start even if anthropic
        # package is missing — it will fail at execution, not at bind.
        from forge.executor import ForgeExecutor, ForgeJobSpec

        spec = ForgeJobSpec(
            goal=goal,
            project_path=Path(project),
            kind=kind,
            trigger=str(body.get("trigger", "user_request")),
            target_model=str(body.get("target_model")
                              or os.environ.get("GEMMA_MODEL", "gemma4:e2b")),
            target_skill_id=str(body.get("target_skill_id", "")),
            signal=str(body.get("signal", "")),
            evidence=str(body.get("evidence", "")),
            current_skill=str(body.get("current_skill", "")),
        )
        result = ForgeExecutor().run(spec)
        self._respond(200, {
            "job_id": result.job_id,
            "outcome": result.outcome,
            "candidates_path": (
                str(result.candidates_path) if result.candidates_path else None
            ),
            "artifacts": [str(p) for p in result.artifacts],
            "tokens": result.tokens,
            "usd": result.usd,
            "wall_clock_s": result.wall_clock_s,
            "notes": result.notes,
        })

    # --- response helper -------------------------------------------

    def _respond(self, status: int, payload: Any) -> None:
        body = _dump(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


# --- utilities -------------------------------------------------------

def _project_from_query(url) -> Path:
    q = parse_qs(url.query)
    raw = (q.get("project") or [str(Path.cwd())])[0]
    return Path(raw)


def _qbool(values) -> bool:
    if not values:
        return False
    return str(values[0]).strip().lower() in {"1", "true", "yes", "on"}


def _as_float(v: Any) -> float | None:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# --- server class (exposed for tests) --------------------------------

class ForgeHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer with a short shutdown timeout.

    Tests construct this directly so they can start/stop it in-process
    without racing on the default 1-second poll interval.
    """

    daemon_threads = True
    allow_reuse_address = True


def make_server(host: str = "127.0.0.1", port: int = 8765) -> ForgeHTTPServer:
    return ForgeHTTPServer((host, port), ForgeAPIHandler)


# --- CLI entry -------------------------------------------------------

def serve_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="forge serve",
        description="Start the SkillOS forge HTTP API.",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--bind-any", action="store_true",
                        help="bind 0.0.0.0; ignored without FORGE_API_TOKEN")
    args = parser.parse_args(argv)
    host = "0.0.0.0" if args.bind_any and os.environ.get("FORGE_API_TOKEN") \
                    else args.host
    srv = make_server(host=host, port=args.port)
    print(f"forge API listening on http://{host}:{args.port}", file=sys.stderr)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        thread.join()
    except KeyboardInterrupt:
        print("shutting down", file=sys.stderr)
        srv.shutdown()
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(serve_main())
