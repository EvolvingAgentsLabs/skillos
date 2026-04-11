"""Tests for sandbox.py — SandboxExecutor implementations."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sandbox import LocalExecutor, SandboxResult, create_executor


# ── LocalExecutor tests ──────────────────────────────────────────

class TestLocalExecutor:

    def setup_method(self):
        self.executor = LocalExecutor()

    def test_echo_hello(self):
        result = self.executor.execute("echo hello")
        assert result.stdout == "hello"
        assert result.returncode == 0

    def test_returns_sandbox_result(self):
        result = self.executor.execute("echo ok")
        assert isinstance(result, SandboxResult)

    def test_env_vars_passed(self):
        result = self.executor.execute("echo $MY_VAR", env={"MY_VAR": "42"})
        assert result.stdout == "42"

    def test_timeout_raises(self):
        with pytest.raises(Exception):  # subprocess.TimeoutExpired
            self.executor.execute("sleep 10", timeout=1)

    def test_nonzero_exit_code(self):
        result = self.executor.execute("exit 42")
        assert result.returncode == 42

    def test_stderr_captured(self):
        result = self.executor.execute("echo err >&2")
        assert "err" in result.stderr

    def test_multiline_stdout(self):
        result = self.executor.execute("echo line1; echo line2")
        assert "line1" in result.stdout
        assert "line2" in result.stdout


# ── Factory tests ────────────────────────────────────────────────

class TestCreateExecutor:

    def test_local_returns_local_executor(self):
        e = create_executor("local")
        assert isinstance(e, LocalExecutor)

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown sandbox mode"):
            create_executor("unknown")

    def test_e2b_fails_gracefully(self):
        """E2B mode raises ImportError when package not installed."""
        with pytest.raises((ImportError, RuntimeError)):
            create_executor("e2b")
