"""CI check and fix operations for the implement workflow.

This module handles CI pipeline monitoring, failure analysis, and automated
fix attempts. Extracted from core.py for maintainability.
"""

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from mcp_coder.checks.branch_status import get_failed_jobs_summary
from mcp_coder.constants import PROMPTS_FILE_PATH
from mcp_coder.llm.env import prepare_llm_environment
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.mcp_workspace_git import get_latest_commit_sha
from mcp_coder.mcp_workspace_github import (
    CIResultsManager,
    CIStatusData,
)
from mcp_coder.prompt_manager import get_prompt_with_substitutions
from mcp_coder.utils.git_utils import get_branch_name_for_logging

from .constants import (
    CI_MAX_FIX_ATTEMPTS,
    CI_MAX_POLL_ATTEMPTS,
    CI_NEW_RUN_MAX_POLL_ATTEMPTS,
    CI_NEW_RUN_POLL_INTERVAL_SECONDS,
    CI_POLL_INTERVAL_SECONDS,
    LLM_CI_ANALYSIS_TIMEOUT_SECONDS,
    LLM_IMPLEMENTATION_TIMEOUT_SECONDS,
    PR_INFO_DIR,
)
from .task_processing import (
    commit_changes,
    push_changes,
    run_formatters,
)

# Setup logger
logger = logging.getLogger(__name__)


@dataclass
class CIFixConfig:
    """Configuration for CI fix operations."""

    project_dir: Path
    provider: str
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
    branch_name: Optional[str] = None,
) -> Optional[str]:
    """Run CI failure analysis and return problem description.

    Args:
        config: CI fix configuration
        failed_summary: Summary of failed jobs from _get_failed_jobs_summary()
        fix_attempt: Current fix attempt number (0-indexed)
        branch_name: Optional git branch name for session logging

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
        llm_response = prompt_llm(
            analysis_prompt,
            provider=config.provider,
            timeout=LLM_CI_ANALYSIS_TIMEOUT_SECONDS,
            env_vars=config.env_vars,
            execution_dir=config.cwd,
            mcp_config=config.mcp_config,
            branch_name=branch_name,
        )
        analysis_response = llm_response["text"]
    except Exception as e:
        logger.warning(f"LLM analysis failed: {e}")
        return None

    try:
        store_session(
            llm_response,
            analysis_prompt,
            store_path=str(config.project_dir / ".mcp-coder" / "implement_sessions"),
            step_name=f"ci_analysis_{fix_attempt + 1}",
            branch_name=branch_name,
        )
    except Exception as e:
        logger.warning("Failed to store CI analysis session: %s", e)

    # Handle empty response (retry once)
    if not analysis_response or not analysis_response.strip():
        logger.warning("LLM returned empty analysis response")
        return None

    # Read problem description from temp file or use response
    temp_file = config.project_dir / PR_INFO_DIR / ".ci_problem_description.md"
    problem_description = _read_problem_description(temp_file, analysis_response)

    if not problem_description:
        logger.warning("No problem description available")
        return None

    return problem_description


def _run_ci_fix(
    config: CIFixConfig,
    problem_description: str,
    fix_attempt: int,
    branch_name: Optional[str] = None,
) -> bool:
    """Attempt to fix CI failure. Returns True if push succeeded.

    Args:
        config: CI fix configuration
        problem_description: Description of the problem from analysis phase
        fix_attempt: Current fix attempt number (0-indexed)
        branch_name: Optional git branch name for session logging

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
        llm_response = prompt_llm(
            fix_prompt,
            provider=config.provider,
            timeout=LLM_IMPLEMENTATION_TIMEOUT_SECONDS,
            env_vars=config.env_vars,
            execution_dir=config.cwd,
            mcp_config=config.mcp_config,
            branch_name=branch_name,
        )
        fix_response = llm_response["text"]
    except Exception as e:
        logger.warning(f"LLM fix failed: {e}")
        return False

    try:
        store_session(
            llm_response,
            fix_prompt,
            store_path=str(config.project_dir / ".mcp-coder" / "implement_sessions"),
            step_name=f"ci_fix_{fix_attempt + 1}",
            branch_name=branch_name,
        )
    except Exception as e:
        logger.warning("Failed to store CI fix session: %s", e)

    # Handle empty response
    if not fix_response or not fix_response.strip():
        logger.warning("LLM returned empty fix response")
        return False

    # Run formatters (non-critical, continue even if fails)
    run_formatters(config.project_dir)

    # Commit changes
    if not commit_changes(config.project_dir, config.provider):
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
    poll_start_time = time.time()
    heartbeat_iteration_interval = 8  # ~2min at 15s intervals

    for poll_attempt in range(CI_MAX_POLL_ATTEMPTS):
        try:
            ci_status = ci_manager.get_latest_ci_status(branch)
        except Exception as e:
            logger.info(
                f"CI_API_ERROR: Could not retrieve CI status - skipping CI check ({e})"
            )
            return None, True  # Graceful exit on API errors

        run_info = ci_status.get("run", {})

        elapsed = time.time() - poll_start_time
        elapsed_min, elapsed_sec = divmod(int(elapsed), 60)

        if len(run_info) == 0:
            if poll_attempt < CI_MAX_POLL_ATTEMPTS - 1:
                logger.debug(
                    f"No CI run found yet (attempt {poll_attempt + 1}/{CI_MAX_POLL_ATTEMPTS}, "
                    f"elapsed: {elapsed_min}m {elapsed_sec}s)"
                )
                time.sleep(CI_POLL_INTERVAL_SECONDS)
                continue
            logger.info("CI_NOT_CONFIGURED: No workflow runs found - skipping CI check")
            return None, True  # Graceful exit

        run_status = run_info.get("status")
        run_conclusion = run_info.get("conclusion")

        if run_status == "completed":
            run_ids = run_info.get("run_ids", [])
            run_sha = run_info.get("commit_sha") or "unknown"
            logger.debug(f"CI run {run_ids} completed (sha: {_short_sha(run_sha)})")

            if run_conclusion == "success":
                logger.info(
                    f"CI_PASSED: Pipeline succeeded (sha: {_short_sha(run_sha)})",
                )
                return ci_status, True
            logger.info(
                f"CI run completed with conclusion: {run_conclusion} (sha: {_short_sha(run_sha)})",
            )
            return ci_status, False  # Needs fixing

        logger.debug(
            f"CI run in progress (status: {run_status}, "
            f"attempt {poll_attempt + 1}/{CI_MAX_POLL_ATTEMPTS}, "
            f"elapsed: {elapsed_min}m {elapsed_sec}s)"
        )

        if (poll_attempt + 1) % heartbeat_iteration_interval == 0:
            logger.info(
                "CI polling heartbeat: waiting for CI completion "
                "(attempt %d/%d, elapsed: %dm %ds)",
                poll_attempt + 1,
                CI_MAX_POLL_ATTEMPTS,
                elapsed_min,
                elapsed_sec,
            )

        time.sleep(CI_POLL_INTERVAL_SECONDS)

    logger.info("CI_TIMEOUT: No completed run after polling - skipping CI check")
    return None, True  # Graceful exit after max polling


