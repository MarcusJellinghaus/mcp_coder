"""Shared helpers for the vscodeclaude detection tests."""

from datetime import UTC, datetime, timedelta

import pytest

from mcp_coder.workflows.vscodeclaude.detection import DetectionSnapshot
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession

DETECTION = "mcp_coder.workflows.vscodeclaude.detection"


def _session(
    folder: str,
    *,
    issue_number: int = 38,
    repo: str = "owner/mcp_coder",
    vscode_pid: int | None = None,
    vscode_pid_create_time: float | None = None,
    started_at: str | None = None,
) -> VSCodeClaudeSession:
    """Build a session dict with sensible defaults for detection tests."""
    if started_at is None:
        # Default well outside the launch grace window.
        started_at = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    return {
        "folder": folder,
        "repo": repo,
        "issue_number": issue_number,
        "status": "status-07:code-review",
        "vscode_pid": vscode_pid,
        "vscode_pid_create_time": vscode_pid_create_time,
        "started_at": started_at,
        "is_intervention": False,
        "last_active": None,
        "last_active_rule": None,
    }


def _snapshot(
    *,
    processes: tuple[dict[str, object], ...] = (),
    window_titles: tuple[tuple[int, str], ...] = (),
    pids: frozenset[int] = frozenset(),
    window_enum_ok: bool = True,
    captured_at: datetime | None = None,
) -> DetectionSnapshot:
    """Build a DetectionSnapshot with empty defaults."""
    return DetectionSnapshot(
        processes=processes,
        window_titles=window_titles,
        pids=pids,
        window_enum_ok=window_enum_ok,
        captured_at=captured_at or datetime.now(UTC),
    )


def _force_windows(monkeypatch: pytest.MonkeyPatch, enabled: bool = True) -> None:
    """Force the HAS_WIN32GUI flag as seen by the detection module."""
    monkeypatch.setattr(f"{DETECTION}.HAS_WIN32GUI", enabled)


def _stub_pid_alive(monkeypatch: pytest.MonkeyPatch, alive: bool) -> None:
    """Stub check_vscode_running in the detection module."""
    monkeypatch.setattr(f"{DETECTION}.check_vscode_running", lambda *_: alive)
