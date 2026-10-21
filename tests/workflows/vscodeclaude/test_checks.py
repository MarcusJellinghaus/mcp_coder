"""Tests for PR-health checks on status-10 issues (checks.py)."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import IssueData
from mcp_coder.workflows.vscodeclaude.session_launch import (
    process_eligible_issues,
)

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
            "mcp_coder.workflows.vscodeclaude.checks._build_pr_manager",
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
            "mcp_coder.workflows.vscodeclaude.checks._build_pr_manager",
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
            "mcp_coder.workflows.vscodeclaude.checks._build_pr_manager",
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
            "mcp_coder.workflows.vscodeclaude.checks._build_pr_manager",
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
            "mcp_coder.workflows.vscodeclaude.checks._build_pr_manager",
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
            "mcp_coder.workflows.vscodeclaude.checks._build_pr_manager",
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
            "mcp_coder.workflows.vscodeclaude.checks._build_pr_manager",
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
            "mcp_coder.workflows.vscodeclaude.checks._build_pr_manager",
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
            "mcp_coder.workflows.vscodeclaude.checks._build_pr_manager",
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
