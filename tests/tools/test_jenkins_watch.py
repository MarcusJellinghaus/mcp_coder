"""Unit tests for tools/jenkins_watch.py (JenkinsClient and clock faked)."""

from __future__ import annotations

import dataclasses
import importlib
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.utils.jenkins_operations import BuildInfo, JenkinsError

_TOOL_DIR = Path(__file__).resolve().parents[2] / "tools"
if str(_TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOL_DIR))

jenkins_watch = importlib.import_module("jenkins_watch")

FAILING_LOG = "2026-11-26 18:04:00 - ERROR - LLM timed out\nFinished: FAILURE"

# Shape of an Executor log: the script source echoes the markers, then they run.
EXECUTOR_LOG = "\r\n".join(
    [
        "echo command execution  =====================================",  # 1
        "echo archive after execution =======================================",  # 2
        "2026-11-26 18:00:00 - ERROR - before the section",  # 3
        "C:\\env>echo command execution  ===================================== ",  # 4
        "",  # 5
        "command execution  =====================================",  # 6
        "2026-11-26 18:04:00 - ERROR - LLM timed out",  # 7
        "C:\\env>echo archive after execution ======================================= ",  # 8
        "",  # 9
        "archive after execution =======================================",  # 10
        "2026-11-26 18:04:00 - ERROR - LLM timed out",  # 11: Text Finder echo
        "Finished: FAILURE",  # 12
    ]
)


SAVED_AT = datetime(2026, 11, 26, 19, 4, 8)


def build(number: int, status: str, name: str | None = None) -> BuildInfo:
    if name is None:
        name = f"repo - #43 - implement - #{number}"
    return BuildInfo(
        job_path="Windows-Agents/Executor",
        folder="Windows-Agents",
        job_name="Executor",
        number=number,
        status=status,
        timestamp=datetime(2026, 11, 26, tzinfo=UTC),
        duration_ms=None,
        url="",
        display_name=name,
    )


class FakeClock:
    """Monotonic clock that only moves when the watcher sleeps."""

    def __init__(self) -> None:
        self.now = 0.0

    def sleep(self, seconds: float) -> None:
        self.now += seconds

    def time(self) -> float:
        return self.now


def run_watch(
    client: MagicMock,
    tmp_path: Path,
    idle: float = 5,
    stall: float = 60,
    report: float = 120,
    watch_only: bool = False,
) -> str:
    clock = FakeClock()
    options = jenkins_watch.Options(
        job="Windows-Agents/Executor",
        pattern=None,
        limit=30,
        interval=60,
        idle=idle,
        stall=stall,
        report=report,
        log_dir=tmp_path / "logs",
        watch_only=watch_only,
    )
    return str(jenkins_watch.watch(client, options, sleep=clock.sleep, now=clock.time))


def client_listing(*listings: list[BuildInfo]) -> MagicMock:
    """Client whose get_recent_builds returns the listings in turn, then the last forever."""
    client = MagicMock()
    queue = list(listings)
    client.get_recent_builds.side_effect = lambda **_: (
        queue.pop(0) if len(queue) > 1 else queue[0]
    )
    client.get_console_output.return_value = FAILING_LOG
    return client


def growing_log() -> Callable[..., str]:
    """get_console_output side effect: one line more on every call."""
    lines: list[str] = []

    def fetch(*_: object) -> str:
        lines.append("- INFO - working")
        return "\n".join(lines)

    return fetch


