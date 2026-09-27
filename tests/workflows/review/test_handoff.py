"""Step 6 — handoff helper tests (``_flush_round_log`` + ``_route_to_human``).

These deterministic tests exercise the two terminal-routing helpers in
isolation with the git / GitHub externals mocked. ``_flush_round_log`` must be
best-effort (never raise, warn on a falsy or raised result, skip the push when
the commit did not succeed); ``_route_to_human`` must flush, post a gated
comment, transition to the escalate label, and return ``0``.

Step 4 adds ``_fail`` coverage for the optional ``details`` line, which reads
directly beneath the ``❌`` header and is backward compatible when omitted.
"""

import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mcp_coder.workflows.review import handoff
from mcp_coder.workflows.review.config import REVIEW_PLAN

# --- _flush_round_log ------------------------------------------------------


def test_flush_commits_then_pushes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The happy path commits the round log, then pushes it."""
    commit = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    handoff._flush_round_log(tmp_path)

    commit.assert_called_once()
    assert commit.call_args.args[1] == tmp_path
    push.assert_called_once_with(tmp_path)


def test_flush_falsy_commit_warns_and_skips_push(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A falsy commit result warns and does not push (nothing landed to push)."""
    commit = MagicMock(return_value={"success": False, "error": "nothing to commit"})
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path)  # must not raise

    push.assert_not_called()
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_falsy_push_warns(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A falsy push return warns but does not raise."""
    commit = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    push = MagicMock(return_value=False)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path)

    push.assert_called_once()
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_swallows_commit_raise(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An unexpected raise from the commit is swallowed (warned, not propagated)."""
    commit = MagicMock(side_effect=RuntimeError("boom"))
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path)  # must not raise

    push.assert_not_called()
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_swallows_push_raise(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An unexpected raise from the push is swallowed too."""
    commit = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    push = MagicMock(side_effect=RuntimeError("boom"))
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path)  # must not raise

    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_no_commit_skips_push(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A successful commit that committed nothing skips the push, quietly.

    ``commit_all_changes`` reports an empty tree as ``success: True`` with
    ``commit_hash: None``; there is nothing to push and nothing to warn about
    (unlike the ``success: False`` path above, which does warn).
    """
    commit = MagicMock(
        return_value={
            "success": True,
            "commit_hash": None,
            "error": None,
            "error_category": None,
        }
    )
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path)

    push.assert_not_called()
    assert not any(r.levelno == logging.WARNING for r in caplog.records)


