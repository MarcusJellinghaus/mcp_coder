"""Test cleanup functions for VSCode Claude.

Cleanup is an assessment consumer: ``get_stale_sessions``,
``cleanup_stale_sessions`` and ``delete_session_folder`` read a prebuilt
:class:`SessionAssessment` map (built once per run by ``build_assessments``).
The eligibility / git-status safety matrix is decided upstream in
``assess_session`` and covered by ``test_assessment.py``; these tests cover the
consumer behaviour: action dispatch, deletion ordering, the lock-failure veto,
and the ``.to_be_deleted`` retry loop.
"""

import json
import logging
import shutil
from pathlib import Path

import pytest

from mcp_coder.utils.folder_deletion import DeletionResult
from mcp_coder.workflows.vscodeclaude.cleanup import (
    cleanup_stale_sessions,
    delete_session_folder,
    get_stale_sessions,
)
from mcp_coder.workflows.vscodeclaude.types import (
    Decision,
    DetectionSignals,
    IssueState,
    LivenessRule,
    LivenessVerdict,
    SessionAction,
    SessionAssessment,
    Transition,
    VSCodeClaudeSession,
)


def _session(folder: Path | str, *, issue_number: int = 123) -> VSCodeClaudeSession:
    """Build a minimal session dict pointing at ``folder``."""
    return {
        "folder": str(folder),
        "repo": "owner/repo",
        "issue_number": issue_number,
        "status": "status-07:code-review",
        "vscode_pid": None,
        "vscode_pid_create_time": None,
        "last_active": None,
        "last_active_rule": None,
        "started_at": "2024-01-01T00:00:00Z",
        "is_intervention": False,
    }


def _assessment(
    folder: Path | str,
    *,
    active: bool = False,
    action: SessionAction = SessionAction.DELETE,
    reason: str = "stale",
) -> SessionAssessment:
    """Build a minimal :class:`SessionAssessment` for cleanup consumer tests.

    Cleanup only reads ``verdict.active`` and ``decision.{action,reason}``; the
    remaining typed sub-results are filled with neutral defaults.
    """
    signals = DetectionSignals(
        folder_exists=True,
        title_match=active,
        cmdline_match=False,
        pid_alive=False,
        found_pid=None,
        age_seconds=0.0,
        within_grace=False,
        directory_empty=False,
    )
    rule = LivenessRule.TITLE if active else LivenessRule.NO_MATCH
    return SessionAssessment(
        folder=str(folder),
        signals=signals,
        verdict=LivenessVerdict(active=active, rule=rule),
        issue_state=IssueState(
            is_open=True,
            is_stale=False,
            is_blocked=False,
            is_unassigned=False,
            is_eligible=False,
        ),
        transition=Transition(flipped_to_inactive=False),
        decision=Decision(
            action=action,
            reason=reason,
            destructive=action == SessionAction.DELETE,
        ),
        pid_needs_refresh=False,
        found_pid=None,
    )


def _patch_sessions_file(
    monkeypatch: pytest.MonkeyPatch,
    sessions_file: Path,
    sessions: list[VSCodeClaudeSession],
) -> None:
    """Point ``load_sessions`` at ``sessions_file`` seeded with ``sessions``."""
    monkeypatch.setattr(
        "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
        lambda: sessions_file,
    )
    sessions_file.write_text(
        json.dumps({"sessions": sessions, "last_updated": "2024-01-01T00:00:00Z"})
    )


