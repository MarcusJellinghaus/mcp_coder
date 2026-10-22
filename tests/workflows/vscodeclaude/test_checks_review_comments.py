"""Tests for review-comment detection in checks.py."""

from typing import Any, cast
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import (
    ChangesRequestedData,
    ConversationCommentData,
    EventData,
    IssueData,
    PullRequestData,
)
from mcp_coder.workflows.vscodeclaude.checks import (
    _check_review_comments,
    _review_comments_watermark,
)

REVIEW_LABEL = "status-91:pr-review-comments"
CREATED_LABEL = "status-10:pr-created"
PR = cast(PullRequestData, {"number": 1})

BEFORE_WATERMARK = "2024-01-15T00:00:00+00:00"
AFTER_WATERMARK = "2024-07-01T00:00:00+00:00"


def _labeled(label: str, created_at: str) -> EventData:
    return {
        "event": "labeled",
        "label": label,
        "created_at": created_at,
        "actor": "someone",
    }


def _review(submitted_at: str | None, body: str = "please fix") -> ChangesRequestedData:
    return {
        "author": "reviewer",
        "body": body,
        "submitted_at": submitted_at,
        "author_association": "MEMBER",
    }


def _comment(
    created_at: str | None, body: str = "y", comment_id: int = 1
) -> ConversationCommentData:
    return {
        "author": "reviewer",
        "body": body,
        "id": comment_id,
        "created_at": created_at,
        "author_association": "MEMBER",
    }


# Watermark = 2024-06-01 (status-10 relabel after the last status-91).
WATERMARK_EVENTS: list[EventData] = [
    _labeled(CREATED_LABEL, "2024-01-01T00:00:00+00:00"),
    _labeled(REVIEW_LABEL, "2024-03-01T00:00:00+00:00"),
    _labeled(CREATED_LABEL, "2024-06-01T00:00:00+00:00"),
]


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
        "author_association": None,
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
        """An unresolved review thread escalates even with a watermark present."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(
                unresolved_threads=[{"body": "fix this"}],
                conversation_comments=[_comment(BEFORE_WATERMARK)],
            )
        )
        issue_manager.get_issue_events.return_value = WATERMARK_EVENTS

        result = self._call(_make_issue(1), pr_manager, issue_manager)

        assert result is True
        pr_manager.get_pr_feedback.assert_called_once_with(1)
        issue_manager.transition_issue_label.assert_called_once()
        issue_manager.get_issue_events.assert_not_called()

    @pytest.mark.parametrize(
        ("submitted_at", "events", "expected"),
        [
            pytest.param(BEFORE_WATERMARK, WATERMARK_EVENTS, False, id="before"),
            pytest.param(AFTER_WATERMARK, WATERMARK_EVENTS, True, id="after"),
            pytest.param(BEFORE_WATERMARK, [], True, id="no-watermark"),
            pytest.param(None, WATERMARK_EVENTS, True, id="none-submitted-at"),
        ],
    )
    def test_changes_requested_watermark(
        self,
        monkeypatch: pytest.MonkeyPatch,
        submitted_at: str | None,
        events: list[EventData],
        expected: bool,
    ) -> None:
        """A CHANGES_REQUESTED review counts only if newer than the watermark."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(changes_requested=[_review(submitted_at)])
        )
        issue_manager.get_issue_events.return_value = events

        result = self._call(_make_issue(2), pr_manager, issue_manager)

        assert result is expected
        issue_manager.get_issue_events.assert_called_once()

    def test_no_feedback_does_not_escalate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No threads, reviews or comments: no escalation, no events fetch."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(_empty_pr_feedback())

        result = self._call(_make_issue(8), pr_manager, issue_manager)

        assert result is False
        issue_manager.get_issue_events.assert_not_called()
        issue_manager.transition_issue_label.assert_not_called()

    def test_marked_comment_only_does_not_escalate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An automated ❌ note alone never escalates, and skips the events fetch."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(
                conversation_comments=[
                    _comment(AFTER_WATERMARK, "## ❌ Implementation Failed\ndetails")
                ]
            )
        )
        issue_manager.get_issue_events.return_value = WATERMARK_EVENTS

        result = self._call(_make_issue(9), pr_manager, issue_manager)

        assert result is False
        issue_manager.get_issue_events.assert_not_called()

    def test_marker_on_later_line_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A ❌ outside the first line does not mark the comment as automated."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(
                conversation_comments=[
                    _comment(AFTER_WATERMARK, "Please check\n❌ this fails")
                ]
            )
        )
        issue_manager.get_issue_events.return_value = WATERMARK_EVENTS

        result = self._call(_make_issue(12), pr_manager, issue_manager)

        assert result is True

    def test_marked_and_human_comment_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A new human comment escalates even alongside a ❌ note."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(
                conversation_comments=[
                    _comment(AFTER_WATERMARK, "## ❌ Implementation Failed", 1),
                    _comment(AFTER_WATERMARK, "please rename this", 2),
                ]
            )
        )
        issue_manager.get_issue_events.return_value = WATERMARK_EVENTS

        result = self._call(_make_issue(13), pr_manager, issue_manager)

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
            _empty_pr_feedback(conversation_comments=[_comment(BEFORE_WATERMARK)])
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
            _empty_pr_feedback(conversation_comments=[_comment(BEFORE_WATERMARK)])
        )
        issue_manager.get_issue_events.return_value = WATERMARK_EVENTS

        result = self._call(_make_issue(5), pr_manager, issue_manager)

        assert result is False

    def test_comment_after_watermark_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comment newer than the watermark escalates."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(conversation_comments=[_comment(AFTER_WATERMARK)])
        )
        issue_manager.get_issue_events.return_value = WATERMARK_EVENTS

        result = self._call(_make_issue(6), pr_manager, issue_manager)

        assert result is True

    def test_comment_with_none_created_at_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comment with a missing created_at escalates without raising."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(conversation_comments=[_comment(None)])
        )
        issue_manager.get_issue_events.return_value = WATERMARK_EVENTS

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
            _empty_pr_feedback(conversation_comments=[_comment(BEFORE_WATERMARK)])
        )
        issue_manager.get_issue_events.side_effect = RuntimeError("boom")

        result = self._call(_make_issue(11), pr_manager, issue_manager)

        assert result is False
