"""Commit / push / format workflow steps.

Workflow-agnostic composed steps for running formatters, committing changes
(honoring a prepared commit-message file), and pushing to the remote. Moved
here from ``implement/task_processing.py`` so multiple workflows can share them.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_tools_py import run_format_code
from mcp_coder.mcp_workspace_git import commit_all_changes, git_push
from mcp_coder.workflow_utils.commit_operations import (
    generate_commit_message_with_llm,
    parse_llm_commit_response,
)

from .constants import COMMIT_MESSAGE_FILE

# Setup logger
logger = logging.getLogger(__name__)


def run_formatters(project_dir: Path) -> bool:
    """Run code formatters (black, isort) and return success status.

    Args:
        project_dir: Path to the project directory

    Returns:
        True if all formatters completed successfully, False if any formatter failed.
    """
    logger.info("Running code formatters...")

    try:
        results = run_format_code(project_dir)

        # Check if any formatter failed
        for formatter_name, result in results.items():
            if not result.success:
                logger.error(f"{formatter_name} formatting failed: {result.output}")
                return False
            logger.info(f"{formatter_name} formatting completed successfully")

        logger.info("All formatters completed successfully")
        return True

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error running formatters: {e}")
        return False


def commit_changes(project_dir: Path, provider: str = "claude") -> bool:
    """Commit changes using existing git operations and return success status.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')

    Returns:
        True if changes were committed successfully, False on error.
    """
    logger.info("Committing changes...")
    commit_message = ""

    try:
        # Check for prepared commit message file
        commit_msg_path = project_dir / COMMIT_MESSAGE_FILE
        if commit_msg_path.exists():
            file_content = commit_msg_path.read_text(encoding="utf-8").strip()
            # Delete file before git operations (even if empty)
            commit_msg_path.unlink()
            if file_content:
                # Parse the commit message
                commit_message, _ = parse_llm_commit_response(file_content)
                logger.info("Using prepared commit message from file")

        # Fall back to LLM generation if no prepared message
        if not commit_message:
            success, commit_message, error = generate_commit_message_with_llm(
                project_dir, provider
            )

            if not success:
                logger.error(f"Error generating commit message: {error}")
                return False

        # Commit using the message
        commit_result = commit_all_changes(commit_message, project_dir)

        if not commit_result["success"]:
            logger.error(f"Error committing changes: {commit_result['error']}")
            # Log commit message so it's not lost
            logger.error(f"Commit message was: {commit_message}")
            return False

        # Show commit message first line along with hash
        commit_lines = commit_message.strip().split("\n")
        first_line = commit_lines[0].strip() if commit_lines else commit_message.strip()
        logger.info(
            f"Changes committed successfully: {commit_result['commit_hash']} - {first_line}",
        )
        return True

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error committing changes: {e}")
        if commit_message:
            logger.error(f"Commit message was: {commit_message}")
        return False


def push_changes(project_dir: Path, force_with_lease: bool = False) -> bool:
    """Push changes to remote repository and return success status.

    Args:
        project_dir: Path to the project directory
        force_with_lease: If True, use --force-with-lease for safe force push

    Returns:
        True if push succeeded, False otherwise
    """
    if force_with_lease:
        logger.info("Pushing changes to remote with --force-with-lease...")
    else:
        logger.info("Pushing changes to remote...")

    try:
        push_result = git_push(project_dir, force_with_lease=force_with_lease)

        if not push_result["success"]:
            logger.error(f"Error pushing changes: {push_result['error']}")
            return False

        if force_with_lease:
            logger.info("Changes force-pushed successfully to remote (with lease)")
        else:
            logger.info("Changes pushed successfully to remote")
        return True

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error pushing changes: {e}")
        return False
