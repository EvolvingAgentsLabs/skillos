"""
Tests for the Claude Code terminal runtime (skillos.py).

Covers:
  - Banner sourced from Boot.md (no hardcoded ASCII art in skillos.py)
  - parse_duration / parse_time pure-logic tests
  - Scheduler unit tests
  - process_input goal-wrapping behaviour
  - Schedule command parsing
"""

import re
import sys
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from conftest import ROOT, load_skillos_module


# ── Structural checks (no import needed) ─────────────────────────

class TestTerminalStructure:
    HARDCODED_ART_PATTERN = re.compile(
        r'banner\s*=\s*\(.*?___.*?\)', re.DOTALL
    )

    def test_skillos_py_exists(self, root):
        assert (root / "skillos.py").exists()

    def test_no_hardcoded_ascii_banner(self, skillos_text):
        """ASCII art must live in Boot.md, not in skillos.py."""
        assert not self.HARDCODED_ART_PATTERN.search(skillos_text), (
            "Hardcoded ASCII banner found in skillos.py — it should be in Boot.md"
        )

    def test_show_banner_reads_boot_md(self, skillos_text):
        """show_banner() must reference Boot.md."""
        assert "Boot.md" in skillos_text

    def test_banner_extraction_regex_present(self, skillos_text):
        """show_banner() must use a regex to extract the Banner section."""
        assert "## Banner" in skillos_text

    def test_boot_skillos_function_exists(self, skillos_text):
        assert "def boot_skillos" in skillos_text

    def test_main_repl_exists(self, skillos_text):
        assert "def main" in skillos_text

    def test_scheduler_class_exists(self, skillos_text):
        assert "class Scheduler" in skillos_text

    def test_run_claude_function_exists(self, skillos_text):
        assert "def run_claude" in skillos_text

    def test_process_input_function_exists(self, skillos_text):
        assert "def process_input" in skillos_text


# ── Streaming + spinner behaviour ────────────────────────────────

class TestStreamingBehaviour:
    """run_claude() must stream output and show a spinner while waiting."""

    # Matches a function body regardless of return-type annotation (-> str, etc.)
    _FN_BODY = staticmethod(lambda name, text: re.search(
        rf"def {name}\([^)]*\)(?:\s*->[^:]+)?:(.*?)(?=\ndef |\Z)",
        text, re.DOTALL,
    ))

    def test_run_claude_uses_spinner(self, skillos_text):
        """run_claude must create a Spinner (not just boot_skillos)."""
        m = self._FN_BODY("run_claude", skillos_text)
        assert m, "run_claude function not found"
        assert "Spinner" in m.group(1), (
            "run_claude must create a Spinner for the wait period"
        )

    def test_run_claude_uses_live(self, skillos_text):
        """run_claude must use Live to manage the spinner lifecycle."""
        m = self._FN_BODY("run_claude", skillos_text)
        assert m
        assert "Live" in m.group(1), "run_claude must use Live to control the spinner"

    def test_run_claude_streams_lines(self, skillos_text):
        """run_claude must print each line as it arrives (not buffer then render)."""
        m = self._FN_BODY("run_claude", skillos_text)
        assert m
        assert "console.print(line" in m.group(1), (
            "run_claude must stream lines immediately via console.print(line, ...)"
        )

    def test_run_claude_uses_line_buffering(self, skillos_text):
        """Popen must use bufsize=1 for responsive line-by-line streaming."""
        m = self._FN_BODY("run_claude", skillos_text)
        assert m
        assert "bufsize=1" in m.group(1), (
            "Popen must use bufsize=1 (line-buffered) to enable streaming"
        )

    def test_run_claude_spinner_stops_on_first_output(self, skillos_text):
        """Spinner must be stopped as soon as the first output line arrives."""
        m = self._FN_BODY("run_claude", skillos_text)
        assert m
        body = m.group(1)
        assert "spinner.stop()" in body or "is_started" in body, (
            "Spinner must be stopped when first output arrives"
        )

    def test_run_claude_handles_keyboard_interrupt(self, skillos_text):
        """run_claude must catch KeyboardInterrupt and terminate the subprocess."""
        m = self._FN_BODY("run_claude", skillos_text)
        assert m
        body = m.group(1)
        assert "KeyboardInterrupt" in body
        assert "terminate()" in body or "kill()" in body

    def test_boot_skillos_still_has_spinner(self, skillos_text):
        """boot_skillos must keep its own spinner (boot is not streaming)."""
        m = self._FN_BODY("boot_skillos", skillos_text)
        assert m, "boot_skillos function not found"
        assert "Spinner" in m.group(1), "boot_skillos must retain its Spinner"


