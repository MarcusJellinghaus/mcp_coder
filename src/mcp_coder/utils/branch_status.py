"""Branch status reporting functionality.

This module provides data structures and utilities for reporting the readiness
status of branches, including CI status, rebase requirements, and task completion.
"""

from dataclasses import dataclass
from typing import List, Optional

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
