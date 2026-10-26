"""Tests for review-comment detection in checks.py."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import (
    ChangesRequestedData,
    ConversationCommentData,
    EventData,
    IssueData,
    PullRequestData,
    ReviewThreadData,
)
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflows.vscodeclaude.checks import (
    _check_review_comments,
    _review_comments_watermark,
)
from tests.github_factories import make_issue_data

CHECKS = "mcp_coder.workflows.vscodeclaude.checks"
REVIEW_LABEL = "status-91:pr-review-comments"
CREATED_LABEL = "status-10:pr-created"

BEFORE_WATERMARK = "2024-01-15T00:00:00+00:00"
AFTER_WATERMARK = "2024-07-01T00:00:00+00:00"


def _make_pr(
    user: str | None = "owner", association: str | None = "OWNER"
) -> PullRequestData:
    return {
        "number": 1,
        "title": "PR",
        "body": "",
        "state": "open",
        "head_branch": "1-fix",
        "head_sha": None,
        "base_branch": "main",
        "url": "https://github.com/owner/repo/pull/1",
        "created_at": None,
        "updated_at": None,
        "user": user,
        "mergeable": None,
        "mergeable_state": "clean",
        "merged": False,
        "draft": False,
        "assignees": [],
        "author_association": association,
    }


PR = _make_pr()


def _labeled(label: str, created_at: str) -> EventData:
    return {
        "event": "labeled",
        "label": label,
        "created_at": created_at,
        "actor": "someone",
    }


def _thread(
    author: str = "reviewer", association: str | None = "MEMBER"
) -> ReviewThreadData:
    return {
        "path": "src/x.py",
        "line": 1,
        "author": author,
        "body": "fix this",
        "diff_hunk": "@@ -1 +1 @@",
        "comment_id": 1,
        "thread_id": "T_1",
        "author_association": association,
    }


def _review(
    submitted_at: str | None,
    body: str = "please fix",
    *,
    author: str = "reviewer",
    association: str | None = "MEMBER",
) -> ChangesRequestedData:
    return {
        "author": author,
        "body": body,
        "submitted_at": submitted_at,
        "author_association": association,
    }


def _comment(
    created_at: str | None,
    body: str = "y",
    comment_id: int = 1,
    *,
    author: str = "reviewer",
    association: str | None = "MEMBER",
) -> ConversationCommentData:
    return {
        "author": author,
        "body": body,
        "id": comment_id,
        "created_at": created_at,
        "author_association": association,
    }


def _output_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.levelno == OUTPUT]


@pytest.fixture(autouse=True)
def _no_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f"{CHECKS}.get_trusted_commenters", frozenset)


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
    return make_issue_data(
        number=number,
        title="PR Created Issue",
        labels=["status-10:pr-created"],
        assignees=["testuser"],
    )


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
        self,
        issue: IssueData,
        pr_manager: MagicMock,
        issue_manager: MagicMock,
        trusted: frozenset[str] = frozenset(),
        pr: PullRequestData | None = None,
    ) -> bool:
        return _check_review_comments(
            issue,
            pr or PR,
            pr_manager,
            issue_manager,
            "test-repo",
            REVIEW_LABEL,
            CREATED_LABEL,
            trusted,
        )

    def test_unresolved_thread_escalates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An unresolved review thread escalates even with a watermark present."""
        issue_manager = self._issue_manager(monkeypatch)
        pr_manager = self._pr_manager(
            _empty_pr_feedback(
                unresolved_threads=[_thread()],
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


class TestCheckReviewCommentsTrust:
    """Trust gating in _check_review_comments()."""

    def _issue_manager(self, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        issue_manager = MagicMock()
        issue_manager.project_dir = None
        issue_manager.transition_issue_label.return_value = True
        issue_manager.get_issue_events.return_value = []
        monkeypatch.setattr(
            "mcp_coder.workflow_utils.label_transitions.load_labels_config",
            lambda *a, **k: MOCK_REVIEW_LABELS_CONFIG,
        )
        return issue_manager

    def _call(
        self,
        feedback: dict[str, Any],
        issue_manager: MagicMock,
        caplog: pytest.LogCaptureFixture,
        trusted: frozenset[str] = frozenset(),
        pr: PullRequestData | None = None,
    ) -> tuple[bool, MagicMock]:
        pr_manager = MagicMock()
        pr_manager.get_pr_feedback.return_value = feedback
        with caplog.at_level(OUTPUT, logger=CHECKS):
            result = _check_review_comments(
                _make_issue(20),
                pr or PR,
                pr_manager,
                issue_manager,
                "test-repo",
                REVIEW_LABEL,
                CREATED_LABEL,
                trusted,
            )
        return result, pr_manager

    def test_untrusted_thread_only(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An untrusted thread alone logs one line, no label, no events fetch."""
        issue_manager = self._issue_manager(monkeypatch)

        result, _ = self._call(
            _empty_pr_feedback(unresolved_threads=[_thread("stranger", "NONE")]),
            issue_manager,
            caplog,
        )

        assert result is False
        assert _output_messages(caplog) == [
            "PR-health: test-repo #20: untrusted PR feedback from @stranger"
            " — review manually"
        ]
        issue_manager.get_issue_events.assert_not_called()
        issue_manager.transition_issue_label.assert_not_called()

    def test_untrusted_review_only(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A new untrusted changes-requested review logs one line, no label."""
        issue_manager = self._issue_manager(monkeypatch)

        result, _ = self._call(
            _empty_pr_feedback(
                changes_requested=[
                    _review(AFTER_WATERMARK, author="stranger", association="NONE")
                ]
            ),
            issue_manager,
            caplog,
        )

        assert result is False
        messages = _output_messages(caplog)
        assert len(messages) == 1
        assert "@stranger" in messages[0]
        issue_manager.transition_issue_label.assert_not_called()

    def test_untrusted_comment_only(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A new untrusted conversation comment logs one line, no label."""
        issue_manager = self._issue_manager(monkeypatch)

        result, _ = self._call(
            _empty_pr_feedback(
                conversation_comments=[
                    _comment(AFTER_WATERMARK, author="stranger", association="NONE")
                ]
            ),
            issue_manager,
            caplog,
        )

        assert result is False
        messages = _output_messages(caplog)
        assert len(messages) == 1
        assert "@stranger" in messages[0]
        issue_manager.transition_issue_label.assert_not_called()

    @pytest.mark.parametrize(
        ("author", "association", "trusted"),
        [
            pytest.param("boss", "OWNER", frozenset(), id="owner"),
            pytest.param("helper", "COLLABORATOR", frozenset(), id="collaborator"),
            pytest.param("Friend", "NONE", frozenset({"friend"}), id="allowlisted"),
        ],
    )
    def test_trusted_comment_escalates(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
        author: str,
        association: str,
        trusted: frozenset[str],
    ) -> None:
        """A new comment by a trusted author escalates."""
        issue_manager = self._issue_manager(monkeypatch)

        result, _ = self._call(
            _empty_pr_feedback(
                conversation_comments=[
                    _comment(AFTER_WATERMARK, author=author, association=association)
                ]
            ),
            issue_manager,
            caplog,
            trusted=trusted,
        )

        assert result is True
        issue_manager.transition_issue_label.assert_called_once()

    def test_mixed_trusted_and_untrusted_escalates(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A trusted item escalates; no untrusted-feedback line is logged."""
        issue_manager = self._issue_manager(monkeypatch)

        result, _ = self._call(
            _empty_pr_feedback(
                unresolved_threads=[_thread("stranger", "NONE")],
                conversation_comments=[_comment(AFTER_WATERMARK)],
            ),
            issue_manager,
            caplog,
        )

        assert result is True
        assert not any(
            "untrusted PR feedback" in message for message in _output_messages(caplog)
        )

    def test_missing_association_is_untrusted(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A missing association with a non-allowlisted login is untrusted."""
        issue_manager = self._issue_manager(monkeypatch)

        result, _ = self._call(
            _empty_pr_feedback(
                conversation_comments=[
                    _comment(AFTER_WATERMARK, author="ghosty", association=None)
                ]
            ),
            issue_manager,
            caplog,
            trusted=frozenset({"friend"}),
        )

        assert result is False
        issue_manager.transition_issue_label.assert_not_called()
        assert "@ghosty" in _output_messages(caplog)[0]

    def test_untrusted_pr_author_skips_feedback(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An untrusted PR author: no feedback fetch, one OUTPUT line."""
        issue_manager = self._issue_manager(monkeypatch)

        result, pr_manager = self._call(
            _empty_pr_feedback(conversation_comments=[_comment(AFTER_WATERMARK)]),
            issue_manager,
            caplog,
            pr=_make_pr("stranger", "NONE"),
        )

        assert result is False
        pr_manager.get_pr_feedback.assert_not_called()
        issue_manager.transition_issue_label.assert_not_called()
        assert _output_messages(caplog) == [
            "PR-health: test-repo #20: untrusted PR author @stranger"
            " — review comments not checked"
        ]

    def test_events_fetched_at_most_once(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Several reviews and comments share one get_issue_events call."""
        issue_manager = self._issue_manager(monkeypatch)
        issue_manager.get_issue_events.return_value = WATERMARK_EVENTS

        self._call(
            _empty_pr_feedback(
                changes_requested=[
                    _review(BEFORE_WATERMARK, author="a", association="NONE"),
                    _review(BEFORE_WATERMARK),
                ],
                conversation_comments=[
                    _comment(BEFORE_WATERMARK, comment_id=1),
                    _comment(BEFORE_WATERMARK, comment_id=2, association="NONE"),
                ],
            ),
            issue_manager,
            caplog,
        )

        issue_manager.get_issue_events.assert_called_once()

    def test_old_untrusted_items_log_nothing(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Untrusted reviews/comments older than the watermark log no line."""
        issue_manager = self._issue_manager(monkeypatch)
        issue_manager.get_issue_events.return_value = WATERMARK_EVENTS

        result, _ = self._call(
            _empty_pr_feedback(
                changes_requested=[
                    _review(BEFORE_WATERMARK, author="a", association="NONE")
                ],
                conversation_comments=[
                    _comment(BEFORE_WATERMARK, author="b", association="NONE")
                ],
            ),
            issue_manager,
            caplog,
        )

        assert result is False
        assert not _output_messages(caplog)

    def test_untrusted_thread_listed_despite_old_items(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An untrusted thread is reported even when other items are old."""
        issue_manager = self._issue_manager(monkeypatch)
        issue_manager.get_issue_events.return_value = WATERMARK_EVENTS

        result, _ = self._call(
            _empty_pr_feedback(
                unresolved_threads=[_thread("stranger", "NONE")],
                conversation_comments=[
                    _comment(BEFORE_WATERMARK, author="old", association="NONE")
                ],
            ),
            issue_manager,
            caplog,
        )

        assert result is False
        issue_manager.get_issue_events.assert_called_once()
        assert _output_messages(caplog) == [
            "PR-health: test-repo #20: untrusted PR feedback from @stranger"
            " — review manually"
        ]

    def test_same_untrusted_login_listed_once(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A login on both a thread and a comment is listed once."""
        issue_manager = self._issue_manager(monkeypatch)

        self._call(
            _empty_pr_feedback(
                unresolved_threads=[_thread("stranger", "NONE")],
                conversation_comments=[
                    _comment(AFTER_WATERMARK, author="stranger", association="NONE")
                ],
            ),
            issue_manager,
            caplog,
        )

        assert _output_messages(caplog) == [
            "PR-health: test-repo #20: untrusted PR feedback from @stranger"
            " — review manually"
        ]
