"""Task tracker preparation helpers for the implement workflow.

Populates the task tracker with implementation steps when needed and logs a
step-by-step progress summary.
"""

import logging
from collections.abc import Callable
from functools import partial
from pathlib import Path

from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS, PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.mcp_workspace_git import commit_paths, get_full_status
from mcp_coder.prompt_manager import get_prompt
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.workflow_utils.task_tracker import get_step_progress
from mcp_coder.workflow_utils.task_tracker_classify import (
    EXPECTED_FORMAT,
    TrackerState,
    classify_task_tracker,
    classify_tracker_content,
    describe_violations,
)

from .constants import (
    LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS,
    MAX_TRACKER_FEEDBACK_ROUNDS,
    PR_INFO_DIR,
)

logger = logging.getLogger(__name__)

TRACKER_FILE = f"{PR_INFO_DIR}/TASK_TRACKER.md"

# Sends a prompt (resuming the given session) and returns the new session ID
AskLLM = Callable[[str, str | None], str | None]

# Failure reason -> stage label reported by the implement workflow
PREP_STAGES = {
    "task_tracker_prep_failed": "Task tracker preparation",
    "general": "Task tracker validation",
}


class TrackerPrepError(Exception):
    """Task tracker preparation failed.

    Attributes:
        reason: Failure reason passed to the workflow's ``fail``
        stage: Stage label matching ``reason``
    """

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason
        self.stage = PREP_STAGES[reason]


def prepare_task_tracker(
    project_dir: Path,
    provider: str,
    mcp_config: str | None = None,
    settings_file: str | None = None,
) -> None:
    """Prepare task tracker by populating it if it has no implementation steps.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json; forwarded to prompt_llm.

    Raises:
        TrackerPrepError: If the tracker is missing, invalid, or could not be populated
    """
    logger.info("Checking if task tracker needs preparation...")

    # Check if pr_info/steps/ directory exists
    steps_dir = project_dir / PR_INFO_DIR / "steps"
    if not steps_dir.exists():
        message = (
            f"Directory {steps_dir} does not exist."
            " Please create implementation steps first."
        )
        logger.error(message)
        raise TrackerPrepError("task_tracker_prep_failed", message)

    pr_info_dir = str(project_dir / PR_INFO_DIR)
    state, violations = classify_task_tracker(pr_info_dir)
    if state is TrackerState.POPULATED:
        logger.info(
            "Task tracker already has implementation tasks. Skipping preparation."
        )
        return
    if state is TrackerState.MISSING:
        message = f"{TRACKER_FILE} not found"
        logger.error(message)
        raise TrackerPrepError("task_tracker_prep_failed", message)
    reason = "general" if state is TrackerState.INVALID else "task_tracker_prep_failed"
    tracker = project_dir / TRACKER_FILE
    original = tracker.read_bytes()
    ask: AskLLM = partial(
        _ask_llm,
        project_dir=project_dir,
        provider=provider,
        mcp_config=mcp_config,
        settings_file=settings_file,
    )
    done = False
    try:
        if state is TrackerState.INVALID:
            raise TrackerPrepError(reason, describe_violations(violations))

        logger.info(
            "Task tracker has no implementation tasks."
            " Generating tasks from implementation steps..."
        )
        _populate(ask, project_dir, reason)

        commit_result = commit_paths(
            "TASK_TRACKER.md with implementation steps and PR tasks updated",
            [tracker],
            project_dir,
        )
        if not commit_result["success"]:
            raise TrackerPrepError(
                reason,
                f"Error committing task tracker changes: {commit_result['error']}",
            )
        done = True
        logger.info("Task tracker updated and committed successfully")

    except TrackerPrepError as exc:
        logger.error("%s", exc)
        raise
    except Exception as e:
        message = f"Error preparing task tracker: {type(e).__name__}: {e}"
        logger.error(message)
        raise TrackerPrepError(reason, message) from e
    finally:
        # Never leave a half-edited tracker behind, even on SystemExit
        if not done:
            tracker.write_bytes(original)


