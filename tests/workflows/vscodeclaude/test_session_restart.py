"""Tests for session restart orchestration."""

import json
from pathlib import Path

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.vscodeclaude.session_restart import (
    BranchPrepResult,
    restart_closed_sessions,
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
)
from tests.github_factories import make_issue_data


def _make_assessment(
    folder: str,
    *,
    active: bool = False,
    action: SessionAction = SessionAction.RESTART,
) -> SessionAssessment:
    """Build a minimal :class:`SessionAssessment` for restart consumer tests.

    Restart reads ``verdict.active`` and ``decision.action``; the remaining typed
    sub-results are filled with neutral defaults.
    """
    rule = LivenessRule.TITLE if active else LivenessRule.NO_MATCH
    return SessionAssessment(
        folder=folder,
        signals=DetectionSignals(
            folder_exists=True,
            title_match=active,
            cmdline_match=False,
            pid_alive=False,
            found_pid=None,
            age_seconds=0.0,
            within_grace=False,
            directory_empty=False,
        ),
        verdict=LivenessVerdict(active=active, rule=rule),
        issue_state=IssueState(
            is_open=True,
            is_stale=False,
            is_blocked=False,
            is_unassigned=False,
            is_eligible=True,
        ),
        transition=Transition(flipped_to_inactive=False),
        decision=Decision(action=action, reason="", destructive=False),
        pid_needs_refresh=False,
        found_pid=None,
    )


class TestSessionRestart:
    """Test main orchestration functions."""


