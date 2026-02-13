"""Base branch detection utilities.

This module provides a unified function for detecting the base branch
of a feature branch by checking multiple sources in priority order:
1. Linked issue's base branch section (explicit user intent)
2. Open PR base branch (if PR already exists)
3. Git merge-base (heuristic fallback from git history)
4. Default branch (main/master)
"""

import logging
from pathlib import Path
from typing import Optional

from mcp_coder.utils.git_operations import (
    MERGE_BASE_DISTANCE_THRESHOLD,
    detect_parent_branch_via_merge_base,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_default_branch_name,
)
from mcp_coder.utils.github_operations.issues import IssueData, IssueManager
from mcp_coder.utils.github_operations.pr_manager import PullRequestManager

logger = logging.getLogger(__name__)


def detect_base_branch(
    project_dir: Path,
    current_branch: Optional[str] = None,
    issue_data: Optional[IssueData] = None,
) -> Optional[str]:
    """Detect the base branch for the current feature branch.

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
        Branch name string, or None if detection fails.

    Note:
        Makes up to 2 GitHub API calls if issue_data not provided:
        - Issue fetch (if branch has issue number)
        - PR list lookup (if no issue base branch found)
    """
    # Get current branch if not provided
    if current_branch is None:
        current_branch = get_current_branch_name(project_dir)
        logger.debug(f"Detected current branch: {current_branch}")

    if current_branch is None:
        logger.debug("No current branch (detached HEAD), returning None")
        return None

    # 1. Try issue base_branch first (explicit user intent - highest priority)
    logger.debug("Attempting base branch detection via issue base_branch")
    base_branch = _detect_from_issue(project_dir, current_branch, issue_data)
    if base_branch:
        return base_branch

    # 2. Try PR lookup (existing PR knows its base)
    logger.debug("Attempting base branch detection via PR lookup")
    base_branch = _detect_from_pr(project_dir, current_branch)
    if base_branch:
        return base_branch

    # 3. Try git merge-base (heuristic fallback)
    logger.debug("Attempting base branch detection via git merge-base")
    base_branch = detect_parent_branch_via_merge_base(
        project_dir, current_branch, MERGE_BASE_DISTANCE_THRESHOLD
    )
    if base_branch:
        return base_branch

    # 4. Fall back to default branch
    logger.debug("Attempting base branch detection via default branch")
    base_branch = _detect_default_branch(project_dir)
    if base_branch:
        return base_branch

    # All detection methods failed - return None
    logger.warning(
        "Could not detect base branch from issue, PR, merge-base, or default"
    )
    return None


def _detect_from_pr(project_dir: Path, current_branch: str) -> Optional[str]:
    """Detect base branch from open PR.

    Args:
        project_dir: Project directory path
        current_branch: Current branch name

    Returns:
        Base branch name if PR found, None otherwise
    """
    try:
        pr_manager = PullRequestManager(project_dir)
        open_prs = pr_manager.list_pull_requests(state="open")

        for pr in open_prs:
            if pr.get("head_branch") == current_branch:
                base_branch = pr.get("base_branch")
                logger.info(f"Found base branch from PR: {base_branch}")
                return base_branch

        logger.debug(f"No open PR found for branch '{current_branch}'")
        return None

    except Exception as e:
        logger.debug(f"PR detection failed: {e}")
        return None


def _detect_from_issue(
    project_dir: Path,
    current_branch: str,
    issue_data: Optional[IssueData] = None,
) -> Optional[str]:
    """Detect base branch from linked issue.

    If issue_data is provided, uses its base_branch directly.
    Otherwise, extracts issue number from branch name and fetches issue.

    Args:
        project_dir: Project directory path
        current_branch: Current branch name
        issue_data: Optional pre-fetched issue data

    Returns:
        Base branch name if issue has base_branch, None otherwise
    """
    # If issue_data provided, check its base_branch directly
    if issue_data is not None:
        base_branch = issue_data.get("base_branch")
        if base_branch:
            logger.info(f"Found base branch from provided issue data: {base_branch}")
            return base_branch
        logger.debug("Provided issue_data has no base_branch")
        return None

    # Extract issue number from branch name
    issue_number = extract_issue_number_from_branch(current_branch)
    if issue_number is None:
        logger.debug(f"No issue number in branch name '{current_branch}'")
        return None

    try:
        issue_manager = IssueManager(project_dir=project_dir)
        fetched_issue = issue_manager.get_issue(issue_number)

        # Check if issue was found (number=0 indicates not found)
        if fetched_issue.get("number", 0) == 0:
            logger.debug(f"Issue #{issue_number} not found")
            return None

        base_branch = fetched_issue.get("base_branch")
        if base_branch:
            logger.info(f"Found base branch from issue #{issue_number}: {base_branch}")
            return base_branch

        logger.debug(f"Issue #{issue_number} has no base_branch specified")
        return None

    except Exception as e:
        logger.debug(f"Issue detection failed: {e}")
        return None


def _detect_default_branch(project_dir: Path) -> Optional[str]:
    """Detect default branch (main/master).

    Args:
        project_dir: Project directory path

    Returns:
        Default branch name if found, None otherwise
    """
    try:
        default_branch = get_default_branch_name(project_dir)
        if default_branch:
            logger.info(f"Using default branch: {default_branch}")
            return default_branch

        logger.debug("Could not determine default branch")
        return None

    except Exception as e:
        logger.debug(f"Default branch detection failed: {e}")
        return None
