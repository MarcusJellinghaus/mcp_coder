"""Branch status reporting functionality.

This module provides data structures and utilities for reporting the readiness
status of branches, including CI status, rebase requirements, and task completion.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from mcp_coder.checks.ci_log_parser import (
    _extract_failed_step_log as _extract_failed_step_log,
)
from mcp_coder.checks.ci_log_parser import _find_log_content as _find_log_content
from mcp_coder.checks.ci_log_parser import _strip_timestamps as _strip_timestamps
from mcp_coder.checks.ci_log_parser import truncate_ci_details as truncate_ci_details
from mcp_coder.utils.git_operations import needs_rebase
from mcp_coder.utils.git_operations.readers import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.utils.github_operations.ci_results_manager import CIResultsManager
from mcp_coder.utils.github_operations.issues import IssueData, IssueManager
from mcp_coder.workflow_utils.base_branch import detect_base_branch
from mcp_coder.workflow_utils.task_tracker import has_incomplete_work

# Status Constants
CI_PASSED = "PASSED"
CI_FAILED = "FAILED"
CI_NOT_CONFIGURED = "NOT_CONFIGURED"
CI_PENDING = "PENDING"

# Default Values
DEFAULT_LABEL = "unknown"
EMPTY_RECOMMENDATIONS: List[str] = []


@dataclass(frozen=True)
class BranchStatusReport:
    """Branch readiness status report."""

    branch_name: str  # Current git branch name
    base_branch: str  # Detected parent/base branch
    ci_status: str  # "PASSED", "FAILED", "NOT_CONFIGURED", "PENDING"
    ci_details: Optional[str]  # Error logs or None
    rebase_needed: bool  # True if rebase required
    rebase_reason: str  # Reason for rebase status
    tasks_complete: bool  # True if all tracker tasks done
    current_github_label: str  # Current workflow status label
    recommendations: List[str]  # List of suggested actions

    def format_for_human(self) -> str:
        """Format report for human consumption.

        Returns:
            Formatted string with status icons and recommendations.
        """
        # Determine status icons
        ci_icon = {
            CI_PASSED: "✅",
            CI_FAILED: "❌",
            CI_PENDING: "⏳",
            CI_NOT_CONFIGURED: "⚙️",
        }.get(self.ci_status, "❓")

        rebase_icon = "✅" if not self.rebase_needed else "⚠️"
        rebase_status_text = "UP TO DATE" if not self.rebase_needed else "BEHIND"

        tasks_icon = "✅" if self.tasks_complete else "❌"
        tasks_status_text = "COMPLETE" if self.tasks_complete else "INCOMPLETE"

        # Build the report sections - Branch info first
        lines = [
            f"Branch: {self.branch_name}",
            f"Base Branch: {self.base_branch}",
            "",
            "Branch Status Report",
            "",
            f"CI Status: {ci_icon} {self.ci_status}",
        ]

        # Add CI details if they exist
        if self.ci_details:
            lines.extend(
                [
                    "",
                    "CI Error Details:",
                    self.ci_details,
                ]
            )

        lines.extend(
            [
                "",
                f"Rebase Status: {rebase_icon} {rebase_status_text}",
                f"- {self.rebase_reason}",
                "",
                f"Task Tracker: {tasks_icon} {tasks_status_text}",
                "",
                f"GitHub Status: {self.current_github_label}",
                "",
                "Recommendations:",
            ]
        )

        # Add recommendations
        for recommendation in self.recommendations:
            lines.append(f"- {recommendation}")

        return "\n".join(lines)

    def format_for_llm(self, max_lines: int = 300) -> str:
        """Format report for LLM consumption with truncation.

        Args:
            max_lines: Maximum number of lines for CI error details.

        Returns:
            Compact formatted string optimized for LLM context windows.
        """
        # Convert rebase_needed to status string
        rebase_status = "BEHIND" if self.rebase_needed else "UP_TO_DATE"
        tasks_status = "COMPLETE" if self.tasks_complete else "INCOMPLETE"

        # Build status summary line
        status_summary = (
            f"Branch Status: CI={self.ci_status}, Rebase={rebase_status}, "
            f"Tasks={tasks_status}"
        )
        recommendations_text = ", ".join(self.recommendations)

        # Branch info on first line
        lines = [
            f"Branch: {self.branch_name} | Base: {self.base_branch}",
            status_summary,
            f"GitHub Label: {self.current_github_label}",
            f"Recommendations: {recommendations_text}",
        ]

        # Add CI details if they exist, with truncation and footer
        if self.ci_details:
            truncated_details = truncate_ci_details(self.ci_details, max_lines)
            lines.extend(
                [
                    "",
                    "CI Errors:",
                    truncated_details,
                    "",
                    "---",
                    f"Summary: {status_summary} | Action: {recommendations_text}",
                ]
            )

        return "\n".join(lines)


def create_empty_report() -> BranchStatusReport:
    """Create empty report with default values.

    Returns:
        BranchStatusReport with unknown/default values for all fields.
    """
    return BranchStatusReport(
        branch_name="unknown",
        base_branch="unknown",
        ci_status=CI_NOT_CONFIGURED,
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Unknown",
        tasks_complete=False,
        current_github_label=DEFAULT_LABEL,
        recommendations=EMPTY_RECOMMENDATIONS,
    )


def get_failed_jobs_summary(
    jobs: Sequence[Mapping[str, Any]], logs: Mapping[str, str]
) -> Dict[str, Any]:
    """Get summary of failed jobs from CI status.

    This is the shared function used by both check-branch-status and implement
    commands to extract failed job information and log excerpts.

    Args:
        jobs: List of job dicts with 'name', 'conclusion', and 'steps' keys
        logs: Dict mapping log filenames to content

    Returns:
        Dict with keys: job_name, step_name, step_number, log_excerpt, other_failed_jobs
    """
    # Filter jobs where conclusion == "failure"
    failed_jobs = [job for job in jobs if job.get("conclusion") == "failure"]

    # Return empty result if no failed jobs
    if not failed_jobs:
        return {
            "job_name": "",
            "step_name": "",
            "step_number": 0,
            "log_excerpt": "",
            "other_failed_jobs": [],
        }

    # Get first failed job
    first_failed = failed_jobs[0]
    job_name = first_failed.get("name", "")

    # Find first step with conclusion == "failure"
    step_name = ""
    step_number = 0
    steps = first_failed.get("steps", [])
    for step in steps:
        if step.get("conclusion") == "failure":
            step_name = step.get("name", "")
            step_number = step.get("number", 0)
            break

    log_content = _find_log_content(logs, job_name, step_number, step_name)

    # Strip timestamps first so ##[group] markers are parseable
    if log_content:
        log_content = _strip_timestamps(log_content)

    # Extract just the failed step's section from the full job log
    if log_content:
        extracted = _extract_failed_step_log(log_content, step_name)
        if extracted:
            log_content = extracted

    log_excerpt = truncate_ci_details(log_content)

    # Other failed jobs
    other_failed_jobs = [job.get("name", "") for job in failed_jobs[1:]]

    return {
        "job_name": job_name,
        "step_name": step_name,
        "step_number": step_number,
        "log_excerpt": log_excerpt,
        "other_failed_jobs": other_failed_jobs,
    }


def collect_branch_status(
    project_dir: Path, max_log_lines: int = 300
) -> BranchStatusReport:
    """Collect comprehensive branch status from all sources.

    Args:
        project_dir: Path to git repository
        max_log_lines: Maximum log lines for CI error details

    Returns:
        BranchStatusReport with all collected information
    """
    logger = logging.getLogger(__name__)

    try:
        # Get current branch name
        branch_name = get_current_branch_name(project_dir)
        if not branch_name:
            logger.error("Could not determine current branch name")
            return create_empty_report()

        logger.info(f"Collecting status for branch: {branch_name}")

        # Fetch issue data once for sharing between detect_base_branch and _collect_github_label
        issue_data: Optional[IssueData] = None
        issue_number = extract_issue_number_from_branch(branch_name)
        if issue_number:
            try:
                issue_manager = IssueManager(project_dir)
                issue_data = issue_manager.get_issue(issue_number)
            except Exception as e:
                logger.debug(f"Could not fetch issue data: {e}")

        # Use shared issue_data and branch_name
        base_branch = detect_base_branch(project_dir, branch_name, issue_data)
        if base_branch is None:
            base_branch = "unknown"
        current_label = _collect_github_label(project_dir, issue_data)

        # Collect status from all sources
        ci_status, ci_details = _collect_ci_status(
            project_dir, branch_name, max_log_lines
        )
        rebase_needed, rebase_reason = _collect_rebase_status(project_dir)
        tasks_complete = _collect_task_status(project_dir)

        # Prepare data for recommendation generation
        report_data = {
            "ci_status": ci_status,
            "rebase_needed": rebase_needed,
            "tasks_complete": tasks_complete,
            "ci_details": ci_details,
        }

        recommendations = _generate_recommendations(report_data)

        return BranchStatusReport(
            branch_name=branch_name,
            base_branch=base_branch,
            ci_status=ci_status,
            ci_details=ci_details,
            rebase_needed=rebase_needed,
            rebase_reason=rebase_reason,
            tasks_complete=tasks_complete,
            current_github_label=current_label,
            recommendations=recommendations,
        )

    except Exception as e:
        logger.error(f"Error collecting branch status: {e}")
        return create_empty_report()


def _collect_ci_status(
    project_dir: Path, branch: str, max_lines: int
) -> Tuple[str, Optional[str]]:
    """Collect CI status and error details.

    When CI has failed, produces a structured output:
    1. Summary of all failed jobs and their failed steps
    2. Detailed logs for the first failed job only (up to max_lines)
    3. List of other failed jobs (names only, no logs)

    Returns:
        Tuple of (ci_status_string, error_details_or_none).
    """
    logger = logging.getLogger(__name__)

    try:
        ci_manager = CIResultsManager(project_dir)
        status_result = ci_manager.get_latest_ci_status(branch)

        # Check if CI data is empty (no runs found)
        if len(status_result["run"]) == 0:
            logger.info("CI not configured")
            return CI_NOT_CONFIGURED, None

        # Extract status from the run data
        run_data = status_result["run"]
        ci_status = run_data.get("conclusion") or run_data.get("status")

        # Map GitHub status to our constants
        if ci_status == "success":
            ci_status = CI_PASSED
        elif ci_status == "failure":
            ci_status = CI_FAILED
        elif ci_status in ["in_progress", "queued", "pending"]:
            ci_status = CI_PENDING
        else:
            ci_status = CI_NOT_CONFIGURED

        if ci_status == CI_FAILED:
            # Build structured error details
            try:
                error_details = _build_ci_error_details(
                    ci_manager, status_result, max_lines
                )
                return ci_status, error_details
            except Exception as log_error:
                logger.warning(f"Failed to get CI logs: {log_error}")
            return ci_status, None

        logger.info(f"CI status: {ci_status}")
        return ci_status, None

    except Exception as e:
        logger.warning(f"Failed to collect CI status: {e}")
        return CI_NOT_CONFIGURED, None


def _build_ci_error_details(
    ci_manager: CIResultsManager,
    status_result: Any,
    max_lines: int,
) -> Optional[str]:
    """Build structured CI error details with logs for multiple failed jobs.

    Shows logs for as many failed jobs as fit within the line limit.

    Args:
        ci_manager: CIResultsManager instance
        status_result: Result from get_latest_ci_status
        max_lines: Maximum total lines for output (default 300)

    Returns:
        Structured error details string or None if no logs available
    """
    logger = logging.getLogger(__name__)
    run_data = status_result["run"]
    jobs_data = status_result.get("jobs", [])
    # Extract GitHub Actions run URL for user navigation
    run_url = run_data.get("url", "")

    # Get all failed jobs
    failed_jobs = [job for job in jobs_data if job.get("conclusion") == "failure"]

    # Collect distinct run_ids from failed jobs, preserving order
    failed_run_ids: List[int] = list(
        dict.fromkeys(j["run_id"] for j in failed_jobs if j.get("run_id"))
    )

    # Fetch logs for up to 3 failed run_ids
    logs: Dict[str, str] = {}
    fetched_run_ids = failed_run_ids[:3]
    for rid in fetched_run_ids:
        try:
            run_logs = ci_manager.get_run_logs(rid)
            logs.update(run_logs)
        except Exception as e:
            logger.warning(f"Failed to get logs for run {rid}: {e}")

    if not failed_jobs:
        logger.info("No failed jobs found in CI results")
        return None

    # Build output sections
    output_lines: List[str] = []
    lines_used = 0
    jobs_shown: List[str] = []
    jobs_truncated: List[str] = []

    # Prepend jobs_fetch_warning if present (Decision 7)
    jobs_fetch_warning = run_data.get("jobs_fetch_warning")
    if jobs_fetch_warning:
        output_lines.append(f"WARNING: {jobs_fetch_warning}")
        output_lines.append("")
        lines_used += 2

    # Section 1: Summary header (will be updated at end)
    summary_placeholder_idx = len(output_lines)
    output_lines.append("")  # Placeholder for summary
    output_lines.append("")
    lines_used += 2

    # Add GitHub Actions run URL if available
    if run_url:
        output_lines.append(f"GitHub Actions: {run_url}")
        output_lines.append("")
        lines_used += 2

    # Section 2: Show logs for each failed job until we hit the limit
    for job in failed_jobs:
        job_name = job.get("name", "unknown")

        # Find first failed step
        step_name = "unknown"
        step_number = 0
        for step in job.get("steps", []):
            if step.get("conclusion") == "failure":
                step_name = step.get("name", "unknown")
                step_number = step.get("number", 0)
                break

        log_content = _find_log_content(logs, job_name, step_number, step_name)

        # Strip timestamps first so ##[group] markers are parseable
        if log_content:
            log_content = _strip_timestamps(log_content)

        # Extract just the failed step's section from the full job log
        if log_content:
            extracted = _extract_failed_step_log(log_content, step_name)
            if extracted:
                log_content = extracted

        # Calculate how many lines this job's section would take
        # Header lines: "## Job:", optional "View job:" (if URL available), "Failed step:", blank line
        job_id = job.get("id")
        has_job_url = bool(run_url and job_id)
        job_header_lines = 4 if has_job_url else 3

        if log_content:
            log_lines = log_content.split("\n")
        elif has_job_url:
            log_lines = [
                "(logs not available locally)",
                f"View on GitHub: {run_url}/job/{job_id}",
            ]
        else:
            log_lines = ["(logs not available)"]

        # Calculate remaining budget for this job
        remaining_budget = (
            max_lines - lines_used - job_header_lines - 5
        )  # Reserve 5 for footer

        if remaining_budget <= 10:
            # Not enough space for meaningful logs, add to truncated list
            jobs_truncated.append(job_name)
            continue

        # Truncate log if needed (only applies to real log content, not fallback messages)
        if log_content and len(log_lines) > remaining_budget:
            # Use head + tail truncation
            head_count = min(10, remaining_budget // 6)
            tail_count = remaining_budget - head_count - 1  # -1 for truncation message
            truncated_log = (
                log_lines[:head_count]
                + [
                    f"[... truncated {len(log_lines) - head_count - tail_count} lines ...]"
                ]
                + log_lines[-tail_count:]
            )
            log_content = "\n".join(truncated_log)
            log_lines = truncated_log

        # Add job section
        output_lines.append(f"## Job: {job_name}")
        if has_job_url:
            output_lines.append(f"View job: {run_url}/job/{job_id}")
        output_lines.append(f"Failed step: {step_name}")
        output_lines.append("")
        if log_content:
            output_lines.append(log_content)
        else:
            output_lines.append("\n".join(log_lines))
        output_lines.append("")

        lines_used += job_header_lines + len(log_lines) + 1
        jobs_shown.append(job_name)

    # Section 3: List jobs that didn't fit
    if jobs_truncated:
        output_lines.append("## Other failed jobs (logs truncated to save space)")
        for job_name in jobs_truncated:
            # Find step name for this job
            for job in failed_jobs:
                if job.get("name") == job_name:
                    step_name = "unknown"
                    for step in job.get("steps", []):
                        if step.get("conclusion") == "failure":
                            step_name = step.get("name", "unknown")
                            break
                    output_lines.append(f'- {job_name}: step "{step_name}" failed')
                    break

    # Update summary placeholder
    all_failed = jobs_shown + jobs_truncated
    output_lines[summary_placeholder_idx] = (
        f"## CI Failure Summary\n"
        f"Failed jobs ({len(all_failed)}): {', '.join(all_failed)}"
    )

    return "\n".join(output_lines)


def _collect_rebase_status(project_dir: Path) -> Tuple[bool, str]:
    """Collect rebase requirements.

    Returns:
        Tuple of (rebase_needed, reason_string).
    """
    logger = logging.getLogger(__name__)

    try:
        rebase_needed, reason = needs_rebase(project_dir)

        if rebase_needed:
            logger.info(f"Rebase needed: {reason}")
        else:
            logger.info(f"No rebase needed: {reason}")

        return rebase_needed, reason

    except Exception as e:
        logger.warning(f"Failed to collect rebase status: {e}")
        return False, f"Error checking rebase status: {e}"


def _collect_task_status(project_dir: Path) -> bool:
    """Collect task tracker completion status.

    Returns:
        True if all tasks are complete, False otherwise.
    """
    logger = logging.getLogger(__name__)

    try:
        # Use the project directory's pr_info folder for task tracking
        pr_info_path = project_dir / "pr_info"
        if pr_info_path.exists():
            incomplete_work = has_incomplete_work(str(pr_info_path))
        else:
            # If no pr_info directory, assume no tasks are tracked
            incomplete_work = False

        tasks_complete = not incomplete_work

        if tasks_complete:
            logger.info("All tasks complete")
        else:
            logger.info("Incomplete tasks found")

        return tasks_complete

    except Exception as e:
        logger.warning(f"Failed to collect task status: {e}")
        return False


def _collect_github_label(
    _project_dir: Path,
    issue_data: Optional[IssueData] = None,
) -> str:
    """Collect current GitHub workflow status label.

    Args:
        _project_dir: Path to the git repository
        issue_data: Optional pre-fetched issue data (contains labels directly)

    Returns:
        Status label string, or DEFAULT_LABEL if not found.

    Note:
        If issue_data is None, returns DEFAULT_LABEL.
        The caller is responsible for fetching issue_data.
    """
    logger = logging.getLogger(__name__)

    # Use provided issue_data if available
    if issue_data is None:
        logger.info("No issue data provided, returning default label")
        return DEFAULT_LABEL

    # Extract status label from issue_data
    labels = issue_data.get("labels", [])
    for label in labels:
        if isinstance(label, str) and label.startswith("status-"):
            logger.info(f"Found GitHub label: {label}")
            return label

    logger.info("No status label found")
    return DEFAULT_LABEL


def _generate_recommendations(report_data: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on status.

    Returns:
        List of recommendation strings prioritized by importance.
    """
    recommendations = []

    # Priority order for recommendations:
    # 1. Fix CI failures (if CI failed)
    # 2. Complete incomplete tasks (if tasks not done)
    # 3. Rebase when ready (if rebase needed)
    # 4. Ready for next workflow step (if all checks pass)

    ci_status = report_data.get("ci_status")
    rebase_needed = report_data.get("rebase_needed", False)
    tasks_complete = report_data.get("tasks_complete", False)

    if ci_status == CI_FAILED:
        recommendations.append("Fix CI test failures")
        if report_data.get("ci_details"):
            recommendations.append("Check CI error details above")
    elif ci_status == CI_PENDING:
        recommendations.append("Wait for CI to complete")
    elif ci_status == CI_NOT_CONFIGURED:
        recommendations.append("Configure CI pipeline")

    if not tasks_complete:
        recommendations.append("Complete remaining tasks")

    if rebase_needed and tasks_complete and ci_status != CI_FAILED:
        recommendations.append("Rebase onto origin/main")

    if (
        ci_status in [CI_PASSED, CI_NOT_CONFIGURED]
        and tasks_complete
        and not rebase_needed
    ):
        recommendations.append("Ready to merge")

    if not recommendations:
        recommendations.append("Continue with current work")

    return recommendations
