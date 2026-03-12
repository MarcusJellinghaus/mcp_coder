"""Tests for branch status reporting functionality.

This module tests the BranchStatusReport dataclass and related utilities
for reporting the readiness status of branches.
"""

from dataclasses import FrozenInstanceError
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.checks.branch_status import (
    CI_FAILED,
    CI_NOT_CONFIGURED,
    CI_PASSED,
    CI_PENDING,
    DEFAULT_LABEL,
    EMPTY_RECOMMENDATIONS,
    BranchStatusReport,
    _build_ci_error_details,
    _collect_ci_status,
    _collect_github_label,
    _collect_rebase_status,
    _collect_task_status,
    _extract_failed_step_log,
    _generate_recommendations,
    collect_branch_status,
    create_empty_report,
    truncate_ci_details,
)
from mcp_coder.utils.github_operations.issues import IssueData


def test_branch_status_report_creation() -> None:
    """Test BranchStatusReport dataclass creation with all fields."""
    report = BranchStatusReport(
        branch_name="feature/123-test",
        base_branch="main",
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Up to date with origin/main",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=["Ready to merge"],
    )

    assert report.branch_name == "feature/123-test"
    assert report.base_branch == "main"
    assert report.ci_status == "PASSED"
    assert report.ci_details is None
    assert report.rebase_needed is False
    assert report.rebase_reason == "Up to date with origin/main"
    assert report.tasks_complete is True
    assert report.current_github_label == "status-03:implementing"
    assert report.recommendations == ["Ready to merge"]


