"""Tests for branch status reporting functionality.

This module tests the BranchStatusReport dataclass and related utilities
for reporting the readiness status of branches.
"""

from dataclasses import dataclass
from typing import List, Optional

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
