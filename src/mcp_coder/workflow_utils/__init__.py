"""Workflow utilities for automated development processes.

This package provides tools for managing development workflows, including
task tracking, project status monitoring, and automation helpers.

Note: commit_operations is imported lazily to avoid circular imports.
      The utils module imports branch_status, which imports task_tracker.
      If we eagerly import commit_operations here, it triggers LLM imports
      that create a circular dependency through utils.subprocess_runner.
"""

from typing import TYPE_CHECKING, Any

from .branch_status import (
    CI_FAILED,
    CI_NOT_CONFIGURED,
    CI_PASSED,
    CI_PENDING,
    BranchStatusReport,
    collect_branch_status,
    create_empty_report,
    get_failed_jobs_summary,
    truncate_ci_details,
)
from .task_tracker import (
    TaskInfo,
    TaskTrackerError,
    TaskTrackerFileNotFoundError,
    TaskTrackerSectionNotFoundError,
    get_incomplete_tasks,
    has_incomplete_work,
    is_task_done,
)

# Type checking imports for static analysis
if TYPE_CHECKING:
    from .commit_operations import (
        generate_commit_message_with_llm,
        parse_llm_commit_response,
        strip_claude_footers,
    )

__all__ = [
    # Branch status operations
    "BranchStatusReport",
    "CI_FAILED",
    "CI_NOT_CONFIGURED",
    "CI_PASSED",
    "CI_PENDING",
    "collect_branch_status",
    "create_empty_report",
    "get_failed_jobs_summary",
    "truncate_ci_details",
    # Task tracker operations
    "get_incomplete_tasks",
    "has_incomplete_work",
    "is_task_done",
    "TaskInfo",
    # Exception types
    "TaskTrackerError",
    "TaskTrackerFileNotFoundError",
    "TaskTrackerSectionNotFoundError",
    # Commit operations (lazy loaded)
    "generate_commit_message_with_llm",
    "parse_llm_commit_response",
    "strip_claude_footers",
]


def __getattr__(name: str) -> Any:
    """Lazy import for commit_operations to avoid circular imports."""
    if name in (
        "generate_commit_message_with_llm",
        "parse_llm_commit_response",
        "strip_claude_footers",
    ):
        from . import commit_operations

        return getattr(commit_operations, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