def test_branch_status_report_failed_ci() -> None:
    """Test BranchStatusReport with failed CI status."""
    ci_error = "FAILED tests/test_example.py::test_function - AssertionError"

    report = BranchStatusReport(
        branch_name="feature/456-bugfix",
        base_branch="develop",
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
    report = BranchStatusReport(
        branch_name="feature/123-test",
        base_branch="main",
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Up to date with origin/main",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=["Ready to merge"],
    )

    formatted = report.format_for_human()

    # NEW assertions - branch info comes first
    assert "Branch: feature/123-test" in formatted
    assert "Base Branch: main" in formatted
    # Verify order: branch info before title
    branch_pos = formatted.find("Branch:")
    title_pos = formatted.find("Branch Status Report")
    assert branch_pos < title_pos

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
    ci_error = "FAILED tests/test_example.py::test_function - AssertionError\nFAILED tests/test_other.py::test_other - KeyError"

    report = BranchStatusReport(
        branch_name="feature/456-bugfix",
        base_branch="develop",
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
    report = BranchStatusReport(
        branch_name="feature/789-pending",
        base_branch="main",
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
    report = BranchStatusReport(
        branch_name="feature/101-no-ci",
        base_branch="main",
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
    report = BranchStatusReport(
        branch_name="feature/123-test",
        base_branch="main",
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Up to date",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=["Ready to merge"],
    )

    formatted = report.format_for_llm()

    # NEW assertion - branch info on first line
    lines = formatted.split("\n")
    assert lines[0] == "Branch: feature/123-test | Base: main"

    assert "Branch Status: CI=PASSED, Rebase=UP_TO_DATE, Tasks=COMPLETE" in formatted
    assert "GitHub Label: status-03:implementing" in formatted
    assert "Recommendations: Ready to merge" in formatted


def test_format_for_llm_truncation() -> None:
    """Test format_for_llm truncates CI details when they exceed max_lines."""
    # Create CI details with 400 lines (exceeds default 300)
    ci_lines = [f"Error line {i+1}" for i in range(400)]
    long_ci_details = "\n".join(ci_lines)

    report = BranchStatusReport(
        branch_name="feature/456-errors",
        base_branch="main",
        ci_status="FAILED",
        ci_details=long_ci_details,
        rebase_needed=True,
        rebase_reason="Behind",
        tasks_complete=False,
        current_github_label="status-02:planning",
        recommendations=["Fix errors"],
    )

    formatted = report.format_for_llm(max_lines=300)

    # Should contain truncation message
    assert "[... truncated" in formatted
    # Should have first 10 and last 290 lines logic applied
    assert "Error line 1" in formatted  # First line
    assert "Error line 10" in formatted  # 10th line (last of head)
    assert "Error line 111" in formatted  # First line of last 290
    assert "Error line 400" in formatted  # Last line


def test_format_for_llm_no_truncation() -> None:
    """Test format_for_llm doesn't truncate short CI details."""
    short_ci_details = "Short error message"

    report = BranchStatusReport(
        branch_name="feature/789-short",
        base_branch="main",
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
    report = create_empty_report()

    assert report.branch_name == "unknown"
    assert report.base_branch == "unknown"
    assert report.ci_status == "NOT_CONFIGURED"
    assert report.ci_details is None
    assert report.rebase_needed is False
    assert report.rebase_reason == "Unknown"
    assert report.tasks_complete is False
    assert report.current_github_label == "unknown"
    assert report.recommendations == []


def test_truncate_ci_details_no_truncation() -> None:
    """Test truncate_ci_details with short content."""
    short_content = "Short error\nAnother line\nThird line"
    result = truncate_ci_details(short_content, max_lines=200)

    assert result == short_content
    assert "[... truncated" not in result


def test_truncate_ci_details_with_truncation() -> None:
    """Test truncate_ci_details with long content requiring truncation."""
    # Create content with 400 lines
    lines = [f"Line {i+1}" for i in range(400)]
    long_content = "\n".join(lines)

    result = truncate_ci_details(long_content, max_lines=300)

    # Should contain truncation marker
    assert "[... truncated 100 lines ...]" in result
    # Should have first 10 lines (head_lines default)
    assert "Line 1" in result
    assert "Line 10" in result
    # Should have last 290 lines (starting from line 111)
    assert "Line 111" in result
    assert "Line 400" in result
    # Should not have middle lines (between head and tail)
    assert "Line 50" not in result
    assert "Line 100" not in result


def test_truncate_ci_details_empty() -> None:
    """Test truncate_ci_details with empty content."""
    assert truncate_ci_details("") == ""


def test_truncate_ci_details_custom_max_lines() -> None:
    """Test truncate_ci_details with custom max_lines parameter."""
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


class TestExtractFailedStepLog:
    """Tests for _extract_failed_step_log function."""

    def test_exact_name_match(self) -> None:
        """Should extract the section matching step_name exactly."""
        log = (
            "##[group]Set up job\n"
            "Setting up runner...\n"
            "##[endgroup]\n"
            "##[group]Run tests\n"
            "pytest output line 1\n"
            "FAILED test_foo.py\n"
            "##[endgroup]\n"
            "##[group]Post actions\n"
            "Cleaning up...\n"
            "##[endgroup]"
        )
        result = _extract_failed_step_log(log, "Run tests")
        assert "pytest output line 1" in result
        assert "FAILED test_foo.py" in result
        assert "Setting up runner" not in result
        assert "Cleaning up" not in result

    def test_prefix_match(self) -> None:
        """Should match when step_name is a prefix of the group label."""
        log = (
            "##[group]Run vulture --version && ./tools/vulture_check.sh\n"
            "vulture output here\n"
            "##[endgroup]"
        )
        result = _extract_failed_step_log(log, "Run vulture")
        assert "vulture output here" in result

    def test_contains_match(self) -> None:
        """Should match when step_name is contained in the group label."""
        log = (
            "##[group]Step 3: Run vulture check\n"
            "vulture found issues\n"
            "##[endgroup]"
        )
        result = _extract_failed_step_log(log, "vulture check")
        assert "vulture found issues" in result

    def test_captures_error_lines_after_endgroup(self) -> None:
        """Should include ##[error] lines after ##[endgroup]."""
        log = (
            "##[group]Run tests\n"
            "test output\n"
            "##[endgroup]\n"
            "##[error]Process completed with exit code 1."
        )
        result = _extract_failed_step_log(log, "Run tests")
        assert "test output" in result
        assert "##[error]Process completed with exit code 1." in result

    def test_returns_empty_when_no_markers(self) -> None:
        """Should return empty string when no ##[group] markers are present."""
        log = "Just plain log output\nNo markers here"
        result = _extract_failed_step_log(log, "Run tests")
        assert result == ""

    def test_returns_empty_when_step_name_empty(self) -> None:
        """Should return empty string when step_name is empty."""
        log = "##[group]Run tests\noutput\n##[endgroup]"
        result = _extract_failed_step_log(log, "")
        assert result == ""

    def test_returns_empty_when_no_match(self) -> None:
        """Should return empty string when no group matches step_name."""
        log = (
            "##[group]Set up job\n"
            "setup output\n"
            "##[endgroup]\n"
            "##[group]Checkout\n"
            "checkout output\n"
            "##[endgroup]"
        )
        result = _extract_failed_step_log(log, "Run tests")
        assert result == ""

    def test_case_insensitive_matching(self) -> None:
        """Should match case-insensitively."""
        log = "##[group]run tests\n" "test output\n" "##[endgroup]"
        result = _extract_failed_step_log(log, "Run Tests")
        assert "test output" in result

    def test_multiple_groups_extracts_only_matching(self) -> None:
        """Should extract only the matching group from multiple groups."""
        log = (
            "##[group]Set up job\n"
            "setup line 1\n"
            "setup line 2\n"
            "##[endgroup]\n"
            "##[group]Install dependencies\n"
            "pip install...\n"
            "##[endgroup]\n"
            "##[group]Run tests\n"
            "FAILED: test_foo\n"
            "AssertionError\n"
            "##[endgroup]\n"
            "##[error]Process completed with exit code 1.\n"
            "##[group]Post checkout\n"
            "post cleanup\n"
            "##[endgroup]"
        )
        result = _extract_failed_step_log(log, "Run tests")
        assert "FAILED: test_foo" in result
        assert "AssertionError" in result
        assert "##[error]Process completed with exit code 1." in result
        assert "setup line" not in result
        assert "pip install" not in result
        assert "post cleanup" not in result

    def test_realistic_github_actions_log(self) -> None:
        """Should work with a realistic GitHub Actions log format."""
        log = (
            "##[group]Set up job\n"
            "Current runner version: '2.321.0'\n"
            "Runner name: 'GitHub Actions 2'\n"
            "##[endgroup]\n"
            "##[group]Run actions/checkout@v4\n"
            "Syncing repository: user/repo\n"
            "##[endgroup]\n"
            "##[group]Set up Python\n"
            "Successfully set up Python 3.12\n"
            "##[endgroup]\n"
            "##[group]Install dependencies\n"
            "Collecting pytest\n"
            "Successfully installed pytest-8.0.0\n"
            "##[endgroup]\n"
            "##[group]Run pytest --tb=short\n"
            "============================= test session starts ============================\n"
            "collected 150 items\n"
            "tests/test_auth.py::test_login FAILED\n"
            "FAILED tests/test_auth.py::test_login - AssertionError: 401 != 200\n"
            "============================= 1 failed, 149 passed ============================\n"
            "##[endgroup]\n"
            "##[error]Process completed with exit code 1."
        )
        result = _extract_failed_step_log(log, "Run pytest")
        assert "test session starts" in result
        assert "FAILED tests/test_auth.py" in result
        assert "1 failed, 149 passed" in result
        assert "##[error]Process completed with exit code 1." in result
        assert "Successfully set up Python" not in result
        assert "Collecting pytest" not in result

    def test_unknown_step_returns_error_groups(self) -> None:
        """When step_name is 'unknown', should return groups with ##[error] lines."""
        log = (
            "##[group]Set up job\n"
            "Setting up runner...\n"
            "##[endgroup]\n"
            "##[group]Run tests\n"
            "FAILED test_foo.py\n"
            "##[endgroup]\n"
            "##[error]Process completed with exit code 1.\n"
            "##[group]Post actions\n"
            "Cleaning up...\n"
            "##[endgroup]"
        )
        result = _extract_failed_step_log(log, "unknown")
        assert "FAILED test_foo.py" in result
        assert "##[error]Process completed with exit code 1." in result
        assert "Setting up runner" not in result
        assert "Cleaning up" not in result

    def test_empty_step_name_returns_error_groups(self) -> None:
        """When step_name is empty, should return groups with ##[error] lines."""
        log = (
            "##[group]Set up job\n"
            "Setting up runner...\n"
            "##[endgroup]\n"
            "##[group]Run tests\n"
            "test output\n"
            "##[endgroup]\n"
            "##[error]Process completed with exit code 1.\n"
            "##[group]Post actions\n"
            "Cleaning up...\n"
            "##[endgroup]"
        )
        result = _extract_failed_step_log(log, "")
        assert "test output" in result
        assert "##[error]Process completed with exit code 1." in result
        assert "Setting up runner" not in result

    def test_no_match_no_errors_returns_empty(self) -> None:
        """When no match and no ##[error] lines, should return empty string."""
        log = (
            "##[group]Set up job\n"
            "setup output\n"
            "##[endgroup]\n"
            "##[group]Checkout\n"
            "checkout output\n"
            "##[endgroup]"
        )
        result = _extract_failed_step_log(log, "unknown")
        assert result == ""

    def test_multiple_error_groups_returned(self) -> None:
        """When multiple groups have ##[error] lines, all should be returned."""
        log = (
            "##[group]Set up job\n"
            "setup output\n"
            "##[endgroup]\n"
            "##[group]Lint check\n"
            "lint output\n"
            "##[endgroup]\n"
            "##[error]Lint failed\n"
            "##[group]Run tests\n"
            "test output\n"
            "##[endgroup]\n"
            "##[error]Tests failed"
        )
        result = _extract_failed_step_log(log, "unknown")
        assert "--- Lint check ---" in result
        assert "lint output" in result
        assert "##[error]Lint failed" in result
        assert "--- Run tests ---" in result
        assert "test output" in result
        assert "##[error]Tests failed" in result
        assert "setup output" not in result

    def test_fallback_excludes_clean_groups(self) -> None:
        """Setup groups without ##[error] should be excluded from fallback."""
        log = (
            "##[group]Set up job\n"
            "Runner version: 2.321.0\n"
            "##[endgroup]\n"
            "##[group]Install dependencies\n"
            "pip install pytest\n"
            "##[endgroup]\n"
            "##[group]Run file-size check\n"
            "Checking file sizes...\n"
            "src/big_file.py: 900 lines (over 750)\n"
            "##[endgroup]\n"
            "##[error]Process completed with exit code 1.\n"
            "##[group]Post checkout\n"
            "Cleaning up...\n"
            "##[endgroup]"
        )
        result = _extract_failed_step_log(log, "unknown")
        assert "Checking file sizes" in result
        assert "900 lines" in result
        assert "##[error]Process completed with exit code 1." in result
        assert "Runner version" not in result
        assert "pip install" not in result
        assert "Cleaning up" not in result


def test_branch_status_constants() -> None:
    """Test that required constants are defined."""
    assert CI_PASSED == "PASSED"
    assert CI_FAILED == "FAILED"
    assert CI_NOT_CONFIGURED == "NOT_CONFIGURED"
    assert CI_PENDING == "PENDING"
    assert DEFAULT_LABEL == "unknown"
    assert EMPTY_RECOMMENDATIONS == []


def test_dataclass_immutability() -> None:
    """Test that BranchStatusReport is immutable (frozen)."""
    report = BranchStatusReport(
        branch_name="feature/123-test",
        base_branch="main",
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Up to date",
        tasks_complete=True,
        current_github_label="status-03:implementing",
        recommendations=[],
    )

    # Should raise FrozenInstanceError when trying to modify frozen dataclass
    # via normal attribute assignment
    with pytest.raises(FrozenInstanceError):
        report.ci_status = "FAILED"  # type: ignore[misc]


# Tests for collect_branch_status() function


def test_collect_branch_status_all_good() -> None:
    """Test collect_branch_status with all systems green."""
    project_dir = Path("/test/repo")

    with (
        patch("mcp_coder.checks.branch_status.get_current_branch_name") as mock_branch,
        patch(
            "mcp_coder.checks.branch_status.extract_issue_number_from_branch"
        ) as mock_extract,
        patch("mcp_coder.checks.branch_status.detect_base_branch") as mock_base,
        patch("mcp_coder.checks.branch_status._collect_ci_status") as mock_ci,
        patch("mcp_coder.checks.branch_status._collect_rebase_status") as mock_rebase,
        patch("mcp_coder.checks.branch_status._collect_task_status") as mock_tasks,
        patch("mcp_coder.checks.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks for all green status
        mock_branch.return_value = "main"
        mock_extract.return_value = None  # No issue number in branch
        mock_base.return_value = "origin/main"
        mock_ci.return_value = ("PASSED", None)
        mock_rebase.return_value = (False, "Up to date with origin/main")
        mock_tasks.return_value = True
        mock_label.return_value = "status-04:reviewing"

        result = collect_branch_status(project_dir)

        # Verify result includes new fields
        assert result.branch_name == "main"
        assert result.base_branch == "origin/main"
        assert result.ci_status == "PASSED"
        assert result.ci_details is None
        assert result.rebase_needed is False
        assert result.rebase_reason == "Up to date with origin/main"
        assert result.tasks_complete is True
        assert result.current_github_label == "status-04:reviewing"
        assert "Ready to merge" in result.recommendations

        # Verify function calls
        mock_branch.assert_called_once_with(project_dir)
        mock_ci.assert_called_once_with(project_dir, "main", 300)
        mock_rebase.assert_called_once_with(project_dir)
        mock_tasks.assert_called_once_with(project_dir)


def test_collect_branch_status_ci_failed() -> None:
    """Test collect_branch_status with CI failures."""
    project_dir = Path("/test/repo")
    ci_error = "FAILED tests/test_example.py::test_function - AssertionError"

    with (
        patch("mcp_coder.checks.branch_status.get_current_branch_name") as mock_branch,
        patch(
            "mcp_coder.checks.branch_status.extract_issue_number_from_branch"
        ) as mock_extract,
        patch("mcp_coder.checks.branch_status.detect_base_branch") as mock_base,
        patch("mcp_coder.checks.branch_status._collect_ci_status") as mock_ci,
        patch("mcp_coder.checks.branch_status._collect_rebase_status") as mock_rebase,
        patch("mcp_coder.checks.branch_status._collect_task_status") as mock_tasks,
        patch("mcp_coder.checks.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks for CI failed
        mock_branch.return_value = "feature/test-branch"
        mock_extract.return_value = None
        mock_base.return_value = "main"
        mock_ci.return_value = ("FAILED", ci_error)
        mock_rebase.return_value = (False, "Up to date with origin/main")
        mock_tasks.return_value = True
        mock_label.return_value = "status-03:implementing"

        result = collect_branch_status(project_dir)

        # Verify result
        assert result.branch_name == "feature/test-branch"
        assert result.base_branch == "main"
        assert result.ci_status == "FAILED"
        assert result.ci_details == ci_error
        assert result.rebase_needed is False
        assert result.tasks_complete is True
        assert "Fix CI test failures" in result.recommendations


def test_collect_branch_status_rebase_needed() -> None:
    """Test collect_branch_status with rebase required."""
    project_dir = Path("/test/repo")

    with (
        patch("mcp_coder.checks.branch_status.get_current_branch_name") as mock_branch,
        patch(
            "mcp_coder.checks.branch_status.extract_issue_number_from_branch"
        ) as mock_extract,
        patch("mcp_coder.checks.branch_status.detect_base_branch") as mock_base,
        patch("mcp_coder.checks.branch_status._collect_ci_status") as mock_ci,
        patch("mcp_coder.checks.branch_status._collect_rebase_status") as mock_rebase,
        patch("mcp_coder.checks.branch_status._collect_task_status") as mock_tasks,
        patch("mcp_coder.checks.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks for rebase needed
        mock_branch.return_value = "feature/test-branch"
        mock_extract.return_value = None
        mock_base.return_value = "main"
        mock_ci.return_value = ("PASSED", None)
        mock_rebase.return_value = (True, "5 commits behind origin/main")
        mock_tasks.return_value = True
        mock_label.return_value = "status-03:implementing"

        result = collect_branch_status(project_dir)

        # Verify result
        assert result.branch_name == "feature/test-branch"
        assert result.base_branch == "main"
        assert result.ci_status == "PASSED"
        assert result.rebase_needed is True
        assert result.rebase_reason == "5 commits behind origin/main"
        assert "Rebase onto origin/main" in result.recommendations


def test_collect_branch_status_tasks_incomplete() -> None:
    """Test collect_branch_status with incomplete tasks."""
    project_dir = Path("/test/repo")

    with (
        patch("mcp_coder.checks.branch_status.get_current_branch_name") as mock_branch,
        patch(
            "mcp_coder.checks.branch_status.extract_issue_number_from_branch"
        ) as mock_extract,
        patch("mcp_coder.checks.branch_status.detect_base_branch") as mock_base,
        patch("mcp_coder.checks.branch_status._collect_ci_status") as mock_ci,
        patch("mcp_coder.checks.branch_status._collect_rebase_status") as mock_rebase,
        patch("mcp_coder.checks.branch_status._collect_task_status") as mock_tasks,
        patch("mcp_coder.checks.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks for incomplete tasks
        mock_branch.return_value = "feature/test-branch"
        mock_extract.return_value = None
        mock_base.return_value = "main"
        mock_ci.return_value = ("PASSED", None)
        mock_rebase.return_value = (False, "Up to date with origin/main")
        mock_tasks.return_value = False
        mock_label.return_value = "status-03:implementing"

        result = collect_branch_status(project_dir)

        # Verify result
        assert result.branch_name == "feature/test-branch"
        assert result.base_branch == "main"
        assert result.ci_status == "PASSED"
        assert result.rebase_needed is False
        assert result.tasks_complete is False
        assert "Complete remaining tasks" in result.recommendations


def test_collect_branch_status_with_truncation() -> None:
    """Test collect_branch_status with CI log truncation enabled."""
    project_dir = Path("/test/repo")
    long_ci_error = "\n".join([f"Error line {i}" for i in range(300)])

    with (
        patch("mcp_coder.checks.branch_status.get_current_branch_name") as mock_branch,
        patch(
            "mcp_coder.checks.branch_status.extract_issue_number_from_branch"
        ) as mock_extract,
        patch("mcp_coder.checks.branch_status.detect_base_branch") as mock_base,
        patch("mcp_coder.checks.branch_status._collect_ci_status") as mock_ci,
        patch("mcp_coder.checks.branch_status._collect_rebase_status") as mock_rebase,
        patch("mcp_coder.checks.branch_status._collect_task_status") as mock_tasks,
        patch("mcp_coder.checks.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks
        mock_branch.return_value = "main"
        mock_extract.return_value = None
        mock_base.return_value = "origin/main"
        mock_ci.return_value = ("FAILED", long_ci_error)
        mock_rebase.return_value = (False, "Up to date")
        mock_tasks.return_value = True
        mock_label.return_value = "status-03:implementing"

        result = collect_branch_status(project_dir, max_log_lines=50)

        # Verify truncation was passed correctly
        mock_branch.assert_called_once_with(project_dir)
        mock_ci.assert_called_once_with(project_dir, "main", 50)
        assert (
            result.ci_details == long_ci_error
        )  # Function should return what mock returns


def test_collect_branch_status_all_failed() -> None:
    """Test collect_branch_status with all systems failing."""
    project_dir = Path("/test/repo")
    ci_error = "Multiple test failures"

    with (
        patch("mcp_coder.checks.branch_status.get_current_branch_name") as mock_branch,
        patch(
            "mcp_coder.checks.branch_status.extract_issue_number_from_branch"
        ) as mock_extract,
        patch("mcp_coder.checks.branch_status.detect_base_branch") as mock_base,
        patch("mcp_coder.checks.branch_status._collect_ci_status") as mock_ci,
        patch("mcp_coder.checks.branch_status._collect_rebase_status") as mock_rebase,
        patch("mcp_coder.checks.branch_status._collect_task_status") as mock_tasks,
        patch("mcp_coder.checks.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks for everything failing
        mock_branch.return_value = "feature/test-branch"
        mock_extract.return_value = None
        mock_base.return_value = "main"
        mock_ci.return_value = ("FAILED", ci_error)
        mock_rebase.return_value = (True, "3 commits behind origin/main")
        mock_tasks.return_value = False
        mock_label.return_value = "status-02:planning"

        result = collect_branch_status(project_dir)

        # Verify result includes new fields
        assert result.branch_name == "feature/test-branch"
        assert result.base_branch == "main"
        assert result.ci_status == "FAILED"
        assert result.ci_details == ci_error
        assert result.rebase_needed is True
        assert result.rebase_reason == "3 commits behind origin/main"
        assert result.tasks_complete is False
        assert result.current_github_label == "status-02:planning"

        # Should have recommendations in priority order
        # Note: Rebase recommendation is NOT added when CI is FAILED and tasks are incomplete
        # (per _generate_recommendations logic: rebase only when tasks_complete AND ci_status != FAILED)
        recommendations = result.recommendations
        assert len(recommendations) >= 2
        assert "Fix CI test failures" in recommendations[0]  # CI first priority
        assert any("Complete remaining tasks" in r for r in recommendations)
        # Rebase recommendation should NOT be present with CI failed and tasks incomplete
        assert not any("Rebase onto origin/main" in r for r in recommendations)


# Tests for helper functions


def test_collect_ci_status_with_truncation() -> None:
    """Test _collect_ci_status with log truncation."""
    project_dir = Path("/test/repo")
    long_logs = "\n".join([f"Log line {i}" for i in range(400)])

    with patch("mcp_coder.checks.branch_status.CIResultsManager") as mock_ci_manager:
        mock_instance = MagicMock()
        mock_ci_manager.return_value = mock_instance
        # Return dict structure matching actual API with jobs data
        mock_instance.get_latest_ci_status.return_value = {
            "run": {"run_ids": [123], "conclusion": "failure", "status": "completed"},
            "jobs": [
                {
                    "name": "test-job",
                    "run_id": 123,
                    "conclusion": "failure",
                    "steps": [{"name": "Run tests", "conclusion": "failure"}],
                }
            ],
        }
        # Log file naming: {number}_{job_name}.txt (GitHub Actions format)
        mock_instance.get_run_logs.return_value = {"2_test-job.txt": long_logs}

        status, details = _collect_ci_status(project_dir, "main", max_lines=100)

        assert status == "FAILED"
        # Should be truncated by the function
        assert details is not None
        # Should have structured output with summary
        assert "CI Failure Summary" in details
        assert "test-job" in details
        # Should be truncated
        assert "[... truncated" in details


def test_collect_ci_status_no_truncation() -> None:
    """Test _collect_ci_status without truncation."""
    project_dir = Path("/test/repo")

    with patch("mcp_coder.checks.branch_status.CIResultsManager") as mock_ci_manager:
        mock_instance = MagicMock()
        mock_ci_manager.return_value = mock_instance
        # Return dict structure matching actual API - success case
        mock_instance.get_latest_ci_status.return_value = {
            "run": {"id": 123, "conclusion": "success", "status": "completed"}
        }

        status, details = _collect_ci_status(project_dir, "main", max_lines=100)

        assert status == "PASSED"
        assert details is None


def test_collect_ci_status_error_handling() -> None:
    """Test _collect_ci_status with API errors."""
    project_dir = Path("/test/repo")

    with patch("mcp_coder.checks.branch_status.CIResultsManager") as mock_ci_manager:
        mock_instance = MagicMock()
        mock_ci_manager.return_value = mock_instance
        mock_instance.get_latest_ci_status.side_effect = Exception("API Error")

        status, details = _collect_ci_status(project_dir, "main", max_lines=100)

        assert status == "NOT_CONFIGURED"
        assert details is None


def test_collect_rebase_status_edge_cases() -> None:
    """Test _collect_rebase_status with various edge cases."""
    project_dir = Path("/test/repo")

    # Test normal case
    with patch("mcp_coder.checks.branch_status.needs_rebase") as mock_needs_rebase:
        mock_needs_rebase.return_value = (False, "up-to-date")

        rebase_needed, reason = _collect_rebase_status(project_dir)

        assert rebase_needed is False
        assert reason == "up-to-date"
        mock_needs_rebase.assert_called_once_with(project_dir)

    # Test error case
    with patch("mcp_coder.checks.branch_status.needs_rebase") as mock_needs_rebase:
        mock_needs_rebase.side_effect = Exception("Git error")

        rebase_needed, reason = _collect_rebase_status(project_dir)

        assert rebase_needed is False
        assert "Error checking rebase status: Git error" in reason


def test_collect_task_status() -> None:
    """Test _collect_task_status function."""
    project_dir = Path("/test/repo")

    # Test tasks complete - pr_info doesn't exist so no incomplete work
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False

        result = _collect_task_status(project_dir)

        assert result is True  # No pr_info dir means no tracking, so complete

    # Test tasks complete - pr_info exists with no incomplete work
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("mcp_coder.checks.branch_status.has_incomplete_work") as mock_incomplete,
    ):
        mock_exists.return_value = True
        mock_incomplete.return_value = False

        result = _collect_task_status(project_dir)

        assert result is True  # No incomplete work means tasks complete

    # Test tasks incomplete
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("mcp_coder.checks.branch_status.has_incomplete_work") as mock_incomplete,
    ):
        mock_exists.return_value = True
        mock_incomplete.return_value = True

        result = _collect_task_status(project_dir)

        assert result is False  # Has incomplete work means tasks not complete

    # Test error case
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("mcp_coder.checks.branch_status.has_incomplete_work") as mock_incomplete,
    ):
        mock_exists.return_value = True
        mock_incomplete.side_effect = Exception("Task tracker error")

        result = _collect_task_status(project_dir)

        assert result is False  # Default to incomplete on error


def test_collect_github_label() -> None:
    """Test _collect_github_label function with issue_data provided."""
    project_dir = Path("/test/repo")

    # Issue data with status labels - must conform to IssueData TypedDict
    mock_issue: IssueData = {
        "number": 123,
        "title": "Test issue",
        "body": "Test body",
        "state": "open",
        "labels": ["status-03:implementing", "priority-high"],
        "assignees": [],
        "user": "testuser",
        "created_at": None,
        "updated_at": None,
        "url": "https://github.com/test/repo/issues/123",
        "locked": False,
    }

    # Call with issue_data directly
    result = _collect_github_label(project_dir, mock_issue)

    assert result == "status-03:implementing"


def test_collect_github_label_without_issue_data() -> None:
    """Test _collect_github_label function without issue_data returns default."""
    project_dir = Path("/test/repo")

    # Call without issue_data (None)
    result = _collect_github_label(project_dir, None)

    assert result == DEFAULT_LABEL


def test_collect_github_label_no_status_label() -> None:
    """Test _collect_github_label when no status label found."""
    project_dir = Path("/test/repo")

    # Issue data with no status labels - must conform to IssueData TypedDict
    mock_issue: IssueData = {
        "number": 123,
        "title": "Test issue",
        "body": "Test body",
        "state": "open",
        "labels": ["priority-high", "bug"],  # No status- label
        "assignees": [],
        "user": "testuser",
        "created_at": None,
        "updated_at": None,
        "url": "https://github.com/test/repo/issues/123",
        "locked": False,
    }

    result = _collect_github_label(project_dir, mock_issue)

    assert result == DEFAULT_LABEL


def test_collect_github_label_empty_labels() -> None:
    """Test _collect_github_label with empty labels list."""
    project_dir = Path("/test/repo")

    # Issue data with empty labels - must conform to IssueData TypedDict
    mock_issue: IssueData = {
        "number": 123,
        "title": "Test issue",
        "body": "Test body",
        "state": "open",
        "labels": [],
        "assignees": [],
        "user": "testuser",
        "created_at": None,
        "updated_at": None,
        "url": "https://github.com/test/repo/issues/123",
        "locked": False,
    }

    result = _collect_github_label(project_dir, mock_issue)

    assert result == DEFAULT_LABEL


def test_generate_recommendations_logic() -> None:
    """Test _generate_recommendations function logic."""
    # Test all good case (CI passed, tasks complete, no rebase needed)
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
    # Note: rebase recommendation only added when tasks_complete AND ci_status != FAILED
    report_data = {
        "ci_status": "FAILED",
        "rebase_needed": True,
        "tasks_complete": False,
    }
    recommendations = _generate_recommendations(report_data)
    assert "Fix CI test failures" == recommendations[0]
    assert "Complete remaining tasks" == recommendations[1]
    # Rebase is NOT added here because CI is FAILED and tasks are incomplete
    assert len(recommendations) == 2

    # Test tasks incomplete only
    report_data = {
        "ci_status": "PASSED",
        "rebase_needed": False,
        "tasks_complete": False,
    }
    recommendations = _generate_recommendations(report_data)
    assert "Complete remaining tasks" == recommendations[0]

    # Test rebase needed only (tasks complete, CI passed)
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

    # Test CI not configured case (with tasks complete)
    # NOT_CONFIGURED is in [CI_PASSED, CI_NOT_CONFIGURED] so "Ready to merge" is added
    report_data = {
        "ci_status": "NOT_CONFIGURED",
        "rebase_needed": False,
        "tasks_complete": True,
    }
    recommendations = _generate_recommendations(report_data)
    assert "Configure CI pipeline" == recommendations[0]
    # Also should have "Ready to merge" since NOT_CONFIGURED counts as passable
    assert "Ready to merge" in recommendations


def test_build_ci_error_details_single_failure() -> None:
    """Test _build_ci_error_details with single failed job."""
    status_result = {
        "run": {"run_ids": [123]},
        "jobs": [
            {
                "name": "test-job",
                "run_id": 123,
                "conclusion": "failure",
                "steps": [{"name": "Run tests", "conclusion": "failure"}],
            }
        ],
    }

    # Mock get_run_logs directly on the passed-in ci_manager instance
    mock_instance = MagicMock()
    # Log filename format: {number}_{job_name}.txt (GitHub Actions format)
    mock_instance.get_run_logs.return_value = {"2_test-job.txt": "Error details here"}

    result = _build_ci_error_details(mock_instance, status_result, 300)

    assert result is not None
    assert "CI Failure Summary" in result
    assert "Failed jobs (1): test-job" in result
    assert "## Job: test-job" in result
    assert "Failed step: Run tests" in result
    assert "Error details here" in result


def test_build_ci_error_details_multiple_failures() -> None:
    """Test _build_ci_error_details shows multiple failed jobs that fit in limit."""
    status_result = {
        "run": {"run_ids": [123]},
        "jobs": [
            {
                "name": "test-job",
                "run_id": 123,
                "conclusion": "failure",
                "steps": [{"name": "Run tests", "conclusion": "failure"}],
            },
            {
                "name": "lint-job",
                "run_id": 123,
                "conclusion": "failure",
                "steps": [{"name": "Run lint", "conclusion": "failure"}],
            },
            {
                "name": "build-job",
                "run_id": 123,
                "conclusion": "failure",
                "steps": [{"name": "Build", "conclusion": "failure"}],
            },
        ],
    }

    # Mock get_run_logs directly on the passed-in ci_manager instance
    mock_instance = MagicMock()
    # Log filename format: {number}_{job_name}.txt (GitHub Actions format)
    mock_instance.get_run_logs.return_value = {
        "2_test-job.txt": "First job error",
        "4_lint-job.txt": "Lint error",
        "9_build-job.txt": "Build error",
    }

    result = _build_ci_error_details(mock_instance, status_result, 300)

    assert result is not None
    # Summary should list all failed jobs
    assert "Failed jobs (3): test-job, lint-job, build-job" in result
    # All jobs should be shown (they fit within the 300 line limit)
    assert "## Job: test-job" in result
    assert "## Job: lint-job" in result
    assert "## Job: build-job" in result
    assert "First job error" in result


def test_build_ci_error_details_includes_github_urls() -> None:
    """Test _build_ci_error_details includes GitHub Actions URLs."""
    status_result = {
        "run": {
            "run_ids": [12345],
            "url": "https://github.com/user/repo/actions/runs/12345",
        },
        "jobs": [
            {
                "id": 67890,
                "run_id": 12345,
                "name": "file-size",
                "conclusion": "failure",
                "steps": [{"name": "Run file-size", "conclusion": "failure"}],
            }
        ],
    }

    mock_instance = MagicMock()
    mock_instance.get_run_logs.return_value = {
        "2_file-size.txt": "File size check failed"
    }

    result = _build_ci_error_details(mock_instance, status_result, 300)

    assert result is not None
    # Check run URL at top
    assert "GitHub Actions: https://github.com/user/repo/actions/runs/12345" in result
    # Check job URL in job section
    assert (
        "View job: https://github.com/user/repo/actions/runs/12345/job/67890" in result
    )
    # Verify other content still present
    assert "## Job: file-size" in result
    assert "Failed step: Run file-size" in result
    assert "File size check failed" in result


def test_build_ci_error_details_logs_not_available_with_url() -> None:
    """Test _build_ci_error_details shows GitHub URL when logs unavailable."""
    status_result = {
        "run": {
            "run_ids": [12345],
            "url": "https://github.com/user/repo/actions/runs/12345",
        },
        "jobs": [
            {
                "id": 67890,
                "run_id": 12345,
                "name": "file-size",
                "conclusion": "failure",
                "steps": [{"name": "Run file-size", "conclusion": "failure"}],
            }
        ],
    }

    mock_instance = MagicMock()
    # Empty dict = no logs available
    mock_instance.get_run_logs.return_value = {}

    result = _build_ci_error_details(mock_instance, status_result, 300)

    assert result is not None
    # Check error message with GitHub URL
    assert "(logs not available locally)" in result
    assert (
        "View on GitHub: https://github.com/user/repo/actions/runs/12345/job/67890"
        in result
    )
    # Check job header still present
    assert "## Job: file-size" in result
    assert "Failed step: Run file-size" in result


def test_build_ci_error_details_fallback_to_old_format() -> None:
    """Test _build_ci_error_details falls back to old log format."""
    status_result = {
        "run": {
            "run_ids": [12345],
            "url": "https://github.com/user/repo/actions/runs/12345",
        },
        "jobs": [
            {
                "id": 67890,
                "run_id": 12345,
                "name": "file-size",
                "conclusion": "failure",
                "steps": [
                    {"name": "Run file-size", "conclusion": "failure", "number": 3}
                ],
            }
        ],
    }

    mock_instance = MagicMock()
    # Use OLD format (pattern match will fail, fallback should work)
    mock_instance.get_run_logs.return_value = {
        "file-size/3_Run file-size.txt": "File size check failed (old format)"
    }

    result = _build_ci_error_details(mock_instance, status_result, 300)

    assert result is not None
    # Verify log content from old format is displayed
    assert "File size check failed (old format)" in result
    assert "## Job: file-size" in result
    assert "Failed step: Run file-size" in result


def test_build_ci_error_details_no_failed_jobs() -> None:
    """Test _build_ci_error_details with no failed jobs returns None."""
    status_result = {
        "run": {"run_ids": [123]},
        "jobs": [
            {
                "name": "test-job",
                "run_id": 123,
                "conclusion": "success",
                "steps": [{"name": "Run tests", "conclusion": "success"}],
            }
        ],
    }

    with patch("mcp_coder.checks.branch_status.CIResultsManager") as mock_ci_manager:
        mock_instance = MagicMock()
        mock_ci_manager.return_value = mock_instance

        result = _build_ci_error_details(mock_instance, status_result, 300)

        assert result is None


def test_build_ci_error_details_fetches_logs_from_multiple_runs() -> None:
    """Logs should be fetched per distinct run_id among failed jobs (up to 3)."""
    status_result = {
        "run": {
            "run_ids": [100, 200],
            "url": "https://github.com/user/repo/actions/runs/100",
        },
        "jobs": [
            {
                "id": 1001,
                "run_id": 100,
                "name": "test-job",
                "conclusion": "failure",
                "steps": [{"name": "Run tests", "conclusion": "failure"}],
            },
            {
                "id": 2001,
                "run_id": 200,
                "name": "lint-job",
                "conclusion": "failure",
                "steps": [{"name": "Run lint", "conclusion": "failure"}],
            },
        ],
    }

    mock_instance = MagicMock()
    mock_instance.get_run_logs.side_effect = [
        {"2_test-job.txt": "Test error from run 100"},
        {"3_lint-job.txt": "Lint error from run 200"},
    ]

    result = _build_ci_error_details(mock_instance, status_result, 300)

    assert result is not None
    # get_run_logs called once per distinct run_id
    assert mock_instance.get_run_logs.call_count == 2
    mock_instance.get_run_logs.assert_any_call(100)
    mock_instance.get_run_logs.assert_any_call(200)
    # Output contains logs from both runs
    assert "Test error from run 100" in result
    assert "Lint error from run 200" in result
    assert "test-job" in result
    assert "lint-job" in result


def test_build_ci_error_details_caps_at_3_failed_runs() -> None:
    """Only fetch logs from first 3 distinct failed run_ids."""
    status_result = {
        "run": {"run_ids": [100, 200, 300, 400]},
        "jobs": [
            {
                "name": "job-a",
                "run_id": 100,
                "conclusion": "failure",
                "steps": [{"name": "Step A", "conclusion": "failure"}],
            },
            {
                "name": "job-b",
                "run_id": 200,
                "conclusion": "failure",
                "steps": [{"name": "Step B", "conclusion": "failure"}],
            },
            {
                "name": "job-c",
                "run_id": 300,
                "conclusion": "failure",
                "steps": [{"name": "Step C", "conclusion": "failure"}],
            },
            {
                "name": "job-d",
                "run_id": 400,
                "conclusion": "failure",
                "steps": [{"name": "Step D", "conclusion": "failure"}],
            },
        ],
    }

    mock_instance = MagicMock()
    mock_instance.get_run_logs.side_effect = [
        {"2_job-a.txt": "Error A"},
        {"3_job-b.txt": "Error B"},
        {"4_job-c.txt": "Error C"},
    ]

    result = _build_ci_error_details(mock_instance, status_result, 300)

    assert result is not None
    # Only 3 calls, not 4
    assert mock_instance.get_run_logs.call_count == 3
    # 4th run's job should be listed by name only (in truncated section or main section)
    assert "job-d" in result


def test_build_ci_error_details_shows_jobs_fetch_warning() -> None:
    """If run_data has jobs_fetch_warning, it should appear in output."""
    status_result = {
        "run": {
            "run_ids": [123],
            "jobs_fetch_warning": "Could not fetch jobs for run(s): [456]",
        },
        "jobs": [
            {
                "name": "test-job",
                "run_id": 123,
                "conclusion": "failure",
                "steps": [{"name": "Run tests", "conclusion": "failure"}],
            }
        ],
    }

    mock_instance = MagicMock()
    mock_instance.get_run_logs.return_value = {"2_test-job.txt": "Error details"}

    result = _build_ci_error_details(mock_instance, status_result, 300)

    assert result is not None
    assert "Could not fetch jobs for run(s): [456]" in result


def test_build_ci_error_details_strips_timestamps_before_extraction() -> None:
    """Test that timestamps are stripped before step extraction.

    GitHub Actions raw logs have timestamps prefixed to every line.
    If _extract_failed_step_log runs before _strip_timestamps, the
    ##[group] markers won't be found and the entire raw log is returned
    instead of just the failed step's output.
    """
    # Raw log with timestamps - mimics real GitHub Actions format
    raw_log = (
        "2026-01-28T12:58:00.0000000Z ##[group]Set up job\n"
        "2026-01-28T12:58:00.1000000Z Runner info here\n"
        "2026-01-28T12:58:00.2000000Z ##[endgroup]\n"
        "2026-01-28T12:58:01.0000000Z ##[group]Run mypy\n"
        "2026-01-28T12:58:01.1000000Z mypy 1.19.1\n"
        "2026-01-28T12:58:01.2000000Z src/foo.py:10: error: Missing type\n"
        "2026-01-28T12:58:01.3000000Z Found 1 error in 1 file\n"
        "2026-01-28T12:58:01.4000000Z ##[error]Process completed with exit code 1.\n"
        "2026-01-28T12:58:01.5000000Z ##[endgroup]\n"
        "2026-01-28T12:58:02.0000000Z ##[group]Post job cleanup\n"
        "2026-01-28T12:58:02.1000000Z Cleaning up\n"
        "2026-01-28T12:58:02.2000000Z ##[endgroup]"
    )

    status_result = {
        "run": {"run_ids": [123]},
        "jobs": [
            {
                "name": "mypy",
                "run_id": 123,
                "conclusion": "failure",
                "steps": [{"name": "Run mypy", "number": 4, "conclusion": "failure"}],
            }
        ],
    }

    mock_instance = MagicMock()
    mock_instance.get_run_logs.return_value = {"2_mypy.txt": raw_log}

    result = _build_ci_error_details(mock_instance, status_result, 300)

    assert result is not None
    # The extracted log should contain the mypy error, not setup/cleanup noise
    assert "Missing type" in result
    # Key assertion: setup and cleanup steps should NOT appear
    assert "Runner info here" not in result
    assert "Cleaning up" not in result


def test_truncate_ci_details_custom_head_lines() -> None:
    """Test truncate_ci_details with custom head_lines parameter."""
    # Create content with 200 lines
    lines = [f"Line {i+1}" for i in range(200)]
    content = "\n".join(lines)

    # Use max_lines=100, head_lines=20 (so tail_lines=80)
    result = truncate_ci_details(content, max_lines=100, head_lines=20)

    # Should contain truncation marker
    assert "[... truncated 100 lines ...]" in result
    # Should have first 20 lines
    assert "Line 1" in result
    assert "Line 20" in result
    # Should have last 80 lines (starting from line 121)
    assert "Line 121" in result
    assert "Line 200" in result
    # Should not have middle lines
    assert "Line 50" not in result


# Tests for branch info collection and issue data sharing


def test_collect_branch_status_includes_branch_info() -> None:
    """Test that collect_branch_status includes branch_name and base_branch."""
    project_dir = Path("/test/repo")

    with (
        patch("mcp_coder.checks.branch_status.get_current_branch_name") as mock_branch,
        patch(
            "mcp_coder.checks.branch_status.extract_issue_number_from_branch"
        ) as mock_extract,
        patch("mcp_coder.checks.branch_status.IssueManager") as mock_issue_manager,
        patch("mcp_coder.checks.branch_status.detect_base_branch") as mock_base,
        patch("mcp_coder.checks.branch_status._collect_ci_status") as mock_ci,
        patch("mcp_coder.checks.branch_status._collect_rebase_status") as mock_rebase,
        patch("mcp_coder.checks.branch_status._collect_task_status") as mock_tasks,
        patch("mcp_coder.checks.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks
        mock_branch.return_value = "feature/123-my-feature"
        mock_extract.return_value = 123
        mock_issue = {"labels": ["status-03:implementing"], "base_branch": "develop"}
        mock_manager_instance = MagicMock()
        mock_issue_manager.return_value = mock_manager_instance
        mock_manager_instance.get_issue.return_value = mock_issue
        mock_base.return_value = "develop"
        mock_ci.return_value = ("PASSED", None)
        mock_rebase.return_value = (False, "Up to date")
        mock_tasks.return_value = True
        mock_label.return_value = "status-03:implementing"

        result = collect_branch_status(project_dir)

        # Verify branch info is included in result
        assert result.branch_name == "feature/123-my-feature"
        assert result.base_branch == "develop"

        # Verify detect_base_branch was called with issue_data
        mock_base.assert_called_once()
        call_args = mock_base.call_args
        assert call_args[0][0] == project_dir
        assert call_args[0][1] == "feature/123-my-feature"


def test_collect_branch_status_shares_issue_data() -> None:
    """Test that collect_branch_status fetches issue data once and shares it."""
    project_dir = Path("/test/repo")

    with (
        patch("mcp_coder.checks.branch_status.get_current_branch_name") as mock_branch,
        patch(
            "mcp_coder.checks.branch_status.extract_issue_number_from_branch"
        ) as mock_extract,
        patch("mcp_coder.checks.branch_status.IssueManager") as mock_issue_manager,
        patch("mcp_coder.checks.branch_status.detect_base_branch") as mock_base,
        patch("mcp_coder.checks.branch_status._collect_ci_status") as mock_ci,
        patch("mcp_coder.checks.branch_status._collect_rebase_status") as mock_rebase,
        patch("mcp_coder.checks.branch_status._collect_task_status") as mock_tasks,
        patch("mcp_coder.checks.branch_status._collect_github_label") as mock_label,
    ):
        # Setup mocks
        mock_branch.return_value = "feature/456-test"
        mock_extract.return_value = 456
        mock_issue = {"labels": ["status-04:reviewing"], "base_branch": "main"}
        mock_manager_instance = MagicMock()
        mock_issue_manager.return_value = mock_manager_instance
        mock_manager_instance.get_issue.return_value = mock_issue
        mock_base.return_value = "main"
        mock_ci.return_value = ("PASSED", None)
        mock_rebase.return_value = (False, "Up to date")
        mock_tasks.return_value = True
        mock_label.return_value = "status-04:reviewing"

        collect_branch_status(project_dir)

        # Verify IssueManager.get_issue was called only once
        mock_manager_instance.get_issue.assert_called_once_with(456)

        # Verify _collect_github_label receives issue_data
        mock_label.assert_called_once()
        label_call_args = mock_label.call_args
        assert label_call_args[0][0] == project_dir
        # Second arg should be the issue_data dict
        assert label_call_args[0][1] == mock_issue
