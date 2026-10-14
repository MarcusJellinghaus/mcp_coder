"""Tests for process_eligible_issues branch requirements and pre-fetched issues."""

import logging
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.vscodeclaude.session_launch import (
    process_eligible_issues,
)


class TestProcessEligibleIssuesBranchRequirement:
    """Tests for branch requirement enforcement in process_eligible_issues()."""

    def test_status_01_without_branch_launches_on_main(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-01 without linked branch launches session on main."""
        # Setup mocks
        mock_issue: IssueData = {
            "number": 123,
            "title": "Test Issue",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/123",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = None

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        # Session should be launched with branch_name=None (defaults to main)
        mock_launch.assert_called_once()
        call_kwargs = mock_launch.call_args.kwargs
        assert call_kwargs["branch_name"] is None

    def test_status_04_without_branch_skips_issue(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """status-04 without linked branch skips issue and logs error."""
        mock_issue: IssueData = {
            "number": 456,
            "title": "Plan Review Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/456",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = None

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        with caplog.at_level(logging.ERROR):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
                current_count=0,
            )

        # Session should NOT be launched
        mock_launch.assert_not_called()
        # Error should be logged
        assert "no linked branch" in caplog.text.lower()
        assert "#456" in caplog.text
        # Empty result
        assert result == []

    def test_status_07_without_branch_skips_issue(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """status-07 without linked branch skips issue."""
        mock_issue: IssueData = {
            "number": 789,
            "title": "Code Review Issue",
            "labels": ["status-07:code-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/789",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = None

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        with caplog.at_level(logging.ERROR):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
                current_count=0,
            )

        mock_launch.assert_not_called()
        assert result == []

    def test_status_04_with_branch_launches_session(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """status-04 with linked branch launches session normally."""
        mock_issue: IssueData = {
            "number": 456,
            "title": "Plan Review Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/456",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "feat-456"

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        mock_launch.assert_called_once()
        call_kwargs = mock_launch.call_args.kwargs
        assert call_kwargs["branch_name"] == "feat-456"

    def test_status_04_with_multiple_branches_skips_issue(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """status-04 with multiple linked branches skips issue and logs error."""
        mock_issue: IssueData = {
            "number": 456,
            "title": "Plan Review Issue",
            "labels": ["status-04:plan-review"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/456",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = None

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )

        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        with caplog.at_level(logging.ERROR):
            result = process_eligible_issues(
                repo_name="test-repo",
                repo_config={"repo_url": "https://github.com/owner/repo"},
                vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
                max_sessions=3,
                current_count=0,
            )

        # Session should NOT be launched
        mock_launch.assert_not_called()
        # Error should be logged
        assert "no linked branch" in caplog.text.lower()
        assert "#456" in caplog.text
        # Empty result
        assert result == []


class TestProcessEligibleIssuesPrefetchedIssues:
    """Tests for pre-fetched issues bypassing get_all_cached_issues."""

    def test_pre_fetched_issues_bypasses_get_all_cached_issues(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When all_cached_issues is passed, get_all_cached_issues is not called."""
        mock_issue: IssueData = {
            "number": 101,
            "title": "Pre-fetched Issue",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/101",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        # Mock IssueManager and IssueBranchManager to avoid token validation
        mock_issue_manager = MagicMock()
        mock_branch_manager = MagicMock()

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )

        # get_all_cached_issues must NOT be called — raises AssertionError if invoked
        def _should_not_be_called(*args: Any, **kwargs: Any) -> list[IssueData]:
            raise AssertionError("get_all_cached_issues should not be called")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            _should_not_be_called,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        # Pass pre-fetched issues directly — get_all_cached_issues must not be called
        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
            all_cached_issues=[mock_issue],
        )

        # The pre-fetched issue was used: session was launched once
        mock_launch.assert_called_once()


