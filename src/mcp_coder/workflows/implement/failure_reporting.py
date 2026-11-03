"""Failure reporting helpers for the implement workflow.

Builds GitHub failure comments via the shared builder and coordinates label
updates / comment posting when the implement workflow fails. Failure *reasons*
are plain strings mapped to stage-specific label IDs via :data:`FAILURE_LABELS`;
the deliberate failure path is :func:`_fail`, while the net (SIGTERM /
unexpected exit) path is handled by
:func:`mcp_coder.workflow_utils.failure_handling.run_guarded`.
"""

import time
from dataclasses import dataclass
from pathlib import Path

from mcp_coder.workflow_utils.failure_handling import (
    CommentField,
    WorkflowFailure,
    build_failure_comment,
    get_diff_stat,
    handle_workflow_failure,
)
from mcp_coder.workflow_utils.task_tracker import get_task_counts

from .constants import PR_INFO_DIR

# Full implement failure taxonomy: reason string -> label ID in labels.json.
FAILURE_LABELS: dict[str, str] = {
    "general": "implementing_failed",
    "timeout": "llm_timeout",
    "mcp_unavailable": "mcp_unavailable",
    "task_tracker_prep_failed": "task_tracker_prep_failed",
    "no_changes_after_retries": "no_changes_after_retries",
    # Deliberately shares the label above: the operator action is identical
    # whether the agent did nothing or did plenty and moved nothing.
    "no_progress_after_retries": "no_changes_after_retries",
    "blocked": "implementation_blocked",
    "ci_fix_exhausted": "ci_fix_needed",
}

# Maps a reason -> the human-readable Category text used in the failure
# comment. Only `timeout` diverges from a naive title-cased reason: it must render
# "Llm Timeout", NOT "Timeout".
CATEGORY_DISPLAY: dict[str, str] = {
    "general": "General",
    "timeout": "Llm Timeout",
    "mcp_unavailable": "Mcp Unavailable",
    "task_tracker_prep_failed": "Task Tracker Prep Failed",
    "no_changes_after_retries": "No Changes After Retries",
    "no_progress_after_retries": "No Progress After Retries",
    "blocked": "Blocked",
    "ci_fix_exhausted": "Ci Fix Exhausted",
}


def append_detail(message: str, detail: str) -> str:
    """Append an agent-reported blocked reason to a failure message.

    Used where a typed LLM failure keeps its own label but a blocked marker was
    also present: the label stays actionable while the agent's text survives.

    Args:
        message: Base failure message.
        detail: Agent-reported reason; empty when no marker was found.

    Returns:
        ``message`` unchanged when ``detail`` is empty, else both combined.
    """
    return f"{message} (agent reported: {detail})" if detail else message


@dataclass
class Progress:
    """Mutable per-run task counter (completed this run, round-cap total).

    Attributes:
        completed: Number of tasks completed so far.
        total: Total number of tasks discovered for this run.
    """

    completed: int = 0
    total: int = 0


def _comment_parts(reason: str, project_dir: Path) -> tuple[list[CommentField], str]:
    """Category + Progress fields and the ### Uncommitted Changes section.

    Shared by the deliberate :func:`_fail` path and the ``run_guarded`` net.
    The Category is rendered from :data:`CATEGORY_DISPLAY` (falling back to the
    ``"general"`` display), not by title-casing ``reason``. Progress is the
    done/total count read from the task tracker; it is omitted when the
    tracker is missing, unparseable or has no tasks.

    Args:
        reason: Failure reason string (key of :data:`FAILURE_LABELS`).
        project_dir: Path to the project git repository.

    Returns:
        ``(fields, section)`` for :func:`build_failure_comment`.
    """
    category = CATEGORY_DISPLAY.get(reason, CATEGORY_DISPLAY["general"])
    try:
        total, done = get_task_counts(str(project_dir / PR_INFO_DIR))
    except Exception:  # pylint: disable=broad-exception-caught
        # Missing / unparseable tracker: the comment must still be posted.
        total, done = 0, 0
    progress_value = f"{done}/{total} tasks completed" if total > 0 else None
    diff = get_diff_stat(project_dir)
    section = f"### Uncommitted Changes\n```\n{diff or 'No uncommitted changes'}\n```"
    return [("Category", category), ("Progress", progress_value)], section


def _fail(
    project_dir: Path,
    reason: str,
    *,
    stage: str,
    message: str,
    start_time: float,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
) -> int:
    """Handle a deliberate implement failure: build comment, set label, log.

    Maps ``reason`` to its stage-specific label via :data:`FAILURE_LABELS`,
    builds the failure comment from the tracker progress and elapsed time, and
    delegates to the shared :func:`handle_workflow_failure`.

    Args:
        project_dir: Path to the project git repository.
        reason: Failure reason string (key of :data:`FAILURE_LABELS`).
        stage: Workflow stage where the failure occurred.
        message: Human-readable error description.
        start_time: Workflow start timestamp; elapsed is derived from it.
        update_issue_labels: Whether to attempt a label transition.
        post_issue_comments: Whether to post a failure comment.

    Returns:
        Always ``1`` (a deliberate, terminal failure exit code).
    """
    elapsed = time.time() - start_time
    fields, extra = _comment_parts(reason, project_dir)
    comment_body = build_failure_comment(
        project_dir,
        title="Implementation",
        kind="Failed",
        fields=[("Stage", stage), ("Error", message), *fields],
        elapsed=elapsed,
        extra_section=extra,
    )
    category = FAILURE_LABELS.get(reason, FAILURE_LABELS["general"])
    handle_workflow_failure(
        failure=WorkflowFailure(
            category=category,
            stage=stage,
            message=message,
            elapsed_time=elapsed,
        ),
        comment_body=comment_body,
        project_dir=project_dir,
        from_label_id="implementing",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )
    return 1
