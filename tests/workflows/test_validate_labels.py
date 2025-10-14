"""
Unit tests for workflows/validate_labels.py module.

Tests cover argument parsing, STALE_TIMEOUTS constant, and basic setup logic.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, cast

import pytest

from mcp_coder.utils.github_operations.issue_manager import IssueData
from workflows.validate_labels import (
    STALE_TIMEOUTS,
    build_label_lookups,
    calculate_elapsed_minutes,
    check_status_labels,
    parse_arguments,
)


def test_stale_timeouts_defined() -> None:
    """Test that timeout constants are properly defined."""
    assert STALE_TIMEOUTS["implementing"] == 60
    assert STALE_TIMEOUTS["planning"] == 15
    assert STALE_TIMEOUTS["pr_creating"] == 15


def test_parse_arguments_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test argument parser with default values."""
    # Simulate command line with no arguments (just script name)
    monkeypatch.setattr("sys.argv", ["validate_labels.py"])

    args = parse_arguments()

    # Verify defaults
    assert args.project_dir is None
    assert args.log_level == "INFO"
    assert args.dry_run is False


def test_parse_arguments_with_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test --dry-run flag parsing."""
    # Simulate command line with --dry-run flag
    monkeypatch.setattr("sys.argv", ["validate_labels.py", "--dry-run"])

    args = parse_arguments()

    assert args.dry_run is True


def test_parse_arguments_with_project_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test --project-dir argument parsing."""
    test_path = "/path/to/project"
    monkeypatch.setattr("sys.argv", ["validate_labels.py", "--project-dir", test_path])

    args = parse_arguments()

    assert args.project_dir == test_path


def test_parse_arguments_with_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test --log-level argument parsing."""
    monkeypatch.setattr("sys.argv", ["validate_labels.py", "--log-level", "DEBUG"])

    args = parse_arguments()

    assert args.log_level == "DEBUG"


def test_parse_arguments_all_options(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test all command-line arguments together."""
    monkeypatch.setattr(
        "sys.argv",
        [
            "validate_labels.py",
            "--project-dir",
            "/test/path",
            "--log-level",
            "ERROR",
            "--dry-run",
        ],
    )

    args = parse_arguments()

    assert args.project_dir == "/test/path"
    assert args.log_level == "ERROR"
    assert args.dry_run is True


def test_calculate_elapsed_minutes_with_z_suffix() -> None:
    """Test calculate_elapsed_minutes with 'Z' suffix timestamp."""
    # Create a timestamp 30 minutes ago
    past_time = datetime.now(timezone.utc) - timedelta(minutes=30)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be approximately 30 minutes (allow ±1 minute for test execution time)
    assert 29 <= elapsed <= 31


def test_calculate_elapsed_minutes_without_z_suffix() -> None:
    """Test calculate_elapsed_minutes with UTC offset format."""
    # Create a timestamp 45 minutes ago
    past_time = datetime.now(timezone.utc) - timedelta(minutes=45)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "+00:00"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be approximately 45 minutes (allow ±1 minute for test execution time)
    assert 44 <= elapsed <= 46


def test_calculate_elapsed_minutes_recent_timestamp() -> None:
    """Test calculate_elapsed_minutes with very recent timestamp."""
    # Create a timestamp just a few seconds ago
    past_time = datetime.now(timezone.utc) - timedelta(seconds=30)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be 0 minutes (30 seconds rounds down to 0)
    assert elapsed == 0


def test_calculate_elapsed_minutes_one_hour_ago() -> None:
    """Test calculate_elapsed_minutes with timestamp one hour ago."""
    # Create a timestamp 60 minutes ago
    past_time = datetime.now(timezone.utc) - timedelta(minutes=60)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be approximately 60 minutes (allow ±1 minute for test execution time)
    assert 59 <= elapsed <= 61


def test_calculate_elapsed_minutes_multiple_hours() -> None:
    """Test calculate_elapsed_minutes with timestamp several hours ago."""
    # Create a timestamp 150 minutes (2.5 hours) ago
    past_time = datetime.now(timezone.utc) - timedelta(minutes=150)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be approximately 150 minutes (allow ±1 minute for test execution time)
    assert 149 <= elapsed <= 151


def test_calculate_elapsed_minutes_with_microseconds() -> None:
    """Test calculate_elapsed_minutes with timestamp containing microseconds."""
    # Create a timestamp 20 minutes ago with microseconds
    past_time = datetime.now(timezone.utc) - timedelta(minutes=20)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"

    elapsed = calculate_elapsed_minutes(timestamp_str)

    # Should be approximately 20 minutes (allow ±1 minute for test execution time)
    assert 19 <= elapsed <= 21


