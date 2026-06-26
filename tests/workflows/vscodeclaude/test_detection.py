"""Tests for the detection snapshot + ``gather_signals`` (IO/Windows boundary).

These exercise the only place that touches psutil/win32. Every test mocks the
sessions helpers, so no real VSCode is required. The key behaviours under test:

- title-positive is authoritative and independent of cmdline (the #38 restore
  case): a window title hit yields ``title_match=True`` even with no cmdline
  reference and no live PID;
- ``folder_exists`` and ``pid_alive`` are gathered independently (R6) — a live
  process for a deleted folder is still reachable (zombie precursor);
- ``directory_empty`` / ``within_grace`` are computed here as plain bools;
- ``capture_detection_snapshot`` refreshes all three caches once and freezes
  the result into immutable tuples.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.detection import (
    DetectionSnapshot,
    capture_detection_snapshot,
    gather_signals,
)
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
        started_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
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
    captured_at: datetime | None = None,
) -> DetectionSnapshot:
    """Build a DetectionSnapshot with empty defaults."""
    return DetectionSnapshot(
        processes=processes,
        window_titles=window_titles,
        pids=pids,
        captured_at=captured_at or datetime.now(timezone.utc),
    )


def _force_windows(monkeypatch: pytest.MonkeyPatch, enabled: bool = True) -> None:
    """Force the HAS_WIN32GUI flag as seen by the detection module."""
    monkeypatch.setattr(f"{DETECTION}.HAS_WIN32GUI", enabled)


def _stub_pid_alive(monkeypatch: pytest.MonkeyPatch, alive: bool) -> None:
    """Stub check_vscode_running as imported into the detection module."""
    monkeypatch.setattr(f"{DETECTION}.check_vscode_running", lambda *_: alive)


class TestGatherSignalsTitle:
    """Title-binding behaviour (Windows-only signal)."""

    def test_title_bind_with_cmdline(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Title `[#38 ...repo` AND owning pid has folder in cmdline -> True."""
        folder = str(tmp_path)
        _force_windows(monkeypatch)
        _stub_pid_alive(monkeypatch, False)
        snapshot = _snapshot(
            processes=({"pid": 100, "cmdline_lower": f"code.exe {folder.lower()}"},),
            window_titles=(
                (100, "[#38 code-review] Fix - mcp_coder - Visual Studio Code"),
            ),
        )

        signals = gather_signals(_session(folder), snapshot)

        assert signals.title_match is True
        assert signals.cmdline_match is True

    def test_restore_case_title_hit_cmdline_miss(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Restored window: title hit, no cmdline reference -> title authoritative."""
        folder = str(tmp_path)
        _force_windows(monkeypatch)
        _stub_pid_alive(monkeypatch, False)
        snapshot = _snapshot(
            processes=({"pid": 100, "cmdline_lower": "code.exe c:/some/other/folder"},),
            window_titles=(
                (100, "[#38 code-review] Fix - mcp_coder - Visual Studio Code"),
            ),
        )

        signals = gather_signals(_session(folder), snapshot)

        assert signals.title_match is True
        assert signals.cmdline_match is False

    def test_non_windows_no_title(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """HAS_WIN32GUI=False -> title_match False, falls to cmdline/pid."""
        folder = str(tmp_path)
        _force_windows(monkeypatch, enabled=False)
        _stub_pid_alive(monkeypatch, False)
        snapshot = _snapshot(
            processes=({"pid": 100, "cmdline_lower": f"code {folder.lower()}"},),
            window_titles=(
                (100, "[#38 code-review] Fix - mcp_coder - Visual Studio Code"),
            ),
        )

        signals = gather_signals(_session(folder), snapshot)

        assert signals.title_match is False
        assert signals.cmdline_match is True

    def test_title_wrong_issue_no_bind(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A window for a different issue number does not bind."""
        folder = str(tmp_path)
        _force_windows(monkeypatch)
        _stub_pid_alive(monkeypatch, False)
        snapshot = _snapshot(
            window_titles=(
                (100, "[#99 code-review] Other - mcp_coder - Visual Studio Code"),
            ),
        )

        signals = gather_signals(_session(folder, issue_number=38), snapshot)

        assert signals.title_match is False


class TestGatherSignalsIndependence:
    """R6: folder_exists and pid_alive are gathered independently."""

    def test_zombie_live_pid_for_missing_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing folder but a live stored PID -> pid_alive still computed."""
        folder = str(tmp_path / "gone")
        _force_windows(monkeypatch, enabled=False)
        _stub_pid_alive(monkeypatch, True)
        snapshot = _snapshot()

        signals = gather_signals(_session(folder, vscode_pid=4321), snapshot)

        assert signals.folder_exists is False
        assert signals.pid_alive is True

    def test_zombie_cmdline_for_missing_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing folder but a cmdline reference -> cmdline_match still computed."""
        folder = str(tmp_path / "gone")
        _force_windows(monkeypatch, enabled=False)
        _stub_pid_alive(monkeypatch, False)
        snapshot = _snapshot(
            processes=({"pid": 7, "cmdline_lower": f"code {folder.lower()}"},),
        )

        signals = gather_signals(_session(folder), snapshot)

        assert signals.folder_exists is False
        assert signals.cmdline_match is True
        assert signals.found_pid == 7


class TestGatherSignalsDirectoryEmpty:
    """directory_empty is a plain bool computed at the IO boundary."""

    def test_empty_existing_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Empty existing folder -> directory_empty True."""
        folder_path = tmp_path / "empty"
        folder_path.mkdir()
        _force_windows(monkeypatch, enabled=False)
        _stub_pid_alive(monkeypatch, False)

        signals = gather_signals(_session(str(folder_path)), _snapshot())

        assert signals.folder_exists is True
        assert signals.directory_empty is True

    def test_non_empty_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Non-empty folder -> directory_empty False."""
        folder_path = tmp_path / "work"
        folder_path.mkdir()
        (folder_path / "file.txt").write_text("x", encoding="utf-8")
        _force_windows(monkeypatch, enabled=False)
        _stub_pid_alive(monkeypatch, False)

        signals = gather_signals(_session(str(folder_path)), _snapshot())

        assert signals.folder_exists is True
        assert signals.directory_empty is False

    def test_missing_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Missing folder -> directory_empty False (folder doesn't exist)."""
        folder = str(tmp_path / "missing")
        _force_windows(monkeypatch, enabled=False)
        _stub_pid_alive(monkeypatch, False)

        signals = gather_signals(_session(folder), _snapshot())

        assert signals.folder_exists is False
        assert signals.directory_empty is False


class TestGatherSignalsGrace:
    """within_grace is a plain bool: age < LAUNCH_GRACE_SECONDS."""

    def test_within_grace_true(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A just-launched session is within grace."""
        folder = str(tmp_path)
        _force_windows(monkeypatch, enabled=False)
        _stub_pid_alive(monkeypatch, False)
        now = datetime.now(timezone.utc)
        session = _session(folder, started_at=(now - timedelta(seconds=5)).isoformat())

        signals = gather_signals(session, _snapshot(captured_at=now))

        assert signals.within_grace is True
        assert signals.age_seconds < 60.0

    def test_within_grace_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An old session is outside grace."""
        folder = str(tmp_path)
        _force_windows(monkeypatch, enabled=False)
        _stub_pid_alive(monkeypatch, False)
        now = datetime.now(timezone.utc)
        session = _session(
            folder, started_at=(now - timedelta(seconds=600)).isoformat()
        )

        signals = gather_signals(session, _snapshot(captured_at=now))

        assert signals.within_grace is False
        assert signals.age_seconds >= 60.0

    def test_unparseable_started_at_is_infinite_age(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A bad started_at yields infinite age and not within grace."""
        folder = str(tmp_path)
        _force_windows(monkeypatch, enabled=False)
        _stub_pid_alive(monkeypatch, False)
        session = _session(folder, started_at="not-a-date")

        signals = gather_signals(session, _snapshot())

        assert signals.within_grace is False
        assert signals.age_seconds == float("inf")


class TestCaptureDetectionSnapshot:
    """capture_detection_snapshot refreshes all three caches once and freezes."""

    def test_refreshes_each_cache_once_and_freezes(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Each refresher is called once; result holds frozen tuples/frozenset."""
        calls: list[str] = []

        def fake_processes(refresh: bool = False) -> list[dict[str, object]]:
            calls.append(f"processes:{refresh}")
            return [{"pid": 1, "cmdline_lower": "code.exe foo"}]

        def fake_titles(refresh: bool = False) -> list[tuple[int, str]]:
            calls.append(f"titles:{refresh}")
            return [(1, "[#38 x] foo")]

        def fake_pids() -> set[int]:
            calls.append("pids")
            return {1, 2}

        monkeypatch.setattr(f"{DETECTION}._get_vscode_processes", fake_processes)
        monkeypatch.setattr(f"{DETECTION}._get_vscode_window_titles", fake_titles)
        monkeypatch.setattr(f"{DETECTION}._get_vscode_pids", fake_pids)

        snapshot = capture_detection_snapshot()

        assert calls == ["processes:True", "titles:True", "pids"]
        assert isinstance(snapshot.processes, tuple)
        assert isinstance(snapshot.window_titles, tuple)
        assert isinstance(snapshot.pids, frozenset)
        assert snapshot.pids == frozenset({1, 2})
        assert snapshot.window_titles == ((1, "[#38 x] foo"),)
        assert isinstance(snapshot.captured_at, datetime)
