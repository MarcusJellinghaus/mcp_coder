import json
from pathlib import Path
from typing import Any

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.vscodeclaude.session_restart import (
    BranchPrepResult,
    restart_closed_sessions,
)
from mcp_coder.workflows.vscodeclaude.sessions import load_sessions
from mcp_coder.workflows.vscodeclaude.types import SessionAction
from tests.github_factories import make_issue_data
from tests.workflows.vscodeclaude.conftest import make_assessment


class TestRestartClosedSessionsLifecycle:
    """Tests for orphan, liveness and relaunch handling in restart_closed_sessions()."""

    def test_restart_closed_sessions_removes_orphans(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Removes sessions with missing folders."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Create session with non-existent folder
        folder = str(tmp_path / "nonexistent")
        session = {
            "folder": folder,
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        restarted = restart_closed_sessions(
            assessments={
                folder: make_assessment(folder, action=SessionAction.REMOVE_MISSING)
            }
        )

        # No sessions restarted
        assert restarted == []

        # Session should be removed
        loaded = load_sessions()
        assert len(loaded["sessions"]) == 0

    def test_restart_closed_sessions_skips_unconfigured_repos(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips sessions for repos not in config file."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock _get_configured_repos to return a different repo (not owner/unconfigured)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/configured_repo"},  # Different from session's repo
        )

        # Create working folder (so it passes the folder exists check)
        working_folder = tmp_path / "unconfigured_123"
        working_folder.mkdir()

        # Create session for an unconfigured repo
        session = {
            "folder": str(working_folder),
            "repo": "owner/unconfigured",  # Not in configured_repos
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        restarted = restart_closed_sessions(
            assessments={str(working_folder): make_assessment(str(working_folder))}
        )

        # No sessions restarted because repo not in config
        assert restarted == []

        # Session should still exist (not removed, just skipped)
        loaded = load_sessions()
        assert len(loaded["sessions"]) == 1

    def test_restart_closed_sessions_relaunches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Relaunches VSCode for valid sessions."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock _get_configured_repos to return the test repo
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Mock regenerate_session_files to avoid issue fetching
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.regenerate_session_files",
            lambda session, issue: tmp_path / "script.bat",
        )

        # Mock _prepare_restart_branch to avoid git operations
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._prepare_restart_branch",
            lambda *args, **kwargs: BranchPrepResult(True, None, None),
        )

        # Create working folder and workspace file
        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_123.code-workspace"
        workspace_file.write_text("{}")

        # Mock launch_vscode
        new_pid = 9999
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.launch_vscode",
            lambda *_args: new_pid,
        )

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Provide cached issues to avoid API calls
        cached_issue = make_issue_data(
            number=123,
            title="Test",
            labels=["status-07:code-review"],
            url="",
        )
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {123: cached_issue}
        }

        restarted = restart_closed_sessions(
            assessments={str(working_folder): make_assessment(str(working_folder))},
            cached_issues_by_repo=cached_issues,
        )

        assert len(restarted) == 1
        assert restarted[0]["vscode_pid"] == new_pid

        # PID should be updated in store
        loaded = load_sessions()
        assert loaded["sessions"][0]["vscode_pid"] == new_pid

    def test_restart_closed_sessions_skips_running(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips sessions with running VSCode."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        folder = str(tmp_path / "existing")
        session = {
            "folder": folder,
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        restarted = restart_closed_sessions(
            assessments={folder: make_assessment(folder, active=True)}
        )

        # No sessions restarted since vscode is running
        assert restarted == []

    def test_restart_closed_sessions_skips_zombie(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: Any
    ) -> None:
        """Zombie (process alive, folder gone) is kept tracked, warned, not restarted."""
        import logging

        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        folder = str(tmp_path / "zombie")
        session = {
            "folder": folder,
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        with caplog.at_level(logging.WARNING):
            restarted = restart_closed_sessions(
                assessments={
                    folder: make_assessment(
                        folder,
                        active=True,
                        action=SessionAction.INVESTIGATE_ZOMBIE,
                    )
                }
            )

        # Not restarted, warning logged, session retained.
        assert restarted == []
        assert "Zombie session for issue #123" in caplog.text
        loaded = load_sessions()
        assert len(loaded["sessions"]) == 1
