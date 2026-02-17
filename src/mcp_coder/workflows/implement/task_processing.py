"""Task processing functions for implement workflow.

This module contains functions for processing individual implementation tasks,
including LLM integration, mypy fixes, formatting, and git operations.
"""

import logging
import re
from pathlib import Path
from typing import Optional

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.formatters import format_code
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import ask_llm
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils import commit_all_changes, get_full_status, git_push
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.workflow_utils.commit_operations import (
    generate_commit_message_with_llm,
    parse_llm_commit_response,
)
from mcp_coder.workflow_utils.task_tracker import get_incomplete_tasks

from .constants import (
    COMMIT_MESSAGE_FILE,
    LLM_IMPLEMENTATION_TIMEOUT_SECONDS,
    PR_INFO_DIR,
    RUN_MYPY_AFTER_EACH_TASK,
)

# Setup logger
logger = logging.getLogger(__name__)


def get_next_task(project_dir: Path) -> Optional[str]:
    """Get next incomplete task from task tracker (excluding meta-tasks)."""
    logger.info("Checking for incomplete tasks...")

    try:
        pr_info_dir = str(project_dir / PR_INFO_DIR)

        # Get incomplete tasks, excluding meta-tasks
        incomplete_tasks = get_incomplete_tasks(pr_info_dir, exclude_meta_tasks=True)

        if not incomplete_tasks:
            logger.info(
                "No incomplete implementation tasks found (meta-tasks excluded)"
            )
            return None

        next_task = incomplete_tasks[0]
        logger.info(f"Found next task: {next_task}")
        return next_task

    except Exception as e:
        logger.error(f"Error getting incomplete tasks: {e}")
        return None


def run_formatters(project_dir: Path) -> bool:
    """Run code formatters (black, isort) and return success status."""
    logger.info("Running code formatters...")

    try:
        results = format_code(project_dir, formatters=["black", "isort"])

        # Check if any formatter failed
        for formatter_name, result in results.items():
            if not result.success:
                logger.error(
                    f"{formatter_name} formatting failed: {result.error_message}"
                )
                return False
            logger.info(f"{formatter_name} formatting completed successfully")

        logger.info("All formatters completed successfully")
        return True

    except Exception as e:
        logger.error(f"Error running formatters: {e}")
        return False


def commit_changes(
    project_dir: Path, provider: str = "claude", method: str = "api"
) -> bool:
    """Commit changes using existing git operations and return success status.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
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
                project_dir, provider, method
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
            f"Changes committed successfully: {commit_result['commit_hash']} - {first_line}"
        )
        return True

    except Exception as e:
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

    except Exception as e:
        logger.error(f"Error pushing changes: {e}")
        return False


def _run_mypy_check(project_dir: Path) -> Optional[str]:
    """Run mypy check using our wrapper and return error output or None if clean."""
    from mcp_coder.mcp_code_checker import run_mypy_check

    try:
        result = run_mypy_check(project_dir)

        # Check if there are errors
        if (result.errors_found or 0) > 0:
            # Return raw output for error details
            return result.raw_output or "Mypy found type errors"
        else:
            return None  # No errors found

    except Exception as e:
        raise Exception(f"Failed to run mypy check: {e}")


def check_and_fix_mypy(
    project_dir: Path,
    step_num: int,
    provider: str,
    method: str,
    env_vars: dict[str, str] | None = None,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Run mypy check and attempt fixes if issues found. Returns True if clean.

    Args:
        project_dir: Path to the project directory
        step_num: Step number for conversation naming
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        env_vars: Optional environment variables for the subprocess
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess
    """
    logger.info("Running mypy type checking...")

    max_identical_attempts = 3
    previous_outputs = []
    mypy_attempt_counter = 0

    try:
        # Initial mypy check using MCP tool
        mypy_result = _run_mypy_check(project_dir)

        if mypy_result is None:
            logger.info("Mypy check passed - no type errors found")
            return True

        logger.info("Type errors found, attempting fixes...")
        identical_count = 0

        # Retry loop with smart retry logic
        while identical_count < max_identical_attempts:
            # Check if current mypy output is identical to a previous one
            if mypy_result in previous_outputs:
                identical_count += 1
                logger.info(
                    f"Identical mypy feedback detected (attempt {identical_count}/{max_identical_attempts})"
                )

                if identical_count >= max_identical_attempts:
                    logger.info(
                        "Maximum identical attempts reached - stopping mypy fixes"
                    )
                    break
            else:
                # New output, reset counter
                identical_count = 0

            # Add current output to history
            previous_outputs.append(mypy_result)
            mypy_attempt_counter += 1

            # Get mypy fix prompt template
            try:
                mypy_prompt_template = get_prompt(
                    str(PROMPTS_FILE_PATH), "Mypy Fix Prompt"
                )
                # Replace placeholder with actual mypy output
                mypy_prompt = mypy_prompt_template.replace("[mypy_output]", mypy_result)
            except Exception as e:
                logger.error(f"Error loading mypy fix prompt: {e}")
                return False

            # Call LLM for fixes
            try:
                branch_name = get_branch_name_for_logging(
                    str(execution_dir) if execution_dir else str(project_dir)
                )
                fix_response = ask_llm(
                    mypy_prompt,
                    provider=provider,
                    method=method,
                    timeout=LLM_IMPLEMENTATION_TIMEOUT_SECONDS,
                    env_vars=env_vars,
                    execution_dir=(
                        str(execution_dir) if execution_dir else str(project_dir)
                    ),
                    mcp_config=mcp_config,
                    branch_name=branch_name,
                )

                if not fix_response or not fix_response.strip():
                    logger.error("LLM returned empty response for mypy fixes")
                    return False

                logger.info(
                    f"Applied mypy fixes from LLM (attempt {mypy_attempt_counter})"
                )

            except Exception as e:
                logger.error(
                    f"Error getting mypy fixes from LLM on attempt {mypy_attempt_counter}: {e}"
                )
                return False

            # Re-run mypy check to see if issues were resolved
            try:
                mypy_result = _run_mypy_check(project_dir)

                if mypy_result is None:
                    logger.info("Mypy check passed after fixes")
                    return True

            except Exception as e:
                logger.error(
                    f"Error re-running mypy check on attempt {mypy_attempt_counter}: {e}"
                )
                return False

        # If we get here, we couldn't fix all issues
        logger.info("Could not resolve all mypy type errors")
        return False

    except Exception as e:
        logger.error(f"Error during mypy check and fix: {e}")
        return False