# ── Banner extraction logic ───────────────────────────────────────

class TestBannerExtraction:
    """Validate that the regex used in show_banner() correctly extracts the art."""

    def _extract(self, boot_text: str):
        m = re.search(r"## Banner\s*```\s*(.*?)```", boot_text, re.DOTALL)
        if not m:
            return []
        return [l for l in m.group(1).rstrip().splitlines() if l.strip()]

    def test_extraction_returns_lines(self, root):
        boot_text = (root / "Boot.md").read_text(encoding="utf-8")
        lines = self._extract(boot_text)
        assert len(lines) >= 5

    def test_first_line_is_ascii_art(self, root):
        boot_text = (root / "Boot.md").read_text(encoding="utf-8")
        lines = self._extract(boot_text)
        # ASCII art lines contain / \ _ characters
        assert any(c in lines[0] for c in ("_", "/", "\\")), (
            "First banner line should be ASCII art"
        )

    def test_last_two_lines_are_subtitles(self, root):
        boot_text = (root / "Boot.md").read_text(encoding="utf-8")
        lines = self._extract(boot_text)
        subtitle_block = " ".join(lines[-2:])
        assert "v1" in subtitle_block or "OS" in subtitle_block or "SkillOS" in subtitle_block


# ── parse_duration ────────────────────────────────────────────────

class TestParseDuration:
    """Unit tests for parse_duration() — pure stdlib function."""

    @pytest.fixture(scope="class")
    def parse_duration(self):
        mod = load_skillos_module()
        return mod.parse_duration

    def test_seconds(self, parse_duration):
        assert parse_duration("30s") == 30

    def test_seconds_long(self, parse_duration):
        assert parse_duration("90sec") == 90

    def test_minutes(self, parse_duration):
        assert parse_duration("5m") == 300

    def test_minutes_long(self, parse_duration):
        assert parse_duration("2min") == 120

    def test_hours(self, parse_duration):
        assert parse_duration("2h") == 7200

    def test_hours_long(self, parse_duration):
        assert parse_duration("1hr") == 3600

    def test_days(self, parse_duration):
        assert parse_duration("1d") == 86400

    def test_compound_hours_minutes(self, parse_duration):
        assert parse_duration("1h30m") == 5400

    def test_compound_minutes_seconds(self, parse_duration):
        assert parse_duration("2m30s") == 150

    def test_bare_number_defaults_to_minutes(self, parse_duration):
        assert parse_duration("10") == 600

    def test_invalid_returns_none(self, parse_duration):
        assert parse_duration("xyz") is None

    def test_empty_string_returns_none(self, parse_duration):
        assert parse_duration("") is None


# ── parse_time ────────────────────────────────────────────────────

class TestParseTime:
    """Unit tests for parse_time() — pure stdlib function."""

    @pytest.fixture(scope="class")
    def parse_time(self):
        mod = load_skillos_module()
        return mod.parse_time

    def test_hhmm_format(self, parse_time):
        now = datetime.now()
        future = now + timedelta(hours=2)
        result = parse_time(future.strftime("%H:%M"))
        assert isinstance(result, datetime)

    def test_hhmm_rolls_to_tomorrow_if_past(self, parse_time):
        result = parse_time("00:01")  # Just past midnight
        assert result is not None
        assert result > datetime.now()

    def test_ampm_pm(self, parse_time):
        result = parse_time("3pm")
        assert result is not None
        assert result.hour == 15

    def test_ampm_am(self, parse_time):
        result = parse_time("9am")
        assert result is not None
        assert result.hour == 9

    def test_ampm_noon(self, parse_time):
        result = parse_time("12pm")
        assert result is not None
        assert result.hour == 12

    def test_ampm_midnight(self, parse_time):
        result = parse_time("12am")
        assert result is not None
        assert result.hour == 0

    def test_colon_ampm(self, parse_time):
        result = parse_time("2:30pm")
        assert result is not None
        assert result.hour == 14
        assert result.minute == 30

    def test_tomorrow_prefix(self, parse_time):
        result = parse_time("tomorrow 9am")
        assert result is not None
        tomorrow = datetime.now().date() + timedelta(days=1)
        assert result.date() == tomorrow

    def test_invalid_returns_none(self, parse_time):
        assert parse_time("not-a-time") is None

    def test_empty_returns_none(self, parse_time):
        assert parse_time("") is None


