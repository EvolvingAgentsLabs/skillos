#!/usr/bin/env python3
"""
SkillOS Terminal - Pure Markdown Operating System Shell
Wraps Claude Code to present SkillOS as a classical Unix terminal
with rendered markdown output and task scheduling.
"""

import subprocess
import sys
import signal
import threading
import time
import uuid
import re
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

# ── Auto-install rich if missing ─────────────────────────────────
try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.theme import Theme
    from rich.spinner import Spinner
    from rich.live import Live
except ImportError:
    print("Installing required dependency: rich...")
    import shutil
    if shutil.which("uv"):
        subprocess.check_call(["uv", "pip", "install", "rich", "-q"])
    else:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "-q"])
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.table import Table
    from rich.theme import Theme
    from rich.spinner import Spinner
    from rich.live import Live

# ── Configuration ────────────────────────────────────────────────
SKILLOS_DIR = Path(__file__).resolve().parent
PROJECTS_DIR = SKILLOS_DIR / "projects"
HISTORY_FILE = SKILLOS_DIR / ".skillos_history"
PID = str(subprocess.os.getpid())

PROJECTS_DIR.mkdir(exist_ok=True)
subprocess.os.chdir(SKILLOS_DIR)

session_booted = False
cmd_count = 0
history: list[str] = []

# ── Console ──────────────────────────────────────────────────────
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green",
    "prompt": "bold green",
    "dim": "dim white",
})
console = Console(theme=custom_theme)


# ═════════════════════════════════════════════════════════════════
# Task Scheduler
# ═════════════════════════════════════════════════════════════════

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    id: str
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    run_at: datetime | None = None
    interval_seconds: int | None = None
    last_run: datetime | None = None
    next_run: datetime | None = None
    run_count: int = 0
    max_runs: int | None = None
    output: str = ""
    error: str = ""


