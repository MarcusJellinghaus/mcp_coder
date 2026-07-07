"""Failure reporting helpers for the implement workflow.

Formats GitHub failure comments and coordinates label updates / comment posting
when the implement workflow fails.
"""

from pathlib import Path

from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure as SharedWorkflowFailure,
)
from mcp_coder.workflow_utils.failure_handling import (
    format_elapsed_time,
    get_diff_stat,
    handle_workflow_failure,
)

from .constants import WorkflowFailure


def _format_failure_comment(failure: WorkflowFailure, diff_stat: str) -> str:
    """Format a GitHub comment for a workflow failure.

    Args:
        failure: The workflow failure details
        diff_stat: Git diff stat string for uncommitted changes

    Returns:
        Formatted GitHub comment string.
    """
    lines = [
        "## Implementation Failed",
        f"**Category:** {failure.category.name.replace('_', ' ').title()}",
        f"**Stage:** {failure.stage}",
        f"**Error:** {failure.message}",
    ]
    if failure.tasks_total > 0:
        lines.append(
            f"**Progress:** {failure.tasks_completed}/{failure.tasks_total} tasks completed"
        )
    if failure.elapsed_time is not None:
        lines.append(f"**Elapsed:** {format_elapsed_time(failure.elapsed_time)}")
    if failure.build_url:
        lines.append(f"**Build:** {failure.build_url}")
    lines.append("")
    lines.append("### Uncommitted Changes")
    lines.append(f"```\n{diff_stat or 'No uncommitted changes'}\n```")
    return "\n".join(lines)


def _handle_workflow_failure(
    failure: WorkflowFailure,
    project_dir: Path,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
) -> None:
    """Handle workflow failure: set label, post comment, log banner."""
    diff_stat = get_diff_stat(project_dir)
    comment_body = _format_failure_comment(failure, diff_stat)
    handle_workflow_failure(
        failure=SharedWorkflowFailure(
            category=failure.category.value,
            stage=failure.stage,
            message=failure.message,
            elapsed_time=failure.elapsed_time,
        ),
        comment_body=comment_body,
        project_dir=project_dir,
        from_label_id="implementing",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )
