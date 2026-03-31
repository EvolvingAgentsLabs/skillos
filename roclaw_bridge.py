#!/usr/bin/env python3
"""
RoClaw Bridge Server — HTTP bridge between SkillOS and RoClaw.

Translates REST API calls into tool invocations sent to a backend:
  - WebSocket → OpenClaw Gateway (real hardware)
  - HTTP → run_sim3d.ts --serve tool server (MuJoCo simulation)
  - Simulation → mock responses (no hardware)

Usage:
    python roclaw_bridge.py --port 8430 --gateway ws://localhost:8080
    python roclaw_bridge.py --port 8430 --tool-server http://localhost:8440
    python roclaw_bridge.py --port 8430 --simulate   # No real hardware
"""

import argparse
import asyncio
import json
import logging
import urllib.request
import urllib.error
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Any

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("roclaw-bridge")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ROCLAW_TOOLS = [
    "robot.go_to",
    "robot.explore",
    "robot.describe_scene",
    "robot.stop",
    "robot.status",
    "robot.read_memory",
    "robot.record_observation",
    "robot.analyze_scene",
    "robot.get_map",
    "robot.telemetry",
]

# ---------------------------------------------------------------------------
# Gateway Client (WebSocket → OpenClaw)
# ---------------------------------------------------------------------------

class GatewayClient:
    """WebSocket client that forwards tool invocations to the OpenClaw Gateway."""

    def __init__(self, gateway_url: str):
        self.gateway_url = gateway_url
        self._ws = None
        self._pending: dict[str, asyncio.Future] = {}
        self._loop: asyncio.AbstractEventLoop | None = None
        self._listen_task: asyncio.Task | None = None

    async def connect(self):
        if not HAS_WEBSOCKETS:
            raise RuntimeError("websockets package required: pip install websockets")
        self._ws = await websockets.connect(self.gateway_url)
        self._loop = asyncio.get_event_loop()
        self._listen_task = asyncio.create_task(self._listen())
        log.info("Connected to OpenClaw Gateway at %s", self.gateway_url)

    async def _listen(self):
        try:
            async for message in self._ws:
                data = json.loads(message)
                msg_id = data.get("id")
                if msg_id and msg_id in self._pending:
                    self._pending[msg_id].set_result(data)
        except Exception as e:
            log.error("Gateway listener error: %s", e)
            for fut in self._pending.values():
                if not fut.done():
                    fut.set_exception(e)

    async def invoke_tool(self, tool: str, args: dict[str, Any], timeout: float = 300) -> dict:
        call_id = f"sk_{uuid.uuid4().hex[:12]}"
        message = {
            "type": "invoke",
            "id": call_id,
            "tool": tool,
            "args": args,
        }
        future = self._loop.create_future()
        self._pending[call_id] = future
        try:
            await self._ws.send(json.dumps(message))
            result = await asyncio.wait_for(future, timeout=timeout)
            return result
        finally:
            self._pending.pop(call_id, None)

    async def close(self):
        if self._listen_task:
            self._listen_task.cancel()
        if self._ws:
            await self._ws.close()


# ---------------------------------------------------------------------------
# Simulation Client (no hardware)
# ---------------------------------------------------------------------------

