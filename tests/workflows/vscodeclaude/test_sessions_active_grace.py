from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.sessions import is_session_active
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession


class TestLaunchGrace:
    """Tests for launch-grace handling in is_session_active().

    For sessions older than LAUNCH_GRACE_SECONDS, a negative window-title
    match is authoritative and short-circuits the PID/cmdline fallback.
    Within the grace window, the title check is skipped to cover VSCode
    cold-start and extension reinstall delays.
    """

    @staticmethod
    def _started_at(seconds_ago: float) -> str:
        return (datetime.now(UTC) - timedelta(seconds=seconds_ago)).isoformat()

    def test_established_no_title_returns_false_no_fallback(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Age >= grace + title miss -> False, even when PID/cmdline would match."""
        folder = tmp_path / "mcp_coder_700"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 700,
            "status": "s",
            "vscode_pid": 12345,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": self._started_at(120.0),
            "is_intervention": False,
        }

        check_pid_calls: list[int | None] = []
        cmdline_calls: list[str] = []

        def mock_check(pid: int | None, expected_create_time: float | None) -> bool:
            check_pid_calls.append(pid)
            return True

        def mock_open_for_folder(folder_path: str) -> tuple[bool, int | None]:
            cmdline_calls.append(folder_path)
            return True, 99999

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_window_open_for_folder",
            lambda folder_path, issue_number=None, repo=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            mock_check,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            mock_open_for_folder,
        )

        result = is_session_active(session)

        assert result is False
        assert check_pid_calls == [], "PID fallback must not run beyond grace"
        assert cmdline_calls == [], "cmdline fallback must not run beyond grace"

    def test_grace_no_title_cmdline_match_returns_true(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Age < grace + title miss + cmdline match -> True (fallback engaged)."""
        folder = tmp_path / "mcp_coder_701"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 701,
            "status": "s",
            "vscode_pid": 12345,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": self._started_at(10.0),
            "is_intervention": False,
        }

        title_calls: list[int] = []

        def mock_title(
            folder_path: str, issue_number: int | None = None, repo: str | None = None
        ) -> bool:
            title_calls.append(issue_number or 0)
            return False

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_window_open_for_folder",
            mock_title,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            lambda f: (True, 12345),
        )

        result = is_session_active(session)

        assert result is True
        assert title_calls == [], "title check must be skipped within grace"

    def test_established_title_match_returns_true(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Age >= grace + title hit -> True without consulting fallback."""
        folder = tmp_path / "mcp_coder_702"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 702,
            "status": "s",
            "vscode_pid": 12345,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": self._started_at(120.0),
            "is_intervention": False,
        }

        check_pid_calls: list[int | None] = []

        def mock_check(pid: int | None, expected_create_time: float | None) -> bool:
            check_pid_calls.append(pid)
            return True

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_window_open_for_folder",
            lambda folder_path, issue_number=None, repo=None: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            mock_check,
        )

        result = is_session_active(session)

        assert result is True
        assert check_pid_calls == [], "PID fallback must not run on title match"

    def test_malformed_started_at_treated_as_established(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Unparseable started_at -> age=inf -> established branch (title authoritative)."""
        folder = tmp_path / "mcp_coder_703"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 703,
            "status": "s",
            "vscode_pid": 12345,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "not-a-date",
            "is_intervention": False,
        }

        check_pid_calls: list[int | None] = []

        def mock_check(pid: int | None, expected_create_time: float | None) -> bool:
            check_pid_calls.append(pid)
            return True

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", True
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_window_open_for_folder",
            lambda folder_path, issue_number=None, repo=None: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            mock_check,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_open_for_folder",
            lambda f: (True, 12345),
        )

        result = is_session_active(session)

        assert result is False
        assert check_pid_calls == [], "fallback must not run when title authoritative"

    def test_non_windows_path_unaffected_by_age(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """HAS_WIN32GUI=False: fallback chain runs regardless of session age."""
        folder = tmp_path / "mcp_coder_704"
        folder.mkdir()

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 704,
            "status": "s",
            "vscode_pid": 12345,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": self._started_at(120.0),
            "is_intervention": False,
        }

        title_calls: list[int] = []

        def mock_title(
            folder_path: str, issue_number: int | None = None, repo: str | None = None
        ) -> bool:
            title_calls.append(issue_number or 0)
            return False

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.HAS_WIN32GUI", False
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.session_has_artifacts",
            lambda f: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.is_vscode_window_open_for_folder",
            mock_title,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid, expected_create_time: True,
        )

        result = is_session_active(session)

        assert result is True
        assert title_calls == [], "title check must be skipped on non-Windows"
