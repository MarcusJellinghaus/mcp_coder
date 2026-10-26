"""Step 6 — handoff routing tests (``_route_to_human`` + ``_fail``).

``_route_to_human`` must flush the round log, post a gated structured
``## ❌ <Lane> Handed Off`` comment, transition to the escalate label, and
return ``0``. Rebase hand-offs take their fields from ``_REBASE_HANDOFF``.

``_fail`` renders the structured ``## ❌ <Lane> Failed`` comment; ``details``,
when given, replaces the reason's default Error sentence.

The ``_flush_round_log`` helper these exercise is covered on its own in
``test_handoff.py``.
"""

import logging
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from git import Repo

from mcp_coder.mcp_workspace_git import get_full_status
from mcp_coder.workflow_steps.rebase import RebaseOutcome
from mcp_coder.workflows.review import handoff
from mcp_coder.workflows.review.config import (
    REVIEW_IMPLEMENTATION,
    REVIEW_PLAN,
    ReviewConfig,
)
from mcp_coder.workflows.review.verdict import Verdict

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
        round_number=1,
        start_time=time.time(),
        category="X",
        reason="Y",
        log_path=log_path,
    )

    assert result == 0
    routed.flush.assert_called_once_with(tmp_path, only=log_path)
    routed.issue_manager.return_value.add_comment.assert_called_once()
    issue, body = routed.issue_manager.return_value.add_comment.call_args.args
    assert issue == 42
    lines = body.splitlines()
    assert lines[0] == "## ❌ Plan Review Handed Off"
    assert "**Category:** X" in lines
    assert "**Reason:** Y" in lines
    assert "**Stage:** Plan Review, round 1" in lines
    routed.update_workflow_label.assert_called_once()
    kwargs = routed.update_workflow_label.call_args.kwargs
    assert kwargs["from_label_id"] == REVIEW_PLAN.busy_label_id
    assert kwargs["to_label_id"] == REVIEW_PLAN.escalate_label_id


def test_route_flushes_before_posting_the_comment(
    routed: SimpleNamespace, tmp_path: Path
) -> None:
    """The round log lands before the hand-off comment is posted."""
    parent = MagicMock()
    parent.attach_mock(routed.flush, "flush")
    parent.attach_mock(routed.issue_manager.return_value.add_comment, "add_comment")

    handoff._route_to_human(
        REVIEW_PLAN,
        tmp_path,
        issue_number=42,
        update_issue_labels=True,
        post_issue_comments=True,
        log_path=tmp_path / "pr_info" / "plan_review_log_1.md",
        round_number=1,
        start_time=time.time(),
        category="X",
        reason="Y",
    )

    names = [c[0] for c in parent.mock_calls]
    assert names.index("flush") < names.index("add_comment")


