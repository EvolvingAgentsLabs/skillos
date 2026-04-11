"""Tests for PathPolicy — path traversal prevention in permission_policy.py."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure skillos root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from permission_policy import PathPolicy, PermissionPolicy, PermissionMode


# ── PathPolicy unit tests ────────────────────────────────────────

class TestPathPolicy:
    """Direct PathPolicy.validate_path() tests."""

    def setup_method(self):
        self.workspace = Path(tempfile.mkdtemp())
        self.policy = PathPolicy(workspace_root=self.workspace)

    # ── Allowed paths ────────────────────────────────────────────

    def test_relative_path_within_workspace(self):
        ok, reason = self.policy.validate_path("read_file", {"path": "projects/foo.md"})
        assert ok
        assert reason == ""

    def test_absolute_path_within_workspace(self):
        inner = self.workspace / "data" / "file.txt"
        ok, reason = self.policy.validate_path("read_file", {"path": str(inner)})
        assert ok

    def test_file_path_arg_variant(self):
        ok, reason = self.policy.validate_path("Read", {"file_path": str(self.workspace / "x.md")})
        assert ok

    def test_directory_arg_variant(self):
        ok, reason = self.policy.validate_path("list_files", {"directory": str(self.workspace / "sub")})
        assert ok

    # ── Blocked paths ────────────────────────────────────────────

    def test_absolute_path_outside_workspace(self):
        ok, reason = self.policy.validate_path("read_file", {"path": "/etc/passwd"})
        assert not ok
        assert "path traversal blocked" in reason

    def test_dot_dot_traversal_attack(self):
        ok, reason = self.policy.validate_path("write_file", {"path": "../../etc/shadow"})
        assert not ok
        assert "path traversal blocked" in reason

    def test_write_tool_outside(self):
        ok, reason = self.policy.validate_path("Write", {"file_path": "/tmp/evil.sh"})
        assert not ok
        assert "path traversal blocked" in reason

    def test_append_tool_outside(self):
        ok, reason = self.policy.validate_path("append_to_file", {"path": "/var/log/syslog"})
        assert not ok

    # ── Symlink escape ───────────────────────────────────────────

    def test_symlink_to_outside_workspace(self, tmp_path):
        policy = PathPolicy(workspace_root=tmp_path)
        target = Path("/etc")
        link = tmp_path / "escape_link"
        try:
            link.symlink_to(target)
        except OSError:
            pytest.skip("Cannot create symlinks on this platform")
        ok, reason = policy.validate_path("read_file", {"path": str(link / "passwd")})
        assert not ok
        assert "path traversal blocked" in reason

    # ── Non-file-IO tools are ignored ────────────────────────────

    def test_non_file_tool_ignores_path(self):
        ok, reason = self.policy.validate_path("call_llm", {"path": "/etc/passwd"})
        assert ok

    def test_bash_tool_not_checked(self):
        ok, reason = self.policy.validate_path("Bash", {"command": "cat /etc/passwd"})
        assert ok

    # ── Edge cases ───────────────────────────────────────────────

    def test_no_args_allowed(self):
        ok, _ = self.policy.validate_path("read_file", None)
        assert ok

    def test_empty_path_allowed(self):
        ok, _ = self.policy.validate_path("read_file", {"path": ""})
        assert ok

    def test_no_path_key_allowed(self):
        ok, _ = self.policy.validate_path("read_file", {"content": "hello"})
        assert ok

    def test_default_workspace_is_cwd(self):
        policy = PathPolicy()
        assert policy.workspace_root == Path(os.getcwd()).resolve()


# ── PermissionPolicy integration ─────────────────────────────────

class TestPermissionPolicyWithPathPolicy:
    """Path validation runs before mode check in authorize()."""

    def setup_method(self):
        self.workspace = Path(tempfile.mkdtemp())
        pp = PathPolicy(workspace_root=self.workspace)
        self.policy = PermissionPolicy(
            default_mode=PermissionMode.ALLOW,
            path_policy=pp,
        )

    def test_allow_mode_still_blocks_path_escape(self):
        """Even with ALLOW mode, path traversal is blocked."""
        ok, reason = self.policy.authorize(
            "read_file", "", args={"path": "/etc/passwd"}
        )
        assert not ok
        assert "path traversal blocked" in reason

    def test_allow_mode_permits_valid_path(self):
        ok, reason = self.policy.authorize(
            "read_file", "", args={"path": str(self.workspace / "ok.txt")}
        )
        assert ok

    def test_backward_compat_no_args(self):
        """authorize() without args= still works (no crash)."""
        ok, reason = self.policy.authorize("read_file", "some preview")
        assert ok  # ALLOW mode, no path to validate
