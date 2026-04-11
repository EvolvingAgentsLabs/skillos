"""Sandbox execution layer for SkillOS.

Provides an abstract SandboxExecutor with two implementations:
  - LocalExecutor  — wraps subprocess.run() (default, zero-dep)
  - E2bExecutor    — wraps e2b_code_interpreter.Sandbox (optional, requires E2B_API_KEY)
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass


@dataclass
class SandboxResult:
    """Uniform result from any executor."""
    stdout: str
    stderr: str
    returncode: int


class SandboxExecutor:
    """Abstract base for shell execution backends."""

    def execute(
        self,
        command: str,
        *,
        env: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> SandboxResult:
        raise NotImplementedError


class LocalExecutor(SandboxExecutor):
    """Runs commands via subprocess on the host machine."""

    def execute(
        self,
        command: str,
        *,
        env: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> SandboxResult:
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        result = subprocess.run(
            ["bash", "-c", command],
            capture_output=True,
            text=True,
            env=run_env,
            timeout=timeout,
        )
        return SandboxResult(
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
            returncode=result.returncode,
        )


class E2bExecutor(SandboxExecutor):
    """Runs commands inside an E2B cloud sandbox.

    Requires the ``e2b_code_interpreter`` package and an ``E2B_API_KEY``
    environment variable.  Both are validated at construction time so
    callers get a clear error before any tool invocation.
    """

    def __init__(self) -> None:
        try:
            from e2b_code_interpreter import Sandbox  # type: ignore[import-untyped]
        except ImportError:
            raise ImportError(
                "E2B sandbox requires the 'e2b_code_interpreter' package. "
                "Install it with: pip install e2b-code-interpreter"
            )
        if not os.getenv("E2B_API_KEY"):
            raise RuntimeError(
                "E2B sandbox requires the E2B_API_KEY environment variable."
            )
        self._Sandbox = Sandbox
        self._sandbox_instance: object | None = None

    def _get_sandbox(self):
        if self._sandbox_instance is None:
            self._sandbox_instance = self._Sandbox()
        return self._sandbox_instance

    def execute(
        self,
        command: str,
        *,
        env: dict[str, str] | None = None,
        timeout: int = 30,
    ) -> SandboxResult:
        sandbox = self._get_sandbox()
        result = sandbox.commands.run(command, timeout=timeout, envs=env or {})
        return SandboxResult(
            stdout=(result.stdout or "").strip(),
            stderr=(result.stderr or "").strip(),
            returncode=result.exit_code,
        )


def create_executor(mode: str = "local") -> SandboxExecutor:
    """Factory: create an executor by name.

    Args:
        mode: ``"local"`` (default) or ``"e2b"``.

    Raises:
        ValueError: Unknown mode.
        ImportError / RuntimeError: E2B deps missing (propagated from E2bExecutor).
    """
    if mode == "local":
        return LocalExecutor()
    if mode == "e2b":
        return E2bExecutor()
    raise ValueError(f"Unknown sandbox mode '{mode}'. Choose 'local' or 'e2b'.")
