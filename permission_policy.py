"""Permission policy for SkillOS tool execution — ported from claw-code's PermissionPolicy pattern.

Provides deny/allow/prompt authorization for tools before execution,
preventing uncontrolled access to dangerous operations.
"""

from __future__ import annotations

from enum import Enum
from typing import Callable, Optional


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
    ) -> None:
        self.default_mode = default_mode
        self.tool_modes: dict[str, PermissionMode] = tool_modes or {}

    def with_tool_mode(self, tool_name: str, mode: PermissionMode) -> "PermissionPolicy":
        """Set mode for a specific tool. Returns self for chaining."""
        self.tool_modes[tool_name] = mode
        return self

    def authorize(
        self,
        tool_name: str,
        input_preview: str = "",
        prompter: Callable[[str, str], tuple[bool, str]] | None = None,
    ) -> tuple[bool, str]:
        """Check if a tool invocation is authorized.

        Returns (authorized, reason) tuple.
        """
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