def test_failed_build_is_a_problem_and_its_log_is_scanned(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = client_listing([build(1, "running")], [build(1, "failure")])
    assert run_watch(client, tmp_path) == "problem"
    client.get_console_output.assert_called_with("Windows-Agents/Executor", 1)
    (log_file,) = (tmp_path / "logs").glob("jenkins_log_43_implement_1_*.txt")
    assert log_file.read_text(encoding="utf-8") == FAILING_LOG
    out = capsys.readouterr().out
    assert "error 1, decision 1, warning 0" in out
    assert "1: 2026-11-26 18:04:00 - ERROR - LLM timed out" in out
    assert "RESULT: problem" in out


def test_newest_build_failed_is_reported_at_once(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = client_listing([build(2, "failure"), build(1, "success")])
    assert run_watch(client, tmp_path) == "problem"
    assert client.get_recent_builds.call_count == 1
    client.get_console_output.assert_called_once_with("Windows-Agents/Executor", 2)
    out = capsys.readouterr().out
    assert "newest failure" in out
    assert "RESULT: problem" in out


def test_older_failure_while_a_build_runs_keeps_watching(tmp_path: Path) -> None:
    client = client_listing(
        [build(2, "running"), build(1, "failure")],
        [build(2, "success"), build(1, "failure")],
    )
    assert run_watch(client, tmp_path) == "idle"


def test_newest_build_succeeded_keeps_watching(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = client_listing([build(1, "success")])
    assert run_watch(client, tmp_path) == "idle"
    client.get_console_output.assert_not_called()
    assert "newest success" in capsys.readouterr().out


def test_watch_only_skips_the_initial_check(tmp_path: Path) -> None:
    client = client_listing([build(1, "failure")])
    assert run_watch(client, tmp_path, watch_only=True) == "idle"
    client.get_console_output.assert_not_called()


@pytest.mark.parametrize("status", ["unstable", "aborted"])
def test_unstable_and_aborted_are_problems(status: str, tmp_path: Path) -> None:
    client = client_listing([build(1, "running")], [build(1, status)])
    assert run_watch(client, tmp_path) == "problem"


def test_success_keeps_watching_until_idle(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = client_listing([build(1, "running")], [build(1, "success")])
    assert run_watch(client, tmp_path) == "idle"
    out = capsys.readouterr().out
    assert "log: " in out
    assert "RESULT: idle" in out


def test_new_build_keeps_watching(tmp_path: Path) -> None:
    client = client_listing(
        [build(1, "success")],
        [build(2, "running"), build(1, "success")],
        [build(2, "failure"), build(1, "success")],
    )
    assert run_watch(client, tmp_path) == "problem"


def test_log_without_new_output_for_stall_minutes_is_stalled(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = client_listing([build(1, "running")])
    assert run_watch(client, tmp_path, stall=3) == "stalled"
    out = capsys.readouterr().out
    assert "no new log output for 3 min" in out
    assert "log: " in out
    assert "RESULT: stalled" in out


def test_growing_log_is_not_stalled_and_reports_a_heartbeat(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = client_listing([build(1, "running")])
    client.get_console_output.side_effect = growing_log()
    assert run_watch(client, tmp_path, stall=3, report=10) == "heartbeat"
    out = capsys.readouterr().out
    assert "still running  #1" in out
    assert "RESULT: heartbeat" in out


def test_stall_clock_restarts_when_the_log_grows(tmp_path: Path) -> None:
    client = client_listing([build(1, "running")])
    logs = ["a", "a", "a\nb", "a\nb", "a\nb"]
    client.get_console_output.side_effect = lambda *_: (
        logs.pop(0) if len(logs) > 1 else logs[0]
    )
    # Polls each minute, checks the log every 5: at minutes 0, 5, 10 (grown), 15, 20.
    # With stall=10 it stalls at minute 20 (the 21st listing), not at minute 10.
    assert run_watch(client, tmp_path, stall=10) == "stalled"
    assert client.get_recent_builds.call_count == 21
    assert client.get_console_output.call_count == 6  # five checks, then the report


def test_running_build_log_is_only_downloaded_every_few_minutes(tmp_path: Path) -> None:
    running = [build(1, "running")]
    client = client_listing(running, running, running, running, [build(1, "success")])
    assert run_watch(client, tmp_path) == "idle"
    # The first check at minute 0, then the finished build's report; none in between.
    assert client.get_console_output.call_count == 2


def test_no_heartbeat_while_nothing_runs(tmp_path: Path) -> None:
    client = client_listing([build(1, "success")])
    assert run_watch(client, tmp_path, idle=30, report=10) == "idle"


def test_jenkins_errors_for_five_minutes_end_the_watch(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = MagicMock()
    # Polls each minute: errors from minute 1 to minute 6, five minutes apart.
    client.get_recent_builds.side_effect = [[build(1, "running")]] + [
        JenkinsError("down")
    ] * 6
    assert run_watch(client, tmp_path) == "jenkins-error"
    assert capsys.readouterr().out.count("Jenkins error: down") == 2  # first and last


def test_shorter_jenkins_outage_is_retried(tmp_path: Path) -> None:
    client = MagicMock()
    client.get_recent_builds.side_effect = (
        [[build(1, "running")]] + [JenkinsError("blip")] * 5 + [[build(1, "failure")]]
    )
    client.get_console_output.return_value = ""
    assert run_watch(client, tmp_path) == "problem"


def test_changed_builds_reports_new_builds_and_status_changes() -> None:
    before = [build(1, "running"), build(2, "success")]
    after = [build(3, "running"), build(1, "failure"), build(2, "success")]
    changed = jenkins_watch.changed_builds(before, after)
    assert [b.number for b in changed] == [3, 1]


def test_renamed_build_is_not_a_change() -> None:
    changed = jenkins_watch.changed_builds(
        [build(1, "running", "#1")], [build(1, "running")]
    )
    assert changed == []


@pytest.mark.parametrize(
    ("repo", "expected"),
    [(None, " - #43 - "), ("a.b", r"^a\.b - #43 - ")],
)
def test_issue_pattern(repo: str | None, expected: str) -> None:
    assert jenkins_watch.issue_pattern(43, repo).pattern == expected


def test_scan_log_finds_errors_warnings_and_deciding_lines() -> None:
    log = "\n".join(
        [
            "2026-11-26 18:03:00 - INFO - starting",
            "2026-11-26 18:03:01 - WARNING - format_code is ignored",
            "Traceback (most recent call last):",
            "2026-11-26 18:04:00 - ERROR - LLM timed out",
            "Successfully updated issue #43 label: status-04:plan-review",
            "Finished: SUCCESS",
        ]
    )
    assert [(m.kind, m.line_number) for m in jenkins_watch.scan_log(log)] == [
        ("warning", 2),
        ("error", 3),
        ("error", 4),
        ("decision", 5),
        ("decision", 6),
    ]


def test_scan_log_ignores_ordinary_lines() -> None:
    assert jenkins_watch.scan_log("- INFO - all good\nno error here") == []


def test_scan_log_ignores_jenkins_text_finder_lines() -> None:
    log = (
        "[Text Finder] Finished searching for pattern ' - ERROR - ' in console output."
    )
    assert jenkins_watch.scan_log(log) == []


def test_command_section_uses_the_run_time_markers() -> None:
    assert jenkins_watch.command_section(EXECUTOR_LOG) == (6, 10)


def test_command_section_runs_to_the_end_without_an_end_marker() -> None:
    log = "start\ncommand execution  =====\nstill running"
    assert jenkins_watch.command_section(log) == (2, 3)


def test_command_section_is_none_without_a_start_marker() -> None:
    assert jenkins_watch.command_section("Finished: FAILURE") is None


def test_scan_log_limits_to_a_line_range() -> None:
    matches = jenkins_watch.scan_log(EXECUTOR_LOG, first=6, last=10)
    assert [m.line_number for m in matches] == [7]


def test_inspect_scans_the_command_section_and_keeps_line_endings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = MagicMock()
    client.get_console_output.return_value = EXECUTOR_LOG
    jenkins_watch.inspect_log(
        client,
        "Windows-Agents/Executor",
        1,
        tmp_path,
        "repo - #43 - implement - #1",
        SAVED_AT,
    )
    saved = tmp_path / "jenkins_log_43_implement_1_2026-11-26_19-04-08.txt"
    assert saved.read_bytes() == EXECUTOR_LOG.encode("utf-8")
    out = capsys.readouterr().out
    assert "command section: lines 6-10" in out
    assert "error 1, decision 0, warning 0" in out


def test_inspect_scans_everything_without_a_command_section(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = MagicMock()
    client.get_console_output.return_value = FAILING_LOG
    jenkins_watch.inspect_log(client, "Windows-Agents/Executor", 1, tmp_path)
    out = capsys.readouterr().out
    assert "no command section" in out
    assert "error 1, decision 1, warning 0" in out


def test_inspect_option_scans_one_build_and_exits(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = MagicMock()
    client.get_console_output.return_value = EXECUTOR_LOG
    client.get_recent_builds.return_value = [build(7, "failure")]
    monkeypatch.setattr(jenkins_watch, "make_client", lambda: client)
    argv = ["--inspect", "7", "--job", "A/Executor", "--log-dir", str(tmp_path)]
    assert jenkins_watch.main(argv) == 0
    client.get_console_output.assert_called_once_with("A/Executor", 7)
    assert list(tmp_path.glob("jenkins_log_43_implement_7_*.txt"))
    assert "command section: lines 6-10" in capsys.readouterr().out


def test_inspect_option_without_a_build_name_uses_the_number(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = MagicMock()
    client.get_console_output.return_value = ""
    client.get_recent_builds.side_effect = JenkinsError("down")
    monkeypatch.setattr(jenkins_watch, "make_client", lambda: client)
    argv = ["--inspect", "7", "--job", "A/Executor", "--log-dir", str(tmp_path)]
    assert jenkins_watch.main(argv) == 0
    assert list(tmp_path.glob("jenkins_log_7_*.txt"))


@pytest.mark.parametrize(
    ("display_name", "expected"),
    [
        (
            "claude-mode-gate - #43 - implement - #3174",
            "jenkins_log_43_implement_3174_2026-11-26_19-04-08.txt",
        ),
        (
            "mcp_coder - #1419 - review-plan - #3174",
            "jenkins_log_1419_review-plan_3174_2026-11-26_19-04-08.txt",
        ),
        ("#3174", "jenkins_log_3174_2026-11-26_19-04-08.txt"),
        ("", "jenkins_log_3174_2026-11-26_19-04-08.txt"),
    ],
)
def test_log_filename(display_name: str, expected: str) -> None:
    assert jenkins_watch.log_filename(3174, display_name, SAVED_AT) == expected


LONG_ERROR = (
    "2026-11-26 18:19:34 - ERROR - Error: LLM modified files: ['" + "x" * 250 + "']"
)
LONG_WARNING = "2026-11-26 18:19:34 - WARNING - " + "w" * 250


def test_inspect_prints_error_lines_in_full_and_shortens_warnings(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = MagicMock()
    client.get_console_output.return_value = f"{LONG_ERROR}\n{LONG_WARNING}"
    jenkins_watch.inspect_log(client, "Windows-Agents/Executor", 1, tmp_path)
    out = capsys.readouterr().out
    assert LONG_ERROR in out
    assert LONG_WARNING not in out
    assert LONG_WARNING[:200] in out


def test_handoff_lines_are_decisions_not_warnings() -> None:
    log = "\n".join(
        [
            "2026-11-26 18:30:00 - mcp_coder.workflows.review.handoff - WARNING - REVIEW HANDED OFF",
            "2026-11-26 18:30:00 - mcp_coder.workflows.review.handoff - WARNING - Reason: rounds cap",
        ]
    )
    assert [m.kind for m in jenkins_watch.scan_log(log)] == ["decision", "decision"]


@pytest.mark.parametrize(
    ("log", "expected"),
    [
        (
            "x - INFO - Successfully updated issue #43 label: status-05:plan-ready → status-06:implementing\n"
            "x - INFO - Successfully updated issue #43 label: status-06:implementing → status-07:code-review",
            "status-06:implementing → status-07:code-review",
        ),
        (
            "Updated issue #43 to status-06f:implementing-failed",
            "status-06f:implementing-failed",
        ),
        ("Finished: SUCCESS", None),
    ],
)
def test_label_change_is_the_last_one_in_the_log(
    log: str, expected: str | None
) -> None:
    assert jenkins_watch.label_change(jenkins_watch.scan_log(log)) == expected


def test_inspect_prints_the_label_change(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    client = MagicMock()
    client.get_console_output.return_value = "x - INFO - Successfully updated issue #43 label: status-06:implementing → status-07:code-review"
    jenkins_watch.inspect_log(client, "Windows-Agents/Executor", 1, tmp_path)
    assert (
        "  label: status-06:implementing → status-07:code-review"
        in capsys.readouterr().out
    )


def test_list_option_prints_the_issues_builds_oldest_first(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    client = MagicMock()
    client.get_recent_builds.return_value = [build(9, "running"), build(8, "failure")]
    monkeypatch.setattr(jenkins_watch, "make_client", lambda: client)
    assert jenkins_watch.main(["--list", "--issue", "43", "--job", "A/Executor"]) == 0
    kwargs = client.get_recent_builds.call_args.kwargs
    assert kwargs["path"] == "A/Executor"
    assert kwargs["name_pattern"].pattern == " - #43 - "
    out = capsys.readouterr().out
    assert out.index("#8  repo - #43 - implement - #8") < out.index("#9  repo")
    client.get_console_output.assert_not_called()


def test_list_option_shows_the_duration() -> None:
    finished = dataclasses.replace(build(8, "failure"), duration_ms=42 * 60_000)
    assert "42 min" in jenkins_watch.list_line(finished)
    assert "min" not in jenkins_watch.list_line(build(9, "running"))


def test_inspect_option_takes_several_builds(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = MagicMock()
    client.get_console_output.return_value = ""
    client.get_recent_builds.return_value = []
    monkeypatch.setattr(jenkins_watch, "make_client", lambda: client)
    argv = ["--inspect", "7", "8", "--job", "A/Executor", "--log-dir", str(tmp_path)]
    assert jenkins_watch.main(argv) == 0
    assert [c.args for c in client.get_console_output.call_args_list] == [
        ("A/Executor", 7),
        ("A/Executor", 8),
    ]


def test_inspect_option_exits_3_when_a_log_cannot_be_read(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    client = MagicMock()
    client.get_console_output.side_effect = JenkinsError("gone")
    client.get_recent_builds.return_value = []
    monkeypatch.setattr(jenkins_watch, "make_client", lambda: client)
    argv = ["--inspect", "7", "--job", "A/Executor", "--log-dir", str(tmp_path)]
    assert jenkins_watch.main(argv) == 3


@pytest.mark.parametrize("result", ["idle", "problem", "stalled", "heartbeat"])
def test_every_watch_result_exits_0(
    result: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(jenkins_watch, "make_client", MagicMock)
    monkeypatch.setattr(jenkins_watch, "watch", lambda *_: result)
    assert jenkins_watch.main(["--job", "A/Executor"]) == 0


def test_default_interval_is_15_seconds(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[float] = []

    def fake_watch(_: object, options: Any) -> str:
        seen.append(options.interval)
        return "idle"

    monkeypatch.setattr(jenkins_watch, "make_client", MagicMock)
    monkeypatch.setattr(jenkins_watch, "watch", fake_watch)
    jenkins_watch.main(["--job", "A/Executor"])
    assert seen == [15]


def test_jenkins_error_result_exits_3(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jenkins_watch, "make_client", MagicMock)
    monkeypatch.setattr(jenkins_watch, "watch", lambda *_: "jenkins-error")
    assert jenkins_watch.main(["--job", "A/Executor"]) == 3


def test_repo_without_issue_exits_2() -> None:
    with pytest.raises(SystemExit) as exc_info:
        jenkins_watch.main(["--repo", "x"])
    assert exc_info.value.code == 2


def test_inspect_without_job_exits_2(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(jenkins_watch, "configured_executor_job", lambda: None)
    # A check after make_client() would return 3 here instead of exiting 2.
    monkeypatch.setattr(jenkins_watch, "make_client", lambda: None)
    with pytest.raises(SystemExit) as exc_info:
        jenkins_watch.main(["--inspect", "7"])
    assert exc_info.value.code == 2
