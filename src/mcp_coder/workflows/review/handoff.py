"""Terminal-routing helpers for the shared review engine.

This module owns the *terminal* paths of the review loop — the points where a
run stops and hands control back to labels / comments / a human. Step 4
relocates the two existing terminal helpers here verbatim (:func:`_set_label`
and :func:`_fail`); Step 6 adds the round-log flush and needs-human routing
helpers alongside them.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_workspace_git import (
    commit_all_changes,
    commit_staged_files,
    stage_specific_files,
)
from mcp_coder.mcp_workspace_github import IssueManager
from mcp_coder.workflow_steps.commit import push_changes
from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    format_elapsed_time,
    handle_workflow_failure,
)
from mcp_coder.workflow_utils.label_transitions import update_workflow_label

from .config import ReviewConfig
from .verdict import Verdict

logger = logging.getLogger(__name__)


def _set_label(
    config: ReviewConfig,
    project_dir: Path,
    to_label_id: str,
    update_issue_labels: bool,
) -> None:
    """Apply a workflow label transition from the busy label, if gating allows.

    Mirrors ``implement/core.py``: gated on ``update_issue_labels`` and given a
    fresh ``IssueManager`` as its first arg, wrapped so a label failure never
    breaks the workflow.

    Args:
        config: The review workflow config (provides ``busy_label_id``).
        project_dir: Repository root.
        to_label_id: Terminal label id to transition to.
        update_issue_labels: When False, this is a no-op.
    """
    if not update_issue_labels:
        return
    try:
        issue_manager = IssueManager(project_dir)
        update_workflow_label(
            issue_manager,
            from_label_id=config.busy_label_id,
            to_label_id=to_label_id,
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Failed to update issue label to '%s': %s", to_label_id, exc)


def _fail(
    config: ReviewConfig,
    project_dir: Path,
    reason: str,
    *,
    update_issue_labels: bool,
    post_issue_comments: bool,
    round_number: int | None = None,
    verdict: Verdict | None = None,
    elapsed: float | None = None,
    details: str | None = None,
) -> int:
    """Route a terminal error through the shared failure handler; return ``1``.

    The comment is enriched — when the values are supplied by the call site (all
    of which are lexically inside the round loop, where these are live locals) —
    with the current round number, the most recently parsed verdict decision,
    and the elapsed wall-clock time.

    Args:
        config: The review workflow config (provides busy + failure labels).
        project_dir: Repository root.
        reason: Failure reason key into ``config.failure_labels``.
        update_issue_labels: Whether to apply the failure label transition.
        post_issue_comments: Whether to post a failure comment on the issue.
        round_number: Current review round, appended to the comment when given.
        verdict: Most recent verdict, whose ``decision`` is appended when given.
        elapsed: Elapsed seconds since the run started, appended when given.
        details: Human-readable cause line, inserted directly beneath the
            header (before Round/Verdict/Elapsed) when given.

    Returns:
        Always ``1``.
    """
    category = config.failure_labels.get(reason, config.failure_labels["general"])
    message = f"{config.name} review failed: {reason}"
    failure = WorkflowFailure(
        category=category,
        stage="Review",
        message=message,
        elapsed_time=elapsed,
    )
    comment_lines = [f"❌ {message}"]
    if details is not None:
        comment_lines.append(details)
    if round_number is not None:
        comment_lines.append(f"Round: {round_number}")
    if verdict is not None:
        comment_lines.append(f"Verdict: {verdict.decision}")
    if elapsed is not None:
        comment_lines.append(f"Elapsed: {format_elapsed_time(elapsed)}")
    comment_body = "\n".join(comment_lines)
    handle_workflow_failure(
        failure,
        comment_body,
        project_dir,
        from_label_id=config.busy_label_id,
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )
    return 1


def _flush_round_log(
    project_dir: Path,
    message: str = "Add review round log",
    *,
    only: Path | None = None,
    push: bool = True,
) -> None:
    """Commit (and usually push) an already-written round log; best-effort.

    The round body always *writes* its log to the working tree. Two kinds of
    caller land that entry in the *committed* review log: the terminal paths,
    which commit the whole tree and push; and the top of the round loop, which
    lands the *previous* round's write scoped to that one file and without
    pushing (``only=``/``push=False``), so the next round's rebase is not
    refused for unstaged changes. Neither re-writes the log — the caller wrote
    it first.

    The push is skipped when the commit failed, when it succeeded but committed
    nothing (``commit_hash is None``), when ``only=`` could not be staged, and
    whenever ``push=False``.

    Every git call reports failure by return value rather than by raising
    (``stage_specific_files``/``push_changes`` return ``bool``;
    ``commit_all_changes``/``commit_staged_files`` return a ``CommitResult``),
    so each falsy result is checked and warned. A broad ``try/except``
    additionally swallows any unexpected raise so a broken-commit terminal path
    never recurses into a second failure.

    Args:
        project_dir: Repository root; git ops target this.
        message: Commit message for the round-log commit.
        only: When given, commit *only* this path — ``stage_specific_files``
            plus ``commit_staged_files`` instead of ``commit_all_changes``, so
            an arbitrarily dirty tree can never ride along under ``message``.
        push: When False, leave the commit local; the caller's own push carries
            it.
    """
    try:
        if only is not None:
            if not stage_specific_files([only], project_dir):
                logger.warning(
                    "Could not stage the round log %s - not committing", only
                )
                return
            result = commit_staged_files(message, project_dir)
        else:
            result = commit_all_changes(message, project_dir)
        if not result["success"]:
            logger.warning(
                "Round-log commit did not succeed: %s",
                result.get("error") or "unknown error",
            )
            return
        if result["commit_hash"] is None:
            logger.debug("Round-log commit had nothing to commit")
            return
        if not push:
            return
        if not push_changes(project_dir):
            logger.warning("Round-log push did not succeed")
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.warning("Round-log flush failed: %s", exc)


def _route_to_human(
    config: ReviewConfig,
    project_dir: Path,
    *,
    issue_number: int | None,
    update_issue_labels: bool,
    post_issue_comments: bool,
    comment_body: str,
) -> int:
    """Hand a converged-but-unresolved run off to a human; return ``0``.

    A needs-human terminal path (escalate verdict, unresolved rebase, or the
    rounds cap): flush the last round's log to the committed review log, post a
    single human-readable issue comment (gated), then transition to the
    ``escalate_label_id`` recovery label. Unlike :func:`_fail`, this is **not**
    an error — it returns ``0`` and never touches a failure label.

    Args:
        config: The review workflow config (provides ``escalate_label_id``).
        project_dir: Repository root.
        issue_number: Issue to comment on, or ``None`` to skip the comment.
        update_issue_labels: Whether to apply the escalate label transition.
        post_issue_comments: Whether to post the handoff comment.
        comment_body: Human-readable explanation of why the run handed off.

    Returns:
        Always ``0``.
    """
    _flush_round_log(project_dir)
    if post_issue_comments and issue_number is not None:
        try:
            IssueManager(project_dir).add_comment(issue_number, comment_body)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to post handoff comment: %s", exc)
    _set_label(config, project_dir, config.escalate_label_id, update_issue_labels)
    return 0
