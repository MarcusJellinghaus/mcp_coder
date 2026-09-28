"""Step 6 — handoff routing tests (``_route_to_human`` + ``_fail``).

``_route_to_human`` must flush the round log, post a gated comment, transition
to the escalate label, and return ``0``.

Step 4 adds ``_fail`` coverage for the optional ``details`` line, which reads
directly beneath the ``❌`` header and is backward compatible when omitted.

The ``_flush_round_log`` helper these exercise is covered on its own in
``test_handoff.py``.
"""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from git import Repo

from mcp_coder.mcp_workspace_git import get_full_status
from mcp_coder.workflows.review import handoff
from mcp_coder.workflows.review.config import REVIEW_PLAN

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


@pytest.mark.git_integration
def test_route_lands_the_round_log_over_an_unrelated_staged_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Against a real repo: the round log lands, the staged file does not.

    The unresolved-rebase handoff is reached precisely because the tree is
    dirty, and that dirt may be *staged*. The round log must still reach the
    committed review log, and the unrelated staged entry must stay staged and
    uncommitted for ``_attempt_rebase_and_push``'s tripwire to name.
    """
    repo = Repo.init(tmp_path)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")
        config.set_value("commit", "gpgsign", "false")
    # LF bytes throughout: with core.autocrlf on, a CRLF working-tree file is
    # hashed differently by GitPython's staging and by the git CLI's commit,
    # which would muddy the index assertions below without testing anything.
    (tmp_path / "README.md").write_bytes(b"# Test\n")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")

    # Someone else's work, already staged.
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "unrelated.py").write_bytes(b"x = 1\n")
    repo.index.add(["src/unrelated.py"])
    repo.index.write()

    # The round the handoff must not lose.
    log_path = tmp_path / "pr_info" / "plan_review_log_1.md"
    log_path.parent.mkdir()
    log_path.write_bytes(b"## Round 3\nEscalate reason: rebase\n")

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

    committed = repo.git.show("HEAD:pr_info/plan_review_log_1.md")
    assert "Escalate reason: rebase" in committed
    touched = repo.git.show("--pretty=format:", "--name-only", "HEAD").split()
    assert touched == ["pr_info/plan_review_log_1.md"]
    assert get_full_status(tmp_path)["staged"] == ["src/unrelated.py"]


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