class TestCleanup:
    """Test cleanup_stale_sessions action dispatch and delete_session_folder."""

    def test_cleanup_stale_sessions_dry_run(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Dry run reports a DELETE but doesn't delete."""
        folder = tmp_path / "stale_folder"
        folder.mkdir()
        session = _session(folder)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [
                (session, _assessment(folder, action=SessionAction.DELETE))
            ],
        )

        result = cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=True
        )

        assert folder.exists()
        assert result.get("deleted", []) == []
        assert "Add --cleanup to delete" in capsys.readouterr().out

    def test_cleanup_stale_sessions_skips_dirty(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SKIP action keeps the folder and reports it as skipped."""
        folder = tmp_path / "dirty_folder"
        folder.mkdir()
        session = _session(folder, issue_number=456)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [
                (
                    session,
                    _assessment(folder, action=SessionAction.SKIP, reason="dirty"),
                )
            ],
        )

        result = cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=False
        )

        assert folder.exists()
        assert str(folder) in result.get("skipped", [])

    def test_cleanup_stale_sessions_deletes_clean(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DELETE action deletes via delete_session_folder."""
        folder = tmp_path / "clean_folder"
        folder.mkdir()
        session = _session(folder, issue_number=789)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [
                (session, _assessment(folder, action=SessionAction.DELETE))
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.delete_session_folder",
            lambda s, workspace_base="": True,
        )

        result = cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=False
        )

        assert str(folder) in result.get("deleted", [])

    def test_delete_session_folder_removes_folder_then_workspace(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """DELETE removes folder, then workspace file, then session record."""
        folder = tmp_path / "to_delete"
        folder.mkdir()
        (folder / "file.txt").write_text("test")
        workspace_file = tmp_path / "to_delete.code-workspace"
        workspace_file.write_text("{}")

        session = _session(folder)
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
            lambda f: True,
        )

        result = delete_session_folder(session, workspace_base=str(tmp_path))

        assert result is True
        assert not folder.exists()
        assert not workspace_file.exists()

    def test_delete_session_folder_handles_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Handles already-deleted folder gracefully (removes session record)."""
        session = _session(tmp_path / "nonexistent")
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
            lambda f: True,
        )

        result = delete_session_folder(session, workspace_base=str(tmp_path))

        assert result is True

    def test_delete_session_folder_uses_safe_delete(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verifies safe_delete_folder is called for folder deletion."""
        folder = tmp_path / "test_folder"
        folder.mkdir()

        safe_delete_called: list[Path] = []

        def mock_safe_delete(path: Path, **kwargs: object) -> DeletionResult:
            safe_delete_called.append(path)
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

        session = _session(folder)
        result = delete_session_folder(session, workspace_base=str(tmp_path))

        assert result is True
        assert safe_delete_called == [folder]

    def test_cleanup_stale_sessions_empty(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Reports when no stale sessions."""
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [],
        )

        result = cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=True
        )

        assert result == {"deleted": [], "skipped": []}
        assert "No stale sessions" in capsys.readouterr().out

    def test_cleanup_handles_missing_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """REMOVE_MISSING removes session when folder is missing."""
        folder = tmp_path / "missing_folder"  # not created
        session = _session(folder, issue_number=999)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [
                (session, _assessment(folder, action=SessionAction.REMOVE_MISSING))
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
            lambda f: True,
        )

        result = cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=False
        )

        assert str(folder) in result.get("deleted", [])

    def test_cleanup_missing_unlinks_orphan_workspace_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """REMOVE_MISSING removes orphan ``.code-workspace`` file and session record.

        Reproduces the orphan-workspace -> false-active -> cleanup-skipped loop
        from issue #953: a session whose folder was deleted but whose
        ``.code-workspace`` file lingered in workspace_base.
        """
        folder_name = "missing_folder"
        folder = tmp_path / folder_name
        session = _session(folder, issue_number=999)

        orphan_workspace = tmp_path / f"{folder_name}.code-workspace"
        orphan_workspace.write_text("{}")

        removed_folders: list[str] = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [
                (session, _assessment(folder, action=SessionAction.REMOVE_MISSING))
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.remove_session",
            removed_folders.append,
        )

        result = cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=False
        )

        assert not orphan_workspace.exists()
        assert removed_folders == [str(folder)]
        assert str(folder) in result.get("deleted", [])

    def test_cleanup_missing_dry_run_keeps_orphan_workspace_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Dry run reports REMOVE_MISSING without unlinking the orphan."""
        folder_name = "missing_folder"
        folder = tmp_path / folder_name
        session = _session(folder, issue_number=999)

        orphan_workspace = tmp_path / f"{folder_name}.code-workspace"
        orphan_workspace.write_text("{}")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [
                (session, _assessment(folder, action=SessionAction.REMOVE_MISSING))
            ],
        )

        cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=True
        )

        assert orphan_workspace.exists()

    def test_cleanup_skips_no_git_folder(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """SKIP action reports the decision reason and keeps the folder."""
        folder = tmp_path / "no_git_folder"
        folder.mkdir()
        (folder / "some_file.txt").write_text("x")
        session = _session(folder, issue_number=888)

        reason = "unverified git status (No Git), non-empty"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [
                (session, _assessment(folder, action=SessionAction.SKIP, reason=reason))
            ],
        )

        result = cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=False
        )

        assert folder.exists()
        assert str(folder) in result.get("skipped", [])
        assert reason in capsys.readouterr().out

    def test_cleanup_deletes_empty_folder(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An empty folder decided DELETE upstream is deleted (no re-check here)."""
        folder = tmp_path / "empty_folder"
        folder.mkdir()  # empty folder, no files
        session = _session(folder, issue_number=888)

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.get_stale_sessions",
            lambda assessments: [
                (
                    session,
                    _assessment(
                        folder, action=SessionAction.DELETE, reason="closed (empty)"
                    ),
                )
            ],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.delete_session_folder",
            lambda s, workspace_base="": True,
        )

        result = cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments={}, dry_run=False
        )

        assert str(folder) in result.get("deleted", [])
        assert str(folder) not in result.get("skipped", [])


class TestGetStaleSessions:
    """Thin filter over assessments: which sessions does cleanup act on?"""

    def test_returns_inactive_actionable_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Inactive DELETE session is returned with its assessment."""
        folder = tmp_path / "stale_folder"
        folder.mkdir()
        session = _session(folder)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(monkeypatch, sessions_file, [session])

        assessment = _assessment(folder, action=SessionAction.DELETE)
        result = get_stale_sessions({str(folder): assessment})

        assert len(result) == 1
        returned_session, returned_assessment = result[0]
        assert returned_session["folder"] == str(folder)
        assert returned_assessment.decision.action == SessionAction.DELETE

    def test_skips_active_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """KEEP_ACTIVE (verdict.active) sessions are skipped — they stay tracked."""
        folder = tmp_path / "active_folder"
        folder.mkdir()
        session = _session(folder)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(monkeypatch, sessions_file, [session])

        assessment = _assessment(
            folder, active=True, action=SessionAction.KEEP_ACTIVE, reason="active"
        )
        result = get_stale_sessions({str(folder): assessment})

        assert result == []

    def test_skips_zombie_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """INVESTIGATE_ZOMBIE is active (process alive, folder gone) -> skipped."""
        folder = tmp_path / "zombie_folder"  # not created (folder gone)
        session = _session(folder)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(monkeypatch, sessions_file, [session])

        assessment = _assessment(
            folder,
            active=True,
            action=SessionAction.INVESTIGATE_ZOMBIE,
            reason="folder missing, process alive",
        )
        result = get_stale_sessions({str(folder): assessment})

        assert result == []

    def test_skips_restart_sessions(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """RESTART is the restart path's job — cleanup ignores it."""
        folder = tmp_path / "restart_folder"
        folder.mkdir()
        session = _session(folder)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(monkeypatch, sessions_file, [session])

        assessment = _assessment(
            folder, action=SessionAction.RESTART, reason="restartable"
        )
        result = get_stale_sessions({str(folder): assessment})

        assert result == []

    def test_skips_sessions_without_assessment(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A session with no assessment entry is left untouched."""
        folder = tmp_path / "unassessed_folder"
        folder.mkdir()
        session = _session(folder)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(monkeypatch, sessions_file, [session])

        result = get_stale_sessions({})

        assert result == []

    def test_returns_skip_and_remove_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """SKIP and REMOVE_MISSING are actionable and returned."""
        skip_folder = tmp_path / "skip_folder"
        skip_folder.mkdir()
        missing_folder = tmp_path / "missing_folder"
        skip_session = _session(skip_folder, issue_number=1)
        missing_session = _session(missing_folder, issue_number=2)
        sessions_file = tmp_path / "sessions.json"
        _patch_sessions_file(
            monkeypatch, sessions_file, [skip_session, missing_session]
        )

        assessments = {
            str(skip_folder): _assessment(
                skip_folder, action=SessionAction.SKIP, reason="dirty"
            ),
            str(missing_folder): _assessment(
                missing_folder, action=SessionAction.REMOVE_MISSING
            ),
        }
        result = get_stale_sessions(assessments)

        returned_actions = {a.decision.action for _, a in result}
        assert returned_actions == {SessionAction.SKIP, SessionAction.REMOVE_MISSING}


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


class TestCompositionScenarios:
    """Cross-cutting acceptance scenarios for the migrated cleanup path."""

    def test_orphan_workspace_file_end_to_end(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Scenario A — orphan workspace file + missing folder self-clean.

        One cleanup pass over a REMOVE_MISSING session whose folder is gone but
        whose ``.code-workspace`` file and ``.to_be_deleted`` entry linger must
        remove all three: session record, orphan workspace file, registry entry.
        The Missing branch must not attempt deletion of an absent folder.
        """
        from mcp_coder.workflows.vscodeclaude.helpers import (
            TO_BE_DELETED_FILENAME,
            load_to_be_deleted,
        )
        from mcp_coder.workflows.vscodeclaude.sessions import load_sessions

        sessions_file = tmp_path / "sessions.json"
        folder_name = "mcp_coder_188"
        folder = tmp_path / folder_name  # absent on disk

        orphan_workspace = tmp_path / f"{folder_name}.code-workspace"
        orphan_workspace.write_text("{}")
        (tmp_path / TO_BE_DELETED_FILENAME).write_text(f"{folder_name}\n")

        session = _session(folder, issue_number=188)
        _patch_sessions_file(monkeypatch, sessions_file, [session])

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
                folder, action=SessionAction.REMOVE_MISSING, reason="folder missing"
            )
        }
        cleanup_stale_sessions(
            workspace_base=str(tmp_path), assessments=assessments, dry_run=False
        )

        # Session record removed from sessions.json.
        assert load_sessions()["sessions"] == []
        # Orphan workspace file unlinked.
        assert not orphan_workspace.exists()
        # .to_be_deleted entry cleared (folder already gone, no assessment-active).
        assert load_to_be_deleted(str(tmp_path)) == set()
        # Missing branch must not attempt deletion of an absent folder.
        assert safe_delete_calls == []

    def test_live_folder_spared_in_retry_queue(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Scenario B — a live folder in the retry queue is never retry-deleted.

        The ``.to_be_deleted`` entry whose assessment is ``verdict.active`` is
        spared: ``safe_delete_folder`` is never invoked, the folder survives, and
        the entry stays queued. Idempotent on replay.
        """
        from mcp_coder.workflows.vscodeclaude.helpers import (
            TO_BE_DELETED_FILENAME,
            load_to_be_deleted,
        )

        sessions_file = tmp_path / "sessions.json"
        folder_name = "mcp_coder_937"
        folder = tmp_path / folder_name
        folder.mkdir()
        (tmp_path / TO_BE_DELETED_FILENAME).write_text(f"{folder_name}\n")

        session = _session(folder, issue_number=937)
        _patch_sessions_file(monkeypatch, sessions_file, [session])

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

        for _ in range(2):  # idempotent on replay
            cleanup_stale_sessions(
                workspace_base=str(tmp_path), assessments=assessments, dry_run=False
            )
            assert safe_delete_calls == []
            assert folder.exists()
            assert load_to_be_deleted(str(tmp_path)) == {folder_name}