class TestRestartClosedSessionsIssueStatus:
    """Tests for issue-status gating in restart_closed_sessions()."""

    def test_restart_closed_sessions_skips_blocked_issues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should not restart sessions for issues with blocked label."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )
        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-01:created",
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        # Cached issue with blocked label
        cached_issue = make_issue_data(
            number=123,
            title="Test",
            labels=["status-01:created", "blocked"],
            url="",
        )
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {123: cached_issue}
        }

        result = restart_closed_sessions(
            assessments={str(working_folder): _make_assessment(str(working_folder))},
            cached_issues_by_repo=cached_issues,
        )

        assert len(result) == 0  # Not restarted

    def test_restart_closed_sessions_updates_session_status(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should update session status when GitHub status differs."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.regenerate_session_files",
            lambda session, issue: tmp_path / "script.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.launch_vscode",
            lambda *_args: 9999,
        )

        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_123.code-workspace"
        workspace_file.write_text("{}")

        # Track status updates
        status_updates = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.update_session_status",
            lambda folder, status: status_updates.append((folder, status)),
        )

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 123,
            "status": "status-01:created",  # Old status
            "vscode_pid": None,
            "started_at": "2024-01-01T00:00:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": ""}
        sessions_file.write_text(json.dumps(store))

        # GitHub has new status
        cached_issue = make_issue_data(
            number=123,
            title="Test",
            labels=["status-04:plan-review"],  # Changed status
            url="",
        )
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {123: cached_issue}
        }

        restart_closed_sessions(
            assessments={str(working_folder): _make_assessment(str(working_folder))},
            cached_issues_by_repo=cached_issues,
        )

        # Verify status was updated
        assert len(status_updates) == 1
        assert status_updates[0][0] == str(working_folder)
        assert status_updates[0][1] == "status-04:plan-review"

    def test_restart_closed_sessions_skips_closed_issues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should not restart sessions for closed issues."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Create working folder (so it passes folder exists check)
        working_folder = tmp_path / "repo_123"
        working_folder.mkdir()

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

        # Cached issue is CLOSED
        cached_issue = make_issue_data(
            number=123,
            title="Test",
            state="closed",  # <-- Issue is closed
            labels=["status-07:code-review"],
            url="",
        )
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {123: cached_issue}
        }

        result = restart_closed_sessions(
            assessments={str(working_folder): _make_assessment(str(working_folder))},
            cached_issues_by_repo=cached_issues,
        )

        # Session should NOT be restarted because issue is closed
        assert len(result) == 0

    def test_restart_closed_sessions_skips_bot_stage_issues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should not restart sessions when issue moved to bot stage."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Create working folder
        working_folder = tmp_path / "repo_456"
        working_folder.mkdir()

        # Session was at code-review, but issue has moved to bot stage
        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 456,
            "status": "status-07:code-review",  # Old status
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Issue is now at bot stage (status-08:ready-pr) - NOT eligible
        cached_issue = make_issue_data(
            number=456,
            title="Test",
            labels=["status-08:ready-pr"],  # <-- Bot stage, not eligible
            url="",
        )
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {456: cached_issue}
        }

        result = restart_closed_sessions(
            assessments={str(working_folder): _make_assessment(str(working_folder))},
            cached_issues_by_repo=cached_issues,
        )

        # Session should NOT be restarted - bot stage is not eligible
        assert len(result) == 0

    def test_restart_closed_sessions_skips_pr_created_issues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should not restart sessions when issue moved to pr-created."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )

        # Create working folder
        working_folder = tmp_path / "repo_789"
        working_folder.mkdir()

        # Session was at code-review, but issue now has PR created
        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 789,
            "status": "status-07:code-review",  # Old status
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Issue is now at pr-created - NOT eligible (no session needed)
        cached_issue = make_issue_data(
            number=789,
            title="Test",
            labels=["status-10:pr-created"],  # <-- PR created, not eligible
            url="",
        )
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {789: cached_issue}
        }

        result = restart_closed_sessions(
            assessments={str(working_folder): _make_assessment(str(working_folder))},
            cached_issues_by_repo=cached_issues,
        )

        # Session should NOT be restarted - pr-created is not eligible
        assert len(result) == 0

    def test_restart_closed_sessions_restarts_eligible_issues(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should restart sessions for eligible issues (01, 04, 07)."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.regenerate_session_files",
            lambda session, issue: tmp_path / "script.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.launch_vscode",
            lambda *_args: 9999,
        )

        # Mock _prepare_restart_branch to avoid git operations
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._prepare_restart_branch",
            lambda *args, **kwargs: BranchPrepResult(True, None, None),
        )

        # Create working folder and workspace file
        working_folder = tmp_path / "repo_101"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_101.code-workspace"
        workspace_file.write_text("{}")

        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 101,
            "status": "status-04:plan-review",
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Issue is at eligible status (04), open
        cached_issue = make_issue_data(
            number=101,
            title="Test",
            labels=["status-04:plan-review"],  # <-- Eligible status
            url="",
        )
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {101: cached_issue}
        }

        result = restart_closed_sessions(
            assessments={str(working_folder): _make_assessment(str(working_folder))},
            cached_issues_by_repo=cached_issues,
        )

        # Session SHOULD be restarted - eligible status, open issue
        assert len(result) == 1
        assert result[0]["vscode_pid"] == 9999

    def test_restart_closed_sessions_eligible_to_eligible_transition(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should restart when status changes between eligible statuses (04 → 07)."""
        sessions_file = tmp_path / "sessions.json"
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.sessions.get_sessions_file_path",
            lambda: sessions_file,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._get_configured_repos",
            lambda: {"owner/repo"},
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.regenerate_session_files",
            lambda session, issue: tmp_path / "script.bat",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.launch_vscode",
            lambda *_args: 8888,
        )

        # Track status updates
        status_updates: list[tuple[str, str]] = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart.update_session_status",
            lambda folder, status: status_updates.append((folder, status)),
        )

        # Mock _prepare_restart_branch to avoid git operations
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_restart._prepare_restart_branch",
            lambda *args, **kwargs: BranchPrepResult(True, None, None),
        )

        # Create working folder and workspace file
        working_folder = tmp_path / "repo_202"
        working_folder.mkdir()
        workspace_file = tmp_path / "repo_202.code-workspace"
        workspace_file.write_text("{}")

        # Session was at 04 (plan-review)
        session = {
            "folder": str(working_folder),
            "repo": "owner/repo",
            "issue_number": 202,
            "status": "status-04:plan-review",  # Old eligible status
            "vscode_pid": 1234,
            "started_at": "2024-01-22T10:30:00Z",
            "is_intervention": False,
        }
        store = {"sessions": [session], "last_updated": "2024-01-22T10:30:00Z"}
        sessions_file.write_text(json.dumps(store))

        # Issue has moved to 07 (code-review) - ALSO eligible
        cached_issue = make_issue_data(
            number=202,
            title="Test",
            labels=["status-07:code-review"],  # <-- New eligible status
            url="",
        )
        cached_issues: dict[str, dict[int, IssueData]] = {
            "owner/repo": {202: cached_issue}
        }

        result = restart_closed_sessions(
            assessments={str(working_folder): _make_assessment(str(working_folder))},
            cached_issues_by_repo=cached_issues,
        )

        # Session SHOULD be restarted - both statuses are eligible
        assert len(result) == 1
        assert result[0]["vscode_pid"] == 8888

        # Status should have been updated from 04 to 07
        assert len(status_updates) == 1
        assert status_updates[0][0] == str(working_folder)
        assert status_updates[0][1] == "status-07:code-review"
