"""Branch-to-issue linkage check.

Decides whether a branch belongs to an issue, using GitHub's linked branches
and, once a PR exists, the head refs of open PRs that close the issue.
"""

import logging
from typing import Optional

from mcp_coder.mcp_workspace_github import IssueBranchManager

logger = logging.getLogger(__name__)

__all__ = ["is_branch_linked_to_issue"]


def is_branch_linked_to_issue(
    branch_manager: IssueBranchManager,
    issue_number: int,
    branch_name: str,
) -> Optional[bool]:
    """Check whether a branch is linked to an issue.

    Linked branches are checked first, then the head refs of open PRs that
    close the issue (``includeClosedPrs: false``). Both come from one GraphQL
    request. Once a PR is opened, GitHub drops the branch from the issue's
    linked branches, so the closing-PR fallback keeps the check working.

    Known limitations:
        - Only PRs that close the issue (``Closes #N`` or a manual link) are
          seen; a hand-made PR without that line fails.
        - Matching uses ``head_ref_name`` only, so a fork PR with the same
          branch name matches.
        - If create-pr's pre-PR linkage check fails, the PR body gets no
          ``Closes #N`` line, so the fallback can never match for that PR.

    On failure, the mcp-workspace method logs its own line too.

    Args:
        branch_manager: Manager used for the lookup.
        issue_number: Issue to check against.
        branch_name: Branch to look for.

    Returns:
        True if linked, False if not linked, None if the lookup failed.
    """
    result = branch_manager.get_linked_branch_and_closing_prs_or_none(issue_number)
    if result is None:
        logger.error(f"Could not determine linkage for issue #{issue_number}")
        return None

    linked_branches, closing_prs = result
    if branch_name in linked_branches:
        logger.info(f"Branch {branch_name} is a linked branch of issue #{issue_number}")
        return True

    for pr in closing_prs:
        if pr.head_ref_name == branch_name:
            logger.info(
                f"Branch {branch_name} is the head of closing PR #{pr.number} "
                f"for issue #{issue_number}"
            )
            return True

    logger.warning(
        f"Branch {branch_name} is not linked to issue #{issue_number}: "
        f"no linked branch or open closing PR matches "
        f"(a PR without 'Closes #{issue_number}' is not detected). "
        f"Linked branches: {linked_branches}, "
        f"closing PRs: {[f'#{pr.number}' for pr in closing_prs]}"
    )
    return False
