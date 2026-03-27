"""
HIL Standardization Test — verifies the bridge contract is runtime-agnostic.

Tests that the RoClaw bridge produces identical responses regardless of
which runtime (Claude, Qwen, Llama, curl) calls it. This is the foundation
of model agnosticism: same HTTP request -> same robot behavior.

Usage:
    cd skillos && python -m pytest tests/test_hil_standardization.py -v
"""

import json
import time
import subprocess
import urllib.request
import urllib.error
import pytest

BRIDGE_PORT = 18430  # Use non-standard port to avoid conflicts
BRIDGE_URL = f"http://localhost:{BRIDGE_PORT}"


@pytest.fixture(scope="module")
def bridge():
    """Start roclaw_bridge.py --simulate on a test port."""
    proc = subprocess.Popen(
        ["python", "roclaw_bridge.py", "--port", str(BRIDGE_PORT), "--simulate"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    # Wait for the server to be ready
    for _ in range(20):
        time.sleep(0.25)
        try:
            req = urllib.request.Request(f"{BRIDGE_URL}/health")
            urllib.request.urlopen(req, timeout=2)
            break
        except Exception:
            continue
    else:
        proc.terminate()
        proc.wait(timeout=5)
        pytest.fail("Bridge did not start within 5 seconds")
    yield proc
    proc.terminate()
    proc.wait(timeout=5)


def _get(path):
    req = urllib.request.Request(f"{BRIDGE_URL}{path}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())


def _post(path, body=None):
    data = json.dumps(body or {}).encode()
    req = urllib.request.Request(
        f"{BRIDGE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


class TestBridgeContract:
    """The bridge must return identical responses regardless of caller."""

    def test_health(self, bridge):
        result = _get("/health")
        assert result["status"] == "ok"
        assert "robot.go_to" in result["tools"]
        assert "robot.telemetry" in result["tools"]
        assert len(result["tools"]) == 10

    def test_go_to(self, bridge):
        result = _post("/tool/robot.go_to", {"location": "kitchen"})
        assert result["success"] is True
        assert "kitchen" in result["message"].lower()
        assert "data" in result
        assert "trace_id" in result["data"]

    def test_describe_scene(self, bridge):
        result = _post("/tool/robot.describe_scene")
        assert result["success"] is True
        assert "data" in result
        assert "description" in result["data"]
        assert "objects" in result["data"]

    def test_status(self, bridge):
        result = _get("/tool/robot.status")
        assert result["success"] is True
        assert "data" in result
        assert "pose" in result["data"]
        assert "x" in result["data"]["pose"]

    def test_telemetry(self, bridge):
        result = _get("/tool/robot.telemetry")
        assert result["success"] is True
        assert "data" in result
        assert "pose" in result["data"]
        assert "stall" in result["data"]

    def test_stop(self, bridge):
        result = _post("/tool/robot.stop")
        assert result["success"] is True

    def test_get_map(self, bridge):
        result = _get("/tool/robot.get_map")
        assert result["success"] is True
        assert "data" in result

    def test_explore(self, bridge):
        result = _post("/tool/robot.explore")
        assert result["success"] is True
        assert "data" in result

    def test_read_memory(self, bridge):
        result = _get("/tool/robot.read_memory")
        assert result["success"] is True
        assert "data" in result

    def test_unknown_tool_rejected(self, bridge):
        req = urllib.request.Request(
            f"{BRIDGE_URL}/tool/robot.nonexistent",
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=10)
            assert False, "Should have returned 400"
        except urllib.error.HTTPError as e:
            assert e.code == 400

    def test_response_schema_consistency(self, bridge):
        """All tools must return JSON with consistent top-level keys."""
        endpoints = [
            ("POST", "/tool/robot.go_to", {"location": "kitchen"}),
            ("POST", "/tool/robot.describe_scene", {}),
            ("POST", "/tool/robot.stop", {}),
            ("GET", "/tool/robot.status", None),
            ("GET", "/tool/robot.telemetry", None),
            ("GET", "/tool/robot.get_map", None),
            ("GET", "/tool/robot.read_memory", None),
        ]
        for method, path, body in endpoints:
            if method == "GET":
                result = _get(path)
            else:
                result = _post(path, body)
            assert "success" in result, f"{path} missing 'success' key"
            assert isinstance(result["success"], bool), f"{path} 'success' not bool"