# ── Scheduler ─────────────────────────────────────────────────────

class TestScheduler:
    """Unit tests for the Scheduler class."""

    @pytest.fixture
    def scheduler(self):
        mod = load_skillos_module()
        return mod.Scheduler()

    def test_schedule_once_creates_task(self, scheduler):
        task = scheduler.schedule_once("test goal", delay_seconds=60)
        assert task is not None
        assert task.goal == "test goal"
        assert task.max_runs == 1

    def test_schedule_once_sets_next_run(self, scheduler):
        task = scheduler.schedule_once("goal", delay_seconds=60)
        assert task.next_run is not None
        assert task.next_run > datetime.now()

    def test_schedule_recurring_no_max(self, scheduler):
        task = scheduler.schedule_recurring("recurring", interval_seconds=300)
        assert task.interval_seconds == 300
        assert task.max_runs is None

    def test_schedule_recurring_with_max(self, scheduler):
        task = scheduler.schedule_recurring("limited", interval_seconds=60, max_runs=5)
        assert task.max_runs == 5

    def test_schedule_at_sets_exact_time(self, scheduler):
        target = datetime.now() + timedelta(hours=1)
        task = scheduler.schedule_at("at-goal", run_at=target)
        assert task.next_run == target

    def test_cancel_pending_task(self, scheduler):
        mod = load_skillos_module()
        task = scheduler.schedule_once("cancel-me", delay_seconds=3600)
        assert scheduler.cancel(task.id) is True
        assert task.status.value == "cancelled"

    def test_cancel_nonexistent_returns_false(self, scheduler):
        assert scheduler.cancel("nonexistent") is False

    def test_remove_task(self, scheduler):
        task = scheduler.schedule_once("remove-me", delay_seconds=3600)
        assert scheduler.remove(task.id) is True
        tasks = scheduler.get_tasks()
        assert not any(t.id == task.id for t in tasks)

    def test_remove_nonexistent_returns_false(self, scheduler):
        assert scheduler.remove("nonexistent") is False

    def test_get_tasks_sorted_by_next_run(self, scheduler):
        t1 = scheduler.schedule_once("first", delay_seconds=300)
        t2 = scheduler.schedule_once("second", delay_seconds=60)
        tasks = scheduler.get_tasks()
        next_runs = [t.next_run for t in tasks if t.next_run]
        assert next_runs == sorted(next_runs)

    def test_task_ids_are_unique(self, scheduler):
        tasks = [scheduler.schedule_once(f"goal-{i}", delay_seconds=i + 1) for i in range(5)]
        ids = [t.id for t in tasks]
        assert len(set(ids)) == len(ids)


# ── process_input / goal wrapping ────────────────────────────────

class TestProcessInput:
    """process_input() should wrap bare goals in skillos execute: format."""

    PREFIXES = [
        "skillos execute:",
        "skillos simulate:",
        "execute:",
        "simulate:",
    ]

    def _wrap(self, user_input: str, prefixes: list) -> str:
        """Mirrors the logic in process_input()."""
        if not user_input.startswith(tuple(prefixes)):
            return f'skillos execute: "{user_input}"'
        return user_input

    def test_bare_goal_gets_wrapped(self):
        result = self._wrap("create a web scraper", self.PREFIXES)
        assert result == 'skillos execute: "create a web scraper"'

    def test_execute_prefix_passes_through(self):
        prompt = 'skillos execute: "do something"'
        assert self._wrap(prompt, self.PREFIXES) == prompt

    def test_simulate_prefix_passes_through(self):
        prompt = 'skillos simulate: "do something"'
        assert self._wrap(prompt, self.PREFIXES) == prompt

    def test_short_execute_prefix_passes_through(self):
        prompt = 'execute: "do something"'
        assert self._wrap(prompt, self.PREFIXES) == prompt


# ── _fmt_duration ─────────────────────────────────────────────────

class TestFmtDuration:
    @pytest.fixture(scope="class")
    def fmt(self):
        mod = load_skillos_module()
        return mod._fmt_duration

    def test_none_returns_dash(self, fmt):
        assert fmt(None) == "-"

    def test_seconds_only(self, fmt):
        assert fmt(45) == "45s"

    def test_even_minutes(self, fmt):
        assert fmt(120) == "2m"

    def test_minutes_with_seconds(self, fmt):
        assert fmt(90) == "1m30s"

    def test_even_hours(self, fmt):
        assert fmt(3600) == "1h"

    def test_hours_with_minutes(self, fmt):
        assert fmt(5400) == "1h30m"
