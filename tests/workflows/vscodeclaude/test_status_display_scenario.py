"""Scenario A cross-module composition test for VSCode Claude status display."""

import json
from pathlib import Path

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.vscodeclaude.status import (
    display_status_table,
)
from mcp_coder.workflows.vscodeclaude.types import (
    VSCodeClaudeSession,
)


class TestScenarioACrossModule:
    """Composition test — display consistency after Scenario A cleanup.

    Pair of ``test_orphan_workspace_file_end_to_end`` in
    ``test_cleanup.py``. Runs the same Scenario A setup, executes the
    cleanup pass, then asserts ``display_status_table`` no longer renders
    the removed session.
    """

    def test_display_status_table_omits_cleaned_up_session(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """After Scenario A cleanup, the status table omits the cleaned session."""
        from mcp_coder.utils.folder_deletion import DeletionResult
        from mcp_coder.workflows.vscodeclaude.cleanup import cleanup_stale_sessions
        from mcp_coder.workflows.vscodeclaude.helpers import TO_BE_DELETED_FILENAME
        from mcp_coder.workflows.vscodeclaude.sessions import load_sessions
        from mcp_coder.workflows.vscodeclaude.types import (
            Decision,
            DetectionSignals,
            IssueState,
            LivenessRule,
            LivenessVerdict,
            SessionAction,
            SessionAssessment,
            Transition,
        )

        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )

        folder_name = "mcp_coder_188"
        folder = tmp_path / folder_name
        # Folder absent on disk.

        orphan_workspace = tmp_path / f"{folder_name}.code-workspace"
        orphan_workspace.write_text("{}")

        (tmp_path / TO_BE_DELETED_FILENAME).write_text(f"{folder_name}\n")

        session: VSCodeClaudeSession = {
            "folder": str(folder),
            "repo": "owner/repo",
            "issue_number": 188,
            "status": "status-07:code-review",
            "vscode_pid": 74544,
            "vscode_pid_create_time": None,
            "last_active": None,
            "last_active_rule": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        sessions_file.write_text(
            json.dumps({"sessions": [session], "last_updated": "2024-01-01T00:00:00Z"})
        )

        closed_issue: IssueData = {
            "number": 188,
            "title": "Closed issue",
            "body": "",
            "state": "closed",
            "labels": ["status-07:code-review"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        cached_issues_by_repo: dict[str, dict[int, IssueData]] = {
            "owner/repo": {188: closed_issue}
        }

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.cleanup.safe_delete_folder",
            lambda path: DeletionResult(success=True),
        )

        # The closed issue's folder is gone -> the upstream assessment resolves
        # to REMOVE_MISSING; cleanup consumes that decision directly.
        assessments = {
            str(folder): SessionAssessment(
                folder=str(folder),
                signals=DetectionSignals(
                    folder_exists=False,
                    title_match=False,
                    cmdline_match=False,
                    pid_alive=False,
                    found_pid=None,
                    age_seconds=0.0,
                    within_grace=False,
                    directory_empty=True,
                ),
                verdict=LivenessVerdict(active=False, rule=LivenessRule.NO_ARTIFACTS),
                issue_state=IssueState(
                    is_open=False,
                    is_stale=False,
                    is_blocked=False,
                    is_unassigned=False,
                    is_eligible=False,
                ),
                transition=Transition(flipped_to_inactive=False),
                decision=Decision(
                    action=SessionAction.REMOVE_MISSING,
                    reason="folder missing",
                    destructive=False,
                ),
                pid_needs_refresh=False,
                found_pid=None,
            )
        }

        cleanup_stale_sessions(
            workspace_base=str(tmp_path),
            assessments=assessments,
            dry_run=False,
        )

        post_cleanup_sessions = load_sessions()["sessions"]
        # Discard captured stdout from cleanup so the assertions only inspect
        # what display_status_table renders.
        capsys.readouterr()

        display_status_table(
            sessions=post_cleanup_sessions,
            eligible_issues=[],
            workspace_base=str(tmp_path),
            assessments={},
            repo_filter=None,
            cached_issues_by_repo=cached_issues_by_repo,
        )

        captured = capsys.readouterr()
        assert "#188" not in captured.out
        assert folder_name not in captured.out
