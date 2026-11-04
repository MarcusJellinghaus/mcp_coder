"""Helpers for the CI fix loop in ``workflow_steps/ci.py``."""

import logging
from dataclasses import dataclass
from pathlib import Path

from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS
from mcp_coder.mcp_workspace_git import get_latest_commit_sha, get_working_tree_status

from .constants import COMMIT_MESSAGE_FILE

# Setup logger
logger = logging.getLogger(__name__)


@dataclass
class CIFixState:
    """Per-run state of the CI fix loop."""

    push_pending: bool = False


def read_head(project_dir: Path) -> str | None:
    """Return HEAD's SHA, or None on any failure. Never raises.

    Args:
        project_dir: Path to the project directory

    Returns:
        The SHA of HEAD, or None if it could not be read
    """
    try:
        return get_latest_commit_sha(project_dir)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning(f"Failed to read HEAD: {e}")
        return None


def discard_if_no_change(project_dir: Path, head_before: str | None) -> bool:
    """Return True if the attempt changed nothing, and delete the unused message file.

    A failed read of HEAD or of the tree counts as "has changes". Never raises.

    Args:
        project_dir: Path to the project directory
        head_before: HEAD's SHA from just before the attempt's fix LLM call

    Returns:
        True if HEAD is unchanged and the tree is clean, ignoring the commit
        message file and build artifacts. False otherwise.
    """
    try:
        if head_before is None or read_head(project_dir) != head_before:
            return False
        status = get_working_tree_status(project_dir)
        ignored = {COMMIT_MESSAGE_FILE, *DEFAULT_IGNORED_BUILD_ARTIFACTS}
        changed = set(status["staged"] + status["modified"] + status["untracked"])
        if not status["success"] or changed - ignored:
            return False
        (project_dir / COMMIT_MESSAGE_FILE).unlink(missing_ok=True)
        return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.warning(f"Failed to check for CI fix changes: {e}")
        return False


def _read_problem_description(temp_file: Path, fallback_response: str) -> str:
    """Read problem description from temp file or use fallback.

    Args:
        temp_file: Path to the temp problem description file
        fallback_response: Fallback text if file doesn't exist or is empty

    Returns:
        Problem description text
    """
    if temp_file.exists():
        try:
            content = temp_file.read_text(encoding="utf-8").strip()
            temp_file.unlink()  # Delete after reading
            if content:  # Only use file content if not empty
                logger.debug(f"Problem description:\n{content}")
                return content
            logger.debug("Temp file was empty, using fallback")
        except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
            logger.warning(f"Failed to read problem description file: {e}")

    logger.debug("Using analysis response as problem description")
    return fallback_response
