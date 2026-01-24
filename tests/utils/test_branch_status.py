"""Tests for branch status reporting functionality.

This module tests the BranchStatusReport dataclass and related utilities
for reporting the readiness status of branches.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional
from unittest.mock import MagicMock, patch

import pytest


def test_branch_status_report_creation() -> None:
    """Test BranchStatusReport dataclass creation with all fields."""
    from src.mcp_coder.utils.branch_status import BranchStatusReport

    report = BranchStatusReport(
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Up to date with origin/main",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=["Ready to merge"],
    )

    assert report.ci_status == "PASSED"
    assert report.ci_details is None
    assert report.rebase_needed is False
    assert report.rebase_reason == "Up to date with origin/main"
    assert report.tasks_complete is True
    assert report.current_github_label == "status-03:implementing"
    assert report.recommendations == ["Ready to merge"]


def test_branch_status_report_failed_ci() -> None:
    """Test BranchStatusReport with failed CI status."""
    from src.mcp_coder.utils.branch_status import BranchStatusReport

    ci_error = "FAILED tests/test_example.py::test_function - AssertionError"

    report = BranchStatusReport(
        ci_status="FAILED",
        ci_details=ci_error,
        rebase_needed=True,
        rebase_reason="3 commits behind origin/main",
        tasks_complete=False,
        current_github_label="status-02:planning",
        recommendations=["Fix CI test failures", "Rebase onto origin/main"],
    )

    assert report.ci_status == "FAILED"
    assert report.ci_details == ci_error
    assert report.rebase_needed is True
    assert report.rebase_reason == "3 commits behind origin/main"
    assert report.tasks_complete is False
    assert report.current_github_label == "status-02:planning"
    assert len(report.recommendations) == 2


def test_format_for_human_passed_status() -> None:
    """Test format_for_human with all systems green."""
    from src.mcp_coder.utils.branch_status import BranchStatusReport

    report = BranchStatusReport(
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Up to date with origin/main",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=["Ready to merge"],
    )

    formatted = report.format_for_human()

    # Check for expected sections
    assert "Branch Status Report" in formatted
    assert "CI Status: ✅ PASSED" in formatted
    assert "Rebase Status: ✅ UP TO DATE" in formatted
    assert "Task Tracker: ✅ COMPLETE" in formatted
    assert "GitHub Status: status-03:implementing" in formatted
    assert "Recommendations:" in formatted
    assert "- Ready to merge" in formatted


def test_format_for_human_failed_status() -> None:
    """Test format_for_human with failures and issues."""
    from src.mcp_coder.utils.branch_status import BranchStatusReport

    ci_error = "FAILED tests/test_example.py::test_function - AssertionError\nFAILED tests/test_other.py::test_other - KeyError"

    report = BranchStatusReport(
        ci_status="FAILED",
        ci_details=ci_error,
        rebase_needed=True,
        rebase_reason="3 commits behind origin/main",
        tasks_complete=False,
        current_github_label="status-02:planning",
        recommendations=[
            "Fix CI test failures",
            "Rebase onto origin/main",
            "Complete remaining tasks",
        ],
    )

    formatted = report.format_for_human()

    # Check for expected sections and status indicators
    assert "CI Status: ❌ FAILED" in formatted
    assert "Rebase Status: ⚠️ BEHIND" in formatted
    assert "Task Tracker: ❌ INCOMPLETE" in formatted
    assert "CI Error Details:" in formatted
    assert "FAILED tests/test_example.py" in formatted
    assert "- Fix CI test failures" in formatted
    assert "- Rebase onto origin/main" in formatted
    assert "- Complete remaining tasks" in formatted


def test_format_for_human_pending_status() -> None:
    """Test format_for_human with pending CI status."""
    from src.mcp_coder.utils.branch_status import BranchStatusReport

    report = BranchStatusReport(
        ci_status="PENDING",
        ci_details="CI pipeline running...",
        rebase_needed=False,
        rebase_reason="Up to date with origin/main",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=["Wait for CI to complete"],
    )

    formatted = report.format_for_human()

    assert "CI Status: ⏳ PENDING" in formatted
    assert "CI pipeline running..." in formatted


def test_format_for_human_not_configured() -> None:
    """Test format_for_human with CI not configured."""
    from src.mcp_coder.utils.branch_status import BranchStatusReport

    report = BranchStatusReport(
        ci_status="NOT_CONFIGURED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Up to date with origin/main",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=["Configure CI pipeline"],
    )

    formatted = report.format_for_human()

    assert "CI Status: ⚙️ NOT_CONFIGURED" in formatted


def test_format_for_llm_basic() -> None:
    """Test format_for_llm basic functionality."""
    from src.mcp_coder.utils.branch_status import BranchStatusReport

    report = BranchStatusReport(
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Up to date",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=["Ready to merge"],
    )

    formatted = report.format_for_llm()

    assert "Branch Status: CI=PASSED, Rebase=UP_TO_DATE, Tasks=COMPLETE" in formatted
    assert "GitHub Label: status-03:implementing" in formatted
    assert "Recommendations: Ready to merge" in formatted


def test_format_for_llm_truncation() -> None:
    """Test format_for_llm truncates CI details when they exceed max_lines."""
    from src.mcp_coder.utils.branch_status import BranchStatusReport

    # Create CI details with 250 lines (exceeds default 200)
    ci_lines = [f"Error line {i+1}" for i in range(250)]
    long_ci_details = "\n".join(ci_lines)

    report = BranchStatusReport(
        ci_status="FAILED",
        ci_details=long_ci_details,
        rebase_needed=True,
        rebase_reason="Behind",
        tasks_complete=False,
        current_github_label="status-02:planning",
        recommendations=["Fix errors"],
    )

    formatted = report.format_for_llm(max_lines=200)

    # Should contain truncation message
    assert "[... truncated" in formatted
    # Should have first 30 and last 170 lines logic applied
    assert "Error line 1" in formatted  # First line
    assert "Error line 30" in formatted  # 30th line
    assert "Error line 81" in formatted  # First line of last 170
    assert "Error line 250" in formatted  # Last line


def test_format_for_llm_no_truncation() -> None:
    """Test format_for_llm doesn't truncate short CI details."""
    from src.mcp_coder.utils.branch_status import BranchStatusReport

    short_ci_details = "Short error message"

    report = BranchStatusReport(
        ci_status="FAILED",
        ci_details=short_ci_details,
        rebase_needed=False,
        rebase_reason="Up to date",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=["Fix error"],
    )

    formatted = report.format_for_llm()

    # Should not contain truncation message
    assert "[... truncated" not in formatted
    # Should contain full message
    assert "Short error message" in formatted


