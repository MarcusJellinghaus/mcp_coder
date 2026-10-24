"""Commit / push / format workflow steps.

Workflow-agnostic composed steps for running formatters, committing changes
(honoring a prepared commit-message file), and pushing to the remote. Moved
here from ``implement/task_processing.py`` so multiple workflows can share them.
"""

import logging
from pathlib import Path

from mcp_coder.mcp_tools_py import resolve_steps, run_format_code
from mcp_coder.mcp_workspace_git import commit_all_changes, git_push
from mcp_coder.utils.pyproject_config import (
    get_format_code,
    has_legacy_format_code_key,
)
from mcp_coder.workflow_utils.commit_operations import (
    generate_commit_message_with_llm,
    parse_llm_commit_response,
)

from .constants import COMMIT_MESSAGE_FILE

# Setup logger
logger = logging.getLogger(__name__)

# Static fallback when LLM commit-message generation fails. Deliberately free
# of error detail: it lands in public git history; logs carry the diagnostics.
FALLBACK_COMMIT_MESSAGE = "chore: automated commit (message generation failed)"


class FormatterConfigError(ValueError):
    """Formatter configuration is invalid; formatting cannot run."""


def check_formatter_config(
    project_dir: Path, warn_legacy_key: bool = False
) -> str | None:
    """Check that formatting is off or the project's formatter resolves.

    Args:
        project_dir: Path to the project directory
        warn_legacy_key: Log a warning if the ignored
            [tool.mcp-coder.implement] format_code key is present

    Returns:
        None when formatting is off or resolves cleanly, else the error message.
    """
    if warn_legacy_key and has_legacy_format_code_key(project_dir):
        logger.warning(
            "[tool.mcp-coder.implement] format_code is ignored; "
            "use [tool.mcp-coder] format_code"
        )
    try:
        if not get_format_code(project_dir).enabled:
            return None
        resolve_steps(project_dir)
        return None
    except ValueError as e:
        return str(e)


def run_formatters(project_dir: Path) -> bool:
    """Run the project's configured formatter and return success status.

    Args:
        project_dir: Path to the project directory

    Returns:
        True when formatting is disabled or all steps succeeded, False if a
        step failed.

    Raises:
        FormatterConfigError: If the formatter configuration is invalid.
    """
    message = check_formatter_config(project_dir)
    if message:
        raise FormatterConfigError(message)
    if not get_format_code(project_dir).enabled:
        logger.info("Code formatting disabled ([tool.mcp-coder] format_code = false)")
        return True

    logger.info("Running code formatters...")

    try:
        results = run_format_code(project_dir)
    except ValueError as e:
        # resolve_steps inside the wrapper: a config error, not a step failure.
        raise FormatterConfigError(str(e)) from e
    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error running formatters: {e}")
        return False

    # Check if any formatter failed
    for formatter_name, result in results.items():
        if not result.success:
            logger.error(f"{formatter_name} formatting failed: {result.output}")
            return False
        logger.info(f"{formatter_name} formatting completed successfully")

    logger.info("All formatters completed successfully")
    return True


def commit_changes(
    project_dir: Path,
    provider: str = "claude",
    *,
    mcp_config: str | None = None,
    settings_file: str | None = None,
) -> bool:
    """Commit changes using existing git operations and return success status.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional MCP config path; forwarded to commit-message
            generation so the LLM call runs scoped like the workflow's main sessions
        settings_file: Optional Claude settings file; forwarded to message generation

    Returns:
        True if changes were committed successfully or the tree was clean
        (no-op); False only on git-level failure. LLM message-generation
        failure is non-fatal: the commit proceeds with
        ``FALLBACK_COMMIT_MESSAGE``.
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
                project_dir,
                provider,
                mcp_config=mcp_config,
                settings_file=settings_file,
            )

            if not success:
                logger.error(f"Error generating commit message: {error}")
                logger.warning("Falling back to static commit message")
                commit_message = FALLBACK_COMMIT_MESSAGE

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

    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
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

    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error pushing changes: {e}")
        return False