def _ask_llm(
    prompt: str,
    session_id: str | None,
    *,
    project_dir: Path,
    provider: str,
    mcp_config: str | None,
    settings_file: str | None,
) -> str | None:
    """Send one task tracker prompt and store the session.

    Args:
        prompt: Prompt text
        session_id: Session to resume, None to start a new one
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        mcp_config: Optional path to MCP configuration file
        settings_file: Optional path to .claude/settings.local.json

    Returns:
        Session ID of the response, for the next call in the same session
    """
    branch_name = get_branch_name_for_logging(project_dir)
    llm_response = prompt_llm(
        prompt,
        provider=provider,
        session_id=session_id,
        # Inactivity budget (was wall-clock), kept below the CI step cap.
        timeout=LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS,
        env_vars=prepare_llm_environment(project_dir),
        project_dir=str(project_dir),
        mcp_config=mcp_config,
        settings_file=settings_file,
        branch_name=branch_name,
    )
    try:
        store_session(
            llm_response,
            prompt,
            store_path=str(project_dir / ".mcp-coder" / "implement_sessions"),
            step_name="task_tracker",
            branch_name=branch_name,
        )
    except Exception as e:
        logger.warning("Failed to store task tracker session: %s", e)
    return llm_response["session_id"]


def _other_changed_files(project_dir: Path) -> list[str]:
    """Return changed files other than the tracker and ignored build artifacts.

    Args:
        project_dir: Path to the project directory

    Returns:
        Staged, modified and untracked paths; empty if only the tracker changed
    """
    status = get_full_status(project_dir)
    all_changed = status["staged"] + status["modified"] + status["untracked"]
    ignore_set = set(DEFAULT_IGNORED_BUILD_ARTIFACTS)
    return [
        f
        for f in all_changed
        if f not in ignore_set and f.casefold() != TRACKER_FILE.casefold()
    ]


def _llm_rounds(
    ask: AskLLM,
    project_dir: Path,
    first_prompt: str,
    check: Callable[[str], list[str]],
    max_calls: int,
    reason: str,
) -> None:
    """Run LLM calls in one session until ``check`` accepts the tracker.

    After every call the changed-files guard runs first, then ``check``. On
    errors the next call gets the feedback prompt with the errors.

    Args:
        ask: Sends a prompt in a session and returns the new session ID
        project_dir: Path to the project directory
        first_prompt: Prompt for the first call
        check: Returns errors for the tracker content; empty means accepted
        max_calls: Maximum number of LLM calls
        reason: Failure reason for TrackerPrepError

    Raises:
        TrackerPrepError: If other files changed or the tracker is still
            rejected after ``max_calls`` calls
    """
    tracker = project_dir / TRACKER_FILE
    session_id: str | None = None
    prompt = first_prompt
    errors: list[str] = []
    for _ in range(max_calls):
        session_id = ask(prompt, session_id)

        others = _other_changed_files(project_dir)
        if others:
            raise TrackerPrepError(
                reason, f"LLM modified files other than {TRACKER_FILE}: {others}"
            )

        errors = check(tracker.read_text(encoding="utf-8"))
        if not errors:
            return
        logger.warning(
            "Task tracker still invalid after LLM call:\n%s", "\n".join(errors)
        )
        prompt = (
            get_prompt(str(PROMPTS_FILE_PATH), "Task Tracker Feedback Prompt")
            .replace("[violations]", describe_violations(errors))
            .replace("[expected_format]", EXPECTED_FORMAT)
        )

    raise TrackerPrepError(
        reason,
        f"Task tracker still invalid after {max_calls} LLM calls:\n"
        + describe_violations(errors),
    )


def _population_errors(content: str) -> list[str]:
    """Return why ``content`` is not a populated tracker; empty if it is."""
    state, violations = classify_tracker_content(content)
    if state is TrackerState.POPULATED:
        return []
    if state is TrackerState.EMPTY:
        return [f"{TRACKER_FILE}: no '### Step N:' sections were added"]
    return violations


def _populate(ask: AskLLM, project_dir: Path, reason: str) -> None:
    """Let the LLM populate an EMPTY tracker, with feedback rounds.

    ``_llm_rounds`` raises TrackerPrepError if the tracker could not be populated.

    Args:
        ask: Sends a prompt in a session and returns the new session ID
        project_dir: Path to the project directory
        reason: Failure reason for TrackerPrepError
    """
    _llm_rounds(
        ask,
        project_dir,
        get_prompt(str(PROMPTS_FILE_PATH), "Task Tracker Update Prompt"),
        _population_errors,
        1 + MAX_TRACKER_FEEDBACK_ROUNDS,
        reason,
    )


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
            assert isinstance(total_val, int), "total should be int"  # noqa: S101
            assert isinstance(  # noqa: S101
                completed_val, int
            ), "completed should be int"
            assert isinstance(  # noqa: S101
                incomplete_val, int
            ), "incomplete should be int"
            assert isinstance(  # noqa: S101
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
