"""Core workflow orchestration for implement workflow.

This module contains the main workflow orchestration functions that coordinate
prerequisites checking, task tracker preparation, and task processing loops.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from mcp_coder.constants import DEFAULT_IGNORED_BUILD_ARTIFACTS, PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import ask_llm
from mcp_coder.prompt_manager import get_prompt, get_prompt_with_substitutions
from mcp_coder.utils import commit_all_changes, get_full_status
from mcp_coder.utils.git_operations import (
    get_current_branch_name,
    get_default_branch_name,
    rebase_onto_branch,
)
from mcp_coder.utils.git_operations.commits import get_latest_commit_sha
from mcp_coder.utils.git_utils import get_branch_name_for_logging
from mcp_coder.utils.github_operations.ci_results_manager import (
    CIResultsManager,
    CIStatusData,
    JobData,
)
from mcp_coder.utils.github_operations.pr_manager import PullRequestManager
from mcp_coder.workflow_utils.branch_status import (
    get_failed_jobs_summary,
    truncate_ci_details,
)
from mcp_coder.workflow_utils.commit_operations import generate_commit_message_with_llm
from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerFileNotFoundError,
    get_step_progress,
    has_incomplete_work,
)

from .constants import (
    CI_MAX_FIX_ATTEMPTS,
    CI_MAX_POLL_ATTEMPTS,
    CI_NEW_RUN_MAX_POLL_ATTEMPTS,
    CI_NEW_RUN_POLL_INTERVAL_SECONDS,
    CI_POLL_INTERVAL_SECONDS,
    COMMIT_MESSAGE_FILE,
    LLM_CI_ANALYSIS_TIMEOUT_SECONDS,
    LLM_FINALISATION_TIMEOUT_SECONDS,
    LLM_IMPLEMENTATION_TIMEOUT_SECONDS,
    LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS,
    PR_INFO_DIR,
    RUN_MYPY_AFTER_EACH_TASK,
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
    process_single_task,
    push_changes,
    run_formatters,
    save_conversation,
)

# Finalisation prompt for completing remaining tasks
FINALISATION_PROMPT = f"""
Please check {PR_INFO_DIR}/TASK_TRACKER.md for unchecked tasks (- [ ]).

For each unchecked task:
1. If it's a "commit message" task and changes are already committed → mark [x] and skip
2. Otherwise: verify if done, complete it if not, then mark [x]

If step files exist in {PR_INFO_DIR}/steps/, use them for context.
If not, analyse based on task names and codebase.

If you cannot complete a task, DO NOT mark the box as done.
Instead, briefly explain the issue.

