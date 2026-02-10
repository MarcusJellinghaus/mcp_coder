"""Tests for coordinator/issue_stats.py - Issue statistics functions.

These tests were moved from tests/workflows/test_issue_stats.py as part of
consolidating CLI functionality into the cli/commands structure.
"""

import json
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from mcp_coder.cli.commands.coordinator.issue_stats import (
    display_statistics,
    filter_ignored_issues,
    format_issue_line,
    group_issues_by_category,
    truncate_title,
    validate_issue_labels,
)
from mcp_coder.utils.github_operations.issue_manager import IssueData


# Test fixtures
@pytest.fixture
def test_labels_config(tmp_path: Path) -> dict[str, Any]:
    """Load test labels configuration from fixture."""
    config_path = (
        Path(__file__).parent.parent.parent.parent
        / "workflows"
        / "config"
        / "test_labels.json"
    )
    with open(config_path, "r", encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


@pytest.fixture
def sample_issue() -> IssueData:
    """Create a sample IssueData for testing."""
    return IssueData(
        number=123,
        title="Test issue",
        body="Test body",
        state="open",
        labels=["status-01:created"],
        assignees=[],
        user="testuser",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        url="https://github.com/owner/repo/issues/123",
        locked=False,
    )


@pytest.fixture
def sample_issues() -> list[IssueData]:
    """Create a list of sample issues for testing."""
    return [
        IssueData(
            number=1,
            title="Issue with status-01",
            body="Body 1",
            state="open",
            labels=["status-01:created", "bug"],
            assignees=[],
            user="user1",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            url="https://github.com/owner/repo/issues/1",
            locked=False,
        ),
        IssueData(
            number=2,
            title="Issue with status-04",
            body="Body 2",
            state="open",
            labels=["status-04:plan-review"],
            assignees=[],
            user="user2",
            created_at="2024-01-02T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/owner/repo/issues/2",
            locked=False,
        ),
        IssueData(
            number=3,
            title="Issue with status-02",
            body="Body 3",
            state="open",
            labels=["status-02:awaiting-planning", "enhancement"],
            assignees=[],
            user="user3",
            created_at="2024-01-03T00:00:00",
            updated_at="2024-01-03T00:00:00",
            url="https://github.com/owner/repo/issues/3",
            locked=False,
        ),
        IssueData(
            number=4,
            title="Issue with status-06",
            body="Body 4",
            state="open",
            labels=["status-06:implementing"],
            assignees=[],
            user="user4",
            created_at="2024-01-04T00:00:00",
            updated_at="2024-01-04T00:00:00",
            url="https://github.com/owner/repo/issues/4",
            locked=False,
        ),
        IssueData(
            number=5,
            title="Issue without status label",
            body="Body 5",
            state="open",
            labels=["bug", "enhancement"],
            assignees=[],
            user="user5",
            created_at="2024-01-05T00:00:00",
            updated_at="2024-01-05T00:00:00",
            url="https://github.com/owner/repo/issues/5",
            locked=False,
        ),
        IssueData(
            number=6,
            title="Issue with multiple status labels",
            body="Body 6",
            state="open",
            labels=["status-01:created", "status-04:plan-review"],
            assignees=[],
            user="user6",
            created_at="2024-01-06T00:00:00",
            updated_at="2024-01-06T00:00:00",
            url="https://github.com/owner/repo/issues/6",
            locked=False,
        ),
    ]


# Configuration Tests
def test_load_labels_config_valid(test_labels_config: dict[str, Any]) -> None:
    """Test loading valid labels configuration."""
    assert "workflow_labels" in test_labels_config
    assert isinstance(test_labels_config["workflow_labels"], list)
    assert len(test_labels_config["workflow_labels"]) == 4


def test_load_labels_config_with_ignore_labels(
    test_labels_config: dict[str, Any],
) -> None:
    """Test loading configuration with ignore_labels field."""
    assert "ignore_labels" in test_labels_config
    assert isinstance(test_labels_config["ignore_labels"], list)


# Validation Tests
def test_validate_issue_labels_single_valid(sample_issue: IssueData) -> None:
    """Test validation with single valid status label."""
    valid_labels = {"status-01:created", "status-02:awaiting-planning"}
    is_valid, error_type = validate_issue_labels(sample_issue, valid_labels)
    assert is_valid is True
    assert error_type == ""


def test_validate_issue_labels_no_status() -> None:
    """Test validation with no status label."""
    issue = IssueData(
        number=1,
        title="Test",
        body="",
        state="open",
        labels=["bug", "enhancement"],
        assignees=[],
        user="user",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        url="https://github.com/owner/repo/issues/1",
        locked=False,
    )
    valid_labels = {"status-01:created", "status-02:awaiting-planning"}
    is_valid, error_type = validate_issue_labels(issue, valid_labels)
    assert is_valid is False
    assert error_type == "no_status"


def test_validate_issue_labels_multiple_status() -> None:
    """Test validation with multiple status labels."""
    issue = IssueData(
        number=1,
        title="Test",
        body="",
        state="open",
        labels=["status-01:created", "status-02:awaiting-planning", "bug"],
        assignees=[],
        user="user",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        url="https://github.com/owner/repo/issues/1",
        locked=False,
    )
    valid_labels = {"status-01:created", "status-02:awaiting-planning"}
    is_valid, error_type = validate_issue_labels(issue, valid_labels)
    assert is_valid is False
    assert error_type == "multiple_status"


# Filtering Tests
def test_filter_ignored_issues_no_ignore_list(sample_issues: list[IssueData]) -> None:
    """Test filtering with empty ignore list returns all issues."""
    filtered = filter_ignored_issues(sample_issues, [])
    assert len(filtered) == len(sample_issues)
    assert filtered == sample_issues


def test_filter_ignored_issues_with_ignored_labels(
    sample_issues: list[IssueData],
) -> None:
    """Test filtering with ignored labels."""
    # Filter out issues with 'bug' label
    filtered = filter_ignored_issues(sample_issues, ["bug"])
    # Issues 1 and 5 have 'bug' label, so should be filtered out
    assert len(filtered) == 4
    assert all(issue["number"] not in [1, 5] for issue in filtered)


def test_filter_ignored_issues_labels_with_spaces() -> None:
    """Test filtering with labels containing spaces."""
    issues = [
        IssueData(
            number=1,
            title="Test 1",
            body="",
            state="open",
            labels=["on hold", "status-01:created"],
            assignees=[],
            user="user",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            url="https://github.com/owner/repo/issues/1",
            locked=False,
        ),
        IssueData(
            number=2,
            title="Test 2",
            body="",
            state="open",
            labels=["status-02:awaiting-planning"],
            assignees=[],
            user="user",
            created_at="2024-01-02T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/owner/repo/issues/2",
            locked=False,
        ),
    ]
    filtered = filter_ignored_issues(issues, ["on hold"])
    assert len(filtered) == 1
    assert filtered[0]["number"] == 2


# Grouping Tests
def test_group_issues_by_category_empty_list(
    test_labels_config: dict[str, Any],
) -> None:
    """Test grouping with empty issue list."""
    grouped = group_issues_by_category([], test_labels_config)

    # Check structure exists
    assert "human_action" in grouped
    assert "bot_pickup" in grouped
    assert "bot_busy" in grouped
    assert "errors" in grouped

    # Check all categories are empty
    assert len(grouped["errors"]["no_status"]) == 0
    assert len(grouped["errors"]["multiple_status"]) == 0


def test_group_issues_by_category_all_valid(
    sample_issues: list[IssueData], test_labels_config: dict[str, Any]
) -> None:
    """Test grouping with all valid issues."""
    # Use only valid issues (exclude #5 and #6)
    valid_issues = [issue for issue in sample_issues if issue["number"] in [1, 2, 3, 4]]
    grouped = group_issues_by_category(valid_issues, test_labels_config)

    # Check human_action category
    assert len(grouped["human_action"]["status-01:created"]) == 1
    assert grouped["human_action"]["status-01:created"][0]["number"] == 1
    assert len(grouped["human_action"]["status-04:plan-review"]) == 1
    assert grouped["human_action"]["status-04:plan-review"][0]["number"] == 2

    # Check bot_pickup category
    assert len(grouped["bot_pickup"]["status-02:awaiting-planning"]) == 1
    assert grouped["bot_pickup"]["status-02:awaiting-planning"][0]["number"] == 3

    # Check bot_busy category
    assert len(grouped["bot_busy"]["status-06:implementing"]) == 1
    assert grouped["bot_busy"]["status-06:implementing"][0]["number"] == 4

    # Check no errors
    assert len(grouped["errors"]["no_status"]) == 0
    assert len(grouped["errors"]["multiple_status"]) == 0


def test_group_issues_by_category_with_errors(
    sample_issues: list[IssueData], test_labels_config: dict[str, Any]
) -> None:
    """Test grouping with validation errors."""
    grouped = group_issues_by_category(sample_issues, test_labels_config)

    # Check error categories
    assert len(grouped["errors"]["no_status"]) == 1
    assert grouped["errors"]["no_status"][0]["number"] == 5

    assert len(grouped["errors"]["multiple_status"]) == 1
    assert grouped["errors"]["multiple_status"][0]["number"] == 6


def test_group_issues_by_category_zero_counts_included(
    test_labels_config: dict[str, Any],
) -> None:
    """Test that labels with zero issues are included in the structure."""
    # Create only one issue
    issues = [
        IssueData(
            number=1,
            title="Test",
            body="",
            state="open",
            labels=["status-01:created"],
            assignees=[],
            user="user",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            url="https://github.com/owner/repo/issues/1",
            locked=False,
        )
    ]

    grouped = group_issues_by_category(issues, test_labels_config)

    # All labels should exist in structure, even with zero counts
    assert "status-01:created" in grouped["human_action"]
    assert "status-04:plan-review" in grouped["human_action"]
    assert "status-02:awaiting-planning" in grouped["bot_pickup"]
    assert "status-06:implementing" in grouped["bot_busy"]

    # Only status-01 should have issues
    assert len(grouped["human_action"]["status-01:created"]) == 1
    assert len(grouped["human_action"]["status-04:plan-review"]) == 0
    assert len(grouped["bot_pickup"]["status-02:awaiting-planning"]) == 0
    assert len(grouped["bot_busy"]["status-06:implementing"]) == 0


# Formatting Tests
def test_format_issue_line_normal(sample_issue: IssueData) -> None:
    """Test formatting issue line with normal title."""
    repo_url = "https://github.com/owner/repo"
    line = format_issue_line(sample_issue, repo_url)

    assert line.startswith("    - #123:")
    assert "Test issue" in line
    assert "(https://github.com/owner/repo/issues/123)" in line


def test_format_issue_line_long_title() -> None:
    """Test formatting issue line with long title that needs truncation."""
    issue = IssueData(
        number=456,
        title="A" * 100,  # Very long title
        body="",
        state="open",
        labels=["status-01:created"],
        assignees=[],
        user="user",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00",
        url="https://github.com/owner/repo/issues/456",
        locked=False,
    )
    repo_url = "https://github.com/owner/repo"
    line = format_issue_line(issue, repo_url, max_title_length=80)

    # Title should be truncated to 80 chars (including "...")
    assert "..." in line
    # Check that the title part is no longer than 80 characters
    title_part = line.split("(https://")[0].split(": ", 1)[1].strip()
    assert len(title_part) <= 80


def test_truncate_title_short() -> None:
    """Test truncate_title with short title."""
    title = "Short title"
    result = truncate_title(title, max_length=80)
    assert result == title
    assert "..." not in result


def test_truncate_title_long() -> None:
    """Test truncate_title with long title."""
    title = "A" * 100
    result = truncate_title(title, max_length=80)
    assert len(result) == 80
    assert result.endswith("...")
    assert result.startswith("A" * 77)


def test_truncate_title_exact_length() -> None:
    """Test truncate_title with title exactly at max length."""
    title = "A" * 80
    result = truncate_title(title, max_length=80)
    assert result == title
    assert "..." not in result


# Display Tests
def test_display_statistics_summary_mode(
    sample_issues: list[IssueData],
    test_labels_config: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test display_statistics in summary mode (no details)."""
    grouped = group_issues_by_category(sample_issues, test_labels_config)
    repo_url = "https://github.com/owner/repo"

    display_statistics(
        grouped, test_labels_config, repo_url, filter_category="all", show_details=False
    )

    captured = capsys.readouterr()
    output = captured.out

    # Check section headers are present
    assert "=== Human Action Required ===" in output
    assert "=== Bot Should Pickup ===" in output
    assert "=== Bot Busy ===" in output
    assert "=== Validation Errors ===" in output

    # Check counts are displayed
    assert "status-01:created" in output
    assert "status-04:plan-review" in output
    assert "status-02:awaiting-planning" in output
    assert "status-06:implementing" in output

    # Check that issue URLs are NOT displayed (summary mode)
    assert "https://github.com/owner/repo/issues/1" not in output
    assert "https://github.com/owner/repo/issues/2" not in output

    # Check totals
    assert "Total:" in output
    assert "6 open issues" in output


def test_display_statistics_details_mode_with_errors(
    sample_issues: list[IssueData],
    test_labels_config: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test display_statistics in details mode with validation errors."""
    grouped = group_issues_by_category(sample_issues, test_labels_config)
    repo_url = "https://github.com/owner/repo"

    display_statistics(
        grouped, test_labels_config, repo_url, filter_category="all", show_details=True
    )

    captured = capsys.readouterr()
    output = captured.out

    # Check that issue URLs ARE displayed (details mode)
    assert "https://github.com/owner/repo/issues/1" in output
    assert "https://github.com/owner/repo/issues/2" in output

    # Check that error issues are displayed with details
    assert "#5:" in output  # Issue without status
    assert "#6:" in output  # Issue with multiple status
    assert "https://github.com/owner/repo/issues/5" in output
    assert "https://github.com/owner/repo/issues/6" in output

    # Check issue titles are displayed
    assert "Issue with status-01" in output
    assert "Issue without status label" in output


def test_display_statistics_filter_human(
    sample_issues: list[IssueData],
    test_labels_config: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test display_statistics with human filter."""
    grouped = group_issues_by_category(sample_issues, test_labels_config)
    repo_url = "https://github.com/owner/repo"

    display_statistics(
        grouped,
        test_labels_config,
        repo_url,
        filter_category="human",
        show_details=False,
    )

    captured = capsys.readouterr()
    output = captured.out

    # Check only human_action section is displayed
    assert "=== Human Action Required ===" in output
    assert "=== Bot Should Pickup ===" not in output
    assert "=== Bot Busy ===" not in output

    # Validation errors should still be displayed
    assert "=== Validation Errors ===" in output


def test_display_statistics_filter_bot(
    sample_issues: list[IssueData],
    test_labels_config: dict[str, Any],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Test display_statistics with bot filter."""
    grouped = group_issues_by_category(sample_issues, test_labels_config)
    repo_url = "https://github.com/owner/repo"

    display_statistics(
        grouped, test_labels_config, repo_url, filter_category="bot", show_details=False
    )

    captured = capsys.readouterr()
    output = captured.out

    # Check only bot sections are displayed
    assert "=== Human Action Required ===" not in output
    assert "=== Bot Should Pickup ===" in output
    assert "=== Bot Busy ===" in output

    # Validation errors should still be displayed
    assert "=== Validation Errors ===" in output


# Integration Tests
def test_ignore_labels_integration_with_filtering() -> None:
    """Test end-to-end integration of ignore_labels from CLI arguments.

    This test simulates the complete flow from parsing CLI arguments (as the
    batch launcher would provide them) through to filtering issues, verifying
    that the --ignore-labels flag works correctly end-to-end.
    """
    # Create test issues with various labels
    issues = [
        IssueData(
            number=1,
            title="Active issue",
            body="",
            state="open",
            labels=["status-01:created", "bug"],
            assignees=[],
            user="user1",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            url="https://github.com/owner/repo/issues/1",
            locked=False,
        ),
        IssueData(
            number=2,
            title="Won't fix issue",
            body="",
            state="open",
            labels=["status-02:awaiting-planning", "wontfix"],
            assignees=[],
            user="user2",
            created_at="2024-01-02T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/owner/repo/issues/2",
            locked=False,
        ),
        IssueData(
            number=3,
            title="On hold issue",
            body="",
            state="open",
            labels=["status-04:plan-review", "on hold"],
            assignees=[],
            user="user3",
            created_at="2024-01-03T00:00:00",
            updated_at="2024-01-03T00:00:00",
            url="https://github.com/owner/repo/issues/3",
            locked=False,
        ),
    ]

    # Simulate CLI arguments: --ignore-labels "wontfix" --ignore-labels "on hold"
    ignore_labels_from_cli = ["wontfix", "on hold"]

    # Apply filtering (simulating what main() does)
    filtered_issues = filter_ignored_issues(issues, ignore_labels_from_cli)

    # Verify only the active issue remains
    assert len(filtered_issues) == 1
    assert filtered_issues[0]["number"] == 1
    assert filtered_issues[0]["title"] == "Active issue"


def test_ignore_labels_with_labels_containing_special_characters() -> None:
    """Test --ignore-labels works with labels containing special characters.

    GitHub labels can contain various special characters including colons,
    dashes, spaces, etc. This test ensures the batch launcher and Python
    script handle these correctly.
    """
    issues = [
        IssueData(
            number=1,
            title="Issue 1",
            body="",
            state="open",
            labels=["status-01:created", "type:bug-fix"],
            assignees=[],
            user="user1",
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            url="https://github.com/owner/repo/issues/1",
            locked=False,
        ),
        IssueData(
            number=2,
            title="Issue 2",
            body="",
            state="open",
            labels=["status-02:awaiting-planning", "priority: low"],
            assignees=[],
            user="user2",
            created_at="2024-01-02T00:00:00",
            updated_at="2024-01-02T00:00:00",
            url="https://github.com/owner/repo/issues/2",
            locked=False,
        ),
    ]

    # Test filtering with labels containing special characters
    filtered = filter_ignored_issues(issues, ["type:bug-fix"])
    assert len(filtered) == 1
    assert filtered[0]["number"] == 2

    filtered = filter_ignored_issues(issues, ["priority: low"])
    assert len(filtered) == 1
    assert filtered[0]["number"] == 1
