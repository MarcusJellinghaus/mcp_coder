"""Base branch detection utilities.

This module provides a unified function for detecting the base branch
of a feature branch by checking multiple sources in priority order:
1. Linked issue's base branch section (explicit user intent)
2. Open PR base branch (if PR already exists)
3. Git merge-base (heuristic fallback from git history; upstream also checks
   that the winner still exists on origin, via a network ``ls-remote``)
4. Default branch (main/master)

Detection is done upstream (``mcp_workspace``); this module only builds and
injects the GitHub managers it needs.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_workspace_git import (
    BaseBranchSource,
    extract_issue_number_from_branch,
    get_current_branch_name,
    probe_origin_branch,
)
from mcp_coder.mcp_workspace_git import (
    detect_base_branch_with_source as _upstream_detect_with_source,
)
from mcp_coder.mcp_workspace_github import IssueData, IssueManager, PullRequestManager

logger = logging.getLogger(__name__)


def detect_base_branch(
    project_dir: Path,
    current_branch: str | None = None,
    issue_data: IssueData | None = None,
) -> str | None:
    """Detect the base branch for the current feature branch.

    See detect_base_branch_with_source for the detection priority.

    Args:
        project_dir: Path to git repository
        current_branch: Optional current branch name (avoids git call if provided)
        issue_data: Optional pre-fetched issue data (avoids duplicate API calls)

    Returns:
        Branch name string, or None if detection fails.
    """
    result = detect_base_branch_with_source(project_dir, current_branch, issue_data)
    return result[0] if result else None


def detect_base_branch_with_source(
    project_dir: Path,
    current_branch: str | None = None,
    issue_data: IssueData | None = None,
) -> tuple[str, BaseBranchSource] | None:
    """Detect the base branch and the source it was detected from.

    Detection priority:
    1. Linked issue's `### Base Branch` section (explicit user intent)
    2. GitHub PR base branch (if open PR exists for current branch)
    3. Git merge-base (heuristic fallback from git history)
    4. Default branch (main/master)
    5. None if all detection fails

    The issue's base branch takes priority over merge-base because:
    - Users explicitly specify their intended base branch in the issue
    - Merge-base can be misleading when parent branches are merged to main
      (e.g., stacked PR workflows where the parent branch was merged)

    Args:
        project_dir: Path to git repository
        current_branch: Optional current branch name (avoids git call if provided)
        issue_data: Optional pre-fetched issue data (avoids duplicate API calls)

    Returns:
        Tuple of (branch name, source), or None if detection fails.

    Note:
        Makes up to 2 GitHub API calls if issue_data not provided:
        - Issue fetch (if branch has issue number)
        - PR lookup (if no issue base branch found)
    """
    if current_branch is None:
        current_branch = get_current_branch_name(project_dir)
        logger.debug(f"Detected current branch: {current_branch}")

    if current_branch is None:
        logger.debug("No current branch (detached HEAD), returning None")
        return None

    pr_manager, issue_manager = _build_managers(project_dir, current_branch, issue_data)
    return _upstream_detect_with_source(
        project_dir, current_branch, issue_data, pr_manager, issue_manager
    )


def check_base_branch_on_origin(project_dir: Path, base_branch: str) -> str | None:
    """Check that the base branch exists on origin.

    Asks origin directly (``probe_origin_branch``), so it works in a fresh
    clone that lacks ``origin/<base_branch>``.

    Args:
        project_dir: Path to git repository
        base_branch: Base branch name to look up

    Returns:
        None if the branch exists on origin, else an error message.
    """
    probe = probe_origin_branch(project_dir, base_branch)
    if probe["exists"] is True:
        return None
    detail = (probe["stderr"] or probe["error"] or "").strip()
    message = (
        f"Base branch '{base_branch}' not found on origin; create and push it first"
    )
    return f"{message} ({detail})" if detail else message


def _build_managers(
    project_dir: Path, current_branch: str, issue_data: IssueData | None
) -> tuple[PullRequestManager | None, IssueManager | None]:
    """Build the GitHub managers upstream detection needs.

    Each manager is built in its own try; a failure (e.g. missing token)
    yields None, so upstream skips that detection step. No IssueManager is
    built when issue_data is given or the branch has no issue number.

    Args:
        project_dir: Project directory path
        current_branch: Current branch name
        issue_data: Optional pre-fetched issue data

    Returns:
        Tuple of (pr_manager, issue_manager), each None if unavailable.
    """
    pr_manager: PullRequestManager | None = None
    try:
        pr_manager = PullRequestManager(project_dir)
    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.debug(f"PR manager unavailable: {e}")

    issue_manager: IssueManager | None = None
    if (
        issue_data is None
        and extract_issue_number_from_branch(current_branch) is not None
    ):
        try:
            issue_manager = IssueManager(project_dir=project_dir)
        except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
            logger.debug(f"Issue manager unavailable: {e}")

    return pr_manager, issue_manager
