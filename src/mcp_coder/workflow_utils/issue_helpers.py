"""Issue helpers shared by workflows: status label, comment marker, linked branch."""

import logging

from mcp_coder.mcp_workspace_github import (
    BranchLookupCache,
    BranchLookupError,
    GithubException,
    IssueData,
)

logger = logging.getLogger(__name__)

__all__ = ["get_issue_status", "is_marked", "lookup_branch"]


def get_issue_status(issue: IssueData) -> str:
    """Get the status label from an issue.

    Args:
        issue: Issue data dict

    Returns:
        Status label string or empty string if none found
    """
    for label in issue["labels"]:
        if label.startswith("status-"):
            return label
    return ""


def is_marked(body: str, marker: str = "❌") -> bool:
    """Return True if the first line of ``body`` contains ``marker``.

    mcp-coder's automated notes carry the marker on their first line.

    Args:
        body: Comment body text
        marker: Marker string to look for

    Returns:
        True if the first line contains the marker
    """
    if not body:
        return False
    return marker in body.splitlines()[0]


def lookup_branch(cache: BranchLookupCache, issue: IssueData) -> str | None:
    """Return the issue's single branch, or None for not_found/ambiguous/lookup errors.

    Raises:
        GitHubRateLimitError: On a rate limit (propagates).
    """  # noqa: DOC502  # raised by cache.lookup, not caught here
    try:
        return cache.lookup(issue).branch
    except (BranchLookupError, ValueError, GithubException) as exc:
        logger.warning("Branch lookup failed for issue #%d: %s", issue["number"], exc)
        return None
