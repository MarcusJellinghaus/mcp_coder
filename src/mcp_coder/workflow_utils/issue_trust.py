"""Decide whether an issue body is trusted LLM input.

Wraps the upstream ``IssueManager.check_body_trust`` so every caller fails
closed the same way: only a rate limit propagates; any other error becomes
``LOOKUP_FAILED``.
"""

from mcp_coder.mcp_workspace_github import (
    BodyTrust,
    BodyTrustResult,
    IssueData,
    IssueManager,
)
from mcp_coder.workflow_utils.rate_limit import raise_if_rate_limited

__all__ = ["evaluate_body_trust"]


def evaluate_body_trust(
    issue_manager: IssueManager, issue: IssueData
) -> BodyTrustResult:
    """Return the body-trust result for issue; fail closed.

    Args:
        issue_manager: Manager for the issue's repository.
        issue: The issue whose body is checked.

    Returns:
        The upstream result unchanged, or ``LOOKUP_FAILED`` with the exception
        type name as reason if the lookup raised anything but a rate limit.

    Raises:
        GitHubRateLimitError: If the lookup hit a GitHub rate limit.
    """  # noqa: DOC502 - raised inside raise_if_rate_limited
    try:
        return issue_manager.check_body_trust(issue)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # Broad on purpose: any failure must count as not trusted.
        raise_if_rate_limited(exc)
        return BodyTrustResult(
            status=BodyTrust.LOOKUP_FAILED, reason=type(exc).__name__
        )