class SimulationClient:
    """Simulated robot responses for testing without hardware."""

    def __init__(self):
        self._pose = {"x": 0.0, "y": 0.0, "heading": 0.0}
        self._locations: list[dict] = []
        self._is_moving = False
        log.info("Simulation mode — no real hardware connected")

    async def connect(self):
        pass

    async def invoke_tool(self, tool: str, args: dict[str, Any], timeout: float = 300) -> dict:
        call_id = f"sim_{uuid.uuid4().hex[:8]}"

        if tool == "robot.status":
            return {"id": call_id, "success": True, "data": {
                "pose": self._pose, "motor_state": "idle",
                "battery_level": 85, "is_moving": self._is_moving,
            }}

        if tool == "robot.stop":
            self._is_moving = False
            return {"id": call_id, "success": True, "message": "Robot stopped"}

        if tool == "robot.go_to":
            location = args.get("location", "unknown")
            self._is_moving = True
            await asyncio.sleep(0.5)  # Simulate travel
            self._pose["x"] += 1.0
            self._is_moving = False
            trace_id = f"tr_{uuid.uuid4().hex[:8]}"
            return {"id": call_id, "success": True, "message": f"Arrived at {location} (simulated)",
                    "data": {"trace_id": trace_id, "steps_taken": 3}}

        if tool == "robot.explore":
            self._is_moving = True
            await asyncio.sleep(0.3)
            self._is_moving = False
            return {"id": call_id, "success": True, "data": {
                "locations_discovered": ["room_a", "corridor"],
                "map_updates": 2, "trace_id": f"tr_{uuid.uuid4().hex[:8]}",
            }}

        if tool == "robot.describe_scene":
            return {"id": call_id, "success": True, "data": {
                "description": "Simulated room with a table, two chairs, and a doorway to the left.",
                "objects": ["table", "chair", "chair", "doorway"],
                "spatial_layout": "Table center, chairs flanking, doorway left wall",
            }}

        if tool == "robot.read_memory":
            return {"id": call_id, "success": True, "data": {
                "memory": "## Hardware\nRoClaw v1 — dual 28BYJ-48 steppers\n\n## Identity\nAutonomous indoor navigation robot",
                "sections": ["hardware", "identity", "strategies", "traces"],
            }}

        if tool == "robot.record_observation":
            label = args.get("label", "unknown")
            confidence = args.get("confidence", 0.8)
            entry = {"label": label, "pose": dict(self._pose), "confidence": confidence}
            self._locations.append(entry)
            return {"id": call_id, "success": True, "data": {"pose": self._pose}}

        if tool == "robot.analyze_scene":
            return {"id": call_id, "success": True, "data": {
                "analysis": "Simulated deep scene analysis",
                "features": [
                    {"name": "table", "bbox": [120, 80, 300, 250], "confidence": 0.92},
                    {"name": "door", "bbox": [10, 50, 60, 280], "confidence": 0.88},
                ],
            }}

        if tool == "robot.get_map":
            return {"id": call_id, "success": True, "data": {
                "pose_map": self._locations,
                "semantic_graph": {"nodes": [], "edges": []},
            }}

        if tool == "robot.telemetry":
            import time
            return {"id": call_id, "success": True, "data": {
                "pose": self._pose, "vel": {"left": 0.0, "right": 0.0},
                "stall": False, "ts": int(time.time() * 1000),
            }}

        return {"id": call_id, "success": False, "message": f"Unknown tool: {tool}"}

    async def close(self):
        pass


# ---------------------------------------------------------------------------
# HTTP Tool Server Client (run_sim3d.ts --serve)
# ---------------------------------------------------------------------------

class HttpToolClient:
    """HTTP client that forwards tool invocations to a run_sim3d.ts --serve tool server."""

    def __init__(self, tool_server_url: str):
        self.tool_server_url = tool_server_url.rstrip("/")
        log.info("HTTP tool client targeting %s", self.tool_server_url)

    async def connect(self):
        """Verify the tool server is reachable."""
        url = f"{self.tool_server_url}/health"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                log.info("Tool server healthy: %s", data)
        except Exception as e:
            raise RuntimeError(f"Cannot reach tool server at {url}: {e}") from e

    async def invoke_tool(self, tool: str, args: dict[str, Any], timeout: float = 300) -> dict:
        # robot.telemetry uses GET /telemetry on the tool server (not POST /invoke)
        if tool == "robot.telemetry":
            url = f"{self.tool_server_url}/telemetry"
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read())
            except Exception as e:
                return {"success": False, "message": str(e)}

        url = f"{self.tool_server_url}/invoke"
        payload = json.dumps({"tool": tool, "args": args}).encode()
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode() if e.fp else ""
            try:
                return json.loads(body)
            except Exception:
                return {"success": False, "message": f"HTTP {e.code}: {body}"}
        except Exception as e:
            return {"success": False, "message": str(e)}

    async def close(self):
        """Send shutdown to the tool server (best-effort)."""
        url = f"{self.tool_server_url}/shutdown"
        try:
            req = urllib.request.Request(url, data=b"", method="POST")
            urllib.request.urlopen(req, timeout=5)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# HTTP Request Handler
