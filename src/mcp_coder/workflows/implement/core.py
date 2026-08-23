"""Core workflow orchestration for implement workflow.

This module contains the main workflow orchestration functions that coordinate
prerequisites checking, task tracker preparation, and task processing loops.
"""

import logging
import os
import time
from functools import partial
from pathlib import Path
from typing import Optional

from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import LLMTimeoutError
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.mcp_workspace_git import get_current_branch_name, get_full_status
from mcp_coder.mcp_workspace_github import IssueManager
from mcp_coder.utils.pyproject_config import get_implement_config
from mcp_coder.utils.repo_config import get_repo_flag
from mcp_coder.workflow_steps.ci import check_and_fix_ci
from mcp_coder.workflow_steps.commit import (
    commit_changes,
    push_changes,
    run_formatters,
)
from mcp_coder.workflow_steps.rebase import _attempt_rebase_and_push
from mcp_coder.workflow_utils.failure_handling import (
    GuardOutcome,
    get_diff_stat,
    llm_failure_reason,
    run_guarded,
)
from mcp_coder.workflow_utils.label_transitions import update_workflow_label
from mcp_coder.workflow_utils.task_tracker import get_step_progress

from .constants import (
    MAX_NO_CHANGE_RETRIES,
    PR_INFO_DIR,
    RUN_MYPY_AFTER_EACH_TASK,
)
from .failure_reporting import (
    Progress,
    _fail,
    append_detail,
    format_failure_comment,
)
from .finalisation import run_finalisation
from .prerequisites import check_git_clean, check_main_branch, check_prerequisites
from .task_processing import (
    check_and_fix_mypy,
    process_task_with_retry,
    read_and_clear_blocked,
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
        The prerequisite checks and rebase run *before* the safety net (unlabeled,
        as before); everything after is wrapped in :func:`run_guarded`, which nets
        SIGTERM / unexpected exits into the general ``implementing_failed`` label.
    """
    logger.info(f"Starting implement workflow for project: {project_dir}")

    start_time = time.time()
    build_url = os.environ.get("BUILD_URL")

    # Step 1: Check git status and prerequisites (early returns, no safety net needed)
    if not check_git_clean(project_dir):
        return 1

    if not check_main_branch(project_dir):
        return 1

    if not check_prerequisites(project_dir):
        return 1

    # Step 1.5: Attempt rebase onto parent branch (never blocks workflow)
    _attempt_rebase_and_push(project_dir)

    # Mutable progress holder bridging the body to the net's comment, plus a
    # `fail` binding that carries the shared per-run failure context so each
    # deliberate failure site only supplies its reason/stage/message.
    progress = Progress()
    fail = partial(
        _fail,
        project_dir,
        progress=progress,
        start_time=start_time,
        build_url=build_url,
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )

    def body() -> int:
        # Read implement config from pyproject.toml
        implement_config = get_implement_config(project_dir)

        # Step 2: Prepare task tracker if needed
        if not prepare_task_tracker(
            project_dir, provider, mcp_config, settings_file, execution_dir
        ):
            return fail(
                "task_tracker_prep_failed",
                stage="Task tracker preparation",
                message="Failed to prepare task tracker",
            )

        # Step 3: Show initial progress summary
        log_progress_summary(project_dir)

        try:
            pr_info_path = str(project_dir / PR_INFO_DIR)
            step_progress = get_step_progress(pr_info_path)
            for step in step_progress.values():
                step_total = step["total"]
                assert isinstance(step_total, int)
                progress.total += step_total
        except Exception:  # pylint: disable=broad-exception-caught
            pass

        # Step 4: Process all incomplete tasks in a loop
        while True:
            outcome = process_task_with_retry(
                project_dir,
                provider,
                mcp_config,
                settings_file,
                execution_dir,
                format_code=implement_config.format_code,
                check_type_hints=implement_config.check_type_hints,
            )

            if not outcome.success:
                if outcome.reason == "no_tasks":
                    # Legitimate completion - no more tasks
                    break
                if outcome.reason == "blocked":
                    # The agent reported it could not proceed - terminal, no retry.
                    # Logged unconditionally: comment posting can be off, and the
                    # reason text is the whole point of this exit.
                    logger.error("Implementation blocked: %s", outcome.detail)
                    return fail(
                        "blocked",
                        stage="Task implementation",
                        message=outcome.detail,
                    )
                if outcome.reason == "timeout":
                    # LLM timeout during task processing
                    return fail(
                        "timeout",
                        stage="Task implementation",
                        message=append_detail(
                            "LLM timed out during task processing", outcome.detail
                        ),
                    )
                if outcome.reason == "mcp_unavailable":
                    # A required MCP server was unavailable during task processing
                    return fail(
                        "mcp_unavailable",
                        stage="Task implementation",
                        message=append_detail(
                            "MCP servers unavailable during task processing",
                            outcome.detail,
                        ),
                    )
                if outcome.reason == "no_changes_after_retries":
                    # Task produced no changes after all retry attempts
                    return fail(
                        "no_changes_after_retries",
                        stage="Task implementation",
                        message=(
                            f"Task produced no file changes after"
                            f" {MAX_NO_CHANGE_RETRIES} retry attempts"
                        ),
                    )
                if outcome.reason == "error":
                    # Error occurred during task processing
                    return fail(
                        "general",
                        stage="Task implementation",
                        message="Task processing failed",
                    )

            progress.completed += 1
            logger.info(f"Completed {progress.completed} task(s). Checking for more...")

            # Show updated progress after each task
            log_progress_summary(project_dir)

        # Step 5: Run final mypy check if not running after each task
        if (
            not RUN_MYPY_AFTER_EACH_TASK
            and progress.completed > 0
            and implement_config.check_type_hints
        ):
            logger.info("Running final mypy check after all tasks...")
            env_vars = prepare_llm_environment(project_dir)

            # Use step number 0 for final mypy check conversation.
            # check_and_fix_mypy no longer swallows the two typed LLM failures;
            # categorize them here (the only live call site) into
            # timeout / mcp_unavailable.
            try:
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
                    reason = llm_failure_reason(exc) or "general"
                    return fail(
                        reason,
                        stage="Final mypy check",
                        message="LLM failure during final mypy check",
                    )
                if not mypy_clean:
                    logger.warning(
                        "Final mypy check found unresolved issues - continuing anyway"
                    )

                # Format code after mypy fixes
                if implement_config.format_code and not run_formatters(project_dir):
                    logger.error("Formatting failed after final mypy check")
                    return fail(
                        "general",
                        stage="Post-implementation formatting",
                        message="Formatting failed after final mypy check",
                    )
            finally:
                # check_and_fix_mypy runs its own LLM turns, so drop any marker
                # it wrote: before the staging below so it never reaches a
                # commit, and on both early returns above so it cannot poison
                # the next run at check_git_clean / prepare_task_tracker.
                read_and_clear_blocked(project_dir)

            # Commit mypy fixes if any changes were made.
            status = get_full_status(project_dir)
            all_changes = status["staged"] + status["modified"] + status["untracked"]

            if all_changes:
                logger.info("Committing final mypy fixes...")
                if not commit_changes(
                    project_dir,
                    provider,
                    mcp_config=mcp_config,
                    execution_dir=str(execution_dir) if execution_dir else None,
                    settings_file=settings_file,
                ):
                    logger.error("Failed to commit final mypy fixes")
                    return fail(
                        "general",
                        stage="Post-implementation commit",
                        message="Failed to commit final mypy fixes",
                    )

                if not push_changes(project_dir):
                    logger.error("Failed to push final mypy fixes")
                    return fail(
                        "general",
                        stage="Post-implementation commit",
                        message="Failed to push final mypy fixes",
                    )
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
            # here — categorize it into timeout / mcp_unavailable.
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
                reason = llm_failure_reason(exc) or "general"
                return fail(
                    reason,
                    stage="CI pipeline analysis",
                    message="LLM failure during CI failure analysis",
                )
            if not ci_success:
                logger.error("CI check failed after maximum fix attempts")
                return fail(
                    "ci_fix_exhausted",
                    stage="CI pipeline fix",
                    message="CI check failed after maximum fix attempts",
                )
        else:
            logger.error("Could not determine current branch - skipping CI check")

        # Step 6: Success label transition
        if update_issue_labels:
            try:
                to_label_id = (
                    "code_review_bot"
                    if get_repo_flag(project_dir, "auto_review_implementation")
                    else "code_review"
                )
                issue_manager = IssueManager(project_dir)
                update_workflow_label(
                    issue_manager,
                    from_label_id="implementing",
                    to_label_id=to_label_id,
                )
            except Exception as exc:  # pylint: disable=broad-exception-caught
                logger.warning("Failed to update issue label on success: %s", exc)

        # Step 7: Show final progress summary with appropriate messaging
        if progress.completed > 0:
            logger.info(
                f"Implement workflow completed successfully! "
                f"Processed {progress.completed} task(s).",
            )
            logger.info("\nFinal Progress:")
            log_progress_summary(project_dir)
        else:
            logger.info("No incomplete implementation tasks found - workflow complete")

        return 0

    def build_comment(outcome: GuardOutcome) -> str:
        # Net (SIGTERM / unexpected exit) comment: reuse the deliberate-path
        # formatter with the general reason so the comment (including the live
        # Progress line) stays byte-identical to the pre-refactor safety net.
        return format_failure_comment(
            "general",
            outcome.stage,
            outcome.message,
            completed=progress.completed,
            total=progress.total,
            elapsed=outcome.elapsed_time,
            build_url=build_url,
            diff_stat=get_diff_stat(project_dir),
        )

    return run_guarded(
        body,
        project_dir=project_dir,
        from_label_id="implementing",
        general_category="implementing_failed",
        comment_header="## Implementation Failed",
        build_comment=build_comment,
        update_issue_labels=update_issue_labels,
        post_issue_comments=post_issue_comments,
    )