class Scheduler:
    """Background task scheduler with cron-style and one-shot support."""

    def __init__(self):
        self.tasks: dict[str, ScheduledTask] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        """Start the scheduler background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the scheduler."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def schedule_once(self, goal: str, delay_seconds: int) -> ScheduledTask:
        """Schedule a task to run once after a delay."""
        task = ScheduledTask(
            id=self._gen_id(),
            goal=goal,
            run_at=datetime.now() + timedelta(seconds=delay_seconds),
            next_run=datetime.now() + timedelta(seconds=delay_seconds),
            max_runs=1,
        )
        with self._lock:
            self.tasks[task.id] = task
        return task

    def schedule_recurring(self, goal: str, interval_seconds: int, max_runs: int | None = None) -> ScheduledTask:
        """Schedule a task to run on a recurring interval."""
        task = ScheduledTask(
            id=self._gen_id(),
            goal=goal,
            interval_seconds=interval_seconds,
            next_run=datetime.now() + timedelta(seconds=interval_seconds),
            max_runs=max_runs,
        )
        with self._lock:
            self.tasks[task.id] = task
        return task

    def schedule_at(self, goal: str, run_at: datetime) -> ScheduledTask:
        """Schedule a task to run at a specific time."""
        task = ScheduledTask(
            id=self._gen_id(),
            goal=goal,
            run_at=run_at,
            next_run=run_at,
            max_runs=1,
        )
        with self._lock:
            self.tasks[task.id] = task
        return task

    def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        with self._lock:
            if task_id in self.tasks and self.tasks[task_id].status in (TaskStatus.PENDING,):
                self.tasks[task_id].status = TaskStatus.CANCELLED
                return True
        return False

    def remove(self, task_id: str) -> bool:
        """Remove a task from the queue entirely."""
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                return True
        return False

    def get_tasks(self) -> list[ScheduledTask]:
        """Get all tasks sorted by next_run."""
        with self._lock:
            return sorted(self.tasks.values(), key=lambda t: t.next_run or datetime.max)

    def _gen_id(self) -> str:
        return uuid.uuid4().hex[:8]

    def _run_loop(self):
        """Background loop that checks for due tasks."""
        while not self._stop_event.is_set():
            now = datetime.now()
            due_tasks = []

            with self._lock:
                for task in self.tasks.values():
                    if task.status == TaskStatus.PENDING and task.next_run and task.next_run <= now:
                        due_tasks.append(task)

            for task in due_tasks:
                self._execute_task(task)

            self._stop_event.wait(timeout=5)

    def _execute_task(self, task: ScheduledTask):
        """Execute a single task via Claude Code."""
        with self._lock:
            task.status = TaskStatus.RUNNING

        console.print(f"\n[yellow]  [scheduler] Running task {task.id}: {task.goal}[/yellow]")

        prompt = f'skillos execute: "{task.goal}"'
        cmd = ["claude", "-p", "--output-format", "text"]
        if session_booted:
            cmd.append("--continue")
        cmd.append(prompt)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(SKILLOS_DIR),
                timeout=300,
            )
            output = result.stdout.strip()

            with self._lock:
                task.output = output
                task.run_count += 1
                task.last_run = datetime.now()

                if output:
                    console.print(f"\n[dim]  [scheduler] Task {task.id} output:[/dim]")
                    console.print(Markdown(output))

                # Determine next state
                if task.max_runs and task.run_count >= task.max_runs:
                    task.status = TaskStatus.DONE
                    task.next_run = None
                    console.print(f"[success]  [scheduler] Task {task.id} completed.[/success]\n")
                elif task.interval_seconds:
                    task.status = TaskStatus.PENDING
                    task.next_run = datetime.now() + timedelta(seconds=task.interval_seconds)
                    console.print(
                        f"[info]  [scheduler] Task {task.id} next run: "
                        f"{task.next_run.strftime('%H:%M:%S')}[/info]\n"
                    )
                else:
                    task.status = TaskStatus.DONE
                    task.next_run = None

        except subprocess.TimeoutExpired:
            with self._lock:
                task.status = TaskStatus.FAILED
                task.error = "Timed out after 5 minutes"
                task.next_run = None
            console.print(f"[error]  [scheduler] Task {task.id} timed out.[/error]\n")
        except Exception as e:
            with self._lock:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.next_run = None
            console.print(f"[error]  [scheduler] Task {task.id} failed: {e}[/error]\n")


# ── Global scheduler instance ────────────────────────────────────
scheduler = Scheduler()


# ── Parse duration strings ───────────────────────────────────────
def parse_duration(text: str) -> int | None:
    """Parse a human duration like '5m', '2h', '30s', '1h30m' into seconds."""
    text = text.strip().lower()
    total = 0
    pattern = re.compile(r"(\d+)\s*(s|sec|seconds?|m|min|minutes?|h|hr|hours?|d|days?)")
    matches = pattern.findall(text)
    if not matches:
        # Try bare number (default to minutes)
        try:
            return int(text) * 60
        except ValueError:
            return None
    for value, unit in matches:
        v = int(value)
        if unit.startswith("s"):
            total += v
        elif unit.startswith("m"):
            total += v * 60
        elif unit.startswith("h"):
            total += v * 3600
        elif unit.startswith("d"):
            total += v * 86400
    return total if total > 0 else None


def parse_time(text: str) -> datetime | None:
    """Parse a time string like '14:30', '2:30pm', 'tomorrow 9am'."""
    text = text.strip().lower()
    now = datetime.now()

    # Try HH:MM format
    match = re.match(r"^(\d{1,2}):(\d{2})$", text)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    # Try "3pm", "9am"
    match = re.match(r"^(\d{1,2})\s*(am|pm)$", text)
    if match:
        h = int(match.group(1))
        if match.group(2) == "pm" and h != 12:
            h += 12
        if match.group(2) == "am" and h == 12:
            h = 0
        target = now.replace(hour=h, minute=0, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    # Try "2:30pm"
    match = re.match(r"^(\d{1,2}):(\d{2})\s*(am|pm)$", text)
    if match:
        h, m = int(match.group(1)), int(match.group(2))
        if match.group(3) == "pm" and h != 12:
            h += 12
        if match.group(3) == "am" and h == 12:
            h = 0
        target = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target

    # "tomorrow HH:MM" or "tomorrow Xam/pm"
    match = re.match(r"^tomorrow\s+(.+)$", text)
    if match:
        inner = parse_time(match.group(1))
        if inner:
            # If it already rolled to tomorrow, fine; otherwise add a day
            if inner.date() <= now.date():
                inner += timedelta(days=1)
            return inner

    return None


# ── Scheduler command handlers ───────────────────────────────────
def handle_schedule_command(user_input: str):
    """Parse and handle schedule commands.

    Formats:
        schedule in <duration> <goal>
        schedule every <duration> <goal>
        schedule at <time> <goal>
        schedule list  /  jobs
        schedule cancel <id>
        schedule remove <id>
        schedule log <id>
    """
    parts = user_input.strip()

    # schedule list / jobs
    if parts in ("schedule list", "schedule ls", "jobs"):
        show_scheduled_tasks()
        return

    # schedule cancel <id>
    match = re.match(r"^schedule\s+cancel\s+(\w+)$", parts)
    if match:
        tid = match.group(1)
        if scheduler.cancel(tid):
            console.print(f"[success]Task {tid} cancelled.[/success]")
        else:
            console.print(f"[error]Cannot cancel task {tid} (not found or not pending).[/error]")
        return

    # schedule remove <id>
    match = re.match(r"^schedule\s+remove\s+(\w+)$", parts)
    if match:
        tid = match.group(1)
        if scheduler.remove(tid):
            console.print(f"[success]Task {tid} removed.[/success]")
        else:
            console.print(f"[error]Task {tid} not found.[/error]")
        return

    # schedule log <id>
    match = re.match(r"^schedule\s+log\s+(\w+)$", parts)
    if match:
        tid = match.group(1)
        show_task_log(tid)
        return

    # schedule in <duration> <goal>
    match = re.match(r"^schedule\s+in\s+(\S+)\s+(.+)$", parts)
    if match:
        duration_str, goal = match.group(1), match.group(2).strip().strip('"\'')
        seconds = parse_duration(duration_str)
        if seconds is None:
            console.print("[error]Invalid duration. Use: 30s, 5m, 2h, 1d[/error]")
            return
        task = scheduler.schedule_once(goal, seconds)
        run_time = task.next_run.strftime("%H:%M:%S") if task.next_run else "?"
        console.print(f"[success]Scheduled task {task.id} to run at {run_time} (in {_fmt_duration(seconds)})[/success]")
        console.print(f"  [dim]Goal: {goal}[/dim]")
        return

    # schedule every <duration> <goal>   (optional: x<N> for max runs)
    match = re.match(r"^schedule\s+every\s+(\S+)\s+(?:x(\d+)\s+)?(.+)$", parts)
    if match:
        duration_str = match.group(1)
        max_runs_str = match.group(2)
        goal = match.group(3).strip().strip('"\'')
        seconds = parse_duration(duration_str)
        if seconds is None:
            console.print("[error]Invalid interval. Use: 30s, 5m, 2h, 1d[/error]")
            return
        max_runs = int(max_runs_str) if max_runs_str else None
        task = scheduler.schedule_recurring(goal, seconds, max_runs)
        next_time = task.next_run.strftime("%H:%M:%S") if task.next_run else "?"
        repeat = f" (max {max_runs} runs)" if max_runs else " (until cancelled)"
        console.print(
            f"[success]Scheduled recurring task {task.id} every {_fmt_duration(seconds)}{repeat}[/success]"
        )
        console.print(f"  [dim]Goal: {goal}[/dim]")
        console.print(f"  [dim]Next run: {next_time}[/dim]")
        return

    # schedule at <time> <goal>
    match = re.match(r"^schedule\s+at\s+(\S+(?:\s+\S+)?)\s+(.+)$", parts)
    if match:
        time_str, goal = match.group(1), match.group(2).strip().strip('"\'')
        target = parse_time(time_str)
        if target is None:
            console.print("[error]Invalid time. Use: 14:30, 3pm, 9:30am, tomorrow 8am[/error]")
            return
        task = scheduler.schedule_at(goal, target)
        console.print(f"[success]Scheduled task {task.id} for {target.strftime('%Y-%m-%d %H:%M')}[/success]")
        console.print(f"  [dim]Goal: {goal}[/dim]")
        return

    # Unknown format
    console.print("[error]Unknown schedule command. Type [white]help[/white] for usage.[/error]")


def show_scheduled_tasks():
    """Display the task queue as a table."""
    tasks = scheduler.get_tasks()
    console.print()
    if not tasks:
        console.print("[dim]No scheduled tasks.[/dim]")
        console.print()
        return

    table = Table(title="Scheduled Tasks", show_lines=True)
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Status", width=10)
    table.add_column("Goal", max_width=40)
    table.add_column("Next Run", width=18)
    table.add_column("Interval", width=12)
    table.add_column("Runs", width=8)

    status_styles = {
        TaskStatus.PENDING: "yellow",
        TaskStatus.RUNNING: "bold blue",
        TaskStatus.DONE: "green",
        TaskStatus.FAILED: "red",
        TaskStatus.CANCELLED: "dim",
    }

    for t in tasks:
        style = status_styles.get(t.status, "white")
        next_run = t.next_run.strftime("%Y-%m-%d %H:%M") if t.next_run else "-"
        interval = _fmt_duration(t.interval_seconds) if t.interval_seconds else "once"
        max_label = f"/{t.max_runs}" if t.max_runs else ""
        runs = f"{t.run_count}{max_label}"
        table.add_row(
            t.id,
            f"[{style}]{t.status.value}[/{style}]",
            t.goal[:40],
            next_run,
            interval,
            runs,
        )

    console.print(table)
    console.print()


def show_task_log(task_id: str):
    """Show detailed output/error for a task."""
    tasks = scheduler.get_tasks()
    task = next((t for t in tasks if t.id == task_id), None)
    if not task:
        console.print(f"[error]Task {task_id} not found.[/error]")
        return

    console.print()
    console.print(f"[bold]Task {task.id}[/bold]")
    console.print(f"  Status:  [{TaskStatus(task.status).value}]{task.status.value}[/{TaskStatus(task.status).value}]")
    console.print(f"  Goal:    {task.goal}")
    console.print(f"  Created: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    if task.last_run:
        console.print(f"  Last Run: {task.last_run.strftime('%Y-%m-%d %H:%M:%S')}")
    console.print(f"  Runs:    {task.run_count}")
    if task.output:
        console.print()
        console.print("[bold]Output:[/bold]")
        console.print(Markdown(task.output))
    if task.error:
        console.print()
        console.print(f"[error]Error: {task.error}[/error]")
    console.print()


def _fmt_duration(seconds: int | None) -> str:
    """Format seconds into a human-readable duration."""
    if seconds is None:
        return "-"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        m = seconds // 60
        s = seconds % 60
        return f"{m}m{s}s" if s else f"{m}m"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h{m}m" if m else f"{h}h"


# ═════════════════════════════════════════════════════════════════
# Original SkillOS Terminal
# ═════════════════════════════════════════════════════════════════

def clear_screen():
    """Clear terminal screen safely."""
    console.clear()


def show_help():
    help_md = """\
