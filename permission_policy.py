"""Permission policy for SkillOS tool execution — ported from claw-code's PermissionPolicy pattern.

Provides deny/allow/prompt authorization for tools before execution,
preventing uncontrolled access to dangerous operations.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Callable, Optional


class PathPolicy:
    """Validates that file-IO tool arguments stay within the workspace root."""

    FILE_IO_TOOLS: frozenset[str] = frozenset({
        "read_file", "write_file", "append_to_file", "list_files",
        "Read", "Write", "Glob", "Grep", "grep_files",
    })

    def __init__(self, workspace_root: str | Path | None = None) -> None:
        self.workspace_root = Path(workspace_root or os.getcwd()).resolve()

    def validate_path(self, tool_name: str, args: dict | None) -> tuple[bool, str]:
        """Return (allowed, reason). Only checks FILE_IO_TOOLS."""
        if tool_name not in self.FILE_IO_TOOLS:
            return True, ""
        if not args:
            return True, ""

        # Extract path from common arg names
        target = args.get("path") or args.get("file_path") or args.get("directory") or ""
        if not target:
            return True, ""

        try:
            target_path = Path(target)
            if not target_path.is_absolute():
                target_path = self.workspace_root / target_path
            resolved = target_path.resolve()
            resolved.relative_to(self.workspace_root)
        except ValueError:
            return False, (
                f"path traversal blocked: '{target}' resolves outside workspace "
                f"root '{self.workspace_root}'"
            )
        return True, ""


class PermissionMode(Enum):
    ALLOW = "allow"
    DENY = "deny"
    PROMPT = "prompt"


class PermissionPolicy:
    """Controls which tools can execute automatically vs require approval."""

    def __init__(
        self,
        default_mode: PermissionMode = PermissionMode.PROMPT,
        tool_modes: dict[str, PermissionMode] | None = None,
        path_policy: PathPolicy | None = None,
    ) -> None:
        self.default_mode = default_mode
        self.tool_modes: dict[str, PermissionMode] = tool_modes or {}
        self.path_policy = path_policy or PathPolicy()

    def with_tool_mode(self, tool_name: str, mode: PermissionMode) -> "PermissionPolicy":
        """Set mode for a specific tool. Returns self for chaining."""
        self.tool_modes[tool_name] = mode
        return self

    def authorize(
        self,
        tool_name: str,
        input_preview: str = "",
        prompter: Callable[[str, str], tuple[bool, str]] | None = None,
        *,
        args: dict | None = None,
    ) -> tuple[bool, str]:
        """Check if a tool invocation is authorized.

        Returns (authorized, reason) tuple.
        """
        # Path validation runs FIRST — even ALLOW-mode tools can't escape workspace
        path_ok, path_reason = self.path_policy.validate_path(tool_name, args)
        if not path_ok:
            return False, path_reason

        mode = self.tool_modes.get(tool_name, self.default_mode)

        if mode == PermissionMode.ALLOW:
            return True, ""

        if mode == PermissionMode.DENY:
            return False, f"tool '{tool_name}' denied by policy"

        # PROMPT mode
        if prompter:
            return prompter(tool_name, input_preview)

        return False, f"tool '{tool_name}' requires interactive approval"


# ── Default policy profiles ─────────────────────────────────────

def _build_default_policy() -> PermissionPolicy:
    """Standard policy: read-only tools auto-allowed, write/exec tools prompt."""
    return (
        PermissionPolicy(PermissionMode.PROMPT)
        .with_tool_mode("Read", PermissionMode.ALLOW)
        .with_tool_mode("Glob", PermissionMode.ALLOW)
        .with_tool_mode("Grep", PermissionMode.ALLOW)
        .with_tool_mode("robot.status", PermissionMode.ALLOW)
        .with_tool_mode("robot.telemetry", PermissionMode.ALLOW)
        .with_tool_mode("robot.get_map", PermissionMode.ALLOW)
        .with_tool_mode("Bash", PermissionMode.PROMPT)
        .with_tool_mode("Write", PermissionMode.PROMPT)
        .with_tool_mode("robot.go_to", PermissionMode.PROMPT)
    )


def _build_autonomous_policy() -> PermissionPolicy:
    """Autonomous policy: everything allowed except shell execution."""
    return (
        PermissionPolicy(PermissionMode.ALLOW)
        .with_tool_mode("Bash", PermissionMode.PROMPT)
    )


SKILLOS_DEFAULT_POLICY = _build_default_policy()
SKILLOS_AUTONOMOUS_POLICY = _build_autonomous_policy()


POLICY_REGISTRY: dict[str, PermissionPolicy] = {
    "default": SKILLOS_DEFAULT_POLICY,
    "autonomous": SKILLOS_AUTONOMOUS_POLICY,
}


def get_policy(name: str) -> PermissionPolicy:
    """Look up a named policy profile."""
    if name not in POLICY_REGISTRY:
        raise ValueError(f"Unknown policy '{name}'. Available: {list(POLICY_REGISTRY.keys())}")
    return POLICY_REGISTRY[name]
