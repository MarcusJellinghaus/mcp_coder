"""Helper functions for the create-pr workflow.

Contains failure handling utilities extracted from core.py to keep module
size manageable, and re-exports the PR text helpers from
``mcp_coder.workflow_steps.pr_description``.
"""

import logging
from pathlib import Path

from mcp_coder.workflow_steps.pr_description import (
    ensure_closing_reference as ensure_closing_reference,
)
from mcp_coder.workflow_steps.pr_description import (
    parse_pr_summary as parse_pr_summary,
)
from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure,
    build_failure_comment,
    handle_workflow_failure,
)

logger = logging.getLogger(__name__)


def handle_create_pr_failure(
    stage: str,
    message: str,
    project_dir: Path,
    update_issue_labels: bool,
    post_issue_comments: bool = False,
    elapsed_time: float | None = None,
    issue_number: int | None = None,
    pr_url: str | None = None,
    pr_number: int | None = None,
    is_cleanup_failure: bool = False,
    category: str = "pr_creating_failed",
) -> None:
    """Convenience wrapper: format comment + call shared handler.

    ``category`` is the label ID applied to the issue for this failure; it
    defaults to the general ``pr_creating_failed``, while the summary-generation
    catch passes the classified ``pr_creating_timeout`` / ``pr_creating_mcp``.
    """
    pr = f"[#{pr_number}]({pr_url})" if pr_url and pr_number else None
    note = (
        "> **Note:** pr_info/ directory may still exist on the branch"
        if is_cleanup_failure
        else None
    )
    comment = build_failure_comment(
        project_dir,
        title="PR Creation",
        kind="Failed",
        fields=[("Stage", stage), ("Error", message), ("PR", pr)],
        elapsed=elapsed_time,
        extra_section=note,
    )
    failure = WorkflowFailure(
        category=category,
        stage=stage,
        message=message,
        elapsed_time=elapsed_time,
    )
    handle_workflow_failure(
        failure=failure,
        comment_body=comment,
        project_dir=project_dir,
        from_label_id="pr_creating",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
        issue_number=issue_number,
    )
