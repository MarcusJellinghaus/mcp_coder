"""Core workflow orchestration for implement workflow.

This module contains the main workflow orchestration functions that coordinate
prerequisites checking, task tracker preparation, and task processing loops.
"""

import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Optional

from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS, PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.mcp_workspace_git import (
    commit_all_changes,
    extract_issue_number_from_branch,
    get_current_branch_name,
    get_full_status,
    rebase_onto_branch,
)
from mcp_coder.prompt_manager import get_prompt, get_prompt_with_substitutions
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.utils.github_operations.issues import IssueManager
from mcp_coder.utils.pyproject_config import get_implement_config
from mcp_coder.workflow_utils.base_branch import detect_base_branch
from mcp_coder.workflow_utils.commit_operations import generate_commit_message_with_llm
from mcp_coder.workflow_utils.failure_handling import (
    WorkflowFailure as SharedWorkflowFailure,
)
from mcp_coder.workflow_utils.failure_handling import (
    format_elapsed_time,
    get_diff_stat,
    handle_workflow_failure,
)
from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerFileNotFoundError,
    get_step_progress,
    has_incomplete_work,
)

from .ci_operations import check_and_fix_ci
from .constants import (
    COMMIT_MESSAGE_FILE,
    LLM_FINALISATION_TIMEOUT_SECONDS,
    LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS,
    MAX_NO_CHANGE_RETRIES,
    PR_INFO_DIR,
    RUN_MYPY_AFTER_EACH_TASK,
    FailureCategory,
    WorkflowFailure,
)
from .prerequisites import (
    check_git_clean,
    check_main_branch,
    check_prerequisites,
    has_implementation_tasks,
)
from .task_processing import (
    check_and_fix_mypy,
    commit_changes,
    process_task_with_retry,
    push_changes,
    run_formatters,
)

# Setup logger
logger = logging.getLogger(__name__)


def _format_failure_comment(failure: WorkflowFailure, diff_stat: str) -> str:
    """Format a GitHub comment for a workflow failure.

    Args:
        failure: The workflow failure details
        diff_stat: Git diff stat string for uncommitted changes

    Returns:
        Formatted GitHub comment string.
    """
    lines = [
        "## Implementation Failed",
        f"**Category:** {failure.category.name.replace('_', ' ').title()}",
        f"**Stage:** {failure.stage}",
        f"**Error:** {failure.message}",
    ]
    if failure.tasks_total > 0:
        lines.append(
            f"**Progress:** {failure.tasks_completed}/{failure.tasks_total} tasks completed"
        )
    if failure.elapsed_time is not None:
        lines.append(f"**Elapsed:** {format_elapsed_time(failure.elapsed_time)}")
    if failure.build_url:
        lines.append(f"**Build:** {failure.build_url}")
    lines.append("")
    lines.append("### Uncommitted Changes")
    lines.append(f"```\n{diff_stat or 'No uncommitted changes'}\n```")
    return "\n".join(lines)


def _handle_workflow_failure(
    failure: WorkflowFailure,
    project_dir: Path,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
) -> None:
    """Handle workflow failure: set label, post comment, log banner."""
    diff_stat = get_diff_stat(project_dir)
    comment_body = _format_failure_comment(failure, diff_stat)
    handle_workflow_failure(
        failure=SharedWorkflowFailure(
            category=failure.category.value,
            stage=failure.stage,
            message=failure.message,
            elapsed_time=failure.elapsed_time,
        ),
        comment_body=comment_body,
        project_dir=project_dir,
        from_label_id="implementing",
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )


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


