import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflows.vscodeclaude.detection import (
    is_vscode_window_open_for_folder,
)
from mcp_coder.workflows.vscodeclaude.sessions import (
    is_session_active,
)
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession


class TestIsSessionActiveFallbackChain:
    """Tests for is_session_active() fallback chain behaviour.

    Within the launch-grace window, is_session_active() skips the title
    check and runs the PID -> cmdline fallback chain. These tests use a
    recent ``started_at`` to stay inside the grace window so the fallback
    paths are exercised on the Windows path.
    """

    def test_windows_title_miss_pid_alive_returns_active(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Within grace, PID alive -> active (title check skipped)."""
        recent = (datetime.now(UTC) - timedelta(seconds=5)).isoformat()
        folder = tmp_path / "mcp_coder_542"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 542,
            "status": "s",
            "vscode_pid": 28036,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": recent,
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: True,
        )

        with caplog.at_level(
            logging.DEBUG, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            result = is_session_active(session)

        assert result is True
        assert any(
            "active (PID 28036 alive)" in record.message for record in caplog.records
        )

    def test_windows_title_miss_cmdline_match_refreshes_pid(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Within grace, PID dead + cmdline match w/ new PID -> refresh + active."""
        recent = (datetime.now(UTC) - timedelta(seconds=5)).isoformat()
        folder = tmp_path / "mcp_coder_542"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 542,
            "status": "s",
            "vscode_pid": 28036,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": recent,
            "is_intervention": False,
        }

        update_mock = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            lambda f: (True, 54321),
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.update_session_pid",
            update_mock,
        )

        with caplog.at_level(
            logging.DEBUG, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            result = is_session_active(session)

        assert result is True
        update_mock.assert_called_once_with(str(folder), 54321)
        assert any(
            "active (cmdline match PID=54321)" in record.message
            for record in caplog.records
        )
        assert any(
            "refreshing stored PID 28036 -> 54321" in record.message
            for record in caplog.records
        )

    def test_windows_all_miss_returns_inactive(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Within grace, PID dead + cmdline miss -> inactive with INFO summary."""
        recent = (datetime.now(UTC) - timedelta(seconds=5)).isoformat()
        folder = tmp_path / "mcp_coder_542"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 542,
            "status": "s",
            "vscode_pid": 28036,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": recent,
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            lambda f: (False, None),
        )

        with caplog.at_level(
            logging.DEBUG, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            result = is_session_active(session)

        assert result is False
        assert any(
            "inactive (PID 28036 gone / no cmdline match)" in record.message
            for record in caplog.records
        )

    def test_non_windows_pid_alive_info_format(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """HAS_WIN32GUI=False + PID alive -> 'active (PID 1234 alive)' only."""
        folder = tmp_path / "mcp_coder_100"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 100,
            "status": "s",
            "vscode_pid": 1234,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: True,
        )

        with caplog.at_level(
            logging.DEBUG, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            result = is_session_active(session)

        assert result is True
        matching = [
            record
            for record in caplog.records
            if "active (PID 1234 alive)" in record.message
        ]
        assert matching, "Expected INFO line 'active (PID 1234 alive)'"
        assert "window-title" not in matching[0].message

    @pytest.mark.parametrize(
        "session_data",
        [
            {"issue_number": 100, "vscode_pid": 1234},
            {"repo": "owner/repo", "vscode_pid": 1234},
        ],
        ids=["missing_repo", "missing_issue_number"],
    )
    def test_guard_none_falls_through_to_pid_check(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        session_data: dict[str, object],
    ) -> None:
        """When repo or issue_number is None, falls through to PID check."""
        folder = tmp_path / "mcp_coder_session"
        folder.mkdir()

        session: dict[str, object] = {
            "folder": str(folder),
            "status": "s",
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
            **session_data,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: True,
        )

        result = is_session_active(session)  # type: ignore[arg-type]

        assert result is True

    def test_non_windows_uses_pid_fallback(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """HAS_WIN32GUI=False preserves existing PID-based behavior."""
        folder = tmp_path / "mcp_coder_100"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 100,
            "status": "s",
            "vscode_pid": 1234,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: True,
        )

        result = is_session_active(session)

        assert result is True

    def test_returns_false_on_non_windows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should return False when win32gui not available."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection.HAS_WIN32GUI",
            False,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="owner/mcp_coder",
        )

        assert result is False

    def test_requires_both_issue_and_repo_in_title(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should require BOTH issue number AND repo name in title."""
        # Window has issue number but wrong repo
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection._get_vscode_window_titles",
            lambda: [
                (100, "[#219 review] Title - different_repo - Visual Studio Code")
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection._get_vscode_processes",
            lambda: [
                {"pid": 100, "cmdline_lower": "code.exe /workspace/mcp_coder_219"}
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="owner/mcp_coder",
        )

        assert result is False

    def test_does_not_match_title_without_bracket_prefix(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should NOT match window where issue number appears without [ prefix.

        Regression test: GitHub extension can show e.g. '#219 - mcp_coder' in
        the window title when browsing an issue, which should NOT be treated as
        an active vscodeclaude workspace session.
        """
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection._get_vscode_window_titles",
            lambda: [(100, "#219 Fix the thing - mcp_coder - Visual Studio Code")],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection._get_vscode_processes",
            lambda: [
                {"pid": 100, "cmdline_lower": "code.exe /workspace/mcp_coder_219"}
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.detection.HAS_WIN32GUI",
            True,
        )

        result = is_vscode_window_open_for_folder(
            folder_path="/workspace/mcp_coder_219",
            issue_number=219,
            repo="owner/mcp_coder",
        )

        assert result is False