MOCK_MERGE_CONFLICT_LABELS_CONFIG: dict[str, Any] = {
    "workflow_labels": [
        {
            "internal_id": "pr_created",
            "name": "status-10:pr-created",
            "color": "8b5cf6",
            "description": "Pull request created, awaiting approval/merge",
            "category": "human_action",
        },
        {
            "internal_id": "merge_conflict",
            "name": "status-71:merge-conflict",
            "color": "fda4af",
            "description": "PR is no longer cleanly mergeable against its base",
            "category": "bot_pickup",
        },
    ],
    "ignore_labels": [],
}

MOCK_CI_LABELS_CONFIG: dict[str, Any] = {
    "workflow_labels": [
        {
            "internal_id": "pr_created",
            "name": "status-10:pr-created",
            "color": "8b5cf6",
            "description": "Pull request created, awaiting approval/merge",
            "category": "human_action",
        },
        {
            "internal_id": "merge_conflict",
            "name": "status-71:merge-conflict",
            "color": "fda4af",
            "description": "PR is no longer cleanly mergeable against its base",
            "category": "bot_pickup",
        },
        {
            "internal_id": "failing_ci",
            "name": "status-81:failing-ci",
            "color": "f87171",
            "description": "PR's latest CI run failed",
            "category": "bot_pickup",
        },
    ],
    "ignore_labels": [],
}


class TestProcessEligibleIssuesMergeConflictDetection:
    """Tests for merge-conflict detection on status-10:pr-created issues."""

    def _make_pr_issue(self, number: int) -> IssueData:
        return {
            "number": number,
            "title": "PR Created Issue",
            "labels": ["status-10:pr-created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": f"https://github.com/owner/repo/issues/{number}",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

    def _setup_common_mocks(
        self,
        monkeypatch: pytest.MonkeyPatch,
        mock_issue: IssueData,
        mock_issue_manager: MagicMock,
        mock_branch_manager: MagicMock,
        labels_config: dict[str, Any] | None = None,
    ) -> MagicMock:
        if labels_config is None:
            labels_config = MOCK_MERGE_CONFLICT_LABELS_CONFIG
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = {"run": {}, "jobs": []}
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.CIResultsManager",
            lambda **kwargs: mock_ci_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [mock_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )
        monkeypatch.setattr(
            "mcp_coder.workflow_utils.label_transitions.load_labels_config",
            lambda *args, **kwargs: labels_config,
        )
        return mock_ci_manager

    def test_dirty_pr_transitions_to_merge_conflict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A status-10 issue whose PR is dirty gets escalated to status-71."""
        mock_issue = self._make_pr_issue(999)
        mock_issue_manager = MagicMock()
        mock_issue_manager.project_dir = None
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "999-fix"
        self._setup_common_mocks(
            monkeypatch, mock_issue, mock_issue_manager, mock_branch_manager
        )

        mock_pr_manager = MagicMock()
        mock_pr_manager.find_pull_request_by_head.return_value = [
            {"number": 1, "mergeable_state": "dirty"}
        ]
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            lambda repo_url: mock_pr_manager,
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        mock_issue_manager.transition_issue_label.assert_called_once()
        call_args = mock_issue_manager.transition_issue_label.call_args
        assert call_args[0][0] == 999
        assert call_args[0][1] == "status-71:merge-conflict"

    def test_clean_pr_does_not_transition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A status-10 issue whose PR is clean is left untouched."""
        mock_issue = self._make_pr_issue(998)
        mock_issue_manager = MagicMock()
        mock_issue_manager.project_dir = None
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "998-fix"
        self._setup_common_mocks(
            monkeypatch, mock_issue, mock_issue_manager, mock_branch_manager
        )

        mock_pr_manager = MagicMock()
        mock_pr_manager.find_pull_request_by_head.return_value = [
            {"number": 1, "mergeable_state": "clean"}
        ]
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            lambda repo_url: mock_pr_manager,
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        mock_issue_manager.transition_issue_label.assert_not_called()

    def test_no_branch_skips_pr_lookup_entirely(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A status-10 issue with no resolvable branch never calls the PR API."""
        mock_issue = self._make_pr_issue(997)
        mock_issue_manager = MagicMock()
        mock_issue_manager.project_dir = None
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = None
        self._setup_common_mocks(
            monkeypatch, mock_issue, mock_issue_manager, mock_branch_manager
        )

        mock_build_pr_manager = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            mock_build_pr_manager,
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        mock_build_pr_manager.assert_not_called()
        mock_issue_manager.transition_issue_label.assert_not_called()

    def test_pr_lookup_failure_does_not_raise_and_other_issues_still_processed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A PR-lookup exception is swallowed; other issues still get processed."""
        pr_issue = self._make_pr_issue(996)
        other_issue: IssueData = {
            "number": 123,
            "title": "Normal Issue",
            "labels": ["status-01:created"],
            "assignees": ["testuser"],
            "state": "open",
            "url": "https://github.com/owner/repo/issues/123",
            "body": "",
            "user": None,
            "created_at": None,
            "updated_at": None,
            "locked": False,
        }

        mock_issue_manager = MagicMock()
        mock_issue_manager.project_dir = None
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "996-fix"

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueManager",
            lambda **kwargs: mock_issue_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.IssueBranchManager",
            lambda **kwargs: mock_branch_manager,
        )
        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = {"run": {}, "jobs": []}
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.CIResultsManager",
            lambda **kwargs: mock_ci_manager,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_all_cached_issues",
            lambda *args, **kwargs: [pr_issue, other_issue],
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._filter_eligible_vscodeclaude_issues",
            lambda *args, **kwargs: [pr_issue, other_issue],
        )
        mock_launch = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.prepare_and_launch_session",
            mock_launch,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_session_for_issue",
            lambda *args, **kwargs: None,
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.get_github_username",
            lambda: "testuser",
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.load_repo_vscodeclaude_config",
            lambda *args, **kwargs: {},
        )

        def _raise(*args: Any, **kwargs: Any) -> Any:
            raise RuntimeError("GitHub API boom")

        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            _raise,
        )

        result = process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        mock_issue_manager.transition_issue_label.assert_not_called()
        # other_issue (status-01) is still processed and launched normally
        mock_launch.assert_called_once()
        assert len(result) == 1