def prepare_task_tracker(
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Prepare task tracker by populating it if it has no implementation steps.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
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
            timeout=LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS,
            env_vars=env_vars,
            execution_dir=str(execution_dir) if execution_dir else None,
            mcp_config=mcp_config,
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


def run_finalisation(
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Run implementation finalisation to verify and complete remaining tasks.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess

    Returns:
        bool: True if finalisation succeeded or was skipped (no tasks), False on error
    """
    logger.info("Running implementation finalisation...")

    # 1. Check if there are incomplete tasks
    try:
        pr_info_path = str(project_dir / PR_INFO_DIR)
        if not has_incomplete_work(pr_info_path):
            logger.info("No incomplete tasks - skipping finalisation")
            return True
    except TaskTrackerFileNotFoundError:
        logger.error("Task tracker not found - cannot run finalisation")
        return False

    logger.info("Found incomplete tasks - calling LLM to finalise...")

    # 2. Prepare environment and call LLM with finalisation prompt
    env_vars = prepare_llm_environment(project_dir)
    branch_name = get_branch_name_for_logging(project_dir)

    finalisation_prompt = get_prompt_with_substitutions(
        str(PROMPTS_FILE_PATH),
        "Finalisation Prompt",
        {
            "pr_info_dir": PR_INFO_DIR,
            "commit_message_path": f"{PR_INFO_DIR}/{COMMIT_MESSAGE_FILE}",
        },
    )

    llm_response = prompt_llm(
        finalisation_prompt,
        provider=provider,
        timeout=LLM_FINALISATION_TIMEOUT_SECONDS,
        env_vars=env_vars,
        execution_dir=str(execution_dir) if execution_dir else None,
        mcp_config=mcp_config,
        branch_name=branch_name,
    )
    response = llm_response["text"]
    try:
        store_session(
            llm_response,
            finalisation_prompt,
            store_path=str(project_dir / ".mcp-coder" / "implement_sessions"),
            step_name="finalisation",
            branch_name=branch_name,
        )
    except Exception as e:
        logger.warning("Failed to store finalisation session: %s", e)

    # 3. Check for empty/failed response
    if not response or not response.strip():
        logger.error("Finalisation LLM returned empty response")
        return False

    logger.debug("Finalisation LLM response received")

    # 4. Check if there are changes to commit
    status = get_full_status(project_dir)
    if not status["staged"] and not status["modified"] and not status["untracked"]:
        logger.info("No changes after finalisation - nothing to commit")
        return True

    # 5. Get commit message (3-level fallback: file → LLM → default)
    commit_message = None
    commit_msg_path = project_dir / COMMIT_MESSAGE_FILE

    # Level 1: Read from file
    if commit_msg_path.exists():
        commit_message = commit_msg_path.read_text(encoding="utf-8").strip()
        # Always delete file after reading (even if empty)
        commit_msg_path.unlink()
        if commit_message:
            logger.debug("Read and deleted commit message file")
        else:
            logger.debug("Commit message file was empty, deleted")

    # Level 2: Generate with LLM
    if not commit_message:
        logger.info("Generating commit message with LLM...")
        success, llm_message, error = generate_commit_message_with_llm(
            project_dir,
            provider=provider,
            execution_dir=str(execution_dir) if execution_dir else None,
        )
        if success and llm_message:
            commit_message = llm_message
            logger.debug("Commit message generated by LLM")
        else:
            logger.warning(f"LLM commit message generation failed: {error}")

    # Level 3: Use default
    if not commit_message:
        commit_message = "Finalisation: complete remaining tasks"
        logger.warning("Using default commit message")

    # 6. Stage all changes and commit
    logger.info("Committing finalisation changes...")
    commit_result = commit_all_changes(commit_message, project_dir)
    if not commit_result["success"]:
        logger.error(f"Failed to commit finalisation changes: {commit_result['error']}")
        return False

    # 7. Push changes
    logger.info("Pushing finalisation changes...")
    if not push_changes(project_dir):
        logger.warning("Failed to push finalisation changes")
        return False

    return True


def run_implement_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
) -> int:
    """Main workflow orchestration function - processes all implementation tasks in sequence.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess
        update_issue_labels: If True, update GitHub issue labels on success/failure
        post_issue_comments: If True, post comments on the issue on failure

    Returns:
        int: Exit code (0 for success, 1 for error)

    Note:
        Coordinates the full workflow from prerequisites through task completion.
        Handles errors gracefully and provides comprehensive progress tracking.

    Raises:
        SystemExit: If SIGTERM signal is received during workflow execution.
    """
    logger.info(f"Starting implement workflow for project: {project_dir}")

    start_time = time.time()
    build_url = os.environ.get("BUILD_URL")
    reached_terminal_state = False
    sigterm_received = False
    completed_tasks = 0
    total_tasks = 0
    previous_sigterm_handler = None

    def sigterm_handler(_signum: int, _frame: Any) -> None:
        nonlocal sigterm_received
        sigterm_received = True
        sys.exit(1)

    # Step 1: Check git status and prerequisites (early returns, no safety net needed)
    if not check_git_clean(project_dir):
        return 1

    if not check_main_branch(project_dir):
        return 1

    if not check_prerequisites(project_dir):
        return 1

    # Step 1.5: Attempt rebase onto parent branch (never blocks workflow)
    _attempt_rebase_and_push(project_dir)

    # Register SIGTERM handler (after early checks, before protected region)
    try:
        previous_sigterm_handler = signal.signal(signal.SIGTERM, sigterm_handler)
    except (OSError, ValueError):
        logger.debug("Could not register SIGTERM handler")

    try:
        # Read implement config from pyproject.toml
        implement_config = get_implement_config(project_dir)

        # Step 2: Prepare task tracker if needed
        if not prepare_task_tracker(project_dir, provider, mcp_config, execution_dir):
            _handle_workflow_failure(
                WorkflowFailure(
                    category=FailureCategory.TASK_TRACKER_PREP_FAILED,
                    stage="Task tracker preparation",
                    message="Failed to prepare task tracker",
                    build_url=build_url,
                    elapsed_time=time.time() - start_time,
                ),
                project_dir,
                update_issue_labels=update_issue_labels,
                post_issue_comments=post_issue_comments,
            )
            reached_terminal_state = True
            return 1

        # Step 3: Show initial progress summary
        log_progress_summary(project_dir)

        try:
            pr_info_path = str(project_dir / PR_INFO_DIR)
            progress = get_step_progress(pr_info_path)
            for step in progress.values():
                step_total = step["total"]
                assert isinstance(step_total, int)
                total_tasks += step_total
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        # Step 4: Process all incomplete tasks in a loop
        while True:
            success, reason = process_task_with_retry(
                project_dir,
                provider,
                mcp_config,
                execution_dir,
                format_code=implement_config.format_code,
                check_type_hints=implement_config.check_type_hints,
            )

            if not success:
                if reason == "no_tasks":
                    # Legitimate completion - no more tasks
                    break
                if reason == "timeout":
                    # LLM timeout during task processing
                    _handle_workflow_failure(
                        WorkflowFailure(
                            category=FailureCategory.LLM_TIMEOUT,
                            stage="Task implementation",
                            message="LLM timed out during task processing",
                            tasks_completed=completed_tasks,
                            tasks_total=total_tasks,
                            build_url=build_url,
                            elapsed_time=time.time() - start_time,
                        ),
                        project_dir,
                        update_issue_labels=update_issue_labels,
                        post_issue_comments=post_issue_comments,
                    )
                    reached_terminal_state = True
                    return 1
                if reason == "no_changes_after_retries":
                    # Task produced no changes after all retry attempts
                    _handle_workflow_failure(
                        WorkflowFailure(
                            category=FailureCategory.NO_CHANGES_AFTER_RETRIES,
                            stage="Task implementation",
                            message=(
                                f"Task produced no file changes after"
                                f" {MAX_NO_CHANGE_RETRIES} retry attempts"
                            ),
                            tasks_completed=completed_tasks,
                            tasks_total=total_tasks,
                            build_url=build_url,
                            elapsed_time=time.time() - start_time,
                        ),
                        project_dir,
                        update_issue_labels=update_issue_labels,
                        post_issue_comments=post_issue_comments,
                    )
                    reached_terminal_state = True
                    return 1
                if reason == "error":
                    # Error occurred during task processing
                    _handle_workflow_failure(
                        WorkflowFailure(
                            category=FailureCategory.GENERAL,
                            stage="Task implementation",
                            message="Task processing failed",
                            tasks_completed=completed_tasks,
                            tasks_total=total_tasks,
                            build_url=build_url,
                            elapsed_time=time.time() - start_time,
                        ),
                        project_dir,
                        update_issue_labels=update_issue_labels,
                        post_issue_comments=post_issue_comments,
                    )
                    reached_terminal_state = True
                    return 1

            completed_tasks += 1
            logger.info(f"Completed {completed_tasks} task(s). Checking for more...")

            # Show updated progress after each task
            log_progress_summary(project_dir)

        # Step 5: Run final mypy check if not running after each task
        if (
            not RUN_MYPY_AFTER_EACH_TASK
            and completed_tasks > 0
            and implement_config.check_type_hints
        ):
            logger.info("Running final mypy check after all tasks...")
            env_vars = prepare_llm_environment(project_dir)

            # Use step number 0 for final mypy check conversation
            if not check_and_fix_mypy(
                project_dir,
                0,
                provider,
                env_vars,
                mcp_config,
                execution_dir=execution_dir,
            ):
                logger.warning(
                    "Final mypy check found unresolved issues - continuing anyway"
                )

            # Format code after mypy fixes
            if implement_config.format_code and not run_formatters(project_dir):
                logger.error("Formatting failed after final mypy check")
                _handle_workflow_failure(
                    WorkflowFailure(
                        category=FailureCategory.GENERAL,
                        stage="Post-implementation formatting",
                        message="Formatting failed after final mypy check",
                        tasks_completed=completed_tasks,
                        tasks_total=total_tasks,
                        build_url=build_url,
                        elapsed_time=time.time() - start_time,
                    ),
                    project_dir,
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                )
                reached_terminal_state = True
                return 1

            # Commit mypy fixes if any changes were made
            status = get_full_status(project_dir)
            all_changes = status["staged"] + status["modified"] + status["untracked"]

            if all_changes:
                logger.info("Committing final mypy fixes...")
                if not commit_changes(project_dir, provider):
                    logger.error("Failed to commit final mypy fixes")
                    _handle_workflow_failure(
                        WorkflowFailure(
                            category=FailureCategory.GENERAL,
                            stage="Post-implementation commit",
                            message="Failed to commit final mypy fixes",
                            tasks_completed=completed_tasks,
                            tasks_total=total_tasks,
                            build_url=build_url,
                            elapsed_time=time.time() - start_time,
                        ),
                        project_dir,
                        update_issue_labels=update_issue_labels,
                        post_issue_comments=post_issue_comments,
                    )
                    reached_terminal_state = True
                    return 1

                if not push_changes(project_dir):
                    logger.error("Failed to push final mypy fixes")
                    _handle_workflow_failure(
                        WorkflowFailure(
                            category=FailureCategory.GENERAL,
                            stage="Post-implementation commit",
                            message="Failed to push final mypy fixes",
                            tasks_completed=completed_tasks,
                            tasks_total=total_tasks,
                            build_url=build_url,
                            elapsed_time=time.time() - start_time,
                        ),
                        project_dir,
                        update_issue_labels=update_issue_labels,
                        post_issue_comments=post_issue_comments,
                    )
                    reached_terminal_state = True
                    return 1
            else:
                logger.info("No changes from final mypy check - skipping commit")

        # Step 5.5: Run finalisation to complete any remaining tasks
        finalisation_success = run_finalisation(
            project_dir,
            provider,
            mcp_config,
            execution_dir,
        )
        if not finalisation_success:
            logger.warning("Finalisation encountered issues - continuing anyway")

        # Step 5.6: Check CI pipeline and auto-fix if needed
        logger.info("Checking CI pipeline status...")
        current_branch = get_current_branch_name(project_dir)
        if current_branch:
            ci_success = check_and_fix_ci(
                project_dir=project_dir,
                branch=current_branch,
                provider=provider,
                mcp_config=mcp_config,
                execution_dir=execution_dir,
            )
            if not ci_success:
                logger.error("CI check failed after maximum fix attempts")
                _handle_workflow_failure(
                    WorkflowFailure(
                        category=FailureCategory.CI_FIX_EXHAUSTED,
                        stage="CI pipeline fix",
                        message="CI check failed after maximum fix attempts",
                        tasks_completed=completed_tasks,
                        tasks_total=total_tasks,
                        build_url=build_url,
                        elapsed_time=time.time() - start_time,
                    ),
                    project_dir,
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                )
                reached_terminal_state = True
                return 1
        else:
            logger.error("Could not determine current branch - skipping CI check")

        # Step 6: Success label transition
        if update_issue_labels:
            try:
                issue_manager = IssueManager(project_dir)
                issue_manager.update_workflow_label(
                    from_label_id="implementing",
                    to_label_id="code_review",
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.warning("Failed to update issue label on success: %s", exc)

        # Step 7: Show final progress summary with appropriate messaging
        if completed_tasks > 0:
            logger.info(
                f"Implement workflow completed successfully! Processed {completed_tasks} task(s).",
            )
            logger.info("\nFinal Progress:")
            log_progress_summary(project_dir)
        else:
            logger.info("No incomplete implementation tasks found - workflow complete")

        reached_terminal_state = True
        return 0
    except SystemExit:
        raise
    except Exception:  # pylint: disable=broad-exception-caught
        logger.error("Unexpected exception in workflow", exc_info=True)
        return 1
    finally:
        # Restore previous SIGTERM handler
        if previous_sigterm_handler is not None:
            try:
                signal.signal(signal.SIGTERM, previous_sigterm_handler)
            except (OSError, ValueError):
                pass

        # Safety net: handle unexpected exit (including SIGTERM via sys.exit)
        if not reached_terminal_state:
            elapsed = time.time() - start_time
            stage = "SIGTERM received" if sigterm_received else "Unexpected exit"
            message = (
                "Workflow terminated by signal"
                if sigterm_received
                else "Workflow exited without reaching a terminal state"
            )
            try:
                _handle_workflow_failure(
                    WorkflowFailure(
                        category=FailureCategory.GENERAL,
                        stage=stage,
                        message=message,
                        tasks_completed=completed_tasks,
                        tasks_total=total_tasks,
                        build_url=build_url,
                        elapsed_time=elapsed,
                    ),
                    project_dir,
                    update_issue_labels=update_issue_labels,
                    post_issue_comments=post_issue_comments,
                )
            except Exception:  # pylint: disable=broad-exception-caught
                logger.error("Safety net failure handling also failed", exc_info=True)
