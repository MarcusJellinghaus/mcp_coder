"""Tests for review-comment detection in checks.py."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import EventData, IssueData, OpenPullRequest
from mcp_coder.workflows.vscodeclaude.checks import (
    _check_review_comments,
    _review_comments_watermark,
)
from tests.workflows.vscodeclaude._review_comments_helpers import (
    AFTER_WATERMARK,
    BEFORE_WATERMARK,
    CHECKS,
    CREATED_LABEL,
    MOCK_REVIEW_LABELS_CONFIG,
    PR,
    REVIEW_LABEL,
    WATERMARK_EVENTS,
    _comment,
    _empty_pr_feedback,
    _labeled,
    _make_issue,
    _review,
    _thread,
)


@pytest.fixture(autouse=True)
def _no_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f"{CHECKS}.get_trusted_commenters", frozenset)


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

    def _pr_cache(
        self, feedback: dict[str, Any], events: list[EventData] | None = None
    ) -> MagicMock:
        pr_cache = MagicMock()
        pr_cache.feedback.return_value = feedback
        pr_cache.label_events.return_value = [] if events is None else events
        return pr_cache

    def _call(
        self,
        issue: IssueData,
        pr_cache: MagicMock,
        issue_manager: MagicMock,
        trusted: frozenset[str] = frozenset(),
        pr: OpenPullRequest | None = None,
    ) -> bool:
        return _check_review_comments(
            issue,
            pr or PR,
            pr_cache,
            issue_manager,
            "test-repo",
            REVIEW_LABEL,
            CREATED_LABEL,
            trusted,
        )

    def test_unresolved_thread_escalates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An unresolved review thread escalates even with a watermark present."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_cache = self._pr_cache(
            _empty_pr_feedback(
                unresolved_threads=[_thread()],
                conversation_comments=[_comment(BEFORE_WATERMARK)],
            ),
            WATERMARK_EVENTS,
        )
        issue = _make_issue(1)

        result = self._call(issue, pr_cache, issue_manager)

        assert result is True
        pr_cache.feedback.assert_called_once_with(PR, issue)
        issue_manager.transition_issue_label.assert_called_once()
        pr_cache.label_events.assert_not_called()

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
        pr_cache = self._pr_cache(
            _empty_pr_feedback(changes_requested=[_review(submitted_at)]), events
        )
        issue = _make_issue(2)

        result = self._call(issue, pr_cache, issue_manager)

        assert result is expected
        pr_cache.label_events.assert_called_once_with(PR, issue)

    def test_no_feedback_does_not_escalate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No threads, reviews or comments: no escalation, no events fetch."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_cache = self._pr_cache(_empty_pr_feedback())

        result = self._call(_make_issue(8), pr_cache, issue_manager)

        assert result is False
        pr_cache.label_events.assert_not_called()
        issue_manager.transition_issue_label.assert_not_called()

    def test_marked_comment_only_does_not_escalate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An automated ❌ note alone never escalates, and skips the events fetch."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_cache = self._pr_cache(
            _empty_pr_feedback(
                conversation_comments=[
                    _comment(AFTER_WATERMARK, "## ❌ Implementation Failed\ndetails")
                ]
            ),
            WATERMARK_EVENTS,
        )

        result = self._call(_make_issue(9), pr_cache, issue_manager)

        assert result is False
        pr_cache.label_events.assert_not_called()

    def test_marker_on_later_line_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A ❌ outside the first line does not mark the comment as automated."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_cache = self._pr_cache(
            _empty_pr_feedback(
                conversation_comments=[
                    _comment(AFTER_WATERMARK, "Please check\n❌ this fails")
                ]
            ),
            WATERMARK_EVENTS,
        )

        result = self._call(_make_issue(12), pr_cache, issue_manager)

        assert result is True

    def test_marked_and_human_comment_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A new human comment escalates even alongside a ❌ note."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_cache = self._pr_cache(
            _empty_pr_feedback(
                conversation_comments=[
                    _comment(AFTER_WATERMARK, "## ❌ Implementation Failed", 1),
                    _comment(AFTER_WATERMARK, "please rename this", 2),
                ]
            ),
            WATERMARK_EVENTS,
        )

        result = self._call(_make_issue(13), pr_cache, issue_manager)

        assert result is True

    def test_only_alerts_does_not_escalate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Code-scanning alerts alone never trigger escalation."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_cache = self._pr_cache(
            _empty_pr_feedback(alerts=[{"message": "sql injection"}])
        )

        result = self._call(_make_issue(3), pr_cache, issue_manager)

        assert result is False
        issue_manager.transition_issue_label.assert_not_called()

    def test_first_ever_comment_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A conversation comment with no prior status-91 event escalates."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_cache = self._pr_cache(
            _empty_pr_feedback(conversation_comments=[_comment(BEFORE_WATERMARK)])
        )

        result = self._call(_make_issue(4), pr_cache, issue_manager)

        assert result is True

    def test_comment_before_watermark_does_not_escalate(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comment older than the watermark does not escalate."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_cache = self._pr_cache(
            _empty_pr_feedback(conversation_comments=[_comment(BEFORE_WATERMARK)]),
            WATERMARK_EVENTS,
        )

        result = self._call(_make_issue(5), pr_cache, issue_manager)

        assert result is False

    def test_comment_after_watermark_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comment newer than the watermark escalates."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_cache = self._pr_cache(
            _empty_pr_feedback(conversation_comments=[_comment(AFTER_WATERMARK)]),
            WATERMARK_EVENTS,
        )

        result = self._call(_make_issue(6), pr_cache, issue_manager)

        assert result is True

    def test_comment_with_none_created_at_escalates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A comment with a missing created_at escalates without raising."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_cache = self._pr_cache(
            _empty_pr_feedback(conversation_comments=[_comment(None)]),
            WATERMARK_EVENTS,
        )

        result = self._call(_make_issue(7), pr_cache, issue_manager)

        assert result is True

    def test_feedback_exception_swallowed(self) -> None:
        """A feedback exception is swallowed and returns False."""
        pr_cache = MagicMock()
        pr_cache.feedback.side_effect = RuntimeError("boom")

        result = self._call(_make_issue(10), pr_cache, MagicMock())

        assert result is False

    def test_label_events_exception_swallowed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A label_events exception is swallowed and returns False."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_cache = self._pr_cache(
            _empty_pr_feedback(conversation_comments=[_comment(BEFORE_WATERMARK)])
        )
        pr_cache.label_events.side_effect = RuntimeError("boom")

        result = self._call(_make_issue(11), pr_cache, issue_manager)

        assert result is False
