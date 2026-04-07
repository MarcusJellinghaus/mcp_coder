"""Branch status reporting functionality.

This module provides data structures and utilities for reporting the readiness
status of branches, including CI status, rebase requirements, and task completion.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from mcp_coder.checks.ci_log_parser import (
    _build_ci_error_details as _build_ci_error_details,
)
from mcp_coder.checks.ci_log_parser import (
    _extract_failed_step_log as _extract_failed_step_log,
)
from mcp_coder.checks.ci_log_parser import _find_log_content as _find_log_content
from mcp_coder.checks.ci_log_parser import _strip_timestamps as _strip_timestamps
from mcp_coder.checks.ci_log_parser import truncate_ci_details as truncate_ci_details
from mcp_coder.utils.git_operations import needs_rebase
from mcp_coder.utils.git_operations.branch_queries import (
    extract_issue_number_from_branch,
    get_current_branch_name,
)
from mcp_coder.utils.github_operations.ci_results_manager import CIResultsManager
from mcp_coder.utils.github_operations.issues import IssueData, IssueManager
from mcp_coder.workflow_utils.base_branch import detect_base_branch
from mcp_coder.workflow_utils.task_tracker import (
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
    TaskTrackerStatus,
    get_task_counts,
)


class CIStatus(str, Enum):
    """CI pipeline status."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_CONFIGURED = "NOT_CONFIGURED"
    PENDING = "PENDING"


# Default Values
DEFAULT_LABEL = "unknown"
EMPTY_RECOMMENDATIONS: List[str] = []


