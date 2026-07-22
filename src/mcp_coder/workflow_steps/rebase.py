"""Rebase-and-push workflow step.

Detects the parent/base branch and attempts to rebase the current feature
branch onto it before pushing, without ever blocking the workflow. Moved here
from ``implement/rebase.py`` so multiple workflows can share it.
"""

import logging
from pathlib import Path
from typing import Optional

from mcp_coder.mcp_workspace_git import rebase_onto_branch
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


def _attempt_rebase_and_push(project_dir: Path) -> bool:
    """Attempt to rebase onto parent branch and push. Never fails workflow.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if rebase and push succeeded.
        False if rebase skipped, failed, or no target detected.
    """
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
