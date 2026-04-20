"""HTTP API smoke tests.

Start the server in a thread, hit each endpoint, assert shape.  No LLM
calls — the forge/run path is exercised via executor patching.
"""

from __future__ import annotations

import json
import socket
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from forge.server import make_server  # noqa: E402


def _free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


@pytest.fixture
def server():
    port = _free_port()
    srv = make_server(host="127.0.0.1", port=port)
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        srv.shutdown()
        srv.server_close()


def _get(port: int, path: str, headers: dict | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(f"http://127.0.0.1:{port}{path}",
                                 headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def _post(port: int, path: str, body: dict,
          headers: dict | None = None) -> tuple[int, dict]:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


# --- health + 404 ----------------------------------------------------

def test_health(server):
    status, body = _get(server, "/health")
    assert status == 200
    assert body == {"status": "ok"}


def test_unknown_path_404(server):
    status, _ = _get(server, "/nope")
    assert status == 404


# --- /api/route ------------------------------------------------------

def test_route_generate_on_unknown_goal(server):
    status, body = _get(server, "/api/route?goal=something-weird")
    assert status == 200
    assert body["tier"] == "forge"
    assert body["kind"] == "generate"


def test_route_cartridge_match(server):
    status, body = _get(
        server,
        "/api/route?goal=make+breakfast&cartridge=cooking",
    )
    assert status == 200
    assert body["tier"] == "hot"
    assert body["kind"] == "cartridge"


def test_route_rejects_missing_goal(server):
    status, body = _get(server, "/api/route")
    assert status == 400
    assert "goal" in body.get("error", "")


def test_route_post_accepts_body(server):
    status, body = _post(
        server,
        "/api/route",
        {"goal": "x", "cartridge": "cooking"},
    )
    assert status == 200
    assert body["kind"] == "cartridge"


# --- budget + journal + audit ----------------------------------------

def test_budget_returns_fresh_ledger(server, tmp_path):
    status, body = _get(server, f"/api/budget?project={tmp_path}")
    assert status == 200
    assert "caps" in body
    assert "usage" in body


def test_journal_empty(server, tmp_path):
    status, body = _get(server, f"/api/journal?project={tmp_path}")
    assert status == 200
    assert body["count"] == 0
    assert body["records"] == []


def test_audit_returns_status_map(server):
    status, body = _get(server, "/api/audit?model=gemma4:e2b")
    assert status == 200
    assert "status" in body
    # Every cartridge should report something (likely 'missing' at this
    # point — the attestation flow hasn't run yet).
    for name, verdict in body["status"].items():
        assert verdict in {"ok", "weak", "stale", "model_mismatch", "missing"}


# --- /api/forge/run --------------------------------------------------

def test_forge_run_refuses_offline(server, monkeypatch):
    monkeypatch.setenv("SKILLOS_FORGE_OFFLINE", "1")
    status, body = _post(
        server,
        "/api/forge/run",
        {"goal": "x", "project": "/tmp/x", "kind": "generate"},
    )
    assert status == 409
    assert "forge is disabled" in body["error"]


def test_forge_run_requires_goal_and_project(server, monkeypatch):
    monkeypatch.delenv("SKILLOS_FORGE_OFFLINE", raising=False)
    status, _ = _post(server, "/api/forge/run", {"kind": "generate"})
    assert status == 400


def test_forge_run_rejects_unknown_kind(server, monkeypatch):
    monkeypatch.delenv("SKILLOS_FORGE_OFFLINE", raising=False)
    status, _ = _post(
        server,
        "/api/forge/run",
        {"goal": "x", "project": "/tmp/x", "kind": "banana"},
    )
    assert status == 400


# --- auth ------------------------------------------------------------

def test_auth_required_when_token_set(server, monkeypatch):
    monkeypatch.setenv("FORGE_API_TOKEN", "secret")
    status, _ = _get(server, "/health")
    assert status == 401
    status, body = _get(server, "/health",
                        headers={"Authorization": "Bearer secret"})
    assert status == 200
    assert body == {"status": "ok"}