def test_route_logs_a_handed_off_banner(
    routed: SimpleNamespace, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A ``REVIEW HANDED OFF`` warning banner names lane, reason, round, label."""
    with caplog.at_level(logging.WARNING, logger=handoff.__name__):
        handoff._route_to_human(
            REVIEW_IMPLEMENTATION,
            tmp_path,
            issue_number=42,
            update_issue_labels=False,
            post_issue_comments=False,
            log_path=None,
            round_number=3,
            start_time=time.time(),
            category="X",
            reason="Y",
        )

    messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert "REVIEW HANDED OFF" in messages
    assert "Lane: Implementation Review" in messages
    assert "Reason: Y" in messages
    assert "Round: 3" in messages
    assert f"Target label: {REVIEW_IMPLEMENTATION.escalate_label_id}" in messages


_FILES = ("src/a.py", "src/b.py")


def _rebase_outcome(reason: str) -> RebaseOutcome:
    """Build the outcome ``_attempt_rebase_and_push`` returns for ``reason``."""
    if reason == "dirty_tree":
        return RebaseOutcome("dirty_tree", files=_FILES)
    if reason == "no_base":
        return RebaseOutcome("no_base")
    if reason == "base_missing":
        return RebaseOutcome("base_missing", "main")
    if reason == "conflict":
        return RebaseOutcome("conflict", "main", "def5678", _FILES)
    if reason == "rebase_failed":
        return RebaseOutcome("rebase_failed", "main", "def5678")
    return RebaseOutcome("push_failed", "main", "def5678")


def _rebase_comment(routed: SimpleNamespace, tmp_path: Path, reason: str) -> str:
    """Route a rebase hand-off for ``reason`` and return the posted comment."""
    handoff._route_to_human(
        REVIEW_IMPLEMENTATION,
        tmp_path,
        issue_number=42,
        update_issue_labels=True,
        post_issue_comments=True,
        log_path=None,
        round_number=2,
        start_time=time.time(),
        rebase=_rebase_outcome(reason),
    )
    body: str = routed.issue_manager.return_value.add_comment.call_args.args[1]
    return body


@pytest.mark.parametrize("reason", sorted(handoff._REBASE_HANDOFF))
def test_rebase_handoff_fields_follow_the_table(
    routed: SimpleNamespace, tmp_path: Path, reason: str
) -> None:
    """Category, Reason and Next step come from ``_REBASE_HANDOFF``."""
    category, reason_text, next_step = handoff._REBASE_HANDOFF[reason]

    lines = _rebase_comment(routed, tmp_path, reason).splitlines()

    assert lines[0] == "## ❌ Implementation Review Handed Off"
    assert f"**Category:** {category}" in lines
    assert f"**Reason:** {reason_text}" in lines
    assert f"**Next step:** {next_step}" in lines
    assert "**Stage:** Implementation Review, round 2" in lines
    assert routed.update_workflow_label.call_args.kwargs["to_label_id"] == (
        REVIEW_IMPLEMENTATION.escalate_label_id
    )


@pytest.mark.parametrize(
    ("reason", "expected"),
    [
        (
            "dirty_tree",
            "Rebase not attempted: the working tree has staged or modified "
            "tracked files",
        ),
        ("no_base", "Rebase not attempted: no base branch could be detected"),
        (
            "base_missing",
            "Rebase not attempted: the base branch does not exist on origin",
        ),
        ("conflict", "Rebase onto the base branch stopped on a conflict"),
        (
            "rebase_failed",
            "Rebase onto the base branch failed and was not classified as a conflict",
        ),
        ("push_failed", "Rebase succeeded, but the force-with-lease push failed"),
    ],
)
def test_rebase_handoff_reason_line(
    routed: SimpleNamespace, tmp_path: Path, reason: str, expected: str
) -> None:
    """Each reason renders its exact Reason line."""
    lines = _rebase_comment(routed, tmp_path, reason).splitlines()

    assert f"**Reason:** {expected}" in lines


@pytest.mark.parametrize("reason", ["dirty_tree", "push_failed"])
def test_rebase_handoff_does_not_suggest_rebase(
    routed: SimpleNamespace, tmp_path: Path, reason: str
) -> None:
    """A dirty tree or a failed push is not fixed by ``/rebase``."""
    assert "/rebase" not in _rebase_comment(routed, tmp_path, reason)


@pytest.mark.parametrize(
    ("reason", "base_line"),
    [
        ("conflict", "**Base:** origin/main @ def5678"),
        ("rebase_failed", "**Base:** origin/main @ def5678"),
        ("push_failed", "**Base:** origin/main @ def5678"),
        ("base_missing", "**Base:** origin/main"),
        ("dirty_tree", None),
        ("no_base", None),
    ],
)
def test_rebase_handoff_base_line(
    routed: SimpleNamespace, tmp_path: Path, reason: str, base_line: str | None
) -> None:
    """Base carries the SHA when known, the branch alone when not, else absent."""
    lines = _rebase_comment(routed, tmp_path, reason).splitlines()

    base_lines = [line for line in lines if line.startswith("**Base:**")]
    assert base_lines == ([base_line] if base_line else [])


@pytest.mark.parametrize("reason", sorted(handoff._REBASE_HANDOFF))
def test_rebase_handoff_files_field(
    routed: SimpleNamespace, tmp_path: Path, reason: str
) -> None:
    """Conflict lists likely conflicting files; dirty tree lists uncommitted ones."""
    body = _rebase_comment(routed, tmp_path, reason)
    files = "`src/a.py`, `src/b.py`"

    conflicting = f"**Likely conflicting files:** {files}" in body.splitlines()
    uncommitted = f"**Uncommitted files:** {files}" in body.splitlines()
    assert conflicting == (reason == "conflict")
    assert uncommitted == (reason == "dirty_tree")
    assert ("**Likely conflicting files:**" in body) == (reason == "conflict")
    assert ("**Uncommitted files:**" in body) == (reason == "dirty_tree")


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
        round_number=1,
        start_time=time.time(),
        category="X",
        reason="Y",
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
        round_number=1,
        start_time=time.time(),
        category="X",
        reason="Y",
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
        round_number=1,
        start_time=time.time(),
        category="X",
        reason="Y",
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
        round_number=1,
        start_time=time.time(),
        category="X",
        reason="Y",
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
        round_number=1,
        start_time=time.time(),
        category="X",
        reason="Y",
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
    commit_paths = MagicMock(
        return_value={
            "success": True,
            "commit_hash": "abc1234",
            "error": None,
            "error_category": None,
            "returncode": 0,
            "stderr": "",
        }
    )
    commit_all = MagicMock()
    monkeypatch.setattr(handoff, "stage_specific_files", stage)
    monkeypatch.setattr(handoff, "commit_paths", commit_paths)
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
            round_number=1,
            start_time=time.time(),
            category="X",
            reason="Y",
            log_path=log_path,
        )
        == 0
    )

    commit_all.assert_not_called()  # src/foo.py stays dirty
    stage.assert_called_once_with([log_path], tmp_path)
    commit_paths.assert_called_once_with("Add review round log", [log_path], tmp_path)


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
            round_number=1,
            start_time=time.time(),
            category="X",
            reason="Y",
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
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    reason: str = "general",
    config: ReviewConfig = REVIEW_PLAN,
    **kwargs: object,
) -> str:
    """Call ``_fail`` with ``handle_workflow_failure`` patched; return the body."""
    monkeypatch.delenv("BUILD_URL", raising=False)
    net = MagicMock(name="handle_workflow_failure")
    monkeypatch.setattr(handoff, "handle_workflow_failure", net)

    result = handoff._fail(
        config,
        tmp_path,
        reason,
        update_issue_labels=False,
        post_issue_comments=False,
        **kwargs,  # type: ignore[arg-type]
    )

    assert result == 1
    net.assert_called_once()
    comment_body = net.call_args.args[1]
    assert isinstance(comment_body, str)
    return comment_body


def test_fail_renders_structured_comment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """In-loop ``_fail`` renders the Failed heading and bold-label fields."""
    body = _capture_fail_comment(
        monkeypatch,
        tmp_path,
        "ci",
        REVIEW_IMPLEMENTATION,
        round_number=3,
        verdict=Verdict(decision="tasks", tasks=["x"]),
        elapsed=75.0,
    )

    assert body.splitlines() == [
        "## ❌ Implementation Review Failed",
        "**Category:** CI failed",
        "**Stage:** Implementation Review, round 3",
        "**Error:** CI is still red after the review",
        "**Branch:** feat @ abc1234",
        "**Verdict:** tasks",
        "**Elapsed:** 1m 15s",
    ]


def test_fail_details_replace_the_reason_sentence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``details`` given -> it is the Error; the reason sentence is not used."""
    body = _capture_fail_comment(
        monkeypatch, tmp_path, "tasks", round_number=2, details="open tasks remain"
    )

    lines = body.splitlines()
    assert lines[0] == "## ❌ Plan Review Failed"
    assert "**Error:** open tasks remain" in lines
    assert "**Category:** Open tasks" in lines


def test_fail_without_details_uses_the_reason_sentence(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``details`` omitted (or ``None``) -> the reason's default sentence."""
    with_kw = _capture_fail_comment(monkeypatch, tmp_path, "timeout", details=None)
    without_kw = _capture_fail_comment(monkeypatch, tmp_path, "timeout")

    assert with_kw == without_kw
    assert "**Error:** An LLM call timed out" in with_kw.splitlines()


def test_fail_pre_loop_stage_is_the_lane_name(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """``round_number=None`` (pre-loop gates) -> Stage carries no round."""
    body = _capture_fail_comment(monkeypatch, tmp_path, details="bad formatter")

    lines = body.splitlines()
    assert "**Stage:** Plan Review" in lines
    assert not any(line.startswith("**Verdict:**") for line in lines)
    assert not any(line.startswith("**Elapsed:**") for line in lines)


def test_fail_unknown_reason_falls_back_to_general(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """An unknown reason key renders the ``general`` Category and sentence."""
    body = _capture_fail_comment(monkeypatch, tmp_path, "no-such-reason")

    lines = body.splitlines()
    assert "**Category:** General" in lines
    assert (
        "**Error:** The review stopped on an unrecoverable error; check the job log"
        in lines
    )