def test_build_label_lookups() -> None:
    """Test building lookup dictionaries from config."""
    # Create a minimal labels config for testing
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "created",
                "name": "status-01:created",
                "color": "10b981",
                "description": "Fresh issue",
                "category": "human_action",
            },
            {
                "internal_id": "planning",
                "name": "status-03:planning",
                "color": "a7f3d0",
                "description": "Planning in progress",
                "category": "bot_busy",
            },
            {
                "internal_id": "implementing",
                "name": "status-06:implementing",
                "color": "bfdbfe",
                "description": "Implementation in progress",
                "category": "bot_busy",
            },
        ]
    }

    result = build_label_lookups(labels_config)

    # Verify id_to_name mapping
    assert result["id_to_name"]["created"] == "status-01:created"
    assert result["id_to_name"]["planning"] == "status-03:planning"
    assert result["id_to_name"]["implementing"] == "status-06:implementing"
    assert len(result["id_to_name"]) == 3

    # Verify all_names set
    assert "status-01:created" in result["all_names"]
    assert "status-03:planning" in result["all_names"]
    assert "status-06:implementing" in result["all_names"]
    assert len(result["all_names"]) == 3

    # Verify name_to_category mapping
    assert result["name_to_category"]["status-01:created"] == "human_action"
    assert result["name_to_category"]["status-03:planning"] == "bot_busy"
    assert result["name_to_category"]["status-06:implementing"] == "bot_busy"
    assert len(result["name_to_category"]) == 3

    # Verify name_to_id mapping
    assert result["name_to_id"]["status-01:created"] == "created"
    assert result["name_to_id"]["status-03:planning"] == "planning"
    assert result["name_to_id"]["status-06:implementing"] == "implementing"
    assert len(result["name_to_id"]) == 3


def test_build_label_lookups_empty_config() -> None:
    """Test building lookups from empty config."""
    labels_config: dict[str, Any] = {"workflow_labels": []}

    result = build_label_lookups(labels_config)

    # All lookups should be empty
    assert len(result["id_to_name"]) == 0
    assert len(result["all_names"]) == 0
    assert len(result["name_to_category"]) == 0
    assert len(result["name_to_id"]) == 0


def test_build_label_lookups_single_label() -> None:
    """Test building lookups with single label."""
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "test_id",
                "name": "test-label",
                "color": "ffffff",
                "description": "Test label",
                "category": "test_category",
            }
        ]
    }

    result = build_label_lookups(labels_config)

    # Verify single label is properly mapped
    assert result["id_to_name"]["test_id"] == "test-label"
    assert "test-label" in result["all_names"]
    assert result["name_to_category"]["test-label"] == "test_category"
    assert result["name_to_id"]["test-label"] == "test_id"

    # Verify all lookups have exactly one entry
    assert len(result["id_to_name"]) == 1
    assert len(result["all_names"]) == 1
    assert len(result["name_to_category"]) == 1
    assert len(result["name_to_id"]) == 1


def test_build_label_lookups_all_categories() -> None:
    """Test building lookups with all category types."""
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "human1",
                "name": "human-action-label",
                "color": "ffffff",
                "description": "Human action",
                "category": "human_action",
            },
            {
                "internal_id": "pickup1",
                "name": "bot-pickup-label",
                "color": "eeeeee",
                "description": "Bot pickup",
                "category": "bot_pickup",
            },
            {
                "internal_id": "busy1",
                "name": "bot-busy-label",
                "color": "dddddd",
                "description": "Bot busy",
                "category": "bot_busy",
            },
        ]
    }

    result = build_label_lookups(labels_config)

    # Verify category mappings for all types
    assert result["name_to_category"]["human-action-label"] == "human_action"
    assert result["name_to_category"]["bot-pickup-label"] == "bot_pickup"
    assert result["name_to_category"]["bot-busy-label"] == "bot_busy"

    # Verify bidirectional mappings work
    assert result["id_to_name"]["human1"] == "human-action-label"
    assert result["name_to_id"]["human-action-label"] == "human1"

    assert result["id_to_name"]["pickup1"] == "bot-pickup-label"
    assert result["name_to_id"]["bot-pickup-label"] == "pickup1"

    assert result["id_to_name"]["busy1"] == "bot-busy-label"
    assert result["name_to_id"]["bot-busy-label"] == "busy1"


