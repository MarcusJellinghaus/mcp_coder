import json
import logging
from pathlib import Path

import pytest

from mcp_coder.workflows.vscodeclaude.sessions import (
    get_session_for_issue,
    warn_orphan_folders,
)


class TestGetSessionForIssueSoftDelete:
    """Tests for get_session_for_issue with .to_be_deleted exclusion."""

    def test_excludes_soft_deleted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Session found in JSON but folder in .to_be_deleted -> returns None."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        folder_name = "repo_42"

        session = {
            "folder": str(workspace_base / folder_name),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Mark folder as soft-deleted
        (workspace_base / ".to_be_deleted").write_text(folder_name + "\n")

        found = get_session_for_issue("owner/repo", 42, str(workspace_base))
        assert found is None

    def test_returns_non_deleted(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Session found, folder not in .to_be_deleted -> returns session."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        folder_name = "repo_42"

        session = {
            "folder": str(workspace_base / folder_name),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # No .to_be_deleted file
        found = get_session_for_issue("owner/repo", 42, str(workspace_base))
        assert found is not None
        assert found["issue_number"] == 42  # pylint: disable=unsubscriptable-object

    def test_multiple_active_returns_none(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Two sessions for same issue, neither deleted -> log error, return None."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()

        session1 = {
            "folder": str(workspace_base / "repo_42"),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        session2 = {
            "folder": str(workspace_base / "repo_42-folder1"),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-04:plan-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T11:30:00Z",
            "is_intervention": False,
        }
        store = {
            "sessions": [session1, session2],
            "last_updated": "2024-01-22T10:30:00Z",
        }
        sessions_file.write_text(json.dumps(store))

        with caplog.at_level(
            logging.ERROR, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            found = get_session_for_issue("owner/repo", 42, str(workspace_base))

        assert found is None
        assert any(
            "Multiple active folders" in record.message for record in caplog.records
        )


class TestWarnOrphanFolders:
    """Tests for warn_orphan_folders function."""

    def test_logs_warning_for_untracked(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Folder on disk not in sessions.json or .to_be_deleted -> warning logged."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        # Create orphan folder matching pattern
        (workspace_base / "repo_42").mkdir()

        with caplog.at_level(
            logging.WARNING, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            warn_orphan_folders(
                str(workspace_base),
                "owner/repo",
                42,
                session_folders=set(),
                to_be_deleted=set(),
            )

        assert any(
            "Orphan folder detected" in record.message for record in caplog.records
        )

    def test_ignores_tracked_sessions(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Folder on disk in sessions.json -> no warning."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        folder_name = "repo_42"
        (workspace_base / folder_name).mkdir()

        session = {
            "folder": str(workspace_base / folder_name),
            "repo": "owner/repo",
            "issue_number": 42,
            "status": "status-07:code-review",
            "vscode_pid": None,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        with caplog.at_level(
            logging.WARNING, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            warn_orphan_folders(
                str(workspace_base),
                "owner/repo",
                42,
                session_folders={folder_name},
                to_be_deleted=set(),
            )

        assert not any(
            "Orphan folder detected" in record.message for record in caplog.records
        )

    def test_ignores_to_be_deleted(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Folder on disk in .to_be_deleted -> no warning."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        folder_name = "repo_42"
        (workspace_base / folder_name).mkdir()
        (workspace_base / ".to_be_deleted").write_text(folder_name + "\n")

        with caplog.at_level(
            logging.WARNING, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            warn_orphan_folders(
                str(workspace_base),
                "owner/repo",
                42,
                session_folders=set(),
                to_be_deleted={folder_name},
            )

        assert not any(
            "Orphan folder detected" in record.message for record in caplog.records
        )

    def test_ignores_unrelated_folders(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Folder on disk not matching pattern -> no warning."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        store = {"sessions": [], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        workspace_base = tmp_path / "workspace"
        workspace_base.mkdir()
        # Create folder that does NOT match the pattern for issue 42
        (workspace_base / "other_project").mkdir()
        (workspace_base / "repo_99").mkdir()

        with caplog.at_level(
            logging.WARNING, logger="mcp_coder.workflows.vscodeclaude.sessions"
        ):
            warn_orphan_folders(
                str(workspace_base),
                "owner/repo",
                42,
                session_folders=set(),
                to_be_deleted=set(),
            )

        assert not any(
            "Orphan folder detected" in record.message for record in caplog.records
        )