def test_create_empty_report() -> None:
    """Test create_empty_report function."""
    from src.mcp_coder.utils.branch_status import create_empty_report

    report = create_empty_report()

    assert report.ci_status == "NOT_CONFIGURED"
    assert report.ci_details is None
    assert report.rebase_needed is False
    assert report.rebase_reason == "Unknown"
    assert report.tasks_complete is False
    assert report.current_github_label == "unknown"
    assert report.recommendations == []


def test_truncate_ci_details_no_truncation() -> None:
    """Test truncate_ci_details with short content."""
    from src.mcp_coder.utils.branch_status import truncate_ci_details

    short_content = "Short error\nAnother line\nThird line"
    result = truncate_ci_details(short_content, max_lines=200)

    assert result == short_content
    assert "[... truncated" not in result


def test_truncate_ci_details_with_truncation() -> None:
    """Test truncate_ci_details with long content requiring truncation."""
    from src.mcp_coder.utils.branch_status import truncate_ci_details

    # Create content with 250 lines
    lines = [f"Line {i+1}" for i in range(250)]
    long_content = "\n".join(lines)

    result = truncate_ci_details(long_content, max_lines=200)

    # Should contain truncation marker
    assert "[... truncated 50 lines ...]" in result
    # Should have first 30 lines
    assert "Line 1" in result
    assert "Line 30" in result
    # Should have last 170 lines (starting from line 81)
    assert "Line 81" in result
    assert "Line 250" in result
    # Should not have middle lines
    assert "Line 50" not in result


