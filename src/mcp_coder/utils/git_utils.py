"""Git utility functions for logging and context."""

import logging
from pathlib import Path

from .git_operations import get_current_branch_name

logger = logging.getLogger(__name__)


def get_branch_name_for_logging(
    project_dir: str | Path | None = None,
    issue_id: str | int | None = None,
) -> str | None:
    """Get branch name for LLM log file naming.

    Attempts to get the current git branch name for use in log file naming.
    Falls back to issue_id format if branch is unavailable but issue_id is provided.

    Args:
        project_dir: Directory to get git branch from. Can be str or Path.
        issue_id: Fallback issue ID if branch unavailable. Used to create
            "{issue_id}-issue" format fallback.

    Returns:
        - Current git branch name if available and not "HEAD"
        - "{issue_id}-issue" if branch unavailable but issue_id provided
        - None if neither available

    Examples:
        >>> # With valid git repo on branch "fix/improve-logging"
        >>> get_branch_name_for_logging("/path/to/repo")
        'fix/improve-logging'

        >>> # With issue_id fallback
        >>> get_branch_name_for_logging(issue_id=123)
        '123-issue'

        >>> # No context available
        >>> get_branch_name_for_logging()
        None
    """
    # Try to get branch from project_dir
    if project_dir:
        try:
            project_path = (
                Path(project_dir) if isinstance(project_dir, str) else project_dir
            )
            branch = get_current_branch_name(project_path)
            if branch and branch != "HEAD":
                return branch
        except Exception as e:  # pylint: disable=broad-except
            # Log but don't fail - this is optional metadata
            logger.debug(f"Could not get branch name from {project_dir}: {e}")

    # Fall back to issue_id format
    if issue_id is not None:
        return f"{issue_id}-issue"

    return None