## SkillOS Terminal Commands

| Command | Description |
|---------|-------------|
| `execute: "<goal>"` | Execute a goal through SkillOS |
| `simulate: "<goal>"` | Simulate a goal for training data |
| `<goal>` | Direct goal (auto-wrapped in execute) |

## Scheduler Commands

| Command | Description |
|---------|-------------|
| `schedule in <duration> <goal>` | Run once after a delay |
| `schedule every <interval> <goal>` | Run on a recurring interval |
| `schedule every <interval> x<N> <goal>` | Run recurring, max N times |
| `schedule at <time> <goal>` | Run once at a specific time |
| `jobs` / `schedule list` | Show all scheduled tasks |
| `schedule cancel <id>` | Cancel a pending task |
| `schedule remove <id>` | Remove a task from the queue |
| `schedule log <id>` | Show task output/details |

### Duration formats
`30s`, `5m`, `2h`, `1d`, `1h30m`

### Time formats
`14:30`, `3pm`, `9:30am`, `tomorrow 8am`

## Built-in Commands

| Command | Description |
|---------|-------------|
| `help` | Show this help message |
| `status` | Show system and session status |
| `projects` | List available projects |
| `agents` | List discovered agents |
| `history` | Show command history for this session |
| `jobs` | Show scheduled task queue |
| `reboot` | Reboot SkillOS (fresh session) |
| `clear` | Clear the terminal screen |
| `exit` / `quit` | Exit SkillOS terminal |