def test_truncate_ci_details_empty() -> None:
    """Test truncate_ci_details with empty content."""
    from src.mcp_coder.utils.branch_status import truncate_ci_details

    assert truncate_ci_details("") == ""


def test_truncate_ci_details_custom_max_lines() -> None:
    """Test truncate_ci_details with custom max_lines parameter."""
    from src.mcp_coder.utils.branch_status import truncate_ci_details

    # Create content with 100 lines
    lines = [f"Line {i+1}" for i in range(100)]
    content = "\n".join(lines)

    # Set max_lines to 50
    result = truncate_ci_details(content, max_lines=50)

    # Should be truncated
    assert "[... truncated 50 lines ...]" in result
    # Should have appropriate first and last lines based on truncation logic
    assert "Line 1" in result
    assert "Line 100" in result


def test_branch_status_constants() -> None:
    """Test that required constants are defined."""
    from src.mcp_coder.utils.branch_status import (
        CI_FAILED,
        CI_NOT_CONFIGURED,
        CI_PASSED,
        CI_PENDING,
        DEFAULT_LABEL,
        EMPTY_RECOMMENDATIONS,
    )

    assert CI_PASSED == "PASSED"
    assert CI_FAILED == "FAILED"
    assert CI_NOT_CONFIGURED == "NOT_CONFIGURED"
    assert CI_PENDING == "PENDING"
    assert DEFAULT_LABEL == "unknown"
    assert EMPTY_RECOMMENDATIONS == []


def test_dataclass_immutability() -> None:
    """Test that BranchStatusReport is immutable (frozen)."""
    from src.mcp_coder.utils.branch_status import BranchStatusReport

    report = BranchStatusReport(
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Up to date",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=[],
    )

    # Should raise exception when trying to modify frozen dataclass
    with pytest.raises(Exception):  # FrozenInstanceError
        report.ci_status = "FAILED"


# Tests for collect_branch_status() function