# ---------------------------------------------------------------------------

_client = None
_loop = None


class BridgeHandler(BaseHTTPRequestHandler):
    """HTTP handler that translates REST calls to tool invocations."""

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data, indent=2).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw)

    def do_GET(self):
        path = self.path.rstrip("/")

        if path == "/health":
            self._send_json(200, {"status": "ok", "tools": ROCLAW_TOOLS})
            return

        # GET endpoints for read-only tools
        tool_name = None
        if path == "/tool/robot.status":
            tool_name = "robot.status"
        elif path == "/tool/robot.read_memory":
            tool_name = "robot.read_memory"
        elif path == "/tool/robot.get_map":
            tool_name = "robot.get_map"
        elif path == "/tool/robot.telemetry":
            tool_name = "robot.telemetry"

        if tool_name:
            result = asyncio.run_coroutine_threadsafe(
                _client.invoke_tool(tool_name, {}), _loop
            ).result(timeout=30)
            self._send_json(200, result)
            return

        self._send_json(404, {"error": f"Unknown endpoint: {path}"})

    def do_POST(self):
        path = self.path.rstrip("/")

        # Extract tool name from path
        if path.startswith("/tool/"):
            tool_name = path[len("/tool/"):]
        else:
            self._send_json(404, {"error": f"Unknown endpoint: {path}"})
            return

        if tool_name not in ROCLAW_TOOLS:
            self._send_json(400, {"error": f"Unknown tool: {tool_name}", "available": ROCLAW_TOOLS})
            return

        args = self._read_body()

        try:
            result = asyncio.run_coroutine_threadsafe(
                _client.invoke_tool(tool_name, args), _loop
            ).result(timeout=300)
            self._send_json(200, result)
        except TimeoutError:
            self._send_json(504, {"error": "Tool invocation timed out"})
        except Exception as e:
            self._send_json(500, {"error": str(e)})

    def log_message(self, fmt, *args):
        log.info(fmt, *args)


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

def run_async_loop(loop: asyncio.AbstractEventLoop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


def main():
    global _client, _loop

    parser = argparse.ArgumentParser(description="RoClaw Bridge — HTTP ↔ WebSocket bridge for SkillOS")
    parser.add_argument("--port", type=int, default=8430, help="HTTP port (default: 8430)")
    parser.add_argument("--gateway", type=str, default="ws://localhost:8080", help="OpenClaw Gateway URL")
    parser.add_argument("--tool-server", type=str, default=None,
                        help="HTTP tool server URL (e.g. http://localhost:8440) — connects to run_sim3d.ts --serve")
    parser.add_argument("--simulate", action="store_true", help="Use simulated robot (no hardware)")
    args = parser.parse_args()

    # Create async event loop in background thread
    _loop = asyncio.new_event_loop()
    thread = Thread(target=run_async_loop, args=(_loop,), daemon=True)
    thread.start()

    # Initialize client
    if args.simulate:
        _client = SimulationClient()
    elif args.tool_server:
        _client = HttpToolClient(args.tool_server)
    else:
        _client = GatewayClient(args.gateway)

    # Connect client
    asyncio.run_coroutine_threadsafe(_client.connect(), _loop).result(timeout=10)

    # Determine mode label
    if args.simulate:
        mode_label = "SIMULATION"
    elif args.tool_server:
        mode_label = f"TOOL SERVER → {args.tool_server}"
    else:
        mode_label = f"GATEWAY → {args.gateway}"

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", args.port), BridgeHandler)
    log.info("RoClaw Bridge listening on http://0.0.0.0:%d", args.port)
    log.info("Mode: %s", mode_label)
    log.info("Available tools: %s", ", ".join(ROCLAW_TOOLS))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down...")
        asyncio.run_coroutine_threadsafe(_client.close(), _loop).result(timeout=5)
        server.server_close()


if __name__ == "__main__":
    main()
