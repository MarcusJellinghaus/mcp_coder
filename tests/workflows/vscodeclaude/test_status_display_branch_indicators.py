"""Tests for branch-related indicators in the VSCode Claude status table."""

from pathlib import Path

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.vscodeclaude.status import (
    display_status_table,
    get_next_action,
)


class TestDisplayStatusTableBranchIndicators:
    """Tests for branch-related indicators in status table."""

    def test_eligible_issue_without_branch_shows_needs_branch(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Eligible issue without linked branch shows '-> Needs branch'."""
        mock_issue: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "body": "",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        eligible_issues: list[tuple[str, IssueData]] = [("owner/repo", mock_issue)]
        issues_without_branch: set[tuple[str, int]] = {("owner/repo", 123)}

        display_status_table(
            sessions=[],
            eligible_issues=eligible_issues,
            workspace_base=str(tmp_path),
            assessments={},
            issues_without_branch=issues_without_branch,
        )

        captured = capsys.readouterr()
        assert "-> Needs branch" in captured.out
        assert "#123" in captured.out

    def test_eligible_issue_with_branch_shows_create_and_start(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Eligible issue with linked branch shows '-> Create and start'."""
        mock_issue: IssueData = {
            "number": 456,
            "title": "Test Issue",
            "body": "",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        eligible_issues: list[tuple[str, IssueData]] = [("owner/repo", mock_issue)]
        issues_without_branch: set[tuple[str, int]] = set()  # Has branch

        display_status_table(
            sessions=[],
            eligible_issues=eligible_issues,
            workspace_base=str(tmp_path),
            assessments={},
            issues_without_branch=issues_without_branch,
        )

        captured = capsys.readouterr()
        assert "-> Create and start" in captured.out
        assert "#456" in captured.out

    def test_status_01_without_branch_shows_create_and_start(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Status-01 issue without branch still shows '-> Create and start'."""
        mock_issue: IssueData = {
            "number": 789,
            "title": "Test Issue",
            "body": "",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        eligible_issues: list[tuple[str, IssueData]] = [("owner/repo", mock_issue)]
        # Even if in issues_without_branch, status-01 doesn't require branch
        issues_without_branch: set[tuple[str, int]] = {("owner/repo", 789)}

        display_status_table(
            sessions=[],
            eligible_issues=eligible_issues,
            workspace_base=str(tmp_path),
            assessments={},
            issues_without_branch=issues_without_branch,
        )

        captured = capsys.readouterr()
        # Should show Create and start, not Needs branch (status-01 allows main)
        assert "-> Create and start" in captured.out

    def test_session_with_skip_reason_shows_indicator(self) -> None:
        """Session with skip_reason shows appropriate indicator."""
        # Test get_next_action directly with skip_reason
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            skip_reason="No branch",
        )

        assert result == "!! No branch"

    def test_none_issues_without_branch_uses_default_behavior(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """None issues_without_branch uses default '-> Create and start'."""
        mock_issue: IssueData = {
            "number": 111,
            "title": "Test Issue",
            "body": "",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        eligible_issues: list[tuple[str, IssueData]] = [("owner/repo", mock_issue)]

        display_status_table(
            sessions=[],
            eligible_issues=eligible_issues,
            workspace_base=str(tmp_path),
            assessments={},
            issues_without_branch=None,  # Not provided
        )

        captured = capsys.readouterr()
        # Default behavior when branch info not available
        assert "-> Create and start" in captured.out

    def test_status_07_without_branch_shows_needs_branch(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Status-07:code-review without branch shows '-> Needs branch'."""
        mock_issue: IssueData = {
            "number": 222,
            "title": "Test Issue",
            "body": "",
            "labels": ["status-07:code-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        eligible_issues: list[tuple[str, IssueData]] = [("owner/repo", mock_issue)]
        issues_without_branch: set[tuple[str, int]] = {("owner/repo", 222)}

        display_status_table(
            sessions=[],
            eligible_issues=eligible_issues,
            workspace_base=str(tmp_path),
            assessments={},
            issues_without_branch=issues_without_branch,
        )

        captured = capsys.readouterr()
        assert "-> Needs branch" in captured.out
        assert "#222" in captured.out

    def test_skip_reason_dirty_shows_dirty_indicator(self) -> None:
        """Session with skip_reason='Dirty' shows '!! Dirty'."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            skip_reason="Dirty",
        )

        assert result == "!! Dirty"

    def test_skip_reason_git_error_shows_git_error_indicator(self) -> None:
        """Session with skip_reason='Git error' shows '!! Git error'."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            skip_reason="Git error",
        )

        assert result == "!! Git error"

    def test_skip_reason_multi_branch_shows_multi_branch_indicator(self) -> None:
        """Session with skip_reason='Multi-branch' shows '!! Multi-branch'."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            skip_reason="Multi-branch",
        )

        assert result == "!! Multi-branch"

    def test_skip_reason_takes_priority_over_blocked(self) -> None:
        """skip_reason takes priority over blocked_label."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=False,
            blocked_label="wait",
            skip_reason="No branch",
        )

        assert result == "!! No branch"
        assert "Blocked" not in result

    def test_skip_reason_takes_priority_over_stale(self) -> None:
        """skip_reason takes priority over stale status."""
        result = get_next_action(
            is_stale=True,
            is_dirty=False,
            is_vscode_running=False,
            skip_reason="No branch",
        )

        assert result == "!! No branch"
        assert "Delete" not in result

    def test_vscode_running_takes_priority_over_skip_reason(self) -> None:
        """VSCode running takes priority over skip_reason."""
        result = get_next_action(
            is_stale=False,
            is_dirty=False,
            is_vscode_running=True,
            skip_reason="No branch",
        )

        assert result == "(active)"
