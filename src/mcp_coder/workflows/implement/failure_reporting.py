"""Failure reporting helpers for the implement workflow.

Formats GitHub failure comments and coordinates label updates / comment posting
when the implement workflow fails. Failure *reasons* are plain strings mapped to
stage-specific label IDs via :data:`FAILURE_LABELS`; the deliberate failure path
is :func:`_fail`, while the net (SIGTERM / unexpected exit) path is handled by
:func:`mcp_coder.workflow_utils.failure_handling.run_guarded`.
"""

import time
from dataclasses import dataclass
from pathlib import Path

from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    format_elapsed_time,
    get_diff_stat,
    handle_workflow_failure,
)

# Full implement failure taxonomy: reason string -> label ID in labels.json.
FAILURE_LABELS: dict[str, str] = {
    "general": "implementing_failed",
    "timeout": "llm_timeout",
    "mcp_unavailable": "mcp_unavailable",
    "task_tracker_prep_failed": "task_tracker_prep_failed",
    "no_changes_after_retries": "no_changes_after_retries",
    "blocked": "implementation_blocked",
    "ci_fix_exhausted": "ci_fix_needed",
}

# Maps a reason -> the exact human-readable Category text used in the failure
# comment, so the rendered comment stays byte-identical to earlier releases.
# Only `timeout` diverges from a naive title-cased reason: it must render
# "Llm Timeout", NOT "Timeout".
CATEGORY_DISPLAY: dict[str, str] = {
    "general": "General",
    "timeout": "Llm Timeout",
    "mcp_unavailable": "Mcp Unavailable",
    "task_tracker_prep_failed": "Task Tracker Prep Failed",
    "no_changes_after_retries": "No Changes After Retries",
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
    """Mutable task-progress holder bridging the body to the net's comment.

    Attributes:
        completed: Number of tasks completed so far.
        total: Total number of tasks discovered for this run.
    """

    completed: int = 0
    total: int = 0


def format_failure_comment(
    reason: str,
    stage: str,
    message: str,
    *,
    completed: int,
    total: int,
    elapsed: float | None,
    build_url: str | None,
    diff_stat: str,
) -> str:
    """Format a GitHub comment for an implement workflow failure.

    Reproduces the historical ``_format_failure_comment`` output byte-for-byte.
    The Category line is rendered from :data:`CATEGORY_DISPLAY` (falling back to
    the ``"general"`` display), not by title-casing ``reason`` — title-casing
    ``"timeout"`` would yield ``"Timeout"`` whereas the comment must render
    ``"Llm Timeout"``.

    Args:
        reason: Failure reason string (key of :data:`FAILURE_LABELS`).
        stage: Workflow stage where the failure occurred.
        message: Human-readable error description.
        completed: Tasks completed so far (progress line shown when total > 0).
        total: Total tasks discovered (progress line shown when > 0).
        elapsed: Optional elapsed time in seconds.
        build_url: Optional CI build URL.
        diff_stat: Git diff stat string for uncommitted changes.

    Returns:
        Formatted GitHub comment string.
    """
    lines = [
        "## Implementation Failed",
        f"**Category:** {CATEGORY_DISPLAY.get(reason, CATEGORY_DISPLAY['general'])}",
        f"**Stage:** {stage}",
        f"**Error:** {message}",
    ]
    if total > 0:
        lines.append(f"**Progress:** {completed}/{total} tasks completed")
    if elapsed is not None:
        lines.append(f"**Elapsed:** {format_elapsed_time(elapsed)}")
    if build_url:
        lines.append(f"**Build:** {build_url}")
    lines.append("")
    lines.append("### Uncommitted Changes")
    lines.append(f"```\n{diff_stat or 'No uncommitted changes'}\n```")
    return "\n".join(lines)


def _fail(
    project_dir: Path,
    reason: str,
    *,
    stage: str,
    message: str,
    progress: Progress,
    start_time: float,
    build_url: str | None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
) -> int:
    """Handle a deliberate implement failure: build comment, set label, log.

    Maps ``reason`` to its stage-specific label via :data:`FAILURE_LABELS`,
    formats the failure comment from the live progress/elapsed/build context,
    and delegates to the shared :func:`handle_workflow_failure`.

    Args:
        project_dir: Path to the project git repository.
        reason: Failure reason string (key of :data:`FAILURE_LABELS`).
        stage: Workflow stage where the failure occurred.
        message: Human-readable error description.
        progress: Mutable progress holder read for the comment.
        start_time: Workflow start timestamp; elapsed is derived from it.
        build_url: Optional CI build URL.
        update_issue_labels: Whether to attempt a label transition.
        post_issue_comments: Whether to post a failure comment.

    Returns:
        Always ``1`` (a deliberate, terminal failure exit code).
    """
    elapsed = time.time() - start_time
    diff_stat = get_diff_stat(project_dir)
    comment_body = format_failure_comment(
        reason,
        stage,
        message,
        completed=progress.completed,
        total=progress.total,
        elapsed=elapsed,
        build_url=build_url,
        diff_stat=diff_stat,
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
