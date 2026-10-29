"""Tests for the trusted-author gate in _check_review_comments()."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.mcp_workspace_github import EventData, OpenPullRequest
from mcp_coder.utils.log_utils import OUTPUT
from mcp_coder.workflows.vscodeclaude.checks import _check_review_comments
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
    _make_issue,
    _make_pr,
    _output_messages,
    _review,
    _thread,
)


@pytest.fixture(autouse=True)
def _no_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(f"{CHECKS}.get_trusted_commenters", frozenset)


class TestCheckReviewCommentsTrust:
    """Trust gating in _check_review_comments()."""

    def _issue_manager(self, monkeypatch: pytest.MonkeyPatch) -> MagicMock:
        issue_manager = MagicMock()
        issue_manager.project_dir = None
        issue_manager.transition_issue_label.return_value = True
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
        pr: OpenPullRequest | None = None,
        events: list[EventData] | None = None,
    ) -> tuple[bool, MagicMock]:
        pr_cache = MagicMock()
        pr_cache.feedback.return_value = feedback
        pr_cache.label_events.return_value = [] if events is None else events
        with caplog.at_level(OUTPUT, logger=CHECKS):
            result = _check_review_comments(
                _make_issue(20),
                pr or PR,
                pr_cache,
                issue_manager,
                "test-repo",
                REVIEW_LABEL,
                CREATED_LABEL,
                trusted,
            )
        return result, pr_cache

    def test_untrusted_thread_only(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An untrusted thread alone logs one line, no label, no events fetch."""
        issue_manager = self._issue_manager(monkeypatch)

        result, pr_cache = self._call(
            _empty_pr_feedback(unresolved_threads=[_thread("stranger", "NONE")]),
            issue_manager,
            caplog,
        )

        assert result is False
        assert _output_messages(caplog) == [
            "PR-health: test-repo #20: untrusted PR feedback from @stranger"
            " — review manually"
        ]
        pr_cache.label_events.assert_not_called()
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

        result, pr_cache = self._call(
            _empty_pr_feedback(conversation_comments=[_comment(AFTER_WATERMARK)]),
            issue_manager,
            caplog,
            pr=_make_pr("stranger", "NONE"),
        )

        assert result is False
        pr_cache.feedback.assert_not_called()
        issue_manager.transition_issue_label.assert_not_called()
        assert _output_messages(caplog) == [
            "PR-health: test-repo #20: untrusted PR author @stranger"
            " — review comments not checked"
        ]

    def test_events_fetched_at_most_once(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Several reviews and comments share one label_events call."""
        issue_manager = self._issue_manager(monkeypatch)

        _, pr_cache = self._call(
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
            events=WATERMARK_EVENTS,
        )

        pr_cache.label_events.assert_called_once()

    def test_old_untrusted_items_log_nothing(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Untrusted reviews/comments older than the watermark log no line."""
        issue_manager = self._issue_manager(monkeypatch)

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
            events=WATERMARK_EVENTS,
        )

        assert result is False
        assert not _output_messages(caplog)

    def test_untrusted_thread_listed_despite_old_items(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An untrusted thread is reported even when other items are old."""
        issue_manager = self._issue_manager(monkeypatch)

        result, pr_cache = self._call(
            _empty_pr_feedback(
                unresolved_threads=[_thread("stranger", "NONE")],
                conversation_comments=[
                    _comment(BEFORE_WATERMARK, author="old", association="NONE")
                ],
            ),
            issue_manager,
            caplog,
            events=WATERMARK_EVENTS,
        )

        assert result is False
        pr_cache.label_events.assert_called_once()
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