def _wait_for_new_ci_run(
    ci_manager: CIResultsManager, branch: str, previous_run_ids: set[int]
) -> tuple[Optional[CIStatusData], bool]:
    """Wait for a new CI run to start after pushing changes.

    Args:
        ci_manager: CIResultsManager instance
        branch: Branch name to check
        previous_run_ids: Set of run IDs to compare against

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

        new_run_ids = set(new_status.get("run", {}).get("run_ids", []))

        if new_run_ids and not new_run_ids.issubset(previous_run_ids):
            new_sha = new_status.get("run", {}).get("commit_sha") or "unknown"
            logger.info(
                f"New CI run detected: {new_run_ids} (sha: {_short_sha(new_sha)})"
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

    failed_jobs = [j for j in jobs if j.get("conclusion") == "failure"]
    failed_run_ids = list(
        dict.fromkeys(j["run_id"] for j in failed_jobs if j.get("run_id"))
    )
    logs: dict[str, str] = {}
    for rid in failed_run_ids[:3]:
        try:
            logs.update(ci_manager.get_run_logs(rid))
        except Exception as e:
            logger.warning(f"Failed to get logs for run {rid}: {e}")

    failed_summary = get_failed_jobs_summary(jobs, logs)

    if not failed_summary["job_name"]:
        logger.warning("No failed jobs found in CI status")
        return False, True  # Graceful exit (success)

    branch_name = get_branch_name_for_logging(config.project_dir)

    # Run analysis phase
    problem_description = _run_ci_analysis(
        config, failed_summary, fix_attempt, branch_name
    )

    if not problem_description:
        # Analysis failed - retry on first attempt, graceful exit otherwise
        if fix_attempt == 0:
            logger.info("Retrying analysis...")
            return True, None  # Continue to next attempt
        return False, True  # Graceful exit (success)

    # Run fix phase
    fix_succeeded = _run_ci_fix(config, problem_description, fix_attempt, branch_name)

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
        except (
            Exception
        ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow exception type
            logger.warning(f"Failed to read problem description file: {e}")

    logger.debug("Using analysis response as problem description")
    return fallback_response


def check_and_fix_ci(
    project_dir: Path,
    branch: str,
    provider: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
) -> bool:
    """Check CI status after finalisation and attempt fixes if needed.

    Args:
        project_dir: Path to the project directory
        branch: Branch name to check CI for
        provider: LLM provider (e.g., 'claude')
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

    # Store failed run IDs for comparison after fixes
    failed_run_ids = set(ci_status.get("run", {}).get("run_ids", []))

    # Phase 2: Fix loop (max 3 attempts)
    env_vars = prepare_llm_environment(project_dir)
    cwd = str(execution_dir) if execution_dir else str(project_dir)

    # Create config for CI fix operations
    config = CIFixConfig(
        project_dir=project_dir,
        provider=provider,
        env_vars=env_vars,
        cwd=cwd,
        mcp_config=mcp_config,
    )

    for fix_attempt in range(CI_MAX_FIX_ATTEMPTS):
        run_sha = ci_status.get("run", {}).get("commit_sha") or "unknown"
        logger.info(
            f"CI fix attempt {fix_attempt + 1}/{CI_MAX_FIX_ATTEMPTS} (sha: {_short_sha(run_sha)})",
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
            ci_manager, branch, failed_run_ids
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
        failed_run_ids = set(ci_status.get("run", {}).get("run_ids", []))

    # Max fix attempts exhausted
    final_sha = ci_status.get("run", {}).get("commit_sha") or "unknown"
    logger.error(
        f"CI still failing after {CI_MAX_FIX_ATTEMPTS} fix attempts (sha: {_short_sha(final_sha)})"
    )
    return False
