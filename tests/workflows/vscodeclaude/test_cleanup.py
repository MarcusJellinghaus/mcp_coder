"""Test cleanup functions for VSCode Claude."""

import json
import shutil
from pathlib import Path

import pytest

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
            "mcp_coder.workflows.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: False,
        )

        # Mock session is stale - patch at cleanup where it's imported
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s: True,
        )

        # Mock folder not dirty - patch at cleanup where it's imported
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.check_folder_dirty",
            lambda path: False,
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
        assert result[0][1] is False  # Not dirty

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
            "mcp_coder.workflows.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: False,
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
            "mcp_coder.workflows.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: True,
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
            lambda cached_issues_by_repo=None: [(stale_session, False)],  # Not dirty
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
            lambda cached_issues_by_repo=None: [(dirty_session, True)],  # Dirty
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
            lambda cached_issues_by_repo=None: [(clean_session, False)],  # Clean
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

        def mock_safe_delete(path: Path, **kwargs: object) -> bool:
            safe_delete_called.append(path)
            # Actually delete for the test
            if Path(path).exists():
                shutil.rmtree(path)
            return True

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
            "mcp_coder.workflows.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.check_folder_dirty",
            lambda path: False,
        )
        # Mock is_session_stale to return False (not stale, only blocked)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.is_session_stale",
            lambda s: False,
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        assert len(result) == 1
        session, is_dirty = result[0]
        assert session["issue_number"] == 123

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
            "mcp_coder.workflows.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.check_folder_dirty",
            lambda path: False,
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
            "mcp_coder.workflows.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: False,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.check_folder_dirty",
            lambda path: False,
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
        """Should not include blocked sessions with running VSCode."""
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

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: True,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup._get_configured_repos",
            lambda: {"owner/repo"},
        )

        result = get_stale_sessions(cached_issues_by_repo=mock_cached_issues)

        assert len(result) == 0
