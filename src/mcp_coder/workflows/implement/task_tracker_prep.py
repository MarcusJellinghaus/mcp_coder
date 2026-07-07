"""Task tracker preparation helpers for the implement workflow.

Populates the task tracker with implementation steps when needed and logs a
step-by-step progress summary.
"""

import logging
from pathlib import Path
from typing import Optional

from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS, PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.mcp_workspace_git import commit_all_changes, get_full_status
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.workflow_utils.task_tracker import get_step_progress

from .constants import LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS, PR_INFO_DIR
from .prerequisites import has_implementation_tasks

logger = logging.getLogger(__name__)


def prepare_task_tracker(
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    settings_file: str | None = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Prepare task tracker by populating it if it has no implementation steps.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json; forwarded to prompt_llm.
        execution_dir: Optional working directory for Claude subprocess.
            Default: None (uses caller's working directory)

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
        branch_name = get_branch_name_for_logging(project_dir)
        llm_response = prompt_llm(
            prompt_template,
            provider=provider,
            # Inactivity budget (was wall-clock), kept below the CI step cap.
            timeout=LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS,
            env_vars=env_vars,
            execution_dir=str(execution_dir) if execution_dir else None,
            mcp_config=mcp_config,
            settings_file=settings_file,
            branch_name=branch_name,
        )
        response = llm_response["text"]
        try:
            store_session(
                llm_response,
                prompt_template,
                store_path=str(project_dir / ".mcp-coder" / "implement_sessions"),
                step_name="task_tracker",
                branch_name=branch_name,
            )
        except Exception as e:
            logger.warning("Failed to store task tracker session: %s", e)

        if not response or not response.strip():
            logger.error("LLM returned empty response for task tracker update")
            return False

        logger.info("LLM response received for task tracker update")

        # Check what files changed using existing git_operations
        status = get_full_status(project_dir)

        # Only staged and modified files should contain TASK_TRACKER.md
        all_changed = status["staged"] + status["modified"] + status["untracked"]

        # Filter out auto-generated build artifacts (e.g., uv.lock)
        ignore_set = set(DEFAULT_IGNORED_BUILD_ARTIFACTS)
        all_changed = [f for f in all_changed if f not in ignore_set]

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