## Examples

```
skillos$ Create a tutorial on chaos theory
skillos$ schedule in 5m Check deployment status
skillos$ schedule every 1h Monitor tech news
skillos$ schedule at 9am Generate daily briefing
skillos$ schedule every 30m x3 Poll CI pipeline
skillos$ jobs
```
"""
    console.print(Markdown(help_md))


def show_status():
    project_count = sum(1 for p in PROJECTS_DIR.iterdir() if p.is_dir()) if PROJECTS_DIR.exists() else 0

    agents_dir = SKILLOS_DIR / ".claude" / "agents"
    agent_count = len(list(agents_dir.glob("*.md"))) if agents_dir.exists() else 0

    active_tasks = sum(
        1 for t in scheduler.get_tasks() if t.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
    )

    status_md = f"""\
## System Status

| Property | Value |
|----------|-------|
| Booted | {session_booted} |
| Session PID | {PID} |
| Commands Run | {cmd_count} |
| Working Dir | ./projects/ |
| Projects | {project_count} |
| Agents | {agent_count} |
| Scheduled Tasks | {active_tasks} active |
"""
    console.print(Markdown(status_md))


def list_projects():
    console.print()
    console.print("[bold]Projects[/bold]")
    console.print()
    if PROJECTS_DIR.exists():
        dirs = sorted(p.name for p in PROJECTS_DIR.iterdir() if p.is_dir())
        if dirs:
            for name in dirs:
                console.print(f"  [cyan]{name}[/cyan]")
        else:
            console.print("  [dim]No projects found.[/dim]")
    else:
        console.print("  [dim]No projects directory.[/dim]")
    console.print()


def list_agents():
    console.print()
    console.print("[bold]Discovered Agents[/bold]")
    console.print()
    agents_dir = SKILLOS_DIR / ".claude" / "agents"
    if agents_dir.exists():
        agents = sorted(agents_dir.glob("*.md"))
        if agents:
            for agent_file in agents:
                name = agent_file.stem
                desc = ""
                with open(agent_file, "r") as f:
                    for line in f:
                        if line.startswith("name:"):
                            name = line.split(":", 1)[1].strip()
                        if line.startswith("description:"):
                            desc = line.split(":", 1)[1].strip()[:70]
                            break
                console.print(f"  [cyan]{name}[/cyan]")
                if desc:
                    console.print(f"    [dim]{desc}[/dim]")
        else:
            console.print("  [dim]No agents found. Run setup_agents.sh first.[/dim]")
    else:
        console.print("  [dim]No agents found. Run setup_agents.sh first.[/dim]")
    console.print()


def show_history():
    console.print()
    console.print("[bold]Command History[/bold]")
    console.print()
    if history:
        for i, cmd in enumerate(history, 1):
            console.print(f"  {i:3d}  {cmd}")
    else:
        console.print("  [dim]No commands in history yet.[/dim]")
    console.print()


def run_claude(prompt: str) -> str:
    """Run claude with a spinner, then render the full response as Markdown."""
    cmd = ["claude", "-p", "--output-format", "text"]

    if session_booted:
        cmd.append("--continue")

    cmd.append(prompt)

    console.print()

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            cwd=str(SKILLOS_DIR),
        )
    except FileNotFoundError:
        console.print("[error]Error: 'claude' command not found. Is Claude Code installed?[/error]")
        console.print()
        return ""

    output_lines: list[str] = []

    with Live(
        Spinner("dots", text="[yellow]Thinking...[/yellow]"),
        console=console,
        transient=True,
    ):
        try:
            for line in process.stdout:
                output_lines.append(line)
        except KeyboardInterrupt:
            process.terminate()
            console.print("\n[warning]Interrupted.[/warning]")
            console.print()
            return "".join(output_lines)

    process.wait()
    output = "".join(output_lines)

    if output.strip():
        console.print(Markdown(output))

    console.print()
    return output


def show_banner():
    """Display the SkillOS banner, sourced from Boot.md."""
  
    console.print("  [dim]─────────────────Loading system───────────────────────[/dim]")
    


def boot_skillos():
    """Show banner, then boot SkillOS with a spinner."""
    global session_booted

    show_banner()

    cmd = ["claude", "-p", "--output-format", "text", "boot skillos"]

    # Show spinner while the agent boots
    with Live(
        Spinner("dots", text="[yellow] Booting SkillOS...[/yellow]"),
        console=console,
        transient=True,
    ):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(SKILLOS_DIR),
                timeout=120,
            )
            boot_output = result.stdout.strip()
        except subprocess.TimeoutExpired:
            boot_output = ""
            console.print("[error]Boot timed out.[/error]")
        except FileNotFoundError:
            boot_output = ""
            console.print("[error]Error: 'claude' command not found. Is Claude Code installed?[/error]")

    # Render the agent's boot response
    if boot_output:
        console.print(Markdown(boot_output))
        console.print()

    session_booted = True


def process_input(user_input: str):
    global cmd_count

    history.append(user_input)
    cmd_count += 1

    # Wrap bare goals in skillos execute format if not already prefixed
    prompt = user_input
    if not user_input.startswith(("skillos execute:", "skillos simulate:", "execute:", "simulate:")):
        prompt = f'skillos execute: "{user_input}"'

    run_claude(prompt)


def cleanup(*_):
    scheduler.stop()
    console.print()
    console.print("[dim]SkillOS session ended.[/dim]")
    try:
        HISTORY_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    sys.exit(0)


# ── Main REPL ────────────────────────────────────────────────────
def main():
    global session_booted

    signal.signal(signal.SIGINT, lambda *_: cleanup())
    signal.signal(signal.SIGTERM, lambda *_: cleanup())

    # Clear screen
    clear_screen()

    # Start scheduler
    scheduler.start()

    # Boot SkillOS - the agent generates the banner and all starting messages
    boot_skillos()

    # REPL loop
    while True:
        try:
            user_input = console.input("[bold green]skillos[/bold green][bold]$ [/bold]")
        except EOFError:
            cleanup()
        except KeyboardInterrupt:
            cleanup()

        user_input = user_input.strip()
        if not user_input:
            continue

        # Handle built-in commands
        cmd_lower = user_input.lower()

        if cmd_lower in ("help", "--help", "-h"):
            show_help()
        elif cmd_lower == "status":
            show_status()
        elif cmd_lower in ("projects", "ls projects"):
            list_projects()
        elif cmd_lower in ("agents", "ls agents"):
            list_agents()
        elif cmd_lower == "history":
            show_history()
        elif cmd_lower in ("jobs", "schedule list", "schedule ls"):
            show_scheduled_tasks()
        elif cmd_lower.startswith("schedule "):
            handle_schedule_command(user_input)
        elif cmd_lower == "reboot":
            session_booted = False
            console.print("[yellow]Rebooting SkillOS...[/yellow]")
            boot_skillos()
        elif cmd_lower in ("clear", "cls"):
            clear_screen()
            show_banner()
        elif cmd_lower in ("exit", "quit", "q"):
            cleanup()
        else:
            process_input(user_input)


if __name__ == "__main__":
    main()