def _cleanup_commit_message_file(project_dir: Path) -> None:
    """Remove stale commit message file from previous failed runs."""
    commit_msg_path = project_dir / COMMIT_MESSAGE_FILE
    if commit_msg_path.exists():
        commit_msg_path.unlink()
        logger.debug("Cleaned up stale commit message file")


def process_single_task(
    project_dir: Path,
    provider: str,
    method: str,
    mcp_config: str | None = None,
    execution_dir: Optional[Path] = None,
) -> tuple[bool, str]:
    """Process a single implementation task.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess

    Returns:
        Tuple of (success, reason) where:
        - success: True if task completed successfully
        - reason: 'completed' | 'no_tasks' | 'error'
    """
    # Cleanup stale commit message file from previous failed runs
    _cleanup_commit_message_file(project_dir)

    # Prepare environment variables for LLM subprocess
    env_vars = prepare_llm_environment(project_dir)

    # Set working directory for LLM subprocess
    cwd = str(execution_dir) if execution_dir else str(project_dir)

    # Get next incomplete task
    next_task = get_next_task(project_dir)
    if not next_task:
        logger.info("No incomplete tasks found")
        return False, "no_tasks"

    # Step 3: Get implementation prompt template
    logger.debug("Loading implementation prompt template...")
    try:
        prompt_template = get_prompt(
            str(PROMPTS_FILE_PATH), "Implementation Prompt Template using task tracker"
        )
    except Exception as e:
        logger.error(f"Error loading prompt template: {e}")
        return False, "error"

    # Step 4: Call LLM with prompt
    logger.info("Calling LLM for implementation...")
    try:
        # Create the full prompt by combining template with task context
        full_prompt = f"""{prompt_template}

Current task from TASK_TRACKER.md: {next_task}

Please implement this task step by step."""

        branch_name = get_branch_name_for_logging(cwd)
        response = ask_llm(
            full_prompt,
            provider=provider,
            method=method,
            timeout=LLM_IMPLEMENTATION_TIMEOUT_SECONDS,
            env_vars=env_vars,
            execution_dir=cwd,
            mcp_config=mcp_config,
            branch_name=branch_name,
        )

        if not response or not response.strip():
            logger.error("LLM returned empty response")
            logger.debug(f"Response was: {repr(response)}")
            return False, "error"

        logger.info("LLM response received successfully")

    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        return False, "error"

    # Step 5: Extract step number from task
    step_match = re.search(r"Step (\d+)", next_task)
    step_num = int(step_match.group(1)) if step_match else 1

    # Step 6: Check if any files were actually changed
    try:
        status = get_full_status(project_dir)
        all_changes = status["staged"] + status["modified"] + status["untracked"]

        if not all_changes:
            logger.warning(f"No files were changed for task: {next_task}")
            logger.warning(
                "This might indicate the task is already complete or the LLM didn't make changes"
            )
            logger.warning("Skipping commit/push for this task")
            return True, "completed"  # Consider it successful but skip commit
    except Exception as e:
        logger.error(f"Error checking file changes: {e}")
        return False, "error"

    # Step 7: Run mypy check and fixes (each fix will be saved separately)
    if RUN_MYPY_AFTER_EACH_TASK:
        if not check_and_fix_mypy(
            project_dir, step_num, provider, method, env_vars, mcp_config, execution_dir
        ):
            logger.warning(
                "Mypy check failed or found unresolved issues - continuing anyway"
            )
    else:
        logger.info("Skipping mypy check (will run after all tasks complete)")

    # Step 8: Run formatters
    if not run_formatters(project_dir):
        return False, "error"

    # Step 9: Commit changes
    if not commit_changes(project_dir, provider, method):
        return False, "error"

    # Step 10: Push changes to remote
    if not push_changes(project_dir):
        return False, "error"

    logger.info(f"Task completed successfully: {next_task}")
    return True, "completed"
