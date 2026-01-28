"""Branch status reporting functionality.

This module provides data structures and utilities for reporting the readiness
status of branches, including CI status, rebase requirements, and task completion.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mcp_coder.utils.git_operations.branches import needs_rebase
from mcp_coder.utils.git_operations.readers import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.utils.github_operations.ci_results_manager import CIResultsManager
from mcp_coder.utils.github_operations.issue_manager import IssueManager
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

    ci_status: str  # "PASSED", "FAILED", "NOT_CONFIGURED", "PENDING"
    ci_details: Optional[str]  # Error logs or None
    rebase_needed: bool  # True if rebase required
    rebase_reason: str  # Reason for rebase status
    tasks_complete: bool  # True if all tracker tasks done
    current_github_label: str  # Current workflow status label
    recommendations: List[str]  # List of suggested actions

    def format_for_human(self) -> str:
        """Format report for human consumption."""
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

        # Build the report sections
        lines = [
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
        """Format report for LLM consumption with truncation."""
        # Convert rebase_needed to status string
        rebase_status = "BEHIND" if self.rebase_needed else "UP_TO_DATE"
        tasks_status = "COMPLETE" if self.tasks_complete else "INCOMPLETE"

        lines = [
            f"Branch Status: CI={self.ci_status}, Rebase={rebase_status}, Tasks={tasks_status}",
            f"GitHub Label: {self.current_github_label}",
            f"Recommendations: {', '.join(self.recommendations)}",
        ]

        # Add CI details if they exist, with truncation
        if self.ci_details:
            truncated_details = truncate_ci_details(self.ci_details, max_lines)
            lines.extend(
                [
                    "",
                    "CI Errors:",
                    truncated_details,
                ]
            )

        return "\n".join(lines)


def create_empty_report() -> BranchStatusReport:
    """Create empty report with default values."""
    return BranchStatusReport(
        ci_status=CI_NOT_CONFIGURED,
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Unknown",
        tasks_complete=False,
        current_github_label=DEFAULT_LABEL,
        recommendations=EMPTY_RECOMMENDATIONS,
    )


def truncate_ci_details(
    details: str, max_lines: int = 300, head_lines: int = 50
) -> str:
    """Truncate CI details with head + tail preservation.

    Extract log excerpt: first head_lines + last (max_lines - head_lines) lines
    if log exceeds max_lines.

    Args:
        details: Full CI details content as string
        max_lines: Maximum lines before truncation (default 300)
        head_lines: Number of lines to keep from the start (default 50)

    Returns:
        Original details if under max_lines, otherwise truncated with marker
    """
    if not details:
        return ""

    lines = details.split("\n")

    if len(lines) <= max_lines:
        return details

    # Take first head_lines and last (max_lines - head_lines) lines
    tail_lines = max_lines - head_lines
    first_lines = lines[:head_lines]
    last_lines = lines[-tail_lines:]
    truncated_count = len(lines) - max_lines

    return "\n".join(
        first_lines + [f"[... truncated {truncated_count} lines ...]"] + last_lines
    )


def collect_branch_status(
    project_dir: Path, truncate_logs: bool = False, max_log_lines: int = 300
) -> BranchStatusReport:
    """Collect comprehensive branch status from all sources.

    Args:
        project_dir: Path to git repository
        truncate_logs: Whether to truncate CI logs for LLM consumption
        max_log_lines: Maximum log lines when truncating

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

        # Collect status from all sources
        ci_status, ci_details = _collect_ci_status(
            project_dir, branch_name, truncate_logs, max_log_lines
        )
        rebase_needed, rebase_reason = _collect_rebase_status(project_dir)
        tasks_complete = _collect_task_status(project_dir)
        current_label = _collect_github_label(project_dir, branch_name)

        # Prepare data for recommendation generation
        report_data = {
            "ci_status": ci_status,
            "rebase_needed": rebase_needed,
            "tasks_complete": tasks_complete,
            "ci_details": ci_details,
        }

        recommendations = _generate_recommendations(report_data)

        return BranchStatusReport(
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
    project_dir: Path, branch: str, truncate: bool, max_lines: int
) -> Tuple[str, Optional[str]]:
    """Collect CI status and error details.

    When CI has failed, produces a structured output:
    1. Summary of all failed jobs and their failed steps
    2. Detailed logs for the first failed job only (up to max_lines)
    3. List of other failed jobs (names only, no logs)
    """
    logger = logging.getLogger(__name__)

    try:
        ci_manager = CIResultsManager(project_dir)
        status_result = ci_manager.get_latest_ci_status(branch)

        # Check if CI data is empty (no runs found)
        if not status_result["run"]:
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
                    ci_manager, status_result, truncate, max_lines
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
    truncate: bool,
    max_lines: int,
) -> Optional[str]:
    """Build structured CI error details with summary and filtered logs.

    Args:
        ci_manager: CIResultsManager instance
        status_result: Result from get_latest_ci_status
        truncate: Whether to truncate logs
        max_lines: Maximum lines for log output

    Returns:
        Structured error details string or None if no logs available
    """
    logger = logging.getLogger(__name__)
    run_data = status_result["run"]
    jobs_data = status_result.get("jobs", [])

    # Identify failed jobs and their failed steps
    failed_jobs = _get_failed_jobs_info(jobs_data)

    if not failed_jobs:
        logger.info("No failed jobs found in CI results")
        return None

    # Build output sections
    output_lines = []

    # Section 1: Summary of all failed jobs
    job_names = [job["name"] for job in failed_jobs]
    output_lines.append(f"## CI Failure Summary")
    output_lines.append(f"Failed jobs ({len(failed_jobs)}): {', '.join(job_names)}")
    output_lines.append("")

    # Section 2: Detailed logs for first failed job only
    first_job = failed_jobs[0]
    run_id = run_data.get("id")

    if run_id:
        job_logs = _get_filtered_job_logs(
            ci_manager, run_id, first_job, truncate, max_lines
        )
        if job_logs:
            output_lines.append(f"## Job: {first_job['name']}")
            output_lines.append(f"Failed step: {first_job['failed_step']}")
            output_lines.append("")
            output_lines.append(job_logs)
        else:
            output_lines.append(f"## Job: {first_job['name']}")
            output_lines.append(f"Failed step: {first_job['failed_step']}")
            output_lines.append("(logs not available)")

    # Section 3: List other failed jobs (no logs)
    if len(failed_jobs) > 1:
        output_lines.append("")
        output_lines.append("## Other failed jobs (details not shown to save space)")
        for job in failed_jobs[1:]:
            output_lines.append(
                f"- {job['name']}: step \"{job['failed_step']}\" failed"
            )

    return "\n".join(output_lines)


