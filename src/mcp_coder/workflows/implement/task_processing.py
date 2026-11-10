"""Task processing functions for implement workflow.

This module contains functions for processing individual implementation tasks,
including LLM integration, mypy fixes, formatting, and git operations.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import LLMTimeoutError, prompt_llm
from mcp_coder.llm.providers.claude.claude_code_cli import McpServersUnavailableError
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.mcp_workspace_git import get_full_status
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.utils.prompt_slots import fill_prompt, resolve_prompt_slots
from mcp_coder.utils.toolkit_runner import bash_grants_of, llm_permissions
from mcp_coder.workflow_steps.commit import (
    commit_changes,
    push_changes,
    run_formatters,
)
from mcp_coder.workflow_utils.failure_handling import llm_failure_reason
from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerError,
    get_incomplete_tasks,
)

from .blocked import read_and_clear_blocked
from .check_loop import CheckOutcome, check_and_fix_mypy
from .constants import (
    COMMIT_MESSAGE_FILE,
    LLM_INACTIVITY_TIMEOUT_SECONDS,
    MAX_NO_CHANGE_RETRIES,
    PR_INFO_DIR,
)

# Setup logger
logger = logging.getLogger(__name__)

RETRY_REMINDER = (
    "\n\n⚠️ Previous attempt produced NO file changes. "
    "If the task is already complete AND you saw its checks pass, tick the "
    "checkbox [ ] → [x] in pr_info/TASK_TRACKER.md — that file edit IS the "
    "deliverable. If the task genuinely needs code, do the work now. "
    "If something blocks you from either, write one line to "
    "pr_info/.blocked.txt saying what, and stop."
)

NO_PROGRESS_REMINDER = (
    "\n\n⚠️ The previous attempt changed files but did not complete any task in "
    "pr_info/TASK_TRACKER.md — no checkbox went from [ ] to [x]. Writing notes, "
    "logs or prose into a step or plan file is NOT progress and is NOT a way to "
    "report a problem. Either do the work and tick the box, or — if something "
    "blocks you — write one line to pr_info/.blocked.txt saying what blocks you, "
    "and stop."
)

RETRY_REMINDERS: dict[str, str] = {
    "no_changes": RETRY_REMINDER,
    "no_progress": NO_PROGRESS_REMINDER,
}


@dataclass(frozen=True)
class TaskOutcome:
    """Result of one implementation task attempt.

    Attributes:
        success: True if the task completed successfully.
        reason: Category key the orchestrator maps to a failure label.
        detail: Free-text explanation accompanying the category, if any.
        checks_failed: True if the attempt aborted in the per-task check stage.
    """

    success: bool
    reason: str
    detail: str = ""
    checks_failed: bool = False


def _count_incomplete_tasks(project_dir: Path) -> int:
    """Count incomplete non-meta tasks.

    TaskTrackerError propagates if the tracker is unreadable.

    Args:
        project_dir: Path to the project directory

    Returns:
        Number of incomplete non-meta tasks.
    """
    return len(
        get_incomplete_tasks(str(project_dir / PR_INFO_DIR), exclude_meta_tasks=True)
    )


def _cleanup_commit_message_file(project_dir: Path) -> None:
    """Remove stale commit message file from previous failed runs."""
    commit_msg_path = project_dir / COMMIT_MESSAGE_FILE
    if commit_msg_path.exists():
        commit_msg_path.unlink()
        logger.debug("Cleaned up stale commit message file")


def process_single_task(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    attempt: int = 1,
    check_type_hints: bool = False,
    previous_reason: str | None = None,
) -> TaskOutcome:
    """Process a single implementation task.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json; forwarded to prompt_llm.
        attempt: 1-based attempt number; appends retry reminder when > 1
        check_type_hints: If False, the implement_task binding's check@*
            requests are dropped; its other requests still run
        previous_reason: Reason the previous attempt returned; selects which
            retry reminder is appended when attempt > 1

    Returns:
        TaskOutcome where:
        - success: True if task completed successfully
        - reason: 'completed' | 'no_tasks' | 'no_changes' | 'no_progress'
          | 'blocked' | 'error' | 'timeout' | 'mcp_unavailable'. The two LLM
          failures (inactivity timeout, MCP servers unavailable) are
          categorized here into their reason strings so the orchestrator can
          map them to a failure label; they, 'blocked' and 'error' can also
          come from the check stage. Checks still reporting findings at the
          fix-turn cap do not fail the task. 'no_progress' means files changed
          (and were committed) but the incomplete-task count did not decrease.
        - detail: free-text explanation; carries the blocked marker text for
          the 'blocked', 'timeout' and 'mcp_unavailable' reasons, the task
          name for 'no_progress', the tracker fault for an unreadable
          tracker ('error') and the check error ('error'), else empty.
    """
    # Cleanup stale files from previous failed runs
    _cleanup_commit_message_file(project_dir)
    # Drop a stale blocked marker from a previous failed run
    read_and_clear_blocked(project_dir)

    # Prepare environment variables for LLM subprocess
    env_vars = prepare_llm_environment(project_dir)

    # One tracker read both selects the task and snapshots the progress-gate count
    logger.info("Checking for incomplete tasks...")
    try:
        incomplete_tasks = get_incomplete_tasks(
            str(project_dir / PR_INFO_DIR), exclude_meta_tasks=True
        )
    except TaskTrackerError as e:
        logger.error(f"Cannot read task tracker: {e}")
        return TaskOutcome(False, "error", f"Cannot read pr_info/TASK_TRACKER.md: {e}")
    except Exception as e:  # pylint: disable=broad-exception-caught
        # OSError / UnicodeDecodeError from the file read are not TaskTrackerError
        logger.error(f"Cannot read task tracker: {e}")
        return TaskOutcome(
            False,
            "error",
            f"Cannot read pr_info/TASK_TRACKER.md: unexpected {type(e).__name__}: {e}",
        )
    if not incomplete_tasks:
        logger.info("No incomplete implementation tasks found (meta-tasks excluded)")
        return TaskOutcome(False, "no_tasks")
    next_task = incomplete_tasks[0]
    tasks_before = len(incomplete_tasks)
    logger.info(f"Found next task: {next_task}")

    # Step 3: Get implementation prompt template
    logger.debug("Loading implementation prompt template...")
    try:
        bash_grants = bash_grants_of(llm_permissions(project_dir, provider))
        template = get_prompt(
            str(PROMPTS_FILE_PATH), "Implementation Prompt Template using task tracker"
        )
        # Fill before the task line is appended: task names are never filled
        prompt_template = fill_prompt(
            template,
            {},
            resolve_prompt_slots(template, project_dir, provider, bash_grants),
        )
    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error loading prompt template: {e}")
        return TaskOutcome(False, "error")

    # Step 4: Extract step number from task (needed for store_session step_name)
    step_match = re.search(r"Step (\d+)", next_task)
    step_num = int(step_match.group(1)) if step_match else 1

    # Step 5: Call LLM with prompt
    logger.info("Calling LLM for implementation...")
    llm_error: str | None = None
    try:
        # Create the full prompt by combining template with task context
        full_prompt = f"""{prompt_template}