Run quality checks (pylint, pytest, mypy) if any code changes were made.
Write commit message to {PR_INFO_DIR}/{COMMIT_MESSAGE_FILE}.
"""

# Setup logger
logger = logging.getLogger(__name__)


@dataclass
class CIFixConfig:
    """Configuration for CI fix operations."""

    project_dir: Path
    provider: str
    method: str
    env_vars: dict[str, str]
    cwd: str
    mcp_config: Optional[str]


def _short_sha(sha: str) -> str:
    """Return first 7 characters of SHA for display.

    Args:
        sha: Full SHA string or "unknown"

    Returns:
        First 7 characters of SHA, or "unknown" if input is empty/unknown
    """
    if not sha or sha == "unknown":
        return "unknown"
    return sha[:7]


def _run_ci_analysis(
    config: CIFixConfig,
    failed_summary: dict[str, Any],
    fix_attempt: int,
) -> Optional[str]:
    """Run CI failure analysis and return problem description.

    Args:
        config: CI fix configuration
        failed_summary: Summary of failed jobs from _get_failed_jobs_summary()
        fix_attempt: Current fix attempt number (0-indexed)

    Returns:
        Problem description string, or None on failure
    """
    other_jobs = failed_summary["other_failed_jobs"]
    other_jobs_str = ", ".join(other_jobs) if other_jobs else "none"

    # Load analysis prompt with substitutions
    try:
        analysis_prompt = get_prompt_with_substitutions(
            str(PROMPTS_FILE_PATH),
            "CI Failure Analysis Prompt",
            {
                "job_name": failed_summary["job_name"],
                "step_name": failed_summary["step_name"],
                "other_failed_jobs": other_jobs_str,
                "log_excerpt": failed_summary["log_excerpt"],
            },
        )
    except Exception as e:
        logger.error(f"Failed to load CI analysis prompt: {e}")
        return None

    # Call LLM with analysis prompt
    try:
        logger.info("Calling LLM for CI failure analysis...")
        branch_name = get_branch_name_for_logging(config.project_dir)
        analysis_response = ask_llm(
            analysis_prompt,
            provider=config.provider,
            method=config.method,
            timeout=LLM_CI_ANALYSIS_TIMEOUT_SECONDS,
            env_vars=config.env_vars,
            project_dir=str(config.project_dir),
            execution_dir=config.cwd,
            mcp_config=config.mcp_config,
            branch_name=branch_name,
        )

        # Handle empty response (retry once)
        if not analysis_response or not analysis_response.strip():
            logger.warning("LLM returned empty analysis response")
            return None

    except Exception as e:
        logger.warning(f"LLM analysis failed: {e}")
        return None

    # Read problem description from temp file or use response
    temp_file = config.project_dir / PR_INFO_DIR / ".ci_problem_description.md"
    problem_description = _read_problem_description(temp_file, analysis_response)

    if not problem_description:
        logger.warning("No problem description available")
        return None

    # Save conversation for debugging
    save_conversation(
        config.project_dir,
        f"# CI Failure Analysis\n\n{problem_description}",
        0,
        f"ci_analysis_{fix_attempt + 1}",
    )

    return problem_description


def _run_ci_fix(
    config: CIFixConfig,
    problem_description: str,
    fix_attempt: int,
) -> bool:
    """Attempt to fix CI failure. Returns True if push succeeded.

    Args:
        config: CI fix configuration
        problem_description: Description of the problem from analysis phase
        fix_attempt: Current fix attempt number (0-indexed)

    Returns:
        True if fix was successfully committed and pushed, False otherwise
    """
    # Load fix prompt with problem_description
    try:
        fix_prompt = get_prompt_with_substitutions(
            str(PROMPTS_FILE_PATH),
            "CI Fix Prompt",
            {"problem_description": problem_description},
        )
    except Exception as e:
        logger.error(f"Failed to load CI fix prompt: {e}")
        return False

    # Call LLM with fix prompt
    try:
        logger.info("Calling LLM to fix CI issues...")
        branch_name = get_branch_name_for_logging(config.project_dir)
        fix_response = ask_llm(
            fix_prompt,
            provider=config.provider,
            method=config.method,
            timeout=LLM_IMPLEMENTATION_TIMEOUT_SECONDS,
            env_vars=config.env_vars,
            project_dir=str(config.project_dir),
            execution_dir=config.cwd,
            mcp_config=config.mcp_config,
            branch_name=branch_name,
        )

        # Handle empty response
        if not fix_response or not fix_response.strip():
            logger.warning("LLM returned empty fix response")
            return False

    except Exception as e:
        logger.warning(f"LLM fix failed: {e}")
        return False

    # Save conversation for debugging
    save_conversation(
        config.project_dir,
        f"# CI Fix Attempt {fix_attempt + 1}\n\n{fix_response}",
        0,
        f"ci_fix_{fix_attempt + 1}",
    )

    # Run formatters (non-critical, continue even if fails)
    run_formatters(config.project_dir)

    # Commit changes
    if not commit_changes(config.project_dir, config.provider, config.method):
        logger.warning("Failed to commit CI fix changes")
        return False

    # Push changes
    if not push_changes(config.project_dir):
        logger.error("Git push failed during CI fix - failing fast")
        return False

    return True


def _poll_for_ci_completion(
    ci_manager: CIResultsManager, branch: str
) -> tuple[Optional[CIStatusData], bool]:
    """Poll for CI run completion.

    Args:
        ci_manager: CIResultsManager instance
        branch: Branch name to check

    Returns:
        Tuple of (ci_status dict or None, success bool).
        success=True means CI passed, success=False means CI failed or needs fixing.
        If ci_status is None and success is True, it means graceful exit (no CI found).
    """
    for poll_attempt in range(CI_MAX_POLL_ATTEMPTS):
        try:
            ci_status = ci_manager.get_latest_ci_status(branch)
        except Exception as e:
            logger.info(
                f"CI_API_ERROR: Could not retrieve CI status - skipping CI check ({e})"
            )
            return None, True  # Graceful exit on API errors

        run_info = ci_status.get("run", {})

        if not run_info:
            if poll_attempt < CI_MAX_POLL_ATTEMPTS - 1:
                logger.debug(
                    f"No CI run found yet (attempt {poll_attempt + 1}/{CI_MAX_POLL_ATTEMPTS})"
                )
                time.sleep(CI_POLL_INTERVAL_SECONDS)
                continue
            logger.info("CI_NOT_CONFIGURED: No workflow runs found - skipping CI check")
            return None, True  # Graceful exit

        run_status = run_info.get("status")
        run_conclusion = run_info.get("conclusion")

        if run_status == "completed":
            run_id = run_info.get("id")
            run_sha = run_info.get("commit_sha") or "unknown"
            logger.debug(f"CI run {run_id} completed (sha: {_short_sha(run_sha)})")

            if run_conclusion == "success":
                logger.info(
                    f"CI_PASSED: Pipeline succeeded (sha: {_short_sha(run_sha)})"
                )
                return ci_status, True
            logger.info(
                f"CI run completed with conclusion: {run_conclusion} (sha: {_short_sha(run_sha)})"
            )
            return ci_status, False  # Needs fixing

        logger.debug(
            f"CI run in progress (status: {run_status}, "
            f"attempt {poll_attempt + 1}/{CI_MAX_POLL_ATTEMPTS})"
        )
        time.sleep(CI_POLL_INTERVAL_SECONDS)

    logger.info("CI_TIMEOUT: No completed run after polling - skipping CI check")
    return None, True  # Graceful exit after max polling


def _wait_for_new_ci_run(
    ci_manager: CIResultsManager, branch: str, previous_run_id: Any
) -> tuple[Optional[CIStatusData], bool]:
    """Wait for a new CI run to start after pushing changes.

    Args:
        ci_manager: CIResultsManager instance
        branch: Branch name to check
        previous_run_id: Run ID to compare against

    Returns:
        Tuple of (new ci_status or None, new_run_detected bool)
    """
    logger.info("Waiting for new CI run to start...")

    for attempt in range(CI_NEW_RUN_MAX_POLL_ATTEMPTS):
        time.sleep(CI_NEW_RUN_POLL_INTERVAL_SECONDS)

        try:
            new_status = ci_manager.get_latest_ci_status(branch)
        except Exception as e:
            logger.warning(f"API error checking for new CI run: {e}")
            continue

        new_run_id = new_status.get("run", {}).get("id")

        if new_run_id and new_run_id != previous_run_id:
            new_sha = new_status.get("run", {}).get("commit_sha") or "unknown"
            logger.info(
                f"New CI run detected: {new_run_id} (sha: {_short_sha(new_sha)})"
            )
            return new_status, True

        logger.debug(
            f"Waiting for new CI run (attempt {attempt + 1}/{CI_NEW_RUN_MAX_POLL_ATTEMPTS})"
        )

    logger.warning("No new CI run detected after 30s")
    return None, False


def _run_ci_analysis_and_fix(
    config: CIFixConfig,
    ci_status: CIStatusData,
    ci_manager: CIResultsManager,
    fix_attempt: int,
) -> tuple[bool, Optional[bool]]:
    """Run CI failure analysis and attempt a fix.

    Args:
        config: CI fix configuration
        ci_status: Current CI status dict
        ci_manager: CIResultsManager instance
        fix_attempt: Current fix attempt number (0-indexed)

    Returns:
        Tuple of (should_continue, return_value):
        - should_continue: True if should continue to next fix attempt
        - return_value: None to continue loop, True for success (exit 0), False for failure (exit 1)
    """
    jobs = ci_status.get("jobs", [])
    run_id = ci_status.get("run", {}).get("id")

    try:
        logs = ci_manager.get_run_logs(run_id) if run_id else {}
    except Exception as e:
        logger.warning(f"Failed to get CI logs: {e}")
        logs = {}

    failed_summary = get_failed_jobs_summary(jobs, logs)

    if not failed_summary["job_name"]:
        logger.warning("No failed jobs found in CI status")
        return False, True  # Graceful exit (success)

    # Run analysis phase
    problem_description = _run_ci_analysis(config, failed_summary, fix_attempt)

    if not problem_description:
        # Analysis failed - retry on first attempt, graceful exit otherwise
        if fix_attempt == 0:
            logger.info("Retrying analysis...")
            return True, None  # Continue to next attempt
        return False, True  # Graceful exit (success)

    # Run fix phase
    fix_succeeded = _run_ci_fix(config, problem_description, fix_attempt)

    if not fix_succeeded:
        return True, None  # Continue to next attempt

    return False, None  # Successfully pushed, proceed to wait for new run


def _read_problem_description(temp_file: Path, fallback_response: str) -> str:
    """Read problem description from temp file or use fallback.

    Args:
        temp_file: Path to the temp problem description file
        fallback_response: Fallback text if file doesn't exist or is empty

    Returns:
        Problem description text
    """
    if temp_file.exists():
        try:
            content = temp_file.read_text(encoding="utf-8").strip()
            temp_file.unlink()  # Delete after reading
            if content:  # Only use file content if not empty
                logger.debug(f"Problem description:\n{content}")
                return content
            logger.debug("Temp file was empty, using fallback")
        except Exception as e:
            logger.warning(f"Failed to read problem description file: {e}")

    logger.debug("Using analysis response as problem description")
    return fallback_response


def check_and_fix_ci(
    project_dir: Path,
    branch: str,
    provider: str,
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Check CI status after finalisation and attempt fixes if needed.

    Args:
        project_dir: Path to the project directory
        branch: Branch name to check CI for
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'api')
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess

    Returns:
        True if CI passes or on API errors (exit 0 scenarios)
        False if max fix attempts exhausted (exit 1 scenario)
    """
    logger.info("Starting CI check and fix process...")

    # Log latest local commit SHA for debugging
    try:
        local_sha = get_latest_commit_sha(project_dir)
        if local_sha:
            logger.debug(f"Latest local commit SHA: {_short_sha(local_sha)}")
    except Exception as e:
        logger.debug(f"Could not get local commit SHA: {e}")

    # Initialize CI Results Manager
    try:
        ci_manager = CIResultsManager(project_dir)
    except Exception as e:
        logger.info(
            f"CI_API_ERROR: Could not retrieve CI status - skipping CI check ({e})"
        )
        return True  # Graceful exit on API errors

    # Phase 1: Poll for CI completion
    logger.info("Polling for CI completion...")
    ci_status, ci_passed = _poll_for_ci_completion(ci_manager, branch)

    if ci_status is None or ci_passed:
        return True  # Graceful exit or CI passed

    # Store failed run ID for comparison after fixes
    failed_run_id = ci_status.get("run", {}).get("id")

    # Phase 2: Fix loop (max 3 attempts)
    env_vars = prepare_llm_environment(project_dir)
    cwd = str(execution_dir) if execution_dir else str(project_dir)

    # Create config for CI fix operations
    config = CIFixConfig(
        project_dir=project_dir,
        provider=provider,
        method=method,
        env_vars=env_vars,
        cwd=cwd,
        mcp_config=mcp_config,
    )

    for fix_attempt in range(CI_MAX_FIX_ATTEMPTS):
        run_sha = ci_status.get("run", {}).get("commit_sha") or "unknown"
        logger.info(
            f"CI fix attempt {fix_attempt + 1}/{CI_MAX_FIX_ATTEMPTS} (sha: {_short_sha(run_sha)})"
        )

        should_continue, return_value = _run_ci_analysis_and_fix(
            config,
            ci_status,
            ci_manager,
            fix_attempt,
        )

        if return_value is not None:
            return return_value
        if should_continue:
            continue

        # Successfully pushed, wait for new CI run
        new_status, new_run_detected = _wait_for_new_ci_run(
            ci_manager, branch, failed_run_id
        )

        if not new_run_detected:
            return True  # Graceful exit per Decision 17

        # Wait for new CI run to complete
        logger.info("Waiting for new CI run to complete...")
        new_status, ci_passed = _poll_for_ci_completion(ci_manager, branch)

        if new_status is None or ci_passed:
            return True  # CI passed or graceful exit

        # CI still failing, update for next attempt
        ci_status = new_status
        failed_run_id = ci_status.get("run", {}).get("id")

    # Max fix attempts exhausted
    final_sha = ci_status.get("run", {}).get("commit_sha") or "unknown"
    logger.error(
        f"CI still failing after {CI_MAX_FIX_ATTEMPTS} fix attempts (sha: {_short_sha(final_sha)})"
    )
    return False


