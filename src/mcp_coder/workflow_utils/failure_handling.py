"""Shared workflow failure handling utilities.

Provides common failure handling logic used by both the implement and
create-pr workflows: failure logging, label transitions, and comment posting.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from mcp_coder.utils.git_operations.branch_queries import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.utils.git_operations.core import _safe_repo_context
from mcp_coder.utils.github_operations.issues import IssueManager

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WorkflowFailure:
    """Structured failure info shared across workflows.

    Attributes:
        category: Label ID in labels.json, e.g. "pr_creating_failed".
        stage: Workflow stage where failure occurred, e.g. "prerequisites".
        message: Human-readable error description.
        elapsed_time: Optional elapsed time in seconds.
    """

    category: str
    stage: str
    message: str
    elapsed_time: float | None = None


def get_diff_stat(project_dir: Path) -> str:
    """Get git diff --stat for uncommitted changes.

    Returns empty string on error.
    """
    try:
        with _safe_repo_context(project_dir) as repo:
            return str(repo.git.diff("HEAD", "--stat"))
    except Exception:  # pylint: disable=broad-exception-caught
        return ""


def format_elapsed_time(seconds: float) -> str:
    """Format seconds into human-readable string like '12m 34s' or '1h 5m 30s'."""
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


def handle_workflow_failure(
    failure: WorkflowFailure,
    comment_body: str,
    project_dir: Path,
    from_label_id: str,
    update_labels: bool = False,
    issue_number: int | None = None,
) -> None:
    """Handle workflow failure: log banner, set label, post comment.

    Label update respects the ``update_labels`` flag.  The comment is
    always posted regardless of ``update_labels``.

    Args:
        failure: Structured failure information.
        comment_body: Pre-formatted comment body to post on the issue.
        project_dir: Path to the project git repository.
        from_label_id: Current workflow label ID to transition from.
        update_labels: Whether to attempt a label transition.
        issue_number: Caller-provided issue number; falls back to branch
            name extraction when *None*.
    """
    # 1. Log failure banner
    logger.info("=" * 60)
    logger.info("WORKFLOW FAILED")
    logger.info("Category: %s", failure.category)
    logger.info("Stage: %s", failure.stage)
    logger.info("Error: %s", failure.message)
    logger.info("=" * 60)

    # 2. Set failure label (non-blocking)
    if update_labels:
        try:
            issue_manager = IssueManager(project_dir)
            issue_manager.update_workflow_label(
                from_label_id=from_label_id,
                to_label_id=failure.category,
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to update issue label: %s", exc)

    # 3. Resolve issue number
    resolved_issue_number = issue_number
    if resolved_issue_number is None:
        try:
            branch_name = get_current_branch_name(project_dir)
            resolved_issue_number = (
                extract_issue_number_from_branch(branch_name) if branch_name else None
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to extract issue number from branch: %s", exc)

    # 4. Post GitHub comment (non-blocking)
    if resolved_issue_number is not None:
        try:
            mgr = IssueManager(project_dir)
            mgr.add_comment(resolved_issue_number, comment_body)
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to post failure comment: %s", exc)