Current task from TASK_TRACKER.md: {next_task}

Please implement this task step by step."""

        if attempt > 1:
            full_prompt += RETRY_REMINDERS.get(
                previous_reason or "no_changes", RETRY_REMINDER
            )

        branch_name = get_branch_name_for_logging(str(project_dir))
        llm_response = prompt_llm(
            full_prompt,
            provider=provider,
            # Tool-using site (implement task): inactivity budget, not wall-clock.
            timeout=LLM_INACTIVITY_TIMEOUT_SECONDS,
            env_vars=env_vars,
            project_dir=str(project_dir),
            mcp_config=mcp_config,
            settings_file=settings_file,
            branch_name=branch_name,
            bash_grants=bash_grants,
        )
        response = llm_response["text"]

        if not response or not response.strip():
            logger.error("LLM returned empty response")
            logger.debug(f"Response was: {repr(response)}")
            llm_error = "error"
        else:
            logger.info("LLM response received successfully")

            try:
                store_session(
                    response_data=llm_response,
                    prompt=full_prompt,
                    store_path=str(project_dir / ".mcp-coder" / "implement_sessions"),
                    step_name=f"step_{step_num}",
                    branch_name=branch_name,
                )
            except Exception as store_err:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
                logger.warning("Failed to store implement session: %s", store_err)

    except (LLMTimeoutError, McpServersUnavailableError) as e:
        # Categorize the two typed LLM failures into stable workflow reasons
        # ("timeout" / "mcp_unavailable") so the orchestrator can map them to a
        # failure label. Fallback keeps mypy happy; both branches of
        # llm_failure_reason are non-None for these exception types.
        llm_error = llm_failure_reason(e) or "error"
        logger.error("LLM call failed (%s) for task: %s", llm_error, next_task)
    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error calling LLM: {e}")
        llm_error = "error"
    finally:
        # Read in `finally` so no exit path can leave the marker on disk: a
        # stale marker breaks the next run at check_git_clean and
        # prepare_task_tracker.
        blocked = read_and_clear_blocked(project_dir)

    # Branch once, BEFORE the files-changed check below. The marker is itself an
    # untracked change, so checking it later would read as "files changed ->
    # success" and commit the marker - the inverted path this exists to prevent.
    if llm_error in ("timeout", "mcp_unavailable"):
        return TaskOutcome(False, llm_error, blocked or "")
    if blocked:
        # No log here: read_and_clear_blocked already logged the reason at
        # WARNING, and core.py logs it at ERROR when it routes the outcome.
        return TaskOutcome(False, "blocked", blocked)
    if llm_error:
        return TaskOutcome(False, llm_error)

    # Step 6: Check if any files were actually changed
    try:
        status = get_full_status(project_dir)
        all_changes = status["staged"] + status["modified"] + status["untracked"]

        if not all_changes:
            logger.info(f"No files were changed for task: {next_task}")
            logger.info(
                "This might indicate the task is already complete or the LLM didn't make changes"
            )
            logger.info("Skipping commit/push for this task")
            return TaskOutcome(False, "no_changes")
    except Exception as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
        logger.error(f"Error checking file changes: {e}")
        return TaskOutcome(False, "error")

    # Step 7: Run the implement_task checks and their fix loop
    try:
        checks = check_and_fix_mypy(
            project_dir,
            step_num,
            provider,
            env_vars,
            mcp_config,
            settings_file,
            entry="implement_task",
            check_type_hints=check_type_hints,
        )
    finally:
        # Safety net: the fix turns clear their own marker, but none may
        # survive into the commit below
        marker = read_and_clear_blocked(project_dir)
    if checks.status in ("clean", "cap") and marker:
        checks = CheckOutcome("blocked", marker)
    if checks.status == "cap":
        logger.warning(
            "Per-task checks still report findings - committing and continuing"
        )
    elif checks.status != "clean":
        return TaskOutcome(False, checks.status, checks.detail, checks_failed=True)

    # Step 8: Run formatters
    if not run_formatters(project_dir):
        return TaskOutcome(False, "error")

    # Step 9: Commit changes (same session params as the step's main LLM call)
    if not commit_changes(
        project_dir,
        provider,
        mcp_config=mcp_config,
        settings_file=settings_file,
    ):
        return TaskOutcome(False, "error")

    # Step 10: Push changes to remote
    if not push_changes(project_dir):
        return TaskOutcome(False, "error")

    # Progress gate: files changing is not enough, a task must have been ticked
    tasks_after: int | None
    try:
        tasks_after = _count_incomplete_tasks(project_dir)
    except Exception:  # pylint: disable=broad-exception-caught
        # An unreadable tracker after the round is no progress, not a crash
        tasks_after = None
    if tasks_after is None or tasks_after >= tasks_before:
        logger.warning(
            f"No progress on task: {next_task} "
            f"(incomplete tasks before={tasks_before}, after={tasks_after})"
        )
        return TaskOutcome(False, "no_progress", next_task)

    logger.info(f"Task completed successfully: {next_task}")
    return TaskOutcome(True, "completed")


def process_task_with_retry(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
    check_type_hints: bool = False,
) -> TaskOutcome:
    """Process a single task with bounded retry on zero-change results.

    Calls process_single_task up to MAX_NO_CHANGE_RETRIES times.
    Retries on "no_changes" and "no_progress". Timeouts and errors propagate
    immediately.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json; forwarded to prompt_llm.
        check_type_hints: If True, run mypy type checking after implementation

    Returns:
        TaskOutcome whose reason may be:
        - 'completed' | 'no_tasks' | 'blocked' | 'error' | 'timeout' |
          'mcp_unavailable' (from process_single_task, returned unchanged)
        - 'no_changes_after_retries' (every attempt produced zero changes)
        - 'no_progress_after_retries' (at least one attempt changed files
          without completing a task)
    """
    terminal = "no_changes_after_retries"
    last_detail = ""
    previous_reason: str | None = None
    for attempt in range(1, MAX_NO_CHANGE_RETRIES + 1):
        outcome = process_single_task(
            project_dir,
            provider,
            mcp_config=mcp_config,
            settings_file=settings_file,
            attempt=attempt,
            check_type_hints=check_type_hints,
            previous_reason=previous_reason,
        )
        if outcome.reason not in ("no_changes", "no_progress"):
            return outcome
        if outcome.reason == "no_progress":
            # Sticky: the more informative reason wins over a later no_changes
            terminal = "no_progress_after_retries"
        if outcome.detail:
            # Sticky too: a zero-change attempt carries no detail and must not
            # erase the task name a no_progress attempt supplied
            last_detail = outcome.detail
        previous_reason = outcome.reason
        logger.warning(
            f"No progress on attempt {attempt}/{MAX_NO_CHANGE_RETRIES}"
            f" ({outcome.reason})"
        )
    return TaskOutcome(False, terminal, last_detail)
