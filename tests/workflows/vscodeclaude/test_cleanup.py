"""Test cleanup functions for VSCode Claude."""

import json
import shutil
from pathlib import Path

import pytest

from mcp_coder.utils.folder_deletion import DeletionResult
from mcp_coder.utils.github_operations.issues import IssueData
from mcp_coder.workflows.vscodeclaude.cleanup import (
    cleanup_stale_sessions,
    delete_session_folder,
    get_stale_sessions,
)
from mcp_coder.workflows.vscodeclaude.types import VSCodeClaudeSession


class TestCleanup:
    """Test cleanup functions."""

    def test_get_stale_sessions_returns_stale(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns stale sessions with dirty status."""
        sessions_file = tmp_path / "sessions.json"
        # Patch at sessions module since load_sessions calls get_sessions_file_path there
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock VSCode not running - patch at cleanup where it's imported
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: False,
        )

        # Mock session is stale - patch at cleanup where it's imported
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s, cached_issues=None: True,
        )

        # Mock folder git status - patch at cleanup where it's imported
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Clean",
        )

        # Mock _get_configured_repos to return the test repo
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )

        stale_folder = tmp_path / "stale_folder"
        stale_folder.mkdir()

        session = {
            "folder": str(stale_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-01T00:00:00Z"}
        sessions_file.write_text(json.dumps(store))

        result = get_stale_sessions()

        assert len(result) == 1
        assert result[0][0]["folder"] == str(stale_folder)
        assert result[0][1] == "Clean"  # Git status is Clean

    def test_get_stale_sessions_skips_unconfigured_repos(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips sessions for repos not in config."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock VSCode not running
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: False,
        )

        # Mock _get_configured_repos to return a DIFFERENT repo
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/other_repo"},  # Different from session's repo
        )

        stale_folder = tmp_path / "stale_folder"
        stale_folder.mkdir()

        session = {
            "folder": str(stale_folder),
            "repo": "owner/unconfigured_repo",  # Not in configured repos
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-01T00:00:00Z"}
        sessions_file.write_text(json.dumps(store))

        result = get_stale_sessions()

        # Session should be skipped (not checked for staleness)
        assert len(result) == 0

    def test_get_stale_sessions_skips_running(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips sessions with running VSCode."""
        sessions_file = tmp_path / "sessions.json"
        # Patch at sessions module since load_sessions calls get_sessions_file_path there
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock VSCode running - patch at cleanup where it's imported
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: True,
        )

        session = {
            "folder": str(tmp_path / "folder"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-01T00:00:00Z"}
        sessions_file.write_text(json.dumps(store))

        result = get_stale_sessions()

        assert len(result) == 0

    def test_cleanup_stale_sessions_dry_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dry run reports but doesn't delete."""
        stale_session = {
            "folder": str(tmp_path / "stale_folder"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        # Create the folder
        (tmp_path / "stale_folder").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda cached_issues_by_repo=None: [
                (stale_session, "Clean")
            ],  # Clean status
        )

        result = cleanup_stale_sessions(dry_run=True)

        # Folder should still exist
        assert (tmp_path / "stale_folder").exists()
        # Dry run doesn't add to deleted list
        assert len(result.get("deleted", [])) == 0

    def test_cleanup_stale_sessions_skips_dirty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips dirty folders with warning."""
        dirty_session = {
            "folder": str(tmp_path / "dirty_folder"),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        (tmp_path / "dirty_folder").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda cached_issues_by_repo=None: [
                (dirty_session, "Dirty")
            ],  # Dirty status
        )

        result = cleanup_stale_sessions(dry_run=False)

        # Folder should still exist (dirty)
        assert (tmp_path / "dirty_folder").exists()
        assert str(tmp_path / "dirty_folder") in result.get("skipped", [])

    def test_cleanup_stale_sessions_deletes_clean(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Deletes clean stale folders."""
        clean_session = {
            "folder": str(tmp_path / "clean_folder"),
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        (tmp_path / "clean_folder").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda cached_issues_by_repo=None: [
                (clean_session, "Clean")
            ],  # Clean status
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.delete_session_folder",
            lambda s: True,
        )

        result = cleanup_stale_sessions(dry_run=False)

        assert str(tmp_path / "clean_folder") in result.get("deleted", [])

    def test_delete_session_folder_removes_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Deletes folder and removes session."""
        folder = tmp_path / "to_delete"
        folder.mkdir()
        (folder / "file.txt").write_text("test")

        # Create workspace file
        workspace_file = tmp_path / "to_delete.code-workspace"
        workspace_file.write_text("{}")

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
            lambda f: True,
        )

        result = delete_session_folder(session)

        assert result is True
        assert not folder.exists()
        assert not workspace_file.exists()

    def test_delete_session_folder_handles_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Handles already-deleted folder gracefully."""
        # Folder doesn't exist
        session: VSCodeClaudeSession = {
            "folder": str(tmp_path / "nonexistent"),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
            lambda f: True,
        )

        result = delete_session_folder(session)

        assert result is True  # Still succeeds - removes session from store

    def test_delete_session_folder_uses_safe_delete(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifies safe_delete_folder is called for folder deletion."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        safe_delete_called: list[Path] = []

        def mock_safe_delete(path: Path, **kwargs: object) -> DeletionResult:
            safe_delete_called.append(path)
            # Actually delete for the test
            if Path(path).exists():
                shutil.rmtree(path)
            return DeletionResult(success=True)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.safe_delete_folder",
            mock_safe_delete,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
            lambda f: True,
        )

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        result = delete_session_folder(session)

        assert result is True
        assert len(safe_delete_called) == 1
        assert safe_delete_called[0] == folder

    def test_cleanup_stale_sessions_empty(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Reports when no stale sessions."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda cached_issues_by_repo=None: [],
        )

        result = cleanup_stale_sessions(dry_run=True)

        assert result == {"deleted": [], "skipped": []}
        captured = capsys.readouterr()
        assert "No stale sessions" in captured.out

    def test_cleanup_handles_missing_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Removes session when folder is missing."""
        missing_session = {
            "folder": str(tmp_path / "missing_folder"),
            "repo": "owner/repo",
            "issue_number": 999,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        # Folder does NOT exist (don't create it)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda cached_issues_by_repo=None: [(missing_session, "Missing")],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
            lambda f: True,
        )

        result = cleanup_stale_sessions(dry_run=False)

        assert str(tmp_path / "missing_folder") in result.get("deleted", [])

    def test_cleanup_skips_no_git_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips folders without git with warning."""
        no_git_session = {
            "folder": str(tmp_path / "no_git_folder"),
            "repo": "owner/repo",
            "issue_number": 888,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        (tmp_path / "no_git_folder").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda cached_issues_by_repo=None: [(no_git_session, "No Git")],
        )

        result = cleanup_stale_sessions(dry_run=False)

        # Folder should still exist
        assert (tmp_path / "no_git_folder").exists()
        assert str(tmp_path / "no_git_folder") in result.get("skipped", [])

    def test_cleanup_skips_error_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Skips folders with git errors with warning."""
        error_session = {
            "folder": str(tmp_path / "error_folder"),
            "repo": "owner/repo",
            "issue_number": 777,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }

        (tmp_path / "error_folder").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda cached_issues_by_repo=None: [(error_session, "Error")],
        )

        result = cleanup_stale_sessions(dry_run=False)

        # Folder should still exist
        assert (tmp_path / "error_folder").exists()
        assert str(tmp_path / "error_folder") in result.get("skipped", [])


class TestGetStaleSessions:
    """Tests for get_stale_sessions function."""

    def test_includes_blocked_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include sessions with blocked label."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        mock_sessions = {
            "sessions": [
                {
                    "folder": str(tmp_path / "repo_123"),
                    "repo": "owner/repo",
                    "issue_number": 123,
                    "status": "status-01:created",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(mock_sessions))

        mock_issue: IssueData = {
            "number": 123,
            "title": "Test",
            "state": "open",
            "labels": ["status-01:created", "blocked"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        mock_cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {123: mock_issue}
        }

        # Create folder
        (tmp_path / "repo_123").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Clean",
        )
        # Mock is_session_stale to return False (not stale, only blocked)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s: False,
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        assert len(result) == 1
        session, git_status = result[0]
        assert session["issue_number"] == 123
        assert git_status == "Clean"

    def test_includes_wait_labeled_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include sessions with wait label."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        mock_sessions = {
            "sessions": [
                {
                    "folder": str(tmp_path / "repo_456"),
                    "repo": "owner/repo",
                    "issue_number": 456,
                    "status": "status-04:plan-review",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(mock_sessions))

        mock_issue: IssueData = {
            "number": 456,
            "title": "Test",
            "state": "open",
            "labels": ["status-04:plan-review", "wait"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        mock_cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {456: mock_issue}
        }

        (tmp_path / "repo_456").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Clean",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s: False,
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        assert len(result) == 1

    def test_case_insensitive_blocked_detection(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should detect BLOCKED label case-insensitively."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        mock_sessions = {
            "sessions": [
                {
                    "folder": str(tmp_path / "repo_789"),
                    "repo": "owner/repo",
                    "issue_number": 789,
                    "status": "status-01:created",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(mock_sessions))

        mock_issue: IssueData = {
            "number": 789,
            "title": "Test",
            "state": "open",
            "labels": ["status-01:created", "BLOCKED"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        mock_cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {789: mock_issue}
        }

        (tmp_path / "repo_789").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Clean",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s: False,
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        assert len(result) == 1

    def test_excludes_running_blocked_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should not include blocked sessions with running VSCode and existing artifacts."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        mock_sessions = {
            "sessions": [
                {
                    "folder": str(tmp_path / "repo_123"),
                    "repo": "owner/repo",
                    "issue_number": 123,
                    "status": "status-01:created",
                    "vscode_pid": 1234,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(mock_sessions))

        mock_issue: IssueData = {
            "number": 123,
            "title": "Test",
            "state": "open",
            "labels": ["status-01:created", "blocked"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        mock_cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {123: mock_issue}
        }

        # Create the folder so session artifacts exist — VSCode running WITH artifacts
        # is a healthy active session and should be skipped by cleanup.
        (tmp_path / "repo_123").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        assert len(result) == 0

    def test_includes_closed_issue_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include sessions for closed issues."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        mock_sessions = {
            "sessions": [
                {
                    "folder": str(tmp_path / "repo_closed"),
                    "repo": "owner/repo",
                    "issue_number": 100,
                    "status": "status-07:code-review",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(mock_sessions))

        # Issue is CLOSED (state="closed")
        mock_issue: IssueData = {
            "number": 100,
            "title": "Closed Issue",
            "state": "closed",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        mock_cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {100: mock_issue}
        }

        # Create folder
        (tmp_path / "repo_closed").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Clean",
        )
        # Mock is_session_stale to return False (not stale based on status change)
        # Session should still be included because issue is closed
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s: False,
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        assert len(result) == 1
        session, git_status = result[0]
        assert session["issue_number"] == 100
        assert git_status == "Clean"

    def test_includes_bot_pickup_status_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include sessions at bot_pickup status (02, 05, 08)."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        mock_sessions = {
            "sessions": [
                {
                    "folder": str(tmp_path / "repo_bot_pickup"),
                    "repo": "owner/repo",
                    "issue_number": 200,
                    "status": "status-02:awaiting-planning",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(mock_sessions))

        # Issue is OPEN but at bot_pickup status
        mock_issue: IssueData = {
            "number": 200,
            "title": "Bot Pickup Issue",
            "state": "open",
            "labels": ["status-02:awaiting-planning"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        mock_cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {200: mock_issue}
        }

        # Create folder
        (tmp_path / "repo_bot_pickup").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Clean",
        )
        # Mock is_session_stale to return False (not stale based on status change)
        # Session should still be included because status is not eligible
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s: False,
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        assert len(result) == 1
        session, git_status = result[0]
        assert session["issue_number"] == 200
        assert git_status == "Clean"

    def test_includes_bot_busy_status_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include sessions at bot_busy status (03, 06, 09)."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        mock_sessions = {
            "sessions": [
                {
                    "folder": str(tmp_path / "repo_bot_busy"),
                    "repo": "owner/repo",
                    "issue_number": 300,
                    "status": "status-03:planning",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(mock_sessions))

        # Issue is OPEN but at bot_busy status
        mock_issue: IssueData = {
            "number": 300,
            "title": "Bot Busy Issue",
            "state": "open",
            "labels": ["status-03:planning"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        mock_cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {300: mock_issue}
        }

        # Create folder
        (tmp_path / "repo_bot_busy").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Clean",
        )
        # Mock is_session_stale to return False (not stale based on status change)
        # Session should still be included because status is not eligible
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s: False,
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        assert len(result) == 1
        session, git_status = result[0]
        assert session["issue_number"] == 300
        assert git_status == "Clean"

    def test_includes_pr_created_status_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should include sessions at status-10:pr-created."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        mock_sessions = {
            "sessions": [
                {
                    "folder": str(tmp_path / "repo_pr_created"),
                    "repo": "owner/repo",
                    "issue_number": 400,
                    "status": "status-10:pr-created",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(mock_sessions))

        # Issue is OPEN but at pr-created status (no initial_command)
        mock_issue: IssueData = {
            "number": 400,
            "title": "PR Created Issue",
            "state": "open",
            "labels": ["status-10:pr-created"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        mock_cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {400: mock_issue}
        }

        # Create folder
        (tmp_path / "repo_pr_created").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Clean",
        )
        # Mock is_session_stale to return False (not stale based on status change)
        # Session should still be included because pr-created is not eligible
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s: False,
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        assert len(result) == 1
        session, git_status = result[0]
        assert session["issue_number"] == 400
        assert git_status == "Clean"

    def test_closed_issue_does_not_call_is_session_stale(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should NOT call is_session_stale for closed issues (short-circuit evaluation)."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        mock_sessions = {
            "sessions": [
                {
                    "folder": str(tmp_path / "repo_closed"),
                    "repo": "owner/repo",
                    "issue_number": 999,
                    "status": "status-07:code-review",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(mock_sessions))

        # Issue is CLOSED
        mock_issue: IssueData = {
            "number": 999,
            "title": "Closed Issue",
            "state": "closed",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        mock_cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {999: mock_issue}
        }

        # Create folder
        (tmp_path / "repo_closed").mkdir()

        # Track if is_session_stale is called
        stale_called: list[bool] = []

        def mock_is_session_stale(
            session: VSCodeClaudeSession,
            cached_issues: dict[int, IssueData] | None = None,
        ) -> bool:
            stale_called.append(True)
            return False

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Clean",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            mock_is_session_stale,
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        # Session should be included (closed issues are stale)
        assert len(result) == 1
        # But is_session_stale should NOT have been called (short-circuit)
        assert (
            len(stale_called) == 0
        ), "is_session_stale should not be called for closed issues"

    def test_does_not_skip_zombie_vscode_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should NOT skip a session when VSCode is running but all artifacts are gone.

        This is the zombie scenario: the folder and workspace file were deleted
        while VSCode was still open. The process is alive but not meaningful for
        this session, so cleanup should proceed.
        """
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        mock_sessions = {
            "sessions": [
                {
                    "folder": str(tmp_path / "repo_zombie"),  # folder NOT created
                    "repo": "owner/repo",
                    "issue_number": 123,
                    "status": "status-04:plan-review",
                    "vscode_pid": 9999,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(mock_sessions))

        # VSCode PID is "running" but artifacts are gone — is_session_active returns False
        # because session_has_artifacts() returns False (folder not created above).
        # No need to patch is_session_active: the real implementation handles this correctly.
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.check_vscode_running",
            lambda pid: True,  # PID alive (zombie)
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s, cached_issues=None: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Missing",
        )

        result = get_stale_sessions()

        # Zombie session must appear in stale list despite VSCode PID being alive
        assert len(result) == 1
        session, git_status = result[0]
        assert session["issue_number"] == 123
        assert git_status == "Missing"

    def test_excludes_eligible_status_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should NOT include sessions at eligible human_action statuses (01, 04, 07)."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        mock_sessions = {
            "sessions": [
                {
                    "folder": str(tmp_path / "repo_eligible"),
                    "repo": "owner/repo",
                    "issue_number": 500,
                    "status": "status-07:code-review",
                    "vscode_pid": None,
                    "started_at": "2024-01-01T00:00:00Z",
                    "is_intervention": False,
                }
            ],
            "last_updated": "",
        }
        sessions_file.write_text(json.dumps(mock_sessions))

        # Issue is OPEN at eligible status (not stale, not blocked)
        mock_issue: IssueData = {
            "number": 500,
            "title": "Eligible Issue",
            "state": "open",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "body": "",
            "locked": False,
        }
        mock_cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {500: mock_issue}
        }

        # Create folder
        (tmp_path / "repo_eligible").mkdir()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_active",
            lambda session: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_folder_git_status",
            lambda path: "Clean",
        )
        # Mock is_session_stale to return False (status matches, no change)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s, cached_issues=None: False,
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        # Session should NOT be included - it's eligible and should restart
        assert len(result) == 0
