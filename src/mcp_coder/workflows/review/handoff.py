"""Terminal-routing helpers for the shared review engine.

This module owns the *terminal* paths of the review loop — the points where a
run stops and hands control back to labels / comments / a human. Step 4
relocates the two existing terminal helpers here verbatim (:func:`_set_label`
and :func:`_fail`); Step 6 adds the round-log flush and needs-human routing
helpers alongside them.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_workspace_github import IssueManager
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