class TestProcessEligibleIssuesCIDetection:
    """Tests for failing-CI detection on status-10:pr-created issues."""

    def test_failed_ci_run_transitions_to_failing_ci(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A status-10 issue whose latest CI run failed gets escalated to status-81."""
        helper = TestProcessEligibleIssuesMergeConflictDetection()
        mock_issue = helper._make_pr_issue(995)
        mock_issue_manager = MagicMock()
        mock_issue_manager.project_dir = None
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "995-fix"
        helper._setup_common_mocks(
            monkeypatch,
            mock_issue,
            mock_issue_manager,
            mock_branch_manager,
            labels_config=MOCK_CI_LABELS_CONFIG,
        )

        mock_pr_manager = MagicMock()
        mock_pr_manager.find_pull_request_by_head.return_value = [
            {"number": 1, "mergeable_state": "clean"}
        ]
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            lambda repo_url: mock_pr_manager,
        )

        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "failure"},
            "jobs": [],
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.CIResultsManager",
            lambda **kwargs: mock_ci_manager,
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        mock_issue_manager.transition_issue_label.assert_called_once()
        call_args = mock_issue_manager.transition_issue_label.call_args
        assert call_args[0][0] == 995
        assert call_args[0][1] == "status-81:failing-ci"

    def test_successful_ci_run_does_not_transition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A status-10 issue whose latest CI run succeeded is left untouched."""
        helper = TestProcessEligibleIssuesMergeConflictDetection()
        mock_issue = helper._make_pr_issue(994)
        mock_issue_manager = MagicMock()
        mock_issue_manager.project_dir = None
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "994-fix"
        helper._setup_common_mocks(
            monkeypatch,
            mock_issue,
            mock_issue_manager,
            mock_branch_manager,
            labels_config=MOCK_CI_LABELS_CONFIG,
        )

        mock_pr_manager = MagicMock()
        mock_pr_manager.find_pull_request_by_head.return_value = [
            {"number": 1, "mergeable_state": "clean"}
        ]
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            lambda repo_url: mock_pr_manager,
        )

        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "success"},
            "jobs": [],
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.CIResultsManager",
            lambda **kwargs: mock_ci_manager,
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        mock_issue_manager.transition_issue_label.assert_not_called()

    def test_pending_ci_run_does_not_transition(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A status-10 issue whose latest CI run is still in progress is left untouched."""
        helper = TestProcessEligibleIssuesMergeConflictDetection()
        mock_issue = helper._make_pr_issue(993)
        mock_issue_manager = MagicMock()
        mock_issue_manager.project_dir = None
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "993-fix"
        helper._setup_common_mocks(
            monkeypatch,
            mock_issue,
            mock_issue_manager,
            mock_branch_manager,
            labels_config=MOCK_CI_LABELS_CONFIG,
        )

        mock_pr_manager = MagicMock()
        mock_pr_manager.find_pull_request_by_head.return_value = [
            {"number": 1, "mergeable_state": "clean"}
        ]
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            lambda repo_url: mock_pr_manager,
        )

        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.return_value = {
            "run": {"status": "in_progress", "conclusion": None},
            "jobs": [],
        }
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.CIResultsManager",
            lambda **kwargs: mock_ci_manager,
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        mock_issue_manager.transition_issue_label.assert_not_called()

    def test_merge_conflict_escalation_skips_ci_check_same_poll(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A status-10 issue whose PR is dirty never has its CI status checked."""
        helper = TestProcessEligibleIssuesMergeConflictDetection()
        mock_issue = helper._make_pr_issue(992)
        mock_issue_manager = MagicMock()
        mock_issue_manager.project_dir = None
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "992-fix"
        helper._setup_common_mocks(
            monkeypatch,
            mock_issue,
            mock_issue_manager,
            mock_branch_manager,
            labels_config=MOCK_CI_LABELS_CONFIG,
        )

        mock_pr_manager = MagicMock()
        mock_pr_manager.find_pull_request_by_head.return_value = [
            {"number": 1, "mergeable_state": "dirty"}
        ]
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            lambda repo_url: mock_pr_manager,
        )

        mock_ci_manager = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.CIResultsManager",
            lambda **kwargs: mock_ci_manager,
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        mock_ci_manager.get_latest_ci_status.assert_not_called()

    def test_ci_manager_exception_is_swallowed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A CIResultsManager exception is swallowed; it does not raise."""
        helper = TestProcessEligibleIssuesMergeConflictDetection()
        mock_issue = helper._make_pr_issue(991)
        mock_issue_manager = MagicMock()
        mock_issue_manager.project_dir = None
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "991-fix"
        helper._setup_common_mocks(
            monkeypatch,
            mock_issue,
            mock_issue_manager,
            mock_branch_manager,
            labels_config=MOCK_CI_LABELS_CONFIG,
        )

        mock_pr_manager = MagicMock()
        mock_pr_manager.find_pull_request_by_head.return_value = [
            {"number": 1, "mergeable_state": "clean"}
        ]
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            lambda repo_url: mock_pr_manager,
        )

        mock_ci_manager = MagicMock()
        mock_ci_manager.get_latest_ci_status.side_effect = RuntimeError(
            "GitHub API boom"
        )
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch.CIResultsManager",
            lambda **kwargs: mock_ci_manager,
        )

        process_eligible_issues(
            repo_name="test-repo",
            repo_config={"repo_url": "https://github.com/owner/repo"},
            vscodeclaude_config={"workspace_base": "/tmp", "max_sessions": 3},
            max_sessions=3,
            current_count=0,
        )

        mock_issue_manager.transition_issue_label.assert_not_called()