def test_collect_branch_status_all_good():
    """Test collect_branch_status with all systems green."""
    from src.mcp_coder.utils.branch_status import collect_branch_status

    project_dir = Path("/test/repo")

    with (
        patch(
            "src.mcp_coder.utils.branch_status.get_current_branch_name"
        ) as mock_branch,
        patch("src.mcp_coder.utils.branch_status._collect_ci_status") as mock_ci,
        patch(
            "src.mcp_coder.utils.branch_status._collect_rebase_status"
        ) as mock_rebase,
        patch("src.mcp_coder.utils.branch_status._collect_task_status") as mock_tasks,
        patch("src.mcp_coder.utils.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks for all green status
        mock_branch.return_value = "main"
        mock_ci.return_value = ("PASSED", None)
        mock_rebase.return_value = (False, "Up to date with origin/main")
        mock_tasks.return_value = True
        mock_label.return_value = "status-04:reviewing"

        result = collect_branch_status(project_dir)

        # Verify result
        assert result.ci_status == "PASSED"
        assert result.ci_details is None
        assert result.rebase_needed is False
        assert result.rebase_reason == "Up to date with origin/main"
        assert result.tasks_complete is True
        assert result.current_github_label == "status-04:reviewing"
        assert "Ready to merge" in result.recommendations

        # Verify function calls
        mock_branch.assert_called_once_with(project_dir)
        mock_ci.assert_called_once_with(project_dir, "main", False, 200)
        mock_rebase.assert_called_once_with(project_dir)
        mock_tasks.assert_called_once_with(project_dir)
        mock_label.assert_called_once_with(project_dir)


def test_collect_branch_status_ci_failed():
    """Test collect_branch_status with CI failures."""
    from src.mcp_coder.utils.branch_status import collect_branch_status

    project_dir = Path("/test/repo")
    ci_error = "FAILED tests/test_example.py::test_function - AssertionError"

    with (
        patch("src.mcp_coder.utils.branch_status._collect_ci_status") as mock_ci,
        patch(
            "src.mcp_coder.utils.branch_status._collect_rebase_status"
        ) as mock_rebase,
        patch("src.mcp_coder.utils.branch_status._collect_task_status") as mock_tasks,
        patch("src.mcp_coder.utils.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks for CI failed
        mock_ci.return_value = ("FAILED", ci_error)
        mock_rebase.return_value = (False, "Up to date with origin/main")
        mock_tasks.return_value = True
        mock_label.return_value = "status-03:implementing"

        result = collect_branch_status(project_dir)

        # Verify result
        assert result.ci_status == "FAILED"
        assert result.ci_details == ci_error
        assert result.rebase_needed is False
        assert result.tasks_complete is True
        assert "Fix CI test failures" in result.recommendations


def test_collect_branch_status_rebase_needed():
    """Test collect_branch_status with rebase required."""
    from src.mcp_coder.utils.branch_status import collect_branch_status

    project_dir = Path("/test/repo")

    with (
        patch("src.mcp_coder.utils.branch_status._collect_ci_status") as mock_ci,
        patch(
            "src.mcp_coder.utils.branch_status._collect_rebase_status"
        ) as mock_rebase,
        patch("src.mcp_coder.utils.branch_status._collect_task_status") as mock_tasks,
        patch("src.mcp_coder.utils.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks for rebase needed
        mock_ci.return_value = ("PASSED", None)
        mock_rebase.return_value = (True, "5 commits behind origin/main")
        mock_tasks.return_value = True
        mock_label.return_value = "status-03:implementing"

        result = collect_branch_status(project_dir)

        # Verify result
        assert result.ci_status == "PASSED"
        assert result.rebase_needed is True
        assert result.rebase_reason == "5 commits behind origin/main"
        assert "Rebase onto origin/main" in result.recommendations


def test_collect_branch_status_tasks_incomplete():
    """Test collect_branch_status with incomplete tasks."""
    from src.mcp_coder.utils.branch_status import collect_branch_status

    project_dir = Path("/test/repo")

    with (
        patch("src.mcp_coder.utils.branch_status._collect_ci_status") as mock_ci,
        patch(
            "src.mcp_coder.utils.branch_status._collect_rebase_status"
        ) as mock_rebase,
        patch("src.mcp_coder.utils.branch_status._collect_task_status") as mock_tasks,
        patch("src.mcp_coder.utils.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks for incomplete tasks
        mock_ci.return_value = ("PASSED", None)
        mock_rebase.return_value = (False, "Up to date with origin/main")
        mock_tasks.return_value = False
        mock_label.return_value = "status-03:implementing"

        result = collect_branch_status(project_dir)

        # Verify result
        assert result.ci_status == "PASSED"
        assert result.rebase_needed is False
        assert result.tasks_complete is False
        assert "Complete remaining tasks" in result.recommendations


def test_collect_branch_status_with_truncation():
    """Test collect_branch_status with CI log truncation enabled."""
    from src.mcp_coder.utils.branch_status import collect_branch_status

    project_dir = Path("/test/repo")
    long_ci_error = "\n".join([f"Error line {i}" for i in range(300)])

    with (
        patch(
            "src.mcp_coder.utils.branch_status.get_current_branch_name"
        ) as mock_branch,
        patch("src.mcp_coder.utils.branch_status._collect_ci_status") as mock_ci,
        patch(
            "src.mcp_coder.utils.branch_status._collect_rebase_status"
        ) as mock_rebase,
        patch("src.mcp_coder.utils.branch_status._collect_task_status") as mock_tasks,
        patch("src.mcp_coder.utils.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks
        mock_branch.return_value = "main"
        mock_ci.return_value = ("FAILED", long_ci_error)
        mock_rebase.return_value = (False, "Up to date")
        mock_tasks.return_value = True
        mock_label.return_value = "status-03:implementing"

        result = collect_branch_status(
            project_dir, truncate_logs=True, max_log_lines=50
        )

        # Verify truncation was passed correctly
        mock_branch.assert_called_once_with(project_dir)
        mock_ci.assert_called_once_with(project_dir, "main", True, 50)
        assert (
            result.ci_details == long_ci_error
        )  # Function should return what mock returns


def test_collect_branch_status_all_failed():
    """Test collect_branch_status with all systems failing."""
    from src.mcp_coder.utils.branch_status import collect_branch_status

    project_dir = Path("/test/repo")
    ci_error = "Multiple test failures"

    with (
        patch("src.mcp_coder.utils.branch_status._collect_ci_status") as mock_ci,
        patch(
            "src.mcp_coder.utils.branch_status._collect_rebase_status"
        ) as mock_rebase,
        patch("src.mcp_coder.utils.branch_status._collect_task_status") as mock_tasks,
        patch("src.mcp_coder.utils.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks for everything failing
        mock_ci.return_value = ("FAILED", ci_error)
        mock_rebase.return_value = (True, "3 commits behind origin/main")
        mock_tasks.return_value = False
        mock_label.return_value = "status-02:planning"

        result = collect_branch_status(project_dir)

        # Verify result
        assert result.ci_status == "FAILED"
        assert result.ci_details == ci_error
        assert result.rebase_needed is True
        assert result.rebase_reason == "3 commits behind origin/main"
        assert result.tasks_complete is False
        assert result.current_github_label == "status-02:planning"

        # Should have multiple recommendations in priority order
        recommendations = result.recommendations
        assert len(recommendations) >= 3
        assert "Fix CI test failures" in recommendations[0]  # CI first priority
        assert any("Complete remaining tasks" in r for r in recommendations)
        assert any("Rebase onto origin/main" in r for r in recommendations)


# Tests for helper functions


def test_collect_ci_status_with_truncation():
    """Test _collect_ci_status with log truncation."""
    from src.mcp_coder.utils.branch_status import _collect_ci_status

    project_dir = Path("/test/repo")
    long_logs = "\n".join([f"Log line {i}" for i in range(300)])

    with patch(
        "src.mcp_coder.utils.github_operations.ci_results_manager.CIResultsManager"
    ) as mock_ci_manager:
        mock_instance = MagicMock()
        mock_ci_manager.return_value = mock_instance
        mock_instance.get_latest_ci_status.return_value = ("FAILED", long_logs)

        status, details = _collect_ci_status(
            project_dir, "main", truncate=True, max_lines=100
        )

        assert status == "FAILED"
        # Should be truncated by the function
        assert "[... truncated" in details
        assert len(details.split("\n")) <= 102  # 100 + truncation marker + buffer


def test_collect_ci_status_no_truncation():
    """Test _collect_ci_status without truncation."""
    from src.mcp_coder.utils.branch_status import _collect_ci_status

    project_dir = Path("/test/repo")
    short_logs = "Short error message"

    with patch(
        "src.mcp_coder.utils.github_operations.ci_results_manager.CIResultsManager"
    ) as mock_ci_manager:
        mock_instance = MagicMock()
        mock_ci_manager.return_value = mock_instance
        mock_instance.get_latest_ci_status.return_value = ("PASSED", None)

        status, details = _collect_ci_status(
            project_dir, "main", truncate=False, max_lines=100
        )

        assert status == "PASSED"
        assert details is None


def test_collect_ci_status_error_handling():
    """Test _collect_ci_status with API errors."""
    from src.mcp_coder.utils.branch_status import _collect_ci_status

    project_dir = Path("/test/repo")

    with patch(
        "src.mcp_coder.utils.github_operations.ci_results_manager.CIResultsManager"
    ) as mock_ci_manager:
        mock_instance = MagicMock()
        mock_ci_manager.return_value = mock_instance
        mock_instance.get_latest_ci_status.side_effect = Exception("API Error")

        status, details = _collect_ci_status(
            project_dir, "main", truncate=False, max_lines=100
        )

        assert status == "NOT_CONFIGURED"
        assert details is None


def test_collect_rebase_status_edge_cases():
    """Test _collect_rebase_status with various edge cases."""
    from src.mcp_coder.utils.branch_status import _collect_rebase_status

    project_dir = Path("/test/repo")

    # Test normal case
    with patch(
        "src.mcp_coder.utils.git_operations.branches.needs_rebase"
    ) as mock_needs_rebase:
        mock_needs_rebase.return_value = (False, "up-to-date")

        rebase_needed, reason = _collect_rebase_status(project_dir)

        assert rebase_needed is False
        assert reason == "up-to-date"
        mock_needs_rebase.assert_called_once_with(project_dir)

    # Test error case
    with patch(
        "src.mcp_coder.utils.git_operations.branches.needs_rebase"
    ) as mock_needs_rebase:
        mock_needs_rebase.side_effect = Exception("Git error")

        rebase_needed, reason = _collect_rebase_status(project_dir)

        assert rebase_needed is False
        assert "Error checking rebase status: Git error" in reason


def test_collect_task_status():
    """Test _collect_task_status function."""
    from src.mcp_coder.utils.branch_status import _collect_task_status

    project_dir = Path("/test/repo")

    # Test tasks complete
    with patch(
        "src.mcp_coder.workflow_utils.task_tracker.has_incomplete_work"
    ) as mock_incomplete:
        mock_incomplete.return_value = False

        result = _collect_task_status(project_dir)

        assert result is True  # No incomplete work means tasks complete
        mock_incomplete.assert_called_once_with(project_dir)

    # Test tasks incomplete
    with patch(
        "src.mcp_coder.workflow_utils.task_tracker.has_incomplete_work"
    ) as mock_incomplete:
        mock_incomplete.return_value = True

        result = _collect_task_status(project_dir)

        assert result is False  # Has incomplete work means tasks not complete

    # Test error case
    with patch(
        "src.mcp_coder.workflow_utils.task_tracker.has_incomplete_work"
    ) as mock_incomplete:
        mock_incomplete.side_effect = Exception("Task tracker error")

        result = _collect_task_status(project_dir)

        assert result is False  # Default to incomplete on error


def test_collect_github_label():
    """Test _collect_github_label function."""
    from src.mcp_coder.utils.branch_status import _collect_github_label

    project_dir = Path("/test/repo")

    with (
        patch(
            "src.mcp_coder.utils.git_operations.branches.get_current_branch_name"
        ) as mock_branch,
        patch(
            "src.mcp_coder.utils.git_operations.readers.extract_issue_number_from_branch"
        ) as mock_extract,
        patch(
            "src.mcp_coder.utils.github_operations.issue_manager.IssueManager"
        ) as mock_issue_manager,
    ):
        # Setup mocks
        mock_branch.return_value = "feature/123-add-tests"
        mock_extract.return_value = 123
        mock_manager_instance = MagicMock()
        mock_issue_manager.return_value = mock_manager_instance
        mock_issue = {
            "labels": [{"name": "status-03:implementing"}, {"name": "priority-high"}]
        }
        mock_manager_instance.get_issue.return_value = mock_issue

        result = _collect_github_label(project_dir)

        assert result == "status-03:implementing"
        mock_extract.assert_called_once_with("feature/123-add-tests")
        mock_manager_instance.get_issue.assert_called_once_with(123)


def test_collect_github_label_no_status_label():
    """Test _collect_github_label when no status label found."""
    from src.mcp_coder.utils.branch_status import _collect_github_label

    project_dir = Path("/test/repo")

    with (
        patch(
            "src.mcp_coder.utils.git_operations.branches.get_current_branch_name"
        ) as mock_branch,
        patch(
            "src.mcp_coder.utils.git_operations.readers.extract_issue_number_from_branch"
        ) as mock_extract,
        patch(
            "src.mcp_coder.utils.github_operations.issue_manager.IssueManager"
        ) as mock_issue_manager,
    ):
        # Setup mocks with no status labels
        mock_branch.return_value = "feature/123-add-tests"
        mock_extract.return_value = 123
        mock_manager_instance = MagicMock()
        mock_issue_manager.return_value = mock_manager_instance
        mock_issue = {
            "labels": [{"name": "priority-high"}, {"name": "bug"}]  # No status- label
        }
        mock_manager_instance.get_issue.return_value = mock_issue

        result = _collect_github_label(project_dir)

        assert result == "unknown"


def test_collect_github_label_error_handling():
    """Test _collect_github_label with various errors."""
    from src.mcp_coder.utils.branch_status import _collect_github_label

    project_dir = Path("/test/repo")

    # Test branch name extraction error
    with patch(
        "src.mcp_coder.utils.git_operations.branches.get_current_branch_name"
    ) as mock_branch:
        mock_branch.side_effect = Exception("Git error")

        result = _collect_github_label(project_dir)

        assert result == "unknown"

    # Test issue number extraction returns None
    with (
        patch(
            "src.mcp_coder.utils.git_operations.branches.get_current_branch_name"
        ) as mock_branch,
        patch(
            "src.mcp_coder.utils.git_operations.readers.extract_issue_number_from_branch"
        ) as mock_extract,
    ):
        mock_branch.return_value = "main"
        mock_extract.return_value = None

        result = _collect_github_label(project_dir)

        assert result == "unknown"


def test_generate_recommendations_logic():
    """Test _generate_recommendations function logic."""
    from src.mcp_coder.utils.branch_status import _generate_recommendations

    # Test all good case
    report_data = {
        "ci_status": "PASSED",
        "rebase_needed": False,
        "tasks_complete": True,
    }
    recommendations = _generate_recommendations(report_data)
    assert "Ready to merge" in recommendations[0]

    # Test CI failed case
    report_data = {
        "ci_status": "FAILED",
        "rebase_needed": False,
        "tasks_complete": True,
    }
    recommendations = _generate_recommendations(report_data)
    assert "Fix CI test failures" == recommendations[0]

    # Test multiple issues - should prioritize CI first
    report_data = {
        "ci_status": "FAILED",
        "rebase_needed": True,
        "tasks_complete": False,
    }
    recommendations = _generate_recommendations(report_data)
    assert "Fix CI test failures" == recommendations[0]
    assert "Complete remaining tasks" == recommendations[1]
    assert "Rebase onto origin/main" == recommendations[2]

    # Test tasks incomplete only
    report_data = {
        "ci_status": "PASSED",
        "rebase_needed": False,
        "tasks_complete": False,
    }
    recommendations = _generate_recommendations(report_data)
    assert "Complete remaining tasks" == recommendations[0]

    # Test rebase needed only
    report_data = {
        "ci_status": "PASSED",
        "rebase_needed": True,
        "tasks_complete": True,
    }
    recommendations = _generate_recommendations(report_data)
    assert "Rebase onto origin/main" == recommendations[0]

    # Test CI pending case
    report_data = {
        "ci_status": "PENDING",
        "rebase_needed": False,
        "tasks_complete": True,
    }
    recommendations = _generate_recommendations(report_data)
    assert "Wait for CI to complete" == recommendations[0]

    # Test CI not configured case
    report_data = {
        "ci_status": "NOT_CONFIGURED",
        "rebase_needed": False,
        "tasks_complete": True,
    }
    recommendations = _generate_recommendations(report_data)
    assert "Configure CI pipeline" == recommendations[0]
