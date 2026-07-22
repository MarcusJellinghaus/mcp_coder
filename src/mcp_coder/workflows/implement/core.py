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

from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.mcp_workspace_git import get_current_branch_name, get_full_status
from mcp_coder.mcp_workspace_github import IssueManager
from mcp_coder.utils.pyproject_config import get_implement_config
from mcp_coder.workflow_steps.commit import (
    commit_changes,
    push_changes,
    run_formatters,
)
from mcp_coder.workflow_utils.failure_handling import format_mcp_unavailable_message
from mcp_coder.workflow_utils.label_transitions import update_workflow_label
from mcp_coder.workflow_utils.task_tracker import get_step_progress

from .ci_operations import check_and_fix_ci
from .constants import (
    MAX_NO_CHANGE_RETRIES,
    PR_INFO_DIR,
    RUN_MYPY_AFTER_EACH_TASK,
    FailureCategory,
    WorkflowFailure,
)
from .failure_reporting import _handle_workflow_failure
from .finalisation import run_finalisation
from .llm_failures import REASON_TO_CATEGORY, llm_failure_reason
from .prerequisites import check_git_clean, check_main_branch, check_prerequisites
from .rebase import _attempt_rebase_and_push
from .task_processing import (
    check_and_fix_mypy,
    process_task_with_retry,
)
from .task_tracker_prep import log_progress_summary, prepare_task_tracker

# Setup logger
logger = logging.getLogger(__name__)


def run_implement_workflow(
    project_dir: Path,
    provider: str,
    mcp_config: Optional[str] = None,
    settings_file: str | None = None,
    execution_dir: Optional[Path] = None,
    update_issue_labels: bool = False,
    post_issue_comments: bool = False,
) -> int:
    """Main workflow orchestration function - processes all implementation tasks in sequence.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json; forwarded to prompt_llm.
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
    caught_exception: BaseException | None = None

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
        if not prepare_task_tracker(
            project_dir, provider, mcp_config, settings_file, execution_dir
        ):
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
                settings_file,
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
                if reason == "mcp_unavailable":
                    # A required MCP server was unavailable during task processing
                    _handle_workflow_failure(
                        WorkflowFailure(
                            category=REASON_TO_CATEGORY["mcp_unavailable"],
                            stage="Task implementation",
                            message="MCP servers unavailable during task processing",
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

            # Use step number 0 for final mypy check conversation.
            # check_and_fix_mypy no longer swallows the two typed LLM failures;
            # categorize them here (the only live call site) into
            # llm_timeout / mcp_unavailable.
            try:
                mypy_clean = check_and_fix_mypy(
                    project_dir,
                    0,
                    provider,
                    env_vars,
                    mcp_config,
                    settings_file,
                    execution_dir=execution_dir,
                )
            except (LLMTimeoutError, McpServersUnavailableError) as exc:
                # Fallback keeps mypy happy; the reason is non-None for both types.
                reason = llm_failure_reason(exc) or "error"
                _handle_workflow_failure(
                    WorkflowFailure(
                        category=REASON_TO_CATEGORY[reason],
                        stage="Final mypy check",
                        message="LLM failure during final mypy check",
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
            if not mypy_clean:
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
            settings_file,
            execution_dir,
        )
        if not finalisation_success:
            logger.warning("Finalisation encountered issues - continuing anyway")

        # Step 5.6: Check CI pipeline and auto-fix if needed
        logger.info("Checking CI pipeline status...")
        current_branch = get_current_branch_name(project_dir)
        if current_branch:
            # CI-analysis no longer swallows the two typed LLM failures; a
            # fix-phase timeout/MCP-unavailable is still absorbed into the
            # 4-attempt loop (Decision 10). Only an analysis-phase abort reaches
            # here — categorize it into llm_timeout / mcp_unavailable.
            try:
                ci_success = check_and_fix_ci(
                    project_dir=project_dir,
                    branch=current_branch,
                    provider=provider,
                    mcp_config=mcp_config,
                    settings_file=settings_file,
                    execution_dir=execution_dir,
                )
            except (LLMTimeoutError, McpServersUnavailableError) as exc:
                # Fallback keeps mypy happy; the reason is non-None for both types.
                reason = llm_failure_reason(exc) or "error"
                _handle_workflow_failure(
                    WorkflowFailure(
                        category=REASON_TO_CATEGORY[reason],
                        stage="CI pipeline analysis",
                        message="LLM failure during CI failure analysis",
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
                update_workflow_label(
                    issue_manager,
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
    except Exception as exc:  # pylint: disable=broad-exception-caught
        caught_exception = exc
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
            if isinstance(caught_exception, McpServersUnavailableError):
                message = format_mcp_unavailable_message(caught_exception)
            elif sigterm_received:
                message = "Workflow terminated by signal"
            else:
                message = "Workflow exited without reaching a terminal state"
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
