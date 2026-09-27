"""Rebase-and-push workflow step.

Detects the parent/base branch and attempts to rebase the current feature
branch onto it before pushing, without ever blocking the workflow. Moved here
from ``implement/rebase.py`` so multiple workflows can share it.
"""

import logging
from pathlib import Path
from typing import Optional

from mcp_coder.mcp_workspace_git import get_full_status, rebase_onto_branch
from mcp_coder.workflow_steps.commit import push_changes
from mcp_coder.workflow_utils.base_branch import detect_base_branch

logger = logging.getLogger(__name__)


def _get_rebase_target_branch(project_dir: Path) -> Optional[str]:
    """Determine the target branch for rebasing the current feature branch.

    Uses shared detect_base_branch() function for detection.

    Args:
        project_dir: Path to the project directory

    Returns:
        Branch name to rebase onto, or None if detection fails
    """
    return detect_base_branch(project_dir)  # Now returns None directly on failure


def _has_uncommitted_tracked_changes(project_dir: Path) -> bool:
    """Check for uncommitted changes that would make git refuse a rebase.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if any tracked entry is staged or modified (deletions included).
    """
    # get_full_status never raises: it returns empty lists for a non-git-repo
    # and swallows unexpected errors into the same empty result.
    status = get_full_status(project_dir)
    # Untracked files are NOT blocking - git rebase tolerates them.
    # DEFAULT_IGNORED_BUILD_ARTIFACTS is NOT filtered - git refuses on a
    # modified uv.lock like any other tracked modification.
    return bool(status["staged"] + status["modified"])


def _attempt_rebase_and_push(project_dir: Path) -> bool:
    """Attempt to rebase onto parent branch and push. Never fails workflow.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if rebase and push succeeded.
        False if the working tree has staged or modified tracked changes
        (untracked files alone do not count), or if rebase skipped, failed,
        or no target detected.
    """
    # Checked before target detection: detect_base_branch fetches from the
    # remote, and there is no point paying for it when the rebase cannot start.
    if _has_uncommitted_tracked_changes(project_dir):
        logger.warning(
            "Skipping rebase: the working tree has staged or modified tracked "
            "files, which git refuses to rebase over - commit or discard them "
            "and re-run"
        )
        return False

    target = _get_rebase_target_branch(project_dir)
    if target:
        logger.info("Rebasing onto origin/%s...", target)
        if rebase_onto_branch(project_dir, target):
            # Push rebased branch with force_with_lease
            if push_changes(project_dir, force_with_lease=True):
                return True
            else:
                logger.warning(
                    "Rebase succeeded but push failed - "
                    "manual push with --force-with-lease may be required"
                )
                return False
        return False
    else:
        logger.debug("Could not detect parent branch for rebase")
        return False
