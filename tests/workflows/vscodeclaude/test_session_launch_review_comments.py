"""Tests for review-comment detection helpers in session_launch.py."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import EventData, IssueData
from mcp_coder.workflows.vscodeclaude.session_launch import (
    _check_ci,
    _check_review_comments,
    _review_comments_watermark,
    process_eligible_issues,
)

from .test_session_launch_process_issues import (
    MOCK_CI_LABELS_CONFIG,
    TestProcessEligibleIssuesMergeConflictDetection,
)

REVIEW_LABEL = "status-91:pr-review-comments"
CREATED_LABEL = "status-10:pr-created"


def _labeled(label: str, created_at: str) -> EventData:
    return {
        "event": "labeled",
        "label": label,
        "created_at": created_at,
        "actor": "someone",
    }


def _empty_pr_feedback(**overrides: Any) -> dict[str, Any]:
    feedback: dict[str, Any] = {
        "unresolved_threads": [],
        "resolved_thread_count": 0,
        "changes_requested": [],
        "conversation_comments": [],
        "alerts": [],
        "unavailable": {},
    }
    feedback.update(overrides)
    return feedback


def _make_issue(number: int) -> IssueData:
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


MOCK_REVIEW_LABELS_CONFIG: dict[str, Any] = {
    "workflow_labels": [
        {
            "internal_id": "pr_created",
            "name": "status-10:pr-created",
            "color": "8b5cf6",
            "description": "Pull request created, awaiting approval/merge",
            "category": "human_action",
        },
        {
            "internal_id": "pr_review_comments",
            "name": "status-91:pr-review-comments",
            "color": "b60205",
            "description": (
                "PR has new review comments, unresolved threads, or a "
                "changes-requested review"
            ),
            "category": "human_action",
        },
    ],
    "ignore_labels": [],
}


class TestReviewCommentsWatermark:
    """Tests for _review_comments_watermark()."""

    def test_no_status_91_event_returns_none(self) -> None:
        """First-ever arrival: no status-91 event anywhere."""
        events: list[EventData] = [
            _labeled(CREATED_LABEL, "2024-01-01T00:00:00Z"),
        ]

        result = _review_comments_watermark(events, REVIEW_LABEL, CREATED_LABEL)

        assert result is None

    def test_single_cycle_returns_relabel_timestamp(self) -> None:
        """One status-91 event followed by one status-10 event."""
        events: list[EventData] = [
            _labeled(CREATED_LABEL, "2024-01-01T00:00:00Z"),
            _labeled(REVIEW_LABEL, "2024-01-02T00:00:00Z"),
            _labeled(CREATED_LABEL, "2024-01-03T00:00:00Z"),
        ]

        result = _review_comments_watermark(events, REVIEW_LABEL, CREATED_LABEL)

        assert result == "2024-01-03T00:00:00Z"

    def test_two_cycles_uses_last_status_91_event(self) -> None:
        """Two status-91/status-10 relabel cycles: uses the last status-91 event."""
        events: list[EventData] = [
            _labeled(CREATED_LABEL, "2024-01-01T00:00:00Z"),
            _labeled(REVIEW_LABEL, "2024-01-02T00:00:00Z"),
            _labeled(CREATED_LABEL, "2024-01-03T00:00:00Z"),
            _labeled(REVIEW_LABEL, "2024-01-04T00:00:00Z"),
            _labeled(CREATED_LABEL, "2024-01-05T00:00:00Z"),
        ]

        result = _review_comments_watermark(events, REVIEW_LABEL, CREATED_LABEL)

        assert result == "2024-01-05T00:00:00Z"

    def test_no_subsequent_status_10_returns_none(self) -> None:
        """status-91 event with no subsequent status-10 event in the list."""
        events: list[EventData] = [
            _labeled(CREATED_LABEL, "2024-01-01T00:00:00Z"),
            _labeled(REVIEW_LABEL, "2024-01-02T00:00:00Z"),
        ]

        result = _review_comments_watermark(events, REVIEW_LABEL, CREATED_LABEL)

        assert result is None

    def test_empty_events_returns_none(self) -> None:
        """Empty events list returns None."""
        events: list[EventData] = []

        result = _review_comments_watermark(events, REVIEW_LABEL, CREATED_LABEL)

        assert result is None


class TestCheckCiReturnValue:
    """Tests for _check_ci()'s bool return value."""

    def _mocks(
        self, monkeypatch: pytest.MonkeyPatch, run_status: dict[str, Any]
    ) -> tuple[MagicMock, MagicMock, MagicMock]:
        ci_manager = MagicMock()
        ci_manager.get_latest_ci_status.return_value = run_status
        branch_manager = MagicMock()
        branch_manager.get_branch_with_pr_fallback.return_value = "123-fix"
        issue_manager = MagicMock()
        issue_manager.project_dir = None
        issue_manager.transition_issue_label.return_value = True
        monkeypatch.setattr(
            "mcp_coder.workflow_utils.label_transitions.load_labels_config",
            lambda *a, **k: MOCK_CI_LABELS_CONFIG,
        )
        return ci_manager, branch_manager, issue_manager

    def test_returns_true_when_label_transitions(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failed CI run that successfully escalates returns True."""
        ci_manager, branch_manager, issue_manager = self._mocks(
            monkeypatch,
            {"run": {"status": "completed", "conclusion": "failure"}, "jobs": []},
        )
        issue = _make_issue(1)

        result = _check_ci(
            issue, ci_manager, branch_manager, issue_manager, "owner", "repo"
        )

        assert result is True

    def test_returns_false_when_ci_successful(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Successful CI run returns False."""
        ci_manager, branch_manager, issue_manager = self._mocks(
            monkeypatch,
            {"run": {"status": "completed", "conclusion": "success"}, "jobs": []},
        )
        issue = _make_issue(2)

        result = _check_ci(
            issue, ci_manager, branch_manager, issue_manager, "owner", "repo"
        )

        assert result is False

    def test_returns_false_when_ci_pending(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A still-running CI run returns False."""
        ci_manager, branch_manager, issue_manager = self._mocks(
            monkeypatch,
            {"run": {"status": "in_progress", "conclusion": None}, "jobs": []},
        )
        issue = _make_issue(3)

        result = _check_ci(
            issue, ci_manager, branch_manager, issue_manager, "owner", "repo"
        )

        assert result is False

    def test_returns_false_on_exception(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A CIResultsManager exception is swallowed and returns False."""
        ci_manager = MagicMock()
        ci_manager.get_latest_ci_status.side_effect = RuntimeError("boom")
        branch_manager = MagicMock()
        branch_manager.get_branch_with_pr_fallback.return_value = "123-fix"
        issue_manager = MagicMock()
        issue = _make_issue(4)

        result = _check_ci(
            issue, ci_manager, branch_manager, issue_manager, "owner", "repo"
        )

        assert result is False

    def test_returns_false_when_no_branch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No resolvable branch returns False without calling the CI API."""
        ci_manager = MagicMock()
        branch_manager = MagicMock()
        branch_manager.get_branch_with_pr_fallback.return_value = None
        issue_manager = MagicMock()
        issue = _make_issue(5)

        result = _check_ci(
            issue, ci_manager, branch_manager, issue_manager, "owner", "repo"
        )

        assert result is False
        ci_manager.get_latest_ci_status.assert_not_called()


class TestCheckReviewComments:
    """Tests for _check_review_comments()."""

    def _common(
        self, monkeypatch: pytest.MonkeyPatch, branch: str | None = "123-fix"
    ) -> tuple[MagicMock, MagicMock]:
        branch_manager = MagicMock()
        branch_manager.get_branch_with_pr_fallback.return_value = branch
        issue_manager = MagicMock()
        issue_manager.project_dir = None
        issue_manager.transition_issue_label.return_value = True
        monkeypatch.setattr(
            "mcp_coder.workflow_utils.label_transitions.load_labels_config",
            lambda *a, **k: MOCK_REVIEW_LABELS_CONFIG,
        )
        return branch_manager, issue_manager

    def _pr_manager(
        self,
        monkeypatch: pytest.MonkeyPatch,
        feedback: dict[str, Any],
        pr_number: int = 1,
    ) -> MagicMock:
        pr_manager = MagicMock()
        pr_manager.find_pull_request_by_head.return_value = [{"number": pr_number}]
        pr_manager.get_pr_feedback.return_value = feedback
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            lambda repo_url: pr_manager,
        )
        return pr_manager

    def test_unresolved_thread_escalates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An unresolved review thread escalates, regardless of comments."""
        branch_manager, issue_manager = self._common(monkeypatch)
        feedback = _empty_pr_feedback(unresolved_threads=[{"body": "fix this"}])
        self._pr_manager(monkeypatch, feedback)
        issue_manager.get_issue_events.return_value = []
        issue = _make_issue(1)

        result = _check_review_comments(
            issue,
            branch_manager,
            issue_manager,
            "owner",
            "repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

        assert result is True
        issue_manager.transition_issue_label.assert_called_once()

    def test_changes_requested_escalates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A CHANGES_REQUESTED review escalates, with no unresolved threads."""
        branch_manager, issue_manager = self._common(monkeypatch)
        feedback = _empty_pr_feedback(changes_requested=[{"body": "please fix"}])
        self._pr_manager(monkeypatch, feedback)
        issue_manager.get_issue_events.return_value = []
        issue = _make_issue(2)

        result = _check_review_comments(
            issue,
            branch_manager,
            issue_manager,
            "owner",
            "repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

        assert result is True

    def test_only_alerts_does_not_escalate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Code-scanning alerts alone never trigger escalation."""
        branch_manager, issue_manager = self._common(monkeypatch)
        feedback = _empty_pr_feedback(alerts=[{"message": "sql injection"}])
        self._pr_manager(monkeypatch, feedback)
        issue_manager.get_issue_events.return_value = []
        issue = _make_issue(3)

        result = _check_review_comments(
            issue,
            branch_manager,
            issue_manager,
            "owner",
            "repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

        assert result is False
        issue_manager.transition_issue_label.assert_not_called()

    def test_first_ever_comment_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A conversation comment with no prior status-91 event escalates."""
        branch_manager, issue_manager = self._common(monkeypatch)
        feedback = _empty_pr_feedback(
            conversation_comments=[
                {"created_at": "2024-01-01T00:00:00Z", "author": "x", "body": "y"}
            ]
        )
        self._pr_manager(monkeypatch, feedback)
        issue_manager.get_issue_events.return_value = []
        issue = _make_issue(4)

        result = _check_review_comments(
            issue,
            branch_manager,
            issue_manager,
            "owner",
            "repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

        assert result is True

    def test_comment_before_watermark_does_not_escalate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comment older than the watermark does not escalate."""
        branch_manager, issue_manager = self._common(monkeypatch)
        feedback = _empty_pr_feedback(
            conversation_comments=[
                {"created_at": "2024-01-01T00:00:00Z", "author": "x", "body": "y"}
            ]
        )
        self._pr_manager(monkeypatch, feedback)
        issue_manager.get_issue_events.return_value = [
            _labeled(CREATED_LABEL, "2023-01-01T00:00:00Z"),
            _labeled(REVIEW_LABEL, "2023-06-01T00:00:00Z"),
            _labeled(CREATED_LABEL, "2024-06-01T00:00:00Z"),
        ]
        issue = _make_issue(5)

        result = _check_review_comments(
            issue,
            branch_manager,
            issue_manager,
            "owner",
            "repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

        assert result is False

    def test_comment_after_watermark_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comment newer than the watermark escalates."""
        branch_manager, issue_manager = self._common(monkeypatch)
        feedback = _empty_pr_feedback(
            conversation_comments=[
                {"created_at": "2024-07-01T00:00:00Z", "author": "x", "body": "y"}
            ]
        )
        self._pr_manager(monkeypatch, feedback)
        issue_manager.get_issue_events.return_value = [
            _labeled(CREATED_LABEL, "2023-01-01T00:00:00Z"),
            _labeled(REVIEW_LABEL, "2023-06-01T00:00:00Z"),
            _labeled(CREATED_LABEL, "2024-06-01T00:00:00Z"),
        ]
        issue = _make_issue(6)

        result = _check_review_comments(
            issue,
            branch_manager,
            issue_manager,
            "owner",
            "repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

        assert result is True

    def test_comment_with_none_created_at_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comment with a missing created_at escalates without raising."""
        branch_manager, issue_manager = self._common(monkeypatch)
        feedback = _empty_pr_feedback(
            conversation_comments=[{"created_at": None, "author": "x", "body": "y"}]
        )
        self._pr_manager(monkeypatch, feedback)
        issue_manager.get_issue_events.return_value = [
            _labeled(CREATED_LABEL, "2023-01-01T00:00:00Z"),
            _labeled(REVIEW_LABEL, "2023-06-01T00:00:00Z"),
            _labeled(CREATED_LABEL, "2024-06-01T00:00:00Z"),
        ]
        issue = _make_issue(7)

        result = _check_review_comments(
            issue,
            branch_manager,
            issue_manager,
            "owner",
            "repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

        assert result is True

    def test_no_branch_returns_false_never_calls_feedback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No resolvable branch returns False and never calls the PR API."""
        branch_manager = MagicMock()
        branch_manager.get_branch_with_pr_fallback.return_value = None
        issue_manager = MagicMock()
        mock_build_pr_manager = MagicMock()
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            mock_build_pr_manager,
        )
        issue = _make_issue(8)

        result = _check_review_comments(
            issue,
            branch_manager,
            issue_manager,
            "owner",
            "repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

        assert result is False
        mock_build_pr_manager.assert_not_called()

    def test_no_pr_found_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No matching PR for the branch returns False without fetching feedback."""
        branch_manager = MagicMock()
        branch_manager.get_branch_with_pr_fallback.return_value = "123-fix"
        issue_manager = MagicMock()
        pr_manager = MagicMock()
        pr_manager.find_pull_request_by_head.return_value = []
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            lambda repo_url: pr_manager,
        )
        issue = _make_issue(9)

        result = _check_review_comments(
            issue,
            branch_manager,
            issue_manager,
            "owner",
            "repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

        assert result is False
        pr_manager.get_pr_feedback.assert_not_called()

    def test_get_pr_feedback_exception_swallowed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A get_pr_feedback exception is swallowed and returns False."""
        branch_manager = MagicMock()
        branch_manager.get_branch_with_pr_fallback.return_value = "123-fix"
        issue_manager = MagicMock()
        pr_manager = MagicMock()
        pr_manager.find_pull_request_by_head.return_value = [{"number": 1}]
        pr_manager.get_pr_feedback.side_effect = RuntimeError("boom")
        monkeypatch.setattr(
            "mcp_coder.workflows.vscodeclaude.session_launch._build_pr_manager",
            lambda repo_url: pr_manager,
        )
        issue = _make_issue(10)

        result = _check_review_comments(
            issue,
            branch_manager,
            issue_manager,
            "owner",
            "repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

        assert result is False

    def test_get_issue_events_exception_swallowed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A get_issue_events exception is swallowed and returns False."""
        branch_manager, issue_manager = self._common(monkeypatch)
        feedback = _empty_pr_feedback(
            conversation_comments=[
                {"created_at": "2024-01-01T00:00:00Z", "author": "x", "body": "y"}
            ]
        )
        self._pr_manager(monkeypatch, feedback)
        issue_manager.get_issue_events.side_effect = RuntimeError("boom")
        issue = _make_issue(11)

        result = _check_review_comments(
            issue,
            branch_manager,
            issue_manager,
            "owner",
            "repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

        assert result is False


class TestProcessEligibleIssuesPriorityChaining:
    """Tests for the merge-conflict → CI → review-comments priority chain."""

    def test_merge_conflict_escalation_skips_remaining_checks(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A dirty PR never reaches the CI check or the review-comments check."""
        helper = TestProcessEligibleIssuesMergeConflictDetection()
        mock_issue = helper._make_pr_issue(990)
        mock_issue_manager = MagicMock()
        mock_issue_manager.project_dir = None
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "990-fix"
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
        mock_pr_manager.get_pr_feedback.assert_not_called()

    def test_ci_escalation_skips_review_comments_check(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A failing CI run never reaches the review-comments check."""
        helper = TestProcessEligibleIssuesMergeConflictDetection()
        mock_issue = helper._make_pr_issue(989)
        mock_issue_manager = MagicMock()
        mock_issue_manager.project_dir = None
        mock_branch_manager = MagicMock()
        mock_branch_manager.get_branch_with_pr_fallback.return_value = "989-fix"
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

        mock_pr_manager.get_pr_feedback.assert_not_called()