@pytest.mark.parametrize("staged", [True, False])
def test_flush_only_commits_just_the_log(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    staged: bool,
) -> None:
    """``only=`` stages and commits that one path — never the whole tree.

    An arbitrarily dirty working tree can therefore never be committed under
    the round-log message. A failed staging commits nothing and warns.
    """
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    stage = MagicMock(return_value=staged)
    commit_staged = MagicMock(
        return_value={
            "success": True,
            "commit_hash": "abc",
            "error": None,
            "error_category": None,
        }
    )
    commit_all = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "stage_specific_files", stage)
    monkeypatch.setattr(handoff, "commit_staged_files", commit_staged)
    monkeypatch.setattr(handoff, "commit_all_changes", commit_all)
    monkeypatch.setattr(handoff, "push_changes", push)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path, only=log_path)

    stage.assert_called_once_with([log_path], tmp_path)
    commit_all.assert_not_called()
    if staged:
        commit_staged.assert_called_once()
        assert commit_staged.call_args.args[1] == tmp_path
        push.assert_called_once_with(tmp_path)
        assert not any(r.levelno == logging.WARNING for r in caplog.records)
    else:
        commit_staged.assert_not_called()
        push.assert_not_called()
        assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_flush_only_refuses_when_index_holds_unrelated_entries(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A pre-staged file blocks the scoped commit instead of riding along.

    ``commit_staged_files`` commits the whole index, so staging the round log on
    top of someone else's staged work would commit it under "Add review round
    log". The flush refuses and warns; the round log stays uncommitted, which
    ``_attempt_rebase_and_push``'s tripwire then names.
    """
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    stage = MagicMock(return_value=True)
    commit_staged = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    monkeypatch.setattr(
        handoff,
        "get_full_status",
        MagicMock(
            return_value={
                "staged": ["src/unrelated.py"],
                "modified": [],
                "untracked": [],
            }
        ),
    )
    monkeypatch.setattr(handoff, "stage_specific_files", stage)
    monkeypatch.setattr(handoff, "commit_staged_files", commit_staged)

    with caplog.at_level(logging.WARNING):
        handoff._flush_round_log(tmp_path, only=log_path)

    stage.assert_not_called()
    commit_staged.assert_not_called()
    assert "src/unrelated.py" in caplog.text


def test_flush_only_proceeds_when_the_log_itself_is_already_staged(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The round log already sitting in the index is not an unrelated entry."""
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    commit_staged = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    monkeypatch.setattr(
        handoff,
        "get_full_status",
        MagicMock(
            return_value={
                "staged": ["pr_info/plan_review_log_1.md"],
                "modified": [],
                "untracked": [],
            }
        ),
    )
    monkeypatch.setattr(handoff, "stage_specific_files", MagicMock(return_value=True))
    monkeypatch.setattr(handoff, "commit_staged_files", commit_staged)
    monkeypatch.setattr(handoff, "push_changes", MagicMock(return_value=True))

    handoff._flush_round_log(tmp_path, only=log_path)

    commit_staged.assert_called_once()


def test_flush_push_false_commits_without_pushing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``push=False`` lands the commit locally and leaves the push to the caller."""
    commit = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    push = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "commit_all_changes", commit)
    monkeypatch.setattr(handoff, "push_changes", push)

    handoff._flush_round_log(tmp_path, push=False)

    commit.assert_called_once()
    push.assert_not_called()


# --- _route_to_human -------------------------------------------------------


@pytest.fixture
def routed(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Patch the externals ``_route_to_human`` touches; expose the mocks."""
    mocks = SimpleNamespace()
    mocks.flush = MagicMock(name="_flush_round_log")
    monkeypatch.setattr(handoff, "_flush_round_log", mocks.flush)
    mocks.issue_manager = MagicMock(name="IssueManager")
    monkeypatch.setattr(handoff, "IssueManager", mocks.issue_manager)
    mocks.update_workflow_label = MagicMock(return_value=True)
    monkeypatch.setattr(handoff, "update_workflow_label", mocks.update_workflow_label)
    return mocks


def test_route_flushes_comments_labels_returns_zero(
    routed: SimpleNamespace, tmp_path: Path
) -> None:
    """The full gated path: flush, post a comment, escalate label, return 0."""
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    result = handoff._route_to_human(
        REVIEW_PLAN,
        tmp_path,
        issue_number=42,
        update_issue_labels=True,
        post_issue_comments=True,
        comment_body="handing off",
        log_path=log_path,
    )

    assert result == 0
    routed.flush.assert_called_once_with(tmp_path, only=log_path)
    routed.issue_manager.return_value.add_comment.assert_called_once_with(
        42, "handing off"
    )
    kwargs = routed.update_workflow_label.call_args.kwargs
    assert kwargs["from_label_id"] == REVIEW_PLAN.busy_label_id
    assert kwargs["to_label_id"] == REVIEW_PLAN.escalate_label_id


def test_route_skips_comment_when_gated_off(
    routed: SimpleNamespace, tmp_path: Path
) -> None:
    """With comments gated off, still flush + relabel but post no comment."""
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    result = handoff._route_to_human(
        REVIEW_PLAN,
        tmp_path,
        issue_number=42,
        update_issue_labels=True,
        post_issue_comments=False,
        comment_body="handing off",
        log_path=log_path,
    )

    assert result == 0
    routed.flush.assert_called_once_with(tmp_path, only=log_path)
    routed.issue_manager.return_value.add_comment.assert_not_called()
    routed.update_workflow_label.assert_called_once()


def test_route_skips_comment_when_no_issue_number(
    routed: SimpleNamespace, tmp_path: Path
) -> None:
    """No issue number means no comment (but flush + relabel still happen)."""
    result = handoff._route_to_human(
        REVIEW_PLAN,
        tmp_path,
        issue_number=None,
        update_issue_labels=True,
        post_issue_comments=True,
        comment_body="handing off",
        log_path=tmp_path / "pr_info" / "plan_review_log_1.md",
    )

    assert result == 0
    routed.issue_manager.return_value.add_comment.assert_not_called()
    routed.update_workflow_label.assert_called_once()


def test_route_comment_failure_is_best_effort(
    routed: SimpleNamespace, tmp_path: Path
) -> None:
    """A raising comment does not break the handoff: label still transitions."""
    routed.issue_manager.return_value.add_comment.side_effect = RuntimeError("boom")

    result = handoff._route_to_human(
        REVIEW_PLAN,
        tmp_path,
        issue_number=42,
        update_issue_labels=True,
        post_issue_comments=True,
        comment_body="handing off",
        log_path=tmp_path / "pr_info" / "plan_review_log_1.md",
    )

    assert result == 0
    routed.update_workflow_label.assert_called_once()


def test_route_transitions_to_escalate_label_gated(
    routed: SimpleNamespace, tmp_path: Path
) -> None:
    """With label updates gated off, no real label transition is attempted."""
    result = handoff._route_to_human(
        REVIEW_PLAN,
        tmp_path,
        issue_number=42,
        update_issue_labels=False,
        post_issue_comments=True,
        comment_body="handing off",
        log_path=tmp_path / "pr_info" / "plan_review_log_1.md",
    )

    assert result == 0
    routed.update_workflow_label.assert_not_called()


def test_route_without_a_round_log_commits_nothing(
    routed: SimpleNamespace, tmp_path: Path
) -> None:
    """``log_path=None`` means no round wrote a log, so nothing is committed."""
    result = handoff._route_to_human(
        REVIEW_PLAN,
        tmp_path,
        issue_number=42,
        update_issue_labels=True,
        post_issue_comments=True,
        comment_body="handing off",
        log_path=None,
    )

    assert result == 0
    routed.flush.assert_not_called()
    routed.update_workflow_label.assert_called_once()


def test_route_leaves_unrelated_dirty_files_uncommitted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The handoff lands the round log alone, never the tree that reached it.

    The unresolved-rebase handoff is reached *because* the tree was dirty;
    committing all of it here would push exactly what the rebase tripwire
    refused to rebase over.
    """
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    stage = MagicMock(return_value=True)
    commit_staged = MagicMock(return_value={"success": True, "commit_hash": "abc"})
    commit_all = MagicMock(return_value={"success": True, "commit_hash": "def"})
    monkeypatch.setattr(
        handoff,
        "get_full_status",
        MagicMock(
            return_value={"staged": [], "modified": ["src/foo.py"], "untracked": []}
        ),
    )
    monkeypatch.setattr(handoff, "stage_specific_files", stage)
    monkeypatch.setattr(handoff, "commit_staged_files", commit_staged)
    monkeypatch.setattr(handoff, "commit_all_changes", commit_all)
    monkeypatch.setattr(handoff, "push_changes", MagicMock(return_value=True))
    monkeypatch.setattr(handoff, "IssueManager", MagicMock())
    monkeypatch.setattr(handoff, "update_workflow_label", MagicMock(return_value=True))

    assert (
        handoff._route_to_human(
            REVIEW_PLAN,
            tmp_path,
            issue_number=42,
            update_issue_labels=True,
            post_issue_comments=True,
            comment_body="handing off",
            log_path=log_path,
        )
        == 0
    )

    commit_all.assert_not_called()  # src/foo.py stays dirty
    stage.assert_called_once_with([log_path], tmp_path)
    commit_staged.assert_called_once()


# --- _fail (details param) -------------------------------------------------


def _capture_fail_comment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **kwargs: object
) -> str:
    """Call ``_fail`` with ``handle_workflow_failure`` patched; return the body."""
    net = MagicMock(name="handle_workflow_failure")
    monkeypatch.setattr(handoff, "handle_workflow_failure", net)

    result = handoff._fail(
        REVIEW_PLAN,
        tmp_path,
        "general",
        update_issue_labels=False,
        post_issue_comments=False,
        **kwargs,  # type: ignore[arg-type]
    )

    assert result == 1
    net.assert_called_once()
    comment_body = net.call_args.args[1]
    assert isinstance(comment_body, str)
    return comment_body


def test_fail_details_appears_right_after_header(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``details`` reads directly beneath the header, before Round/Verdict/Elapsed."""
    body = _capture_fail_comment(
        monkeypatch,
        tmp_path,
        round_number=2,
        elapsed=3.0,
        details="open tasks remain",
    )

    lines = body.split("\n")
    assert lines[0].startswith("❌ ")
    assert lines[1] == "open tasks remain"
    # The cause line precedes the enrichment lines.
    assert lines.index("open tasks remain") < lines.index("Round: 2")


def test_fail_default_details_none_is_backward_compatible(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """With ``details`` omitted, the body matches the pre-change output exactly."""
    with_kw = _capture_fail_comment(
        monkeypatch, tmp_path, round_number=2, elapsed=3.0, details=None
    )
    without_kw = _capture_fail_comment(
        monkeypatch, tmp_path, round_number=2, elapsed=3.0
    )

    assert with_kw == without_kw
    lines = with_kw.split("\n")
    assert lines[0].startswith("❌ ")
    # No extra/blank line was introduced between header and Round.
    assert lines[1] == "Round: 2"
