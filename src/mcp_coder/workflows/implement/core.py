"""Core workflow orchestration for implement workflow.

This module contains the main workflow orchestration functions that coordinate
prerequisites checking, task tracker preparation, and task processing loops.
"""

import logging
from pathlib import Path
from typing import Optional

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import ask_llm
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils import commit_all_changes, get_full_status
from mcp_coder.workflow_utils.task_tracker import get_step_progress

from .prerequisites import (
    check_git_clean,
    check_main_branch,
    check_prerequisites,
    has_implementation_tasks,
)
from .task_processing import process_single_task

# Constants
PR_INFO_DIR = "pr_info"

# Setup logger
logger = logging.getLogger(__name__)


def prepare_task_tracker(project_dir: Path, provider: str, method: str) -> bool:
    """Prepare task tracker by populating it if it has no implementation steps.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')

    Returns:
        bool: True if task tracker is ready (already had tasks or successfully updated), False on error
    """
    logger.info("Checking if task tracker needs preparation...")

    # Check if pr_info/steps/ directory exists
    steps_dir = project_dir / PR_INFO_DIR / "steps"
    if not steps_dir.exists():
        logger.error(
            f"Directory {steps_dir} does not exist. Please create implementation steps first."
        )
        return False

    # Check if task tracker already has implementation tasks
    if has_implementation_tasks(project_dir):
        logger.info(
            "Task tracker already has implementation tasks. Skipping preparation."
        )
        return True

    logger.info(
        "Task tracker has no implementation tasks. Generating tasks from implementation steps..."
    )

    try:
        # Get the Task Tracker Update Prompt
        prompt_template = get_prompt(
            str(PROMPTS_FILE_PATH), "Task Tracker Update Prompt"
        )

        # Prepare environment variables for LLM subprocess
        env_vars = prepare_llm_environment(project_dir)

        # Call LLM with the prompt

        response = ask_llm(
            prompt_template,
            provider=provider,
            method=method,
            timeout=300,
            env_vars=env_vars,
        )

        if not response or not response.strip():
            logger.error("LLM returned empty response for task tracker update")
            return False

        logger.info("LLM response received for task tracker update")

        # Check what files changed using existing git_operations
        status = get_full_status(project_dir)

        # Only staged and modified files should contain TASK_TRACKER.md
        all_changed = status["staged"] + status["modified"] + status["untracked"]
        task_tracker_file = f"{PR_INFO_DIR}/TASK_TRACKER.md"

        # Check if only TASK_TRACKER.md was modified (case-insensitive comparison)
        if (
            len(all_changed) != 1
            or all_changed[0].casefold() != task_tracker_file.casefold()
        ):
            logger.error("Unexpected files were modified during task tracker update:")
            logger.error(f"  Expected: [{task_tracker_file}]")
            logger.error(f"  Found: {all_changed}")
            return False

        # Verify that task tracker now has implementation steps
        if not has_implementation_tasks(project_dir):
            logger.error(
                "Task tracker still has no implementation steps after LLM update"
            )
            return False

        # Commit the changes
        commit_message = (
            "TASK_TRACKER.md with implementation steps and PR tasks updated"
        )
        commit_result = commit_all_changes(commit_message, project_dir)

        if not commit_result["success"]:
            logger.error(
                f"Error committing task tracker changes: {commit_result['error']}"
            )
            return False

        logger.info("Task tracker updated and committed successfully")
        return True

    except Exception as e:
        logger.error(f"Error preparing task tracker: {e}")
        return False


def log_progress_summary(project_dir: Path) -> None:
    """Log a summary of step-by-step progress from task tracker.

    Args:
        project_dir: Path to the project directory

    Note:
        Handles exceptions gracefully and logs debug messages for failures.
        Creates formatted progress summary with progress bars and completion percentages.
    """
    try:
        pr_info_dir = str(project_dir / PR_INFO_DIR)
        progress = get_step_progress(pr_info_dir)

        if not progress:
            logger.debug("No step progress information available")
            return

        logger.info("=" * 60)
        logger.info("TASK TRACKER PROGRESS SUMMARY")
        logger.info("=" * 60)

        for step_name, step_info in progress.items():
            # Extract and validate types from step_info dict
            total_val = step_info["total"]
            completed_val = step_info["completed"]
            incomplete_val = step_info["incomplete"]
            incomplete_list_val = step_info["incomplete_tasks"]

            # Type narrowing assertions
            assert isinstance(total_val, int), "total should be int"
            assert isinstance(completed_val, int), "completed should be int"
            assert isinstance(incomplete_val, int), "incomplete should be int"
            assert isinstance(
                incomplete_list_val, list
            ), "incomplete_tasks should be list"

            # Now we can use the narrowed types
            total = total_val
            completed = completed_val
            incomplete = incomplete_val
            incomplete_list = incomplete_list_val

            # Calculate percentage
            percentage = (completed / total * 100) if total > 0 else 0

            # Create progress bar
            bar_length = 20
            filled = int(bar_length * completed / total) if total > 0 else 0
            bar = "█" * filled + "░" * (bar_length - filled)

            # Log step summary
            logger.info(f"{step_name}:")
            logger.info(f"  [{bar}] {percentage:.0f}% ({completed}/{total} complete)")

            # Show incomplete tasks for this step if any
            if incomplete > 0:
                task_preview = ", ".join(incomplete_list[:3])
                if len(incomplete_list) > 3:
                    task_preview += "..."
                logger.info(f"  Remaining: {task_preview}")

        logger.info("=" * 60)

    except Exception as e:
        logger.debug(f"Could not generate progress summary: {e}")


def run_implement_workflow(project_dir: Path, provider: str, method: str) -> int:
    """Main workflow orchestration function - processes all implementation tasks in sequence.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')

    Returns:
        int: Exit code (0 for success, 1 for error)

    Note:
        Coordinates the full workflow from prerequisites through task completion.
        Handles errors gracefully and provides comprehensive progress tracking.
    """
    logger.info(f"Starting implement workflow for project: {project_dir}")

    # Step 1: Check git status and prerequisites
    if not check_git_clean(project_dir):
        return 1

    if not check_main_branch(project_dir):
        return 1

    if not check_prerequisites(project_dir):
        return 1

    # Step 2: Prepare task tracker if needed
    if not prepare_task_tracker(project_dir, provider, method):
        return 1

    # Step 3: Show initial progress summary
    log_progress_summary(project_dir)

    # Step 4: Process all incomplete tasks in a loop
    completed_tasks = 0
    error_occurred = False

    while True:
        success, reason = process_single_task(project_dir, provider, method)

        if not success:
            if reason == "no_tasks":
                # Legitimate completion - no more tasks
                break
            elif reason == "error":
                # Error occurred during task processing
                error_occurred = True
                logger.error("Task processing failed - stopping workflow")
                break

        completed_tasks += 1
        logger.info(f"Completed {completed_tasks} task(s). Checking for more...")

        # Show updated progress after each task
        log_progress_summary(project_dir)

    # Step 5: Show final progress summary with appropriate messaging
    if error_occurred:
        logger.info(
            f"Workflow stopped due to error after processing {completed_tasks} task(s)"
        )
        if completed_tasks > 0:
            logger.info("\nProgress before error:")
            log_progress_summary(project_dir)
        return 1
    elif completed_tasks > 0:
        logger.info(
            f"Implement workflow completed successfully! Processed {completed_tasks} task(s)."
        )
        logger.info("\nFinal Progress:")
        log_progress_summary(project_dir)
    else:
        logger.info("No incomplete implementation tasks found - workflow complete")

    return 0
