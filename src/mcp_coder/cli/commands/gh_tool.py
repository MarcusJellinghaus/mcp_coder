"""CLI commands for GitHub tool operations.

This module provides the gh-tool command group for GitHub-related operations.
"""

import argparse
import logging
import re
from pathlib import Path

from mcp_coder.mcp_workspace_git import (
    checkout_branch,
    fetch_remote,
    get_repository_identifier,
    list_remote_branches,
)

from ...mcp_workspace_github import IssueBranchManager, IssueManager
from ...workflow_utils.base_branch import detect_base_branch
from ...workflows.utils import resolve_project_dir

logger = logging.getLogger(__name__)


def execute_get_base_branch(args: argparse.Namespace) -> int:
    """Execute get-base-branch command.

    Detection priority:
    1. Linked issue's ### Base Branch section
    2. Open PR base branch
    3. Git merge-base
    4. Default branch (main/master)

    Args:
        args: Parsed arguments with project_dir option

    Returns:
        0: Success, branch name printed to stdout
        1: Could not detect base branch
        2: Error (not a git repo, API failure)
    """
    try:
        logger.info("Starting get-base-branch detection")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Use the shared detect_base_branch function
        base_branch = detect_base_branch(project_dir)

        if base_branch is None:
            logger.warning(
                "Could not detect base branch from issue, PR, merge-base, or default"
            )
            return 1

        print(base_branch)
        return 0

    except ValueError as e:
        # resolve_project_dir raises ValueError for invalid directories
        logger.error("%s", e)
        return 2
    except Exception as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error("Error detecting base branch: %s", e)
        logger.debug("Exception details:", exc_info=True)
        return 2


def _find_precreate_candidates(
    branch_manager: IssueBranchManager, project_dir: Path, issue_number: int
) -> dict[str, str] | None:
    """Collect existing branches for the issue before creating one.

    Sources, in order: linked branches, head branches of open closing PRs,
    and remote branches matching ``(^|/)N[-_]``.

    Returns:
        Ordered mapping of branch name -> source label (first source wins),
        or None if the linkage lookup or ``git ls-remote`` failed.
    """
    lookup = branch_manager.get_linked_branch_and_closing_prs_or_none(issue_number)
    if lookup is None:
        logger.error(
            "Could not look up linked branches and closing PRs for issue #%s",
            issue_number,
        )
        return None
    linked, closing_prs = lookup

    remote = list_remote_branches(project_dir)
    if not remote["success"]:
        logger.error("git ls-remote failed: %s", remote["stderr"] or remote["error"])
        return None

    pattern = re.compile(rf"(^|/){issue_number}[-_]")
    candidates: dict[str, str] = {}
    for branch in linked:
        candidates.setdefault(branch, f"linked branch {branch}")
    for pr in closing_prs:
        candidates.setdefault(
            pr.head_ref_name, f"closing PR #{pr.number} -> {pr.head_ref_name}"
        )
    for name in remote["branches"]:
        if pattern.search(name):
            candidates.setdefault(name, f"remote branch {name}")
    return candidates


def execute_checkout_issue_branch(args: argparse.Namespace) -> int:
    """Execute checkout-issue-branch command.

    Resolution order:
    1. Library fallback: linked branch, open PR referencing the issue,
       closed PR whose branch still exists, branch-name pattern
    2. Pre-create checks (only if 1 finds nothing): linked branches, open
       closing PRs, remote branches matching the issue number
    3. Create a new linked branch (only if 2 finds no candidate)

    Args:
        args: Parsed arguments with issue_number and project_dir option

    Returns:
        0: Branch checked out (found, single pre-create candidate, or created)
        1: Issue not found, or branch creation failed
        2: Error (invalid project dir, no repo identifier, lookup or
           ls-remote failure, API failure, git checkout failure)
        3: Ambiguous: pre-create checks found two or more candidates
    """
    try:
        logger.info("Starting checkout-issue-branch")

        # Resolve project directory with validation
        project_dir = resolve_project_dir(args.project_dir)

        # Best-effort git fetch
        if not fetch_remote(project_dir):
            logger.debug("git fetch failed (continuing)")

        # Get issue data
        issue_number: int = args.issue_number
        issue_data = IssueManager(project_dir).get_issue(issue_number)

        if issue_data["number"] == 0:
            logger.error("Could not find issue #%s", issue_number)
            return 1

        repo_id = get_repository_identifier(project_dir)
        if repo_id is None:
            logger.error("Could not determine repository identifier")
            return 2

        # Find existing branch (linked, PR head, or name pattern)
        branch_manager = IssueBranchManager(
            project_dir=project_dir, repo_url=repo_id.https_url
        )
        found = branch_manager.get_branch_with_pr_fallback(
            issue_number, repo_id.owner, repo_id.repo_name
        )

        if found is not None:
            branch_name = found
        else:
            # Pre-create checks: fallback returns None for nothing, ambiguous, or error
            candidates = _find_precreate_candidates(
                branch_manager, project_dir, issue_number
            )
            if candidates is None:
                return 2
            if len(candidates) > 1:
                logger.error(
                    "Ambiguous branches for issue #%s: %s",
                    issue_number,
                    "; ".join(candidates.values()),
                )
                return 3
            if candidates:
                branch_name, label = next(iter(candidates.items()))
                logger.info(
                    "Using existing branch for issue #%s: %s", issue_number, label
                )
            else:
                result = branch_manager.create_remote_branch_for_issue(
                    issue_number, base_branch=issue_data.get("base_branch")
                )
                if not result["success"]:
                    logger.error(
                        "Could not create branch for issue #%s: %s",
                        issue_number,
                        result["error"],
                    )
                    return 1
                branch_name = result["branch_name"]

        # Checkout the branch
        if not checkout_branch(branch_name, project_dir):
            logger.error("git checkout failed for branch '%s'", branch_name)
            return 2

        print(branch_name)
        return 0

    except ValueError as e:
        # resolve_project_dir raises ValueError for invalid directories
        logger.error("%s", e)
        return 2
    except Exception as e:  # pylint: disable=broad-exception-caught  # top-level CLI error boundary
        logger.error("Error during checkout-issue-branch: %s", e)
        logger.debug("Exception details:", exc_info=True)
        return 2