def _get_failed_jobs_info(jobs_data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extract failed job names and their failed step names.

    Args:
        jobs_data: List of job data from get_latest_ci_status

    Returns:
        List of dicts with 'name' and 'failed_step' for each failed job
    """
    failed_jobs = []

    for job in jobs_data:
        if job.get("conclusion") == "failure":
            job_name = job.get("name", "unknown")
            failed_step = "unknown"

            # Find the failed step
            for step in job.get("steps", []):
                if step.get("conclusion") == "failure":
                    failed_step = step.get("name", "unknown")
                    break

            failed_jobs.append({"name": job_name, "failed_step": failed_step})

    return failed_jobs


def _get_filtered_job_logs(
    ci_manager: CIResultsManager,
    run_id: int,
    job_info: Dict[str, str],
    truncate: bool,
    max_lines: int,
) -> Optional[str]:
    """Get logs for a specific failed job, filtered to relevant content.

    Args:
        ci_manager: CIResultsManager instance
        run_id: Workflow run ID
        job_info: Dict with 'name' and 'failed_step'
        truncate: Whether to truncate logs
        max_lines: Maximum lines for output

    Returns:
        Filtered and optionally truncated log content
    """
    logger = logging.getLogger(__name__)

    try:
        all_logs = ci_manager.get_run_logs(run_id)

        if not all_logs:
            return None

        job_name = job_info["name"]
        failed_step = job_info["failed_step"]

        # Log files are typically named like:
        # "{job_name}/{step_number}_{step_name}.txt"
        # e.g., "import-linter/7_Run import-linter.txt"

        # Find logs matching this job
        job_logs = []
        for log_path, log_content in all_logs.items():
            # Check if log path starts with job name
            if log_path.startswith(f"{job_name}/"):
                # Prioritize logs containing the failed step name
                if failed_step.lower() in log_path.lower():
                    # This is the failed step - use it directly
                    if truncate:
                        return truncate_ci_details(log_content, max_lines)
                    return log_content
                job_logs.append((log_path, log_content))

        # If we didn't find the exact failed step, combine all job logs
        if job_logs:
            combined = "\n\n".join(
                f"--- {path} ---\n{content}" for path, content in job_logs
            )
            if truncate:
                return truncate_ci_details(combined, max_lines)
            return combined

        # Fallback: return all logs truncated (shouldn't normally happen)
        logger.warning(f"Could not find logs for job '{job_name}', using all logs")
        combined = "\n\n".join(all_logs.values())
        if truncate:
            return truncate_ci_details(combined, max_lines)
        return combined

    except Exception as e:
        logger.warning(f"Error filtering job logs: {e}")
        return None


def _collect_rebase_status(project_dir: Path) -> Tuple[bool, str]:
    """Collect rebase requirements."""
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
    """Collect task tracker completion status."""
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


def _collect_github_label(project_dir: Path, branch_name: Optional[str] = None) -> str:
    """Collect current GitHub workflow status label.

    Uses: IssueManager.get_issue() + extract_issue_number_from_branch()

    Args:
        project_dir: Path to the git repository
        branch_name: Optional branch name. If not provided, will be fetched from git.
    """
    logger = logging.getLogger(__name__)

    # Use provided branch name or get it from git
    if branch_name is None:
        branch_name = get_current_branch_name(project_dir)
        if not branch_name:
            logger.info("No current branch name found")
            return DEFAULT_LABEL
    issue_number = extract_issue_number_from_branch(branch_name)

    if not issue_number:
        logger.info("No issue number found in branch name")
        return DEFAULT_LABEL

    # Get issue details from GitHub
    try:
        issue_manager = IssueManager(project_dir)
        issue = issue_manager.get_issue(issue_number)
    except Exception as e:
        logger.warning(f"Failed to collect GitHub label: {e}")
        return DEFAULT_LABEL

    # Extract status label (labels starting with "status-")
    # IssueData.labels is List[str], so labels are already strings
    labels = issue.get("labels", [])
    for label in labels:
        if isinstance(label, str) and label.startswith("status-"):
            logger.info(f"Found GitHub label: {label}")
            return label

    logger.info("No status label found")
    return DEFAULT_LABEL


def _generate_recommendations(report_data: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations based on status."""
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