@dataclass(frozen=True)
class BranchStatusReport:
    """Branch readiness status report."""

    branch_name: str  # Current git branch name
    base_branch: str  # Detected parent/base branch
    ci_status: CIStatus  # CI pipeline status
    ci_details: Optional[str]  # Error logs or None
    rebase_needed: bool  # True if rebase required
    rebase_reason: str  # Reason for rebase status
    tasks_status: TaskTrackerStatus  # Task tracker status
    tasks_reason: str  # Reason for task status
    tasks_is_blocking: bool  # Whether task status blocks merging
    current_github_label: str  # Current workflow status label
    recommendations: List[str]  # List of suggested actions
    pr_number: Optional[int] = None  # PR number if found
    pr_url: Optional[str] = None  # PR URL if found
    pr_found: Optional[bool] = None  # None=not checked, True=found, False=not found

    def format_for_human(self) -> str:
        """Format report for human consumption.

        Returns:
            Formatted string with status icons and recommendations.
        """
        # Determine status icons (CIStatus is a str-Enum, so str keys match members)
        ci_icon_map: Dict[CIStatus, str] = {
            CIStatus.PASSED: "✅",
            CIStatus.FAILED: "❌",
            CIStatus.PENDING: "⏳",
            CIStatus.NOT_CONFIGURED: "⚙️",
        }
        ci_icon = ci_icon_map.get(self.ci_status, "❓")

        rebase_icon = "✅" if not self.rebase_needed else "⚠️"
        rebase_status_text = "UP TO DATE" if not self.rebase_needed else "BEHIND"

        tasks_icon_map = {
            TaskTrackerStatus.COMPLETE: "✅",
            TaskTrackerStatus.INCOMPLETE: "❌",
            TaskTrackerStatus.ERROR: "⚠️",
        }
        if self.tasks_status == TaskTrackerStatus.N_A:
            tasks_icon = "⚠️" if self.tasks_is_blocking else "➖"
        else:
            tasks_icon = tasks_icon_map.get(self.tasks_status, "❓")
        tasks_status_text = self.tasks_status.value

        # Build the report sections - Branch info first
        lines = [
            f"Branch: {self.branch_name}",
            f"Base Branch: {self.base_branch}",
            "",
            "Branch Status Report",
            "",
        ]

        # PR section (only when pr_found is not None)
        if self.pr_found is not None:
            if self.pr_found:
                lines.append(f"PR: \u2705 #{self.pr_number} ({self.pr_url})")
            else:
                lines.append("PR: \u274c No PR found")
            lines.append("")

        lines.append(f"CI Status: {ci_icon} {self.ci_status.value}")

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
                f"Task Tracker: {tasks_icon} {tasks_status_text} ({self.tasks_reason})",
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

        # Build status summary line
        status_summary = (
            f"Branch Status: CI={self.ci_status.value}, Rebase={rebase_status}, "
            f"Tasks={self.tasks_status.value} ({self.tasks_reason})"
        )
        if self.pr_found is True:
            status_summary += f", PR=#{self.pr_number}"
        elif self.pr_found is False:
            status_summary += ", PR=NOT_FOUND"
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
        ci_status=CIStatus.NOT_CONFIGURED,
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Unknown",
        tasks_status=TaskTrackerStatus.N_A,
        tasks_reason="Unknown",
        tasks_is_blocking=False,
        current_github_label=DEFAULT_LABEL,
        recommendations=EMPTY_RECOMMENDATIONS,
        pr_number=None,
        pr_url=None,
        pr_found=None,
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
            except (
                Exception
            ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow when GitHub/CI exception types are stable
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
        tasks_status, tasks_reason, tasks_is_blocking = _collect_task_status(
            project_dir
        )

        # Prepare data for recommendation generation
        report_data = {
            "ci_status": ci_status,
            "rebase_needed": rebase_needed,
            "tasks_status": tasks_status,
            "tasks_reason": tasks_reason,
            "tasks_is_blocking": tasks_is_blocking,
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
            tasks_status=tasks_status,
            tasks_reason=tasks_reason,
            tasks_is_blocking=tasks_is_blocking,
            current_github_label=current_label,
            recommendations=recommendations,
        )

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow when GitHub/CI exception types are stable
        logger.error(f"Error collecting branch status: {e}")
        return create_empty_report()


def _collect_ci_status(
    project_dir: Path, branch: str, max_lines: int
) -> Tuple[CIStatus, Optional[str]]:
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
            return CIStatus.NOT_CONFIGURED, None

        # Extract status from the run data
        run_data = status_result["run"]
        ci_status = run_data.get("conclusion") or run_data.get("status")

        # Map GitHub status to our constants
        if ci_status == "success":
            ci_status = CIStatus.PASSED
        elif ci_status == "failure":
            ci_status = CIStatus.FAILED
        elif ci_status in ["in_progress", "queued", "pending"]:
            ci_status = CIStatus.PENDING
        else:
            ci_status = CIStatus.NOT_CONFIGURED

        if ci_status == CIStatus.FAILED:
            # Build structured error details
            try:
                error_details = _build_ci_error_details(
                    ci_manager, status_result, max_lines
                )
                return ci_status, error_details
            except (
                Exception
            ) as log_error:  # pylint: disable=broad-exception-caught  # TODO: narrow when GitHub/CI exception types are stable
                logger.warning(f"Failed to get CI logs: {log_error}")
            return ci_status, None

        logger.info(f"CI status: {ci_status}")
        return ci_status, None

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow when GitHub/CI exception types are stable
        logger.warning(f"Failed to collect CI status: {e}")
        return CIStatus.NOT_CONFIGURED, None


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

    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow when GitHub/CI exception types are stable
        logger.warning(f"Failed to collect rebase status: {e}")
        return False, f"Error checking rebase status: {e}"


def _collect_task_status(
    project_dir: Path,
) -> Tuple[TaskTrackerStatus, str, bool]:
    """Collect task tracker completion status.

    Returns:
        Tuple of (status, reason, is_blocking).
    """
    logger = logging.getLogger(__name__)
    pr_info_path = project_dir / "pr_info"

    if not pr_info_path.exists():
        logger.info("No pr_info folder — tasks N/A")
        return TaskTrackerStatus.N_A, "No pr_info folder found", False

    steps_dir = pr_info_path / "steps"
    has_steps_files = (
        any(p.is_file() for p in steps_dir.iterdir()) if steps_dir.exists() else False
    )

    if not has_steps_files:
        logger.info("No implementation plan — tasks N/A")
        return TaskTrackerStatus.N_A, "No implementation plan found", False

    try:
        total, completed = get_task_counts(str(pr_info_path))
        if total == 0:
            logger.info("Task tracker is empty — blocking")
            return TaskTrackerStatus.N_A, "Task tracker is empty", True
        if completed == total:
            reason = f"All {total} tasks complete"
            logger.info(reason)
            return TaskTrackerStatus.COMPLETE, reason, False
        reason = f"{completed} of {total} tasks complete"
        logger.info("Incomplete tasks: %s", reason)
        return TaskTrackerStatus.INCOMPLETE, reason, True
    except TaskTrackerFileNotFoundError:
        logger.info("No TASK_TRACKER.md but steps files exist — blocking")
        return (
            TaskTrackerStatus.N_A,
            "Create task tracker \u2014 implementation plan exists but no TASK_TRACKER.md",
            True,
        )
    except TaskTrackerSectionNotFoundError:
        logger.info("No Tasks section in tracker — blocking=%s", has_steps_files)
        return (
            TaskTrackerStatus.N_A,
            "TASK_TRACKER.md has no Tasks section",
            has_steps_files,
        )
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow when GitHub/CI exception types are stable
        logger.warning("Failed to collect task status: %s", e)
        return TaskTrackerStatus.ERROR, f"Could not read task tracker: {e}", True


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
    tasks_status = report_data.get("tasks_status", TaskTrackerStatus.N_A)
    tasks_reason = report_data.get("tasks_reason", "")
    tasks_is_blocking = report_data.get("tasks_is_blocking", False)
    tasks_ok = not tasks_is_blocking

    if ci_status == CIStatus.FAILED:
        recommendations.append("Fix CI test failures")
        if report_data.get("ci_details"):
            recommendations.append("Check CI error details above")
    elif ci_status == CIStatus.PENDING:
        recommendations.append("Wait for CI to complete")
    elif ci_status == CIStatus.NOT_CONFIGURED:
        recommendations.append("Configure CI pipeline")

    if tasks_status == TaskTrackerStatus.INCOMPLETE:
        recommendations.append(f"Complete remaining tasks ({tasks_reason})")
    elif tasks_status == TaskTrackerStatus.N_A and tasks_is_blocking:
        recommendations.append(f"Fix task tracker: {tasks_reason}")
    elif tasks_status == TaskTrackerStatus.ERROR:
        recommendations.append(f"Fix task tracker error: {tasks_reason}")

    if rebase_needed and tasks_ok and ci_status != CIStatus.FAILED:
        recommendations.append("Rebase onto origin/main")

    if (
        ci_status in [CIStatus.PASSED, CIStatus.NOT_CONFIGURED]
        and tasks_ok
        and not rebase_needed
    ):
        recommendations.append("Ready to merge")

    if not recommendations:
        recommendations.append("Continue with current work")

    return recommendations
