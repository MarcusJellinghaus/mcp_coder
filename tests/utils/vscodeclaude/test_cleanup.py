"""Test cleanup functions for VSCode Claude."""

import json
from pathlib import Path

import pytest

from mcp_coder.utils.vscodeclaude.cleanup import (
    cleanup_stale_sessions,
    delete_session_folder,
    get_stale_sessions,
)
from mcp_coder.utils.vscodeclaude.types import VSCodeClaudeSession


class TestCleanup:
    """Test cleanup functions."""

    def test_get_stale_sessions_returns_stale(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Returns stale sessions with dirty status."""
        sessions_file = tmp_path / "sessions.json"
        # Patch at sessions module since load_sessions calls get_sessions_file_path there
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock VSCode not running - patch at cleanup where it's imported
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: False,
        )

        # Mock session is stale - patch at cleanup where it's imported
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.cleanup.is_session_stale",
            lambda s: True,
        )

        # Mock folder not dirty - patch at cleanup where it's imported
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.cleanup.check_folder_dirty",
            lambda path: False,
        )

        # Mock _get_configured_repos to return the test repo
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.cleanup._get_configured_repos",
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
            "mcp_coder.utils.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock VSCode not running
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.cleanup.check_vscode_running",
            lambda pid: False,
        )

        # Mock _get_configured_repos to return a DIFFERENT repo
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.cleanup._get_configured_repos",
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
            "mcp_coder.utils.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        # Mock VSCode running - patch at cleanup where it's imported
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.cleanup.check_vscode_running",
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
            "mcp_coder.utils.vscodeclaude.cleanup.get_stale_sessions",
            lambda: [(stale_session, False)],  # Not dirty
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
            "mcp_coder.utils.vscodeclaude.cleanup.get_stale_sessions",
            lambda: [(dirty_session, True)],  # Dirty
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
            "mcp_coder.utils.vscodeclaude.cleanup.get_stale_sessions",
            lambda: [(clean_session, False)],  # Clean
        )
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.cleanup.delete_session_folder",
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
            "mcp_coder.utils.vscodeclaude.cleanup.remove_session",
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
            "mcp_coder.utils.vscodeclaude.cleanup.remove_session",
            lambda f: True,
        )

        result = delete_session_folder(session)

        assert result is True  # Still succeeds - removes session from store

    def test_cleanup_stale_sessions_empty(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Reports when no stale sessions."""
        monkeypatch.setattr(
            "mcp_coder.utils.vscodeclaude.cleanup.get_stale_sessions",
            lambda: [],
        )

        result = cleanup_stale_sessions(dry_run=True)

        assert result == {"deleted": [], "skipped": []}
        captured = capsys.readouterr()
        assert "No stale sessions" in captured.out