def test_check_status_labels_none() -> None:
    """Test issue with no status labels."""
    # Create issue with no workflow labels
    issue_dict: dict[str, Any] = {
        "number": 123,
        "title": "Test issue",
        "labels": ["bug", "enhancement"],  # Non-workflow labels
    }

    # Define workflow labels
    workflow_labels = {
        "status-01:created",
        "status-03:planning",
        "status-06:implementing",
    }

    count, labels = check_status_labels(cast(IssueData, issue_dict), workflow_labels)

    # Should have 0 workflow labels
    assert count == 0
    assert labels == []


def test_check_status_labels_one() -> None:
    """Test issue with one status label."""
    # Create issue with one workflow label
    issue_dict: dict[str, Any] = {
        "number": 456,
        "title": "Test issue",
        "labels": ["bug", "status-03:planning", "enhancement"],
    }

    # Define workflow labels
    workflow_labels = {
        "status-01:created",
        "status-03:planning",
        "status-06:implementing",
    }

    count, labels = check_status_labels(cast(IssueData, issue_dict), workflow_labels)

    # Should have 1 workflow label
    assert count == 1
    assert labels == ["status-03:planning"]


def test_check_status_labels_multiple() -> None:
    """Test issue with multiple status labels."""
    # Create issue with multiple workflow labels (error condition)
    issue_dict: dict[str, Any] = {
        "number": 789,
        "title": "Test issue",
        "labels": [
            "bug",
            "status-01:created",
            "status-03:planning",
            "enhancement",
        ],
    }

    # Define workflow labels
    workflow_labels = {
        "status-01:created",
        "status-03:planning",
        "status-06:implementing",
    }

    count, labels = check_status_labels(cast(IssueData, issue_dict), workflow_labels)

    # Should have 2 workflow labels (error condition)
    assert count == 2
    assert "status-01:created" in labels
    assert "status-03:planning" in labels
    assert len(labels) == 2


def test_check_status_labels_empty_issue_labels() -> None:
    """Test issue with no labels at all."""
    # Create issue with empty labels list
    issue_dict: dict[str, Any] = {
        "number": 100,
        "title": "Test issue",
        "labels": [],
    }

    # Define workflow labels
    workflow_labels = {"status-01:created", "status-03:planning"}

    count, labels = check_status_labels(cast(IssueData, issue_dict), workflow_labels)

    # Should have 0 workflow labels
    assert count == 0
    assert labels == []


def test_check_status_labels_all_workflow_labels() -> None:
    """Test issue with only workflow labels (no other labels)."""
    # Create issue with only workflow labels
    issue_dict: dict[str, Any] = {
        "number": 200,
        "title": "Test issue",
        "labels": ["status-06:implementing"],
    }

    # Define workflow labels
    workflow_labels = {
        "status-01:created",
        "status-03:planning",
        "status-06:implementing",
    }

    count, labels = check_status_labels(cast(IssueData, issue_dict), workflow_labels)

    # Should have 1 workflow label
    assert count == 1
    assert labels == ["status-06:implementing"]


def test_check_status_labels_three_or_more() -> None:
    """Test issue with three or more status labels (severe error condition)."""
    # Create issue with three workflow labels
    issue_dict: dict[str, Any] = {
        "number": 300,
        "title": "Test issue",
        "labels": [
            "status-01:created",
            "status-03:planning",
            "status-06:implementing",
            "bug",
        ],
    }

    # Define workflow labels
    workflow_labels = {
        "status-01:created",
        "status-03:planning",
        "status-06:implementing",
    }

    count, labels = check_status_labels(cast(IssueData, issue_dict), workflow_labels)

    # Should have 3 workflow labels
    assert count == 3
    assert "status-01:created" in labels
    assert "status-03:planning" in labels
    assert "status-06:implementing" in labels
    assert len(labels) == 3


def test_check_status_labels_preserves_order() -> None:
    """Test that check_status_labels preserves label order."""
    # Create issue with labels in specific order
    issue_dict: dict[str, Any] = {
        "number": 400,
        "title": "Test issue",
        "labels": [
            "bug",
            "status-06:implementing",
            "enhancement",
            "status-01:created",
        ],
    }

    # Define workflow labels
    workflow_labels = {
        "status-01:created",
        "status-03:planning",
        "status-06:implementing",
    }

    count, labels = check_status_labels(cast(IssueData, issue_dict), workflow_labels)

    # Should preserve order from issue labels
    assert count == 2
    assert labels == ["status-06:implementing", "status-01:created"]
