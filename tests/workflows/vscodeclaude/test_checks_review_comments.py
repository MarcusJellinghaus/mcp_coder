"""Tests for review-comment detection in checks.py."""

from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import EventData, IssueData, PullRequestData
from mcp_coder.workflows.vscodeclaude.checks import (
    _check_review_comments,
    _review_comments_watermark,
)

REVIEW_LABEL = "status-91:pr-review-comments"
CREATED_LABEL = "status-10:pr-created"
PR = cast(PullRequestData, {"number": 1})


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


class TestCheckReviewComments:
    """Tests for _check_review_comments()."""

    def _issue_manager(self, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        issue_manager = MagicMock()
        issue_manager.project_dir = None
        issue_manager.transition_issue_label.return_value = True
        monkeypatch.setattr(
            "mcp_coder.workflow_utils.label_transitions.load_labels_config",
            lambda *a, **k: MOCK_REVIEW_LABELS_CONFIG,
        )
        return issue_manager

    def _pr_manager(self, feedback: dict[str, Any]) -> MagicMock:
        pr_manager = MagicMock()
        pr_manager.get_pr_feedback.return_value = feedback
        return pr_manager

    def _call(
        self, issue: IssueData, pr_manager: MagicMock, issue_manager: MagicMock
    ) -> bool:
        return _check_review_comments(
            issue,
            PR,
            pr_manager,
            issue_manager,
            "test-repo",
            REVIEW_LABEL,
            CREATED_LABEL,
        )

    def test_unresolved_thread_escalates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An unresolved review thread escalates, regardless of comments."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(unresolved_threads=[{"body": "fix this"}])
        )
        issue_manager.get_issue_events.return_value = []

        result = self._call(_make_issue(1), pr_manager, issue_manager)

        assert result is True
        pr_manager.get_pr_feedback.assert_called_once_with(1)
        issue_manager.transition_issue_label.assert_called_once()

    def test_changes_requested_escalates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A CHANGES_REQUESTED review escalates, with no unresolved threads."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(changes_requested=[{"body": "please fix"}])
        )
        issue_manager.get_issue_events.return_value = []

        result = self._call(_make_issue(2), pr_manager, issue_manager)

        assert result is True

    def test_only_alerts_does_not_escalate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Code-scanning alerts alone never trigger escalation."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(alerts=[{"message": "sql injection"}])
        )
        issue_manager.get_issue_events.return_value = []

        result = self._call(_make_issue(3), pr_manager, issue_manager)

        assert result is False
        issue_manager.transition_issue_label.assert_not_called()

    def test_first_ever_comment_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A conversation comment with no prior status-91 event escalates."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(
                conversation_comments=[
                    {"created_at": "2024-01-01T00:00:00Z", "author": "x", "body": "y"}
                ]
            )
        )
        issue_manager.get_issue_events.return_value = []

        result = self._call(_make_issue(4), pr_manager, issue_manager)

        assert result is True

    def test_comment_before_watermark_does_not_escalate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comment older than the watermark does not escalate."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(
                conversation_comments=[
                    {"created_at": "2024-01-01T00:00:00Z", "author": "x", "body": "y"}
                ]
            )
        )
        issue_manager.get_issue_events.return_value = [
            _labeled(CREATED_LABEL, "2023-01-01T00:00:00Z"),
            _labeled(REVIEW_LABEL, "2023-06-01T00:00:00Z"),
            _labeled(CREATED_LABEL, "2024-06-01T00:00:00Z"),
        ]

        result = self._call(_make_issue(5), pr_manager, issue_manager)

        assert result is False

    def test_comment_after_watermark_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comment newer than the watermark escalates."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(
                conversation_comments=[
                    {"created_at": "2024-07-01T00:00:00Z", "author": "x", "body": "y"}
                ]
            )
        )
        issue_manager.get_issue_events.return_value = [
            _labeled(CREATED_LABEL, "2023-01-01T00:00:00Z"),
            _labeled(REVIEW_LABEL, "2023-06-01T00:00:00Z"),
            _labeled(CREATED_LABEL, "2024-06-01T00:00:00Z"),
        ]

        result = self._call(_make_issue(6), pr_manager, issue_manager)

        assert result is True

    def test_comment_with_none_created_at_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comment with a missing created_at escalates without raising."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(
                conversation_comments=[{"created_at": None, "author": "x", "body": "y"}]
            )
        )
        issue_manager.get_issue_events.return_value = [
            _labeled(CREATED_LABEL, "2023-01-01T00:00:00Z"),
            _labeled(REVIEW_LABEL, "2023-06-01T00:00:00Z"),
            _labeled(CREATED_LABEL, "2024-06-01T00:00:00Z"),
        ]

        result = self._call(_make_issue(7), pr_manager, issue_manager)

        assert result is True

    def test_get_pr_feedback_exception_swallowed(self) -> None:
        """A get_pr_feedback exception is swallowed and returns False."""
        pr_manager = MagicMock()
        pr_manager.get_pr_feedback.side_effect = RuntimeError("boom")

        result = self._call(_make_issue(10), pr_manager, MagicMock())

        assert result is False

    def test_get_issue_events_exception_swallowed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A get_issue_events exception is swallowed and returns False."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(
                conversation_comments=[
                    {"created_at": "2024-01-01T00:00:00Z", "author": "x", "body": "y"}
                ]
            )
        )
        issue_manager.get_issue_events.side_effect = RuntimeError("boom")

        result = self._call(_make_issue(11), pr_manager, issue_manager)

        assert result is False
