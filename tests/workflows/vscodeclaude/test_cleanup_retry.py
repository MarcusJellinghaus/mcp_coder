import shutil
from pathlib import Path

import pytest

from mcp_coder.utils.folder_deletion import DeletionResult
from mcp_coder.workflows.vscodeclaude.cleanup import (
    cleanup_stale_sessions,
    delete_session_folder,
)
from mcp_coder.workflows.vscodeclaude.types import SessionAction
from tests.workflows.vscodeclaude.test_cleanup import (
    _assessment,
    _patch_sessions_file,
    _session,
)


class TestSoftDeleteAndRetry:
    """Lock-failure veto and the assessment-driven ``.to_be_deleted`` retry loop."""

    def test_cleanup_retries_to_be_deleted_entries(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Retry-deletes a queued folder with no assessment, removes entry on success."""
        from mcp_coder.workflows.vscodeclaude.helpers import (
            TO_BE_DELETED_FILENAME,
            load_to_be_deleted,
        )

        folder = tmp_path / "old-session"
        folder.mkdir()
        (folder / "somefile.txt").write_text("data")
        (tmp_path / TO_BE_DELETED_FILENAME).write_text("old-session\n")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.safe_delete_folder",
            lambda path: DeletionResult(success=True),
        )

        result = cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=False
        )

        assert load_to_be_deleted(str(tmp_path)) == set()
        assert result == {"deleted": [], "skipped": []}

    def test_cleanup_retry_removes_stale_entry_if_folder_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Drops a ``.to_be_deleted`` entry when no assessment + folder is gone."""
        from mcp_coder.workflows.vscodeclaude.helpers import (
            TO_BE_DELETED_FILENAME,
            load_to_be_deleted,
        )

        (tmp_path / TO_BE_DELETED_FILENAME).write_text("gone-session\n")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [],
        )

        cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=False
        )

        assert load_to_be_deleted(str(tmp_path)) == set()

    def test_cleanup_retry_skipped_in_dry_run(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No retry when dry_run=True."""
        from mcp_coder.workflows.vscodeclaude.helpers import (
            TO_BE_DELETED_FILENAME,
            load_to_be_deleted,
        )

        folder = tmp_path / "pending-session"
        folder.mkdir()
        (tmp_path / TO_BE_DELETED_FILENAME).write_text("pending-session\n")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [],
        )

        cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=True
        )

        assert load_to_be_deleted(str(tmp_path)) == {"pending-session"}

    def test_cleanup_retry_spares_live_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A queued folder whose assessment is active is spared and left queued.

        Title hit / cmdline miss: the assessment is ``verdict.active`` even though
        the cmdline-only check would have missed. safe_delete_folder is never
        invoked and the entry stays in the queue (closes the second #38 door).
        """
        from mcp_coder.workflows.vscodeclaude.helpers import (
            TO_BE_DELETED_FILENAME,
            load_to_be_deleted,
        )

        folder_name = "live-session"
        folder = tmp_path / folder_name
        folder.mkdir()
        (tmp_path / TO_BE_DELETED_FILENAME).write_text(f"{folder_name}\n")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [],
        )

        safe_delete_calls: list[Path] = []

        def mock_safe_delete(path: Path) -> DeletionResult:
            safe_delete_calls.append(path)
            return DeletionResult(success=True)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.safe_delete_folder",
            mock_safe_delete,
        )

        assessments = {
            str(folder): _assessment(
                folder, active=True, action=SessionAction.KEEP_ACTIVE, reason="active"
            )
        }
        cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments=assessments, dry_run=False
        )

        # Live folder spared: never deleted, entry stays queued.
        assert safe_delete_calls == []
        assert folder.exists()
        assert load_to_be_deleted(str(tmp_path)) == {folder_name}

    def test_cleanup_retry_inactive_assessment_retries_delete(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Inactive assessment + folder present -> retry safe_delete_folder."""
        from mcp_coder.workflows.vscodeclaude.helpers import (
            TO_BE_DELETED_FILENAME,
            load_to_be_deleted,
        )

        folder_name = "dead-session"
        folder = tmp_path / folder_name
        folder.mkdir()
        (tmp_path / TO_BE_DELETED_FILENAME).write_text(f"{folder_name}\n")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [],
        )

        safe_delete_calls: list[Path] = []

        def mock_safe_delete(path: Path) -> DeletionResult:
            safe_delete_calls.append(path)
            shutil.rmtree(path)
            return DeletionResult(success=True)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.safe_delete_folder",
            mock_safe_delete,
        )

        assessments = {str(folder): _assessment(folder, action=SessionAction.DELETE)}
        cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments=assessments, dry_run=False
        )

        assert safe_delete_calls == [folder]
        assert load_to_be_deleted(str(tmp_path)) == set()

    def test_delete_session_folder_lock_veto(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Locked clean folder, dead session: workspace retained, session tracked.

        Failed delete -> entry queued in ``.to_be_deleted``, the workspace file is
        NOT unlinked, ``remove_session`` is NEVER called, returns False.
        """
        from mcp_coder.workflows.vscodeclaude.helpers import load_to_be_deleted

        folder = tmp_path / "locked-session"
        folder.mkdir()
        workspace_file = tmp_path / "locked-session.code-workspace"
        workspace_file.write_text("{}")

        session = _session(folder, issue_number=42)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.safe_delete_folder",
            lambda path: DeletionResult(success=False),
        )

        removed_sessions: list[str] = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
            removed_sessions.append,
        )

        result = delete_session_folder(session, workspace_base=str(tmp_path))

        assert result is False
        # Lock veto: workspace file retained.
        assert workspace_file.exists()
        # Entry queued for retry.
        assert "locked-session" in load_to_be_deleted(str(tmp_path))
        # Session stays tracked.
        assert removed_sessions == []

    def test_delete_session_folder_workspace_only_after_folder_gone(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Workspace file removed only AFTER successful folder deletion."""
        folder = tmp_path / "session-ws"
        folder.mkdir()
        workspace_file = tmp_path / "session-ws.code-workspace"
        workspace_file.write_text("{}")

        session = _session(folder, issue_number=44)

        def mock_safe_delete(path: Path) -> DeletionResult:
            shutil.rmtree(path)
            return DeletionResult(success=True)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.safe_delete_folder",
            mock_safe_delete,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
            lambda f: None,
        )

        result = delete_session_folder(session, workspace_base=str(tmp_path))

        assert result is True
        assert not folder.exists()
        assert not workspace_file.exists()

    def test_delete_session_folder_handles_workspace_file_deletion_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Workspace file unlink raises OSError after folder deletion -> still True."""
        folder = tmp_path / "session-oserr"
        folder.mkdir()
        workspace_file = tmp_path / "session-oserr.code-workspace"
        workspace_file.write_text("{}")

        session = _session(folder, issue_number=45)

        original_unlink = Path.unlink

        def mock_unlink(self_path: Path, missing_ok: bool = False) -> None:
            if self_path == workspace_file:
                raise OSError("Permission denied")
            original_unlink(self_path, missing_ok=missing_ok)

        monkeypatch.setattr(Path, "unlink", mock_unlink)

        def mock_safe_delete(path: Path) -> DeletionResult:
            shutil.rmtree(path)
            return DeletionResult(success=True)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.safe_delete_folder",
            mock_safe_delete,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
            lambda f: None,
        )

        result = delete_session_folder(session, workspace_base=str(tmp_path))

        assert result is True
        assert not folder.exists()

    def test_cleanup_soft_delete_then_retry_succeeds(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """First pass: delete fails -> entry queued. Second pass: retry succeeds."""
        from mcp_coder.workflows.vscodeclaude.helpers import load_to_be_deleted

        sessions_file = tmp_path / "sessions.json"
        folder = tmp_path / "retry-session"
        folder.mkdir()
        (folder / "file.txt").write_text("content")
        session = _session(folder, issue_number=50)
        _patch_sessions_file(monkeypatch, sessions_file, [session])

        call_count = 0

        def fail_then_succeed(path: Path) -> DeletionResult:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return DeletionResult(success=False)
            shutil.rmtree(path)
            return DeletionResult(success=True)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.safe_delete_folder",
            fail_then_succeed,
        )

        # First pass: a stale DELETE session whose folder deletion fails.
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [
                (session, _assessment(folder, action=SessionAction.DELETE))
            ],
        )

        cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=False
        )

        assert "retry-session" in load_to_be_deleted(str(tmp_path))

        # Second pass: no new stale sessions; retry loop picks up the entry.
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [],
        )
        folder.mkdir(exist_ok=True)
        (folder / "file.txt").write_text("content")

        cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=False
        )

        assert load_to_be_deleted(str(tmp_path)) == set()
        assert not folder.exists()