def _get_rebase_target_branch(project_dir: Path) -> Optional[str]:
    """Determine the target branch for rebasing the current feature branch.

    Detection priority:
    1. GitHub PR base branch (if open PR exists for current branch)
    2. Default branch (main/master) via get_default_branch_name()

    Args:
        project_dir: Path to the project directory

    Returns:
        Branch name to rebase onto, or None if detection fails

    Note:
        All errors are handled gracefully - returns None on any failure.
        Debug logging indicates which detection method was used.
    """
    # 1. Get current branch name
    current_branch = get_current_branch_name(project_dir)
    if not current_branch:
        return None

    # 2. Try GitHub PR lookup
    try:
        pr_manager = PullRequestManager(project_dir)
        open_prs = pr_manager.list_pull_requests(state="open")
        for pr in open_prs:
            if pr["head_branch"] == current_branch:
                logger.debug(
                    f"Parent branch detected from GitHub PR: {pr['base_branch']}"
                )
                return pr["base_branch"]
    except Exception as e:
        logger.debug(f"GitHub PR lookup failed (will use default branch): {e}")

    # 3. Fall back to default branch
    default = get_default_branch_name(project_dir)
    if default:
        logger.debug(f"Parent branch detected from default branch: {default}")
    return default


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
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Prepare task tracker by populating it if it has no implementation steps.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
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
        response = ask_llm(
            prompt_template,
            provider=provider,
            method=method,
            timeout=LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS,
            env_vars=env_vars,
            project_dir=str(project_dir),
            execution_dir=str(execution_dir) if execution_dir else None,
            mcp_config=mcp_config,
            branch_name=branch_name,
        )

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
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Run implementation finalisation to verify and complete remaining tasks.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
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

    response = ask_llm(
        FINALISATION_PROMPT,
        provider=provider,
        method=method,
        timeout=LLM_FINALISATION_TIMEOUT_SECONDS,
        env_vars=env_vars,
        project_dir=str(project_dir),
        execution_dir=str(execution_dir) if execution_dir else None,
        mcp_config=mcp_config,
        branch_name=branch_name,
    )

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
            method=method,
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
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
    update_labels: bool = False,
) -> int:
    """Main workflow orchestration function - processes all implementation tasks in sequence.

    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess
        update_labels: If True, update GitHub issue labels on success

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

    # Step 1.5: Attempt rebase onto parent branch (never blocks workflow)
    _attempt_rebase_and_push(project_dir)

    # Step 2: Prepare task tracker if needed
    if not prepare_task_tracker(
        project_dir, provider, method, mcp_config, execution_dir
    ):
        return 1

    # Step 3: Show initial progress summary
    log_progress_summary(project_dir)

    # Step 4: Process all incomplete tasks in a loop
    completed_tasks = 0
    error_occurred = False

    while True:
        success, reason = process_single_task(
            project_dir, provider, method, mcp_config, execution_dir
        )

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

    # Step 5: Run final mypy check if not running after each task
    if not RUN_MYPY_AFTER_EACH_TASK and completed_tasks > 0 and not error_occurred:
        logger.info("Running final mypy check after all tasks...")
        env_vars = prepare_llm_environment(project_dir)

        # Use step number 0 for final mypy check conversation
        if not check_and_fix_mypy(
            project_dir,
            0,
            provider,
            method,
            env_vars,
            mcp_config,
            execution_dir=execution_dir,
        ):
            logger.warning(
                "Final mypy check found unresolved issues - continuing anyway"
            )

        # Format code after mypy fixes
        if not run_formatters(project_dir):
            logger.error("Formatting failed after final mypy check")
            return 1

        # Commit mypy fixes if any changes were made
        status = get_full_status(project_dir)
        all_changes = status["staged"] + status["modified"] + status["untracked"]

        if all_changes:
            logger.info("Committing final mypy fixes...")
            if not commit_changes(project_dir, provider, method):
                logger.error("Failed to commit final mypy fixes")
                return 1

            if not push_changes(project_dir):
                logger.error("Failed to push final mypy fixes")
                return 1
        else:
            logger.info("No changes from final mypy check - skipping commit")

    # Step 5.5: Run finalisation to complete any remaining tasks
    if not error_occurred:
        finalisation_success = run_finalisation(
            project_dir,
            provider,
            method,
            mcp_config,
            execution_dir,
        )
        if not finalisation_success:
            logger.warning("Finalisation encountered issues - continuing anyway")

    # Step 5.6: Check CI pipeline and auto-fix if needed
    if not error_occurred:
        logger.info("Checking CI pipeline status...")
        current_branch = get_current_branch_name(project_dir)
        if current_branch:
            ci_success = check_and_fix_ci(
                project_dir=project_dir,
                branch=current_branch,
                provider=provider,
                method=method,
                mcp_config=mcp_config,
                execution_dir=execution_dir,
            )
            if not ci_success:
                logger.error("CI check failed after maximum fix attempts")
                return 1
        else:
            logger.error("Could not determine current branch - skipping CI check")

    # Step 6: Show final progress summary with appropriate messaging
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

    # Step 7: Update GitHub issue label if requested
    if update_labels and completed_tasks > 0 and not error_occurred:
        logger.info("Updating GitHub issue label...")
        try:
            from mcp_coder.utils.github_operations.issue_manager import IssueManager

            issue_manager = IssueManager(project_dir)
            success = issue_manager.update_workflow_label(
                from_label_id="implementing",
                to_label_id="code_review",
            )

            if success:
                logger.info("✓ Issue label updated: implementing → code-review")
            else:
                logger.warning("✗ Failed to update issue label (non-blocking)")

        except Exception as e:
            logger.error(f"Error updating issue label (non-blocking): {e}")

    return 0
