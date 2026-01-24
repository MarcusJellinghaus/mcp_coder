"""Branch status reporting functionality.

This module provides data structures and utilities for reporting the readiness
status of branches, including CI status, rebase requirements, and task completion.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from ...workflow_utils.task_tracker import has_incomplete_work
from ..git_operations.branches import get_current_branch_name, needs_rebase
from ..git_operations.readers import extract_issue_number_from_branch
from ..github_operations.ci_results_manager import CIResultsManager
from ..github_operations.issue_manager import IssueManager

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

    def format_for_llm(self, max_lines: int = 200) -> str:
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


def truncate_ci_details(details: str, max_lines: int = 200) -> str:
    """Truncate CI details using existing logic from implement workflow.

    Extract log excerpt: first 30 + last 170 lines if log exceeds max_lines.

    Args:
        details: Full CI details content as string
        max_lines: Maximum lines before truncation (default 200)

    Returns:
        Original details if under max_lines, otherwise truncated with marker
    """
    if not details:
        return ""

    lines = details.split("\n")

    if len(lines) <= max_lines:
        return details

    # Take first 30 lines and last 170 lines
    first_lines = lines[:30]
    last_lines = lines[-170:]
    truncated_count = len(lines) - 200

    return "\n".join(
        first_lines + [f"[... truncated {truncated_count} lines ...]"] + last_lines
    )


def collect_branch_status(
    project_dir: Path, truncate_logs: bool = False, max_log_lines: int = 200
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
        logger.info(f"Collecting status for branch: {branch_name}")

        # Collect status from all sources
        ci_status, ci_details = _collect_ci_status(
            project_dir, branch_name, truncate_logs, max_log_lines
        )
        rebase_needed, rebase_reason = _collect_rebase_status(project_dir)
        tasks_complete = _collect_task_status(project_dir)
        current_label = _collect_github_label(project_dir)

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
    """Collect CI status and error details."""
    logger = logging.getLogger(__name__)

    try:
        ci_manager = CIResultsManager(project_dir)
        status_result = ci_manager.get_latest_ci_status()

        if status_result is None:
            logger.info("CI not configured")
            return CI_NOT_CONFIGURED, None

        ci_status = status_result["status"]

        if ci_status == CI_FAILED:
            # Get error details
            error_logs = ci_manager.get_error_details()
            if error_logs and truncate:
                error_logs = truncate_ci_details(error_logs, max_lines)
            return ci_status, error_logs

        logger.info(f"CI status: {ci_status}")
        return ci_status, None

    except Exception as e:
        logger.warning(f"Failed to collect CI status: {e}")
        return CI_NOT_CONFIGURED, None


def _collect_rebase_status(project_dir: Path) -> Tuple[bool, str]:
    """Collect rebase requirements."""
    logger = logging.getLogger(__name__)

    try:
        rebase_needed = needs_rebase(project_dir)

        if rebase_needed:
            reason = "Branch is behind main branch and needs rebase"
            logger.info("Rebase needed")
        else:
            reason = "Branch is up to date with main"
            logger.info("No rebase needed")

        return rebase_needed, reason

    except Exception as e:
        logger.warning(f"Failed to collect rebase status: {e}")
        return False, f"Error checking rebase status: {e}"


def _collect_task_status(project_dir: Path) -> bool:
    """Collect task tracker completion status."""
    logger = logging.getLogger(__name__)

    try:
        incomplete_work = has_incomplete_work(project_dir)
        tasks_complete = not incomplete_work

        if tasks_complete:
            logger.info("All tasks complete")
        else:
            logger.info("Incomplete tasks found")

        return tasks_complete

    except Exception as e:
        logger.warning(f"Failed to collect task status: {e}")
        return False


def _collect_github_label(project_dir: Path) -> str:
    """Collect current GitHub workflow status label.

    Uses: IssueManager.get_issue() + extract_issue_number_from_branch()
    """
    logger = logging.getLogger(__name__)

    try:
        # Get current branch and extract issue number
        branch_name = get_current_branch_name(project_dir)
        issue_number = extract_issue_number_from_branch(branch_name)

        if not issue_number:
            logger.info("No issue number found in branch name")
            return DEFAULT_LABEL

        # Get issue details from GitHub
        issue_manager = IssueManager(project_dir)
        issue = issue_manager.get_issue(issue_number)

        if not issue:
            logger.warning(f"Issue #{issue_number} not found")
            return DEFAULT_LABEL

        # Extract status label (labels starting with "status-")
        for label in issue.get("labels", []):
            label_name = label.get("name", "")
            if label_name.startswith("status-"):
                logger.info(f"Found GitHub label: {label_name}")
                return label_name

        logger.info("No status label found")
        return DEFAULT_LABEL

    except Exception as e:
        logger.warning(f"Failed to collect GitHub label: {e}")
        return DEFAULT_LABEL


def _generate_recommendations(report_data: dict) -> List[str]:
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
        recommendations.append("Fix CI failures before proceeding")
        if report_data.get("ci_details"):
            recommendations.append("Check CI error details above")
    elif ci_status == CI_PENDING:
        recommendations.append("Wait for CI to complete")

    if not tasks_complete:
        recommendations.append("Complete remaining tasks in task tracker")

    if rebase_needed and tasks_complete and ci_status != CI_FAILED:
        recommendations.append("Rebase branch with main when tasks are complete")

    if (
        ci_status in [CI_PASSED, CI_NOT_CONFIGURED]
        and tasks_complete
        and not rebase_needed
    ):
        recommendations.append("Branch is ready for next workflow step")

    if not recommendations:
        recommendations.append("Continue with current work")

    return recommendations
