"""PR health checks for status-10 issues: merge conflicts, CI, and review comments."""

import logging

from ...mcp_workspace_github import (
    BaseGitHubManager,
    CIResultsManager,
    EventData,
    IssueBranchManager,
    IssueData,
    IssueEventType,
    IssueManager,
    PullRequestManager,
)
from ...workflow_utils.label_transitions import update_workflow_label

logger = logging.getLogger(__name__)


def _build_pr_manager(repo_url: str) -> PullRequestManager:
    """Build a PullRequestManager from a repo URL only, no local checkout.

    Bypasses PullRequestManager.__init__ (which requires project_dir) the
    same way label_transitions.py already does for IssueBranchManager.

    Returns:
        A PullRequestManager instance backed by the given repo URL.
    """
    manager = PullRequestManager.__new__(PullRequestManager)
    BaseGitHubManager.__init__(manager, repo_url=repo_url)
    return manager


def _review_comments_watermark(
    events: list[EventData],
    review_label_name: str,
    created_label_name: str,
) -> str | None:
    """Derive the comment-watermark timestamp from an issue's label history.

    Returns:
        The ``created_at`` of the ``status-10`` relabel that followed the
        last ``status-91`` event, or ``None`` if there is no such event pair
        (first-ever arrival, or no relabel followed it) — meaning "no
        filter, every existing comment counts."
    """
    last_review_idx: int | None = None
    for idx, event in enumerate(events):
        if event["label"] == review_label_name:
            last_review_idx = idx

    if last_review_idx is None:
        return None

    for event in events[last_review_idx + 1 :]:
        if event["label"] == created_label_name:
            return event["created_at"]

    return None


def _check_merge_conflict(
    issue: IssueData,
    branch_manager: IssueBranchManager,
    issue_manager: IssueManager,
    repo_owner: str,
    repo_name: str,
) -> bool:
    """Escalate a status-10 PR to status-71 if GitHub reports it as "dirty".

    Never raises: any failure is logged and swallowed so one bad issue
    can't block the rest of the batch this poll.

    Returns:
        True iff the issue was escalated to merge_conflict this call.
    """
    try:
        branch = branch_manager.get_branch_with_pr_fallback(
            issue["number"], repo_owner, repo_name
        )
        if branch is None:
            return False
        pr_manager = _build_pr_manager(f"https://github.com/{repo_owner}/{repo_name}")
        prs = pr_manager.find_pull_request_by_head(branch)
        if prs and prs[0]["mergeable_state"] == "dirty":
            update_workflow_label(
                issue_manager,
                "pr_created",
                "merge_conflict",
                validated_issue_number=issue["number"],
            )
            return True
        return False
    except (
        Exception
    ) as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        logger.warning(
            "Failed to check merge conflict for issue #%d: %s",
            issue["number"],
            exc,
        )
        return False


def _check_ci(
    issue: IssueData,
    ci_manager: CIResultsManager,
    branch_manager: IssueBranchManager,
    issue_manager: IssueManager,
    repo_owner: str,
    repo_name: str,
) -> bool:
    """Escalate a status-10 PR to status-81 if its latest CI run failed.

    Never raises: any failure is logged and swallowed so one bad issue
    can't block the rest of the batch this poll.

    Returns:
        True iff the issue was escalated to failing_ci this call.
    """
    try:
        branch = branch_manager.get_branch_with_pr_fallback(
            issue["number"], repo_owner, repo_name
        )
        if branch is None:
            return False
        status = ci_manager.get_latest_ci_status(branch)
        run = status.get("run", {})
        if run.get("status") == "completed" and run.get("conclusion") != "success":
            update_workflow_label(
                issue_manager,
                "pr_created",
                "failing_ci",
                validated_issue_number=issue["number"],
            )
            return True
        return False
    except (
        Exception
    ) as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        logger.warning(
            "Failed to check CI status for issue #%d: %s",
            issue["number"],
            exc,
        )
        return False


def _check_review_comments(
    issue: IssueData,
    branch_manager: IssueBranchManager,
    issue_manager: IssueManager,
    repo_owner: str,
    repo_name: str,
    review_label_name: str,
    created_label_name: str,
) -> bool:
    """Escalate a status-10 PR to status-91 on new review feedback.

    Never raises: any failure is logged and swallowed so one bad issue
    can't block the rest of the batch this poll.

    Returns:
        True iff the issue was escalated to pr_review_comments this call.
    """
    try:
        branch = branch_manager.get_branch_with_pr_fallback(
            issue["number"], repo_owner, repo_name
        )
        if branch is None:
            return False
        pr_manager = _build_pr_manager(f"https://github.com/{repo_owner}/{repo_name}")
        prs = pr_manager.find_pull_request_by_head(branch)
        if not prs:
            return False
        feedback = pr_manager.get_pr_feedback(prs[0]["number"])
        if feedback["unresolved_threads"] or feedback["changes_requested"]:
            triggered = True
        else:
            events = issue_manager.get_issue_events(
                issue["number"], IssueEventType.LABELED
            )
            watermark = _review_comments_watermark(
                events, review_label_name, created_label_name
            )
            triggered = any(
                comment["created_at"] is None
                or watermark is None
                or comment["created_at"] > watermark
                for comment in feedback["conversation_comments"]
            )
        if triggered:
            update_workflow_label(
                issue_manager,
                "pr_created",
                "pr_review_comments",
                validated_issue_number=issue["number"],
            )
            return True
        return False
    except (
        Exception
    ) as exc:  # pylint: disable=broad-exception-caught  # non-blocking by design
        logger.warning(
            "Failed to check review comments for issue #%d: %s",
            issue["number"],
            exc,
        )
        return False
