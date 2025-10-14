"""
Unit tests for workflows/validate_labels.py module.

Tests cover argument parsing, STALE_TIMEOUTS constant, and basic setup logic.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, cast
from unittest.mock import MagicMock, Mock

import pytest

from mcp_coder.utils.github_operations.issue_manager import EventData, IssueData
from workflows.validate_labels import (
    STALE_TIMEOUTS,
    build_label_lookups,
    calculate_elapsed_minutes,
    check_stale_bot_process,
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


def test_check_stale_bot_process_at_exact_timeout_threshold() -> None:
    """Test bot process at exact timeout threshold (should not be stale)."""
    # Create issue data
    issue_dict: dict[str, Any] = {
        "number": 700,
        "title": "Test issue",
        "labels": ["status-03:planning"],
    }

    # Create event from exactly 15 minutes ago (at threshold, not over)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=15)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    events: list[EventData] = [
        cast(
            EventData,
            {
                "event": "labeled",
                "label": "status-03:planning",
                "created_at": timestamp_str,
                "actor": "testuser",
            },
        )
    ]

    # Create mock issue_manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(return_value=events)

    # Call function
    is_stale, elapsed = check_stale_bot_process(
        cast(IssueData, issue_dict), "status-03:planning", "planning", mock_manager
    )

    # At exact threshold, should NOT be stale (uses > not >=)
    assert is_stale is False
    assert elapsed is not None
    assert 14 <= elapsed <= 16  # Allow ±1 minute for test execution


def test_check_stale_bot_process_not_stale() -> None:
    """Test bot process within timeout."""
    # Create issue data
    issue_dict: dict[str, Any] = {
        "number": 123,
        "title": "Test issue",
        "labels": ["status-03:planning"],
    }

    # Create event from 10 minutes ago (within 15 minute planning timeout)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    # Create mock events
    events: list[EventData] = [
        cast(
            EventData,
            {
                "event": "labeled",
                "label": "status-03:planning",
                "created_at": timestamp_str,
                "actor": "testuser",
            },
        )
    ]

    # Create mock issue_manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(return_value=events)

    # Call function
    is_stale, elapsed = check_stale_bot_process(
        cast(IssueData, issue_dict), "status-03:planning", "planning", mock_manager
    )

    # Verify not stale (10 minutes < 15 minute timeout)
    assert is_stale is False
    assert elapsed is not None
    assert 9 <= elapsed <= 11  # Allow ±1 minute for test execution


def test_check_stale_bot_process_is_stale() -> None:
    """Test bot process exceeding timeout."""
    # Create issue data
    issue_dict: dict[str, Any] = {
        "number": 456,
        "title": "Test issue",
        "labels": ["status-03:planning"],
    }

    # Create event from 20 minutes ago (exceeds 15 minute planning timeout)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=20)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    # Create mock events
    events: list[EventData] = [
        cast(
            EventData,
            {
                "event": "labeled",
                "label": "status-03:planning",
                "created_at": timestamp_str,
                "actor": "testuser",
            },
        )
    ]

    # Create mock issue_manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(return_value=events)

    # Call function
    is_stale, elapsed = check_stale_bot_process(
        cast(IssueData, issue_dict), "status-03:planning", "planning", mock_manager
    )

    # Verify stale (20 minutes > 15 minute timeout)
    assert is_stale is True
    assert elapsed is not None
    assert 19 <= elapsed <= 21  # Allow ±1 minute for test execution


def test_check_stale_bot_process_no_events() -> None:
    """Test when no label events found."""
    # Create issue data
    issue_dict: dict[str, Any] = {
        "number": 789,
        "title": "Test issue",
        "labels": ["status-03:planning"],
    }

    # Create mock with no events
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(return_value=[])

    # Call function
    is_stale, elapsed = check_stale_bot_process(
        cast(IssueData, issue_dict), "status-03:planning", "planning", mock_manager
    )

    # Verify returns (False, None) when no events found
    assert is_stale is False
    assert elapsed is None


def test_check_stale_bot_process_no_matching_label_events() -> None:
    """Test when events exist but none match the target label."""
    # Create issue data
    issue_dict: dict[str, Any] = {
        "number": 100,
        "title": "Test issue",
        "labels": ["status-03:planning"],
    }

    # Create events for different labels
    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    events: list[EventData] = [
        cast(
            EventData,
            {
                "event": "labeled",
                "label": "status-01:created",  # Different label
                "created_at": timestamp_str,
                "actor": "testuser",
            },
        ),
        cast(
            EventData,
            {
                "event": "labeled",
                "label": "bug",  # Different label
                "created_at": timestamp_str,
                "actor": "testuser",
            },
        ),
    ]

    # Create mock issue_manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(return_value=events)

    # Call function
    is_stale, elapsed = check_stale_bot_process(
        cast(IssueData, issue_dict), "status-03:planning", "planning", mock_manager
    )

    # Verify returns (False, None) when no matching label events
    assert is_stale is False
    assert elapsed is None


def test_check_stale_bot_process_no_timeout_defined() -> None:
    """Test when internal_id has no timeout threshold defined."""
    # Create issue data
    issue_dict: dict[str, Any] = {
        "number": 200,
        "title": "Test issue",
        "labels": ["status-01:created"],
    }

    # Create mock issue_manager (should not be called)
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock()

    # Call function with internal_id that has no timeout
    is_stale, elapsed = check_stale_bot_process(
        cast(IssueData, issue_dict), "status-01:created", "created", mock_manager
    )

    # Verify returns (False, None) when no timeout defined
    assert is_stale is False
    assert elapsed is None
    # Verify get_issue_events was NOT called
    mock_manager.get_issue_events.assert_not_called()


def test_check_stale_bot_process_multiple_labeled_events() -> None:
    """Test with multiple labeled events, should use most recent."""
    # Create issue data
    issue_dict: dict[str, Any] = {
        "number": 300,
        "title": "Test issue",
        "labels": ["status-03:planning"],
    }

    # Create multiple events at different times
    older_time = datetime.now(timezone.utc) - timedelta(minutes=25)
    recent_time = datetime.now(timezone.utc) - timedelta(minutes=10)

    older_timestamp = older_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    recent_timestamp = recent_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    events: list[EventData] = [
        cast(
            EventData,
            {
                "event": "labeled",
                "label": "status-03:planning",
                "created_at": older_timestamp,  # 25 minutes ago
                "actor": "testuser",
            },
        ),
        cast(
            EventData,
            {
                "event": "labeled",
                "label": "status-03:planning",
                "created_at": recent_timestamp,  # 10 minutes ago (most recent)
                "actor": "testuser",
            },
        ),
    ]

    # Create mock issue_manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(return_value=events)

    # Call function
    is_stale, elapsed = check_stale_bot_process(
        cast(IssueData, issue_dict), "status-03:planning", "planning", mock_manager
    )

    # Should use most recent event (10 minutes), not older one (25 minutes)
    assert is_stale is False  # 10 minutes < 15 minute timeout
    assert elapsed is not None
    assert 9 <= elapsed <= 11  # Should be ~10 minutes, not ~25


def test_check_stale_bot_process_implementing_timeout() -> None:
    """Test implementing label with 60 minute timeout."""
    # Create issue data
    issue_dict: dict[str, Any] = {
        "number": 400,
        "title": "Test issue",
        "labels": ["status-06:implementing"],
    }

    # Create event from 70 minutes ago (exceeds 60 minute implementing timeout)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=70)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    events: list[EventData] = [
        cast(
            EventData,
            {
                "event": "labeled",
                "label": "status-06:implementing",
                "created_at": timestamp_str,
                "actor": "testuser",
            },
        )
    ]

    # Create mock issue_manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(return_value=events)

    # Call function
    is_stale, elapsed = check_stale_bot_process(
        cast(IssueData, issue_dict),
        "status-06:implementing",
        "implementing",
        mock_manager,
    )

    # Verify stale (70 minutes > 60 minute timeout)
    assert is_stale is True
    assert elapsed is not None
    assert 69 <= elapsed <= 71  # Allow ±1 minute for test execution


def test_check_stale_bot_process_pr_creating_timeout() -> None:
    """Test pr_creating label with 15 minute timeout."""
    # Create issue data
    issue_dict: dict[str, Any] = {
        "number": 500,
        "title": "Test issue",
        "labels": ["status-08:pr_creating"],
    }

    # Create event from 5 minutes ago (within 15 minute pr_creating timeout)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=5)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    events: list[EventData] = [
        cast(
            EventData,
            {
                "event": "labeled",
                "label": "status-08:pr_creating",
                "created_at": timestamp_str,
                "actor": "testuser",
            },
        )
    ]

    # Create mock issue_manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(return_value=events)

    # Call function
    is_stale, elapsed = check_stale_bot_process(
        cast(IssueData, issue_dict),
        "status-08:pr_creating",
        "pr_creating",
        mock_manager,
    )

    # Verify not stale (5 minutes < 15 minute timeout)
    assert is_stale is False
    assert elapsed is not None
    assert 4 <= elapsed <= 6  # Allow ±1 minute for test execution


def test_check_stale_bot_process_filters_unlabeled_events() -> None:
    """Test that unlabeled events are filtered out."""
    # Create issue data
    issue_dict: dict[str, Any] = {
        "number": 600,
        "title": "Test issue",
        "labels": ["status-03:planning"],
    }

    # Create mixed labeled/unlabeled events
    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    events: list[EventData] = [
        cast(
            EventData,
            {
                "event": "unlabeled",  # Should be filtered out
                "label": "status-03:planning",
                "created_at": timestamp_str,
                "actor": "testuser",
            },
        ),
        cast(
            EventData,
            {
                "event": "closed",  # Should be filtered out
                "label": None,
                "created_at": timestamp_str,
                "actor": "testuser",
            },
        ),
    ]

    # Create mock issue_manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(return_value=events)

    # Call function
    is_stale, elapsed = check_stale_bot_process(
        cast(IssueData, issue_dict), "status-03:planning", "planning", mock_manager
    )

    # Should return (False, None) since no "labeled" events found
    assert is_stale is False
    assert elapsed is None


def test_process_issues_empty_list() -> None:
    """Test process_issues with empty issue list."""
    from workflows.validate_labels import process_issues

    # Create minimal config
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "created",
                "name": "status-01:created",
                "category": "human_action",
            }
        ],
        "ignore_labels": [],
    }

    # Create mock issue manager
    mock_manager = Mock()

    # Process empty list
    results = process_issues([], labels_config, mock_manager, dry_run=False)

    # Should have zero counts
    assert results["processed"] == 0
    assert results["skipped"] == 0
    assert len(results["initialized"]) == 0
    assert len(results["errors"]) == 0
    assert len(results["warnings"]) == 0
    assert len(results["ok"]) == 0


def test_process_issues_single_issue_needs_initialization() -> None:
    """Test process_issues with issue needing initialization."""
    from workflows.validate_labels import process_issues

    # Create config
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "created",
                "name": "status-01:created",
                "category": "human_action",
            }
        ],
        "ignore_labels": [],
    }

    # Create issue with no workflow labels
    issues: list[IssueData] = [
        cast(
            IssueData,
            {"number": 123, "title": "Test issue", "labels": ["bug", "enhancement"]},
        )
    ]

    # Create mock issue manager
    mock_manager = Mock()
    mock_manager.add_labels = Mock()

    # Process issues (not dry-run)
    results = process_issues(issues, labels_config, mock_manager, dry_run=False)

    # Verify results
    assert results["processed"] == 1
    assert results["skipped"] == 0
    assert results["initialized"] == [123]
    assert len(results["errors"]) == 0
    assert len(results["warnings"]) == 0
    assert len(results["ok"]) == 0

    # Verify add_labels was called
    mock_manager.add_labels.assert_called_once_with(123, ["status-01:created"])


def test_process_issues_dry_run_mode() -> None:
    """Test process_issues in dry-run mode doesn't make changes."""
    from workflows.validate_labels import process_issues

    # Create config
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "created",
                "name": "status-01:created",
                "category": "human_action",
            }
        ],
        "ignore_labels": [],
    }

    # Create issue with no workflow labels
    issues: list[IssueData] = [
        cast(IssueData, {"number": 456, "title": "Test issue", "labels": ["bug"]})
    ]

    # Create mock issue manager
    mock_manager = Mock()
    mock_manager.add_labels = Mock()

    # Process issues in dry-run mode
    results = process_issues(issues, labels_config, mock_manager, dry_run=True)

    # Verify results
    assert results["processed"] == 1
    assert results["initialized"] == [456]

    # Verify add_labels was NOT called
    mock_manager.add_labels.assert_not_called()


def test_process_issues_with_ignore_labels() -> None:
    """Test process_issues filters issues with ignore labels."""
    from workflows.validate_labels import process_issues

    # Create config with ignore labels
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "created",
                "name": "status-01:created",
                "category": "human_action",
            }
        ],
        "ignore_labels": ["wontfix", "duplicate"],
    }

    # Create issues, some with ignore labels
    issues: list[IssueData] = [
        cast(
            IssueData, {"number": 1, "title": "Issue 1", "labels": ["bug", "wontfix"]}
        ),
        cast(IssueData, {"number": 2, "title": "Issue 2", "labels": ["duplicate"]}),
        cast(IssueData, {"number": 3, "title": "Issue 3", "labels": ["bug"]}),
    ]

    # Create mock issue manager
    mock_manager = Mock()
    mock_manager.add_labels = Mock()

    # Process issues
    results = process_issues(issues, labels_config, mock_manager, dry_run=False)

    # Verify only issue 3 was processed
    assert results["processed"] == 1
    assert results["skipped"] == 2
    assert results["initialized"] == [3]

    # Verify add_labels was called only once for issue 3
    mock_manager.add_labels.assert_called_once_with(3, ["status-01:created"])


def test_process_issues_with_multiple_status_labels() -> None:
    """Test process_issues detects issues with multiple status labels (error)."""
    from workflows.validate_labels import process_issues

    # Create config
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "created",
                "name": "status-01:created",
                "category": "human_action",
            },
            {
                "internal_id": "planning",
                "name": "status-03:planning",
                "category": "bot_busy",
            },
        ],
        "ignore_labels": [],
    }

    # Create issue with multiple status labels
    issues: list[IssueData] = [
        cast(
            IssueData,
            {
                "number": 789,
                "title": "Test issue",
                "labels": ["bug", "status-01:created", "status-03:planning"],
            },
        )
    ]

    # Create mock issue manager
    mock_manager = Mock()

    # Process issues
    results = process_issues(issues, labels_config, mock_manager, dry_run=False)

    # Verify error detected
    assert results["processed"] == 1
    assert len(results["errors"]) == 1
    assert results["errors"][0]["issue"] == 789
    assert "status-01:created" in results["errors"][0]["labels"]
    assert "status-03:planning" in results["errors"][0]["labels"]


def test_process_issues_with_ok_status() -> None:
    """Test process_issues with issue that's OK (human_action label)."""
    from workflows.validate_labels import process_issues

    # Create config
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "created",
                "name": "status-01:created",
                "category": "human_action",
            }
        ],
        "ignore_labels": [],
    }

    # Create issue with one human_action label
    issues: list[IssueData] = [
        cast(
            IssueData,
            {
                "number": 100,
                "title": "Test issue",
                "labels": ["bug", "status-01:created"],
            },
        )
    ]

    # Create mock issue manager
    mock_manager = Mock()

    # Process issues
    results = process_issues(issues, labels_config, mock_manager, dry_run=False)

    # Verify issue marked as OK
    assert results["processed"] == 1
    assert results["ok"] == [100]
    assert len(results["errors"]) == 0
    assert len(results["warnings"]) == 0


def test_process_issues_with_stale_bot_process() -> None:
    """Test process_issues detects stale bot_busy labels (warning)."""
    from workflows.validate_labels import process_issues

    # Create config
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "planning",
                "name": "status-03:planning",
                "category": "bot_busy",
            }
        ],
        "ignore_labels": [],
    }

    # Create issue with bot_busy label
    issues: list[IssueData] = [
        cast(
            IssueData,
            {
                "number": 200,
                "title": "Test issue",
                "labels": ["status-03:planning"],
            },
        )
    ]

    # Create event from 20 minutes ago (exceeds 15 minute planning timeout)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=20)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    events: list[EventData] = [
        cast(
            EventData,
            {
                "event": "labeled",
                "label": "status-03:planning",
                "created_at": timestamp_str,
                "actor": "testuser",
            },
        )
    ]

    # Create mock issue manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(return_value=events)

    # Process issues
    results = process_issues(issues, labels_config, mock_manager, dry_run=False)

    # Verify warning generated
    assert results["processed"] == 1
    assert len(results["warnings"]) == 1
    assert results["warnings"][0]["issue"] == 200
    assert results["warnings"][0]["label"] == "status-03:planning"
    assert 19 <= results["warnings"][0]["elapsed"] <= 21

    # Verify get_issue_events was called
    mock_manager.get_issue_events.assert_called_once_with(200)


def test_process_issues_with_not_stale_bot_process() -> None:
    """Test process_issues with bot_busy label within timeout (OK)."""
    from workflows.validate_labels import process_issues

    # Create config
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "planning",
                "name": "status-03:planning",
                "category": "bot_busy",
            }
        ],
        "ignore_labels": [],
    }

    # Create issue with bot_busy label
    issues: list[IssueData] = [
        cast(
            IssueData,
            {
                "number": 300,
                "title": "Test issue",
                "labels": ["status-03:planning"],
            },
        )
    ]

    # Create event from 10 minutes ago (within 15 minute planning timeout)
    past_time = datetime.now(timezone.utc) - timedelta(minutes=10)
    timestamp_str = past_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    events: list[EventData] = [
        cast(
            EventData,
            {
                "event": "labeled",
                "label": "status-03:planning",
                "created_at": timestamp_str,
                "actor": "testuser",
            },
        )
    ]

    # Create mock issue manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(return_value=events)

    # Process issues
    results = process_issues(issues, labels_config, mock_manager, dry_run=False)

    # Verify issue marked as OK
    assert results["processed"] == 1
    assert results["ok"] == [300]
    assert len(results["warnings"]) == 0

    # Verify get_issue_events was called
    mock_manager.get_issue_events.assert_called_once_with(300)


def test_process_issues_mixed_scenarios() -> None:
    """Test process_issues with multiple issues in various states."""
    from workflows.validate_labels import process_issues

    # Create comprehensive config
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "created",
                "name": "status-01:created",
                "category": "human_action",
            },
            {
                "internal_id": "planning",
                "name": "status-03:planning",
                "category": "bot_busy",
            },
            {
                "internal_id": "implementing",
                "name": "status-06:implementing",
                "category": "bot_busy",
            },
        ],
        "ignore_labels": ["wontfix"],
    }

    # Create various issues
    issues: list[IssueData] = [
        # Issue 1: Needs initialization
        cast(IssueData, {"number": 1, "title": "Issue 1", "labels": ["bug"]}),
        # Issue 2: Has ignore label
        cast(IssueData, {"number": 2, "title": "Issue 2", "labels": ["wontfix"]}),
        # Issue 3: Multiple status labels (error)
        cast(
            IssueData,
            {
                "number": 3,
                "title": "Issue 3",
                "labels": ["status-01:created", "status-03:planning"],
            },
        ),
        # Issue 4: OK with human_action label
        cast(
            IssueData,
            {"number": 4, "title": "Issue 4", "labels": ["status-01:created"]},
        ),
        # Issue 5: Stale bot process
        cast(
            IssueData,
            {"number": 5, "title": "Issue 5", "labels": ["status-03:planning"]},
        ),
        # Issue 6: Not stale bot process
        cast(
            IssueData,
            {"number": 6, "title": "Issue 6", "labels": ["status-06:implementing"]},
        ),
    ]

    # Create mock events for issues 5 and 6
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=20)  # Stale
    not_stale_time = datetime.now(timezone.utc) - timedelta(minutes=30)  # Not stale

    stale_timestamp = stale_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    not_stale_timestamp = not_stale_time.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    # Create mock issue manager
    mock_manager = Mock()
    mock_manager.add_labels = Mock()

    # Setup get_issue_events to return different events per issue
    def mock_get_events(issue_number: int) -> list[EventData]:
        if issue_number == 5:
            # Stale planning (20 minutes > 15 minute timeout)
            return [
                cast(
                    EventData,
                    {
                        "event": "labeled",
                        "label": "status-03:planning",
                        "created_at": stale_timestamp,
                        "actor": "testuser",
                    },
                )
            ]
        elif issue_number == 6:
            # Not stale implementing (30 minutes < 60 minute timeout)
            return [
                cast(
                    EventData,
                    {
                        "event": "labeled",
                        "label": "status-06:implementing",
                        "created_at": not_stale_timestamp,
                        "actor": "testuser",
                    },
                )
            ]
        return []

    mock_manager.get_issue_events = Mock(side_effect=mock_get_events)

    # Process issues in dry-run mode to avoid actual API calls
    results = process_issues(issues, labels_config, mock_manager, dry_run=True)

    # Verify results
    assert results["processed"] == 5  # All except ignored issue 2
    assert results["skipped"] == 1  # Issue 2
    assert results["initialized"] == [1]  # Issue 1
    assert len(results["errors"]) == 1  # Issue 3
    assert results["errors"][0]["issue"] == 3
    assert len(results["warnings"]) == 1  # Issue 5
    assert results["warnings"][0]["issue"] == 5
    assert 4 in results["ok"]  # Issue 4
    assert 6 in results["ok"]  # Issue 6

    # Verify add_labels was NOT called (dry-run mode)
    mock_manager.add_labels.assert_not_called()

    # Verify get_issue_events was called for issues 5 and 6 (bot_busy labels)
    assert mock_manager.get_issue_events.call_count == 2


def test_process_issues_with_bot_pickup_category() -> None:
    """Test process_issues with bot_pickup category label (treated as OK)."""
    from workflows.validate_labels import process_issues

    # Create config with bot_pickup label
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "pending_review",
                "name": "status-02:pending-review",
                "category": "bot_pickup",
            }
        ],
        "ignore_labels": [],
    }

    # Create issue with bot_pickup label
    issues: list[IssueData] = [
        cast(
            IssueData,
            {
                "number": 999,
                "title": "Test issue",
                "labels": ["status-02:pending-review"],
            },
        )
    ]

    # Create mock issue manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock()

    # Process issues
    results = process_issues(issues, labels_config, mock_manager, dry_run=False)

    # Verify issue marked as OK (bot_pickup doesn't need staleness check)
    assert results["processed"] == 1
    assert results["ok"] == [999]
    assert len(results["warnings"]) == 0
    assert len(results["errors"]) == 0

    # Verify get_issue_events was NOT called (no staleness check for bot_pickup)
    mock_manager.get_issue_events.assert_not_called()


def test_process_issues_api_exception_on_initialization() -> None:
    """Test process_issues propagates API exceptions during initialization."""
    from github import GithubException

    from workflows.validate_labels import process_issues

    # Create config
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "created",
                "name": "status-01:created",
                "category": "human_action",
            }
        ],
        "ignore_labels": [],
    }

    # Create issue needing initialization
    issues: list[IssueData] = [
        cast(IssueData, {"number": 111, "title": "Test issue", "labels": ["bug"]})
    ]

    # Create mock that raises GithubException
    mock_manager = Mock()
    mock_manager.add_labels = Mock(
        side_effect=GithubException(status=403, data={"message": "API rate limit"})
    )

    # Verify exception propagates
    with pytest.raises(GithubException) as exc_info:
        process_issues(issues, labels_config, mock_manager, dry_run=False)

    assert exc_info.value.status == 403


def test_process_issues_api_exception_on_stale_check() -> None:
    """Test process_issues propagates API exceptions during staleness check."""
    from github import GithubException

    from workflows.validate_labels import process_issues

    # Create config
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "planning",
                "name": "status-03:planning",
                "category": "bot_busy",
            }
        ],
        "ignore_labels": [],
    }

    # Create issue with bot_busy label
    issues: list[IssueData] = [
        cast(
            IssueData,
            {
                "number": 222,
                "title": "Test issue",
                "labels": ["status-03:planning"],
            },
        )
    ]

    # Create mock that raises GithubException on get_issue_events
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(
        side_effect=GithubException(status=500, data={"message": "Server error"})
    )

    # Verify exception propagates
    with pytest.raises(GithubException) as exc_info:
        process_issues(issues, labels_config, mock_manager, dry_run=False)

    assert exc_info.value.status == 500


def test_process_issues_mixed_ignore_label_positions() -> None:
    """Test that issues with ignore labels in any position are skipped."""
    from workflows.validate_labels import process_issues

    # Create config
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "created",
                "name": "status-01:created",
                "category": "human_action",
            }
        ],
        "ignore_labels": ["wontfix", "duplicate", "invalid"],
    }

    # Create issues with ignore labels in different positions
    issues: list[IssueData] = [
        # Ignore label at start
        cast(
            IssueData,
            {"number": 1, "title": "Issue 1", "labels": ["wontfix", "bug"]},
        ),
        # Ignore label in middle
        cast(
            IssueData,
            {
                "number": 2,
                "title": "Issue 2",
                "labels": ["bug", "duplicate", "enhancement"],
            },
        ),
        # Ignore label at end
        cast(
            IssueData,
            {"number": 3, "title": "Issue 3", "labels": ["bug", "invalid"]},
        ),
        # Multiple ignore labels
        cast(
            IssueData,
            {
                "number": 4,
                "title": "Issue 4",
                "labels": ["wontfix", "duplicate"],
            },
        ),
        # No ignore labels
        cast(
            IssueData,
            {"number": 5, "title": "Issue 5", "labels": ["bug"]},
        ),
    ]

    # Create mock issue manager
    mock_manager = Mock()
    mock_manager.add_labels = Mock()

    # Process issues
    results = process_issues(issues, labels_config, mock_manager, dry_run=False)

    # Verify only issue 5 was processed
    assert results["processed"] == 1
    assert results["skipped"] == 4
    assert results["initialized"] == [5]

    # Verify add_labels was called only for issue 5
    mock_manager.add_labels.assert_called_once_with(5, ["status-01:created"])


def test_process_issues_no_ignore_labels_in_config() -> None:
    """Test process_issues when config has no ignore_labels key."""
    from workflows.validate_labels import process_issues

    # Create config WITHOUT ignore_labels key
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "created",
                "name": "status-01:created",
                "category": "human_action",
            }
        ]
        # Note: no "ignore_labels" key
    }

    # Create issues with various labels
    issues: list[IssueData] = [
        cast(
            IssueData,
            {"number": 1, "title": "Issue 1", "labels": ["wontfix", "bug"]},
        ),
        cast(IssueData, {"number": 2, "title": "Issue 2", "labels": ["bug"]}),
    ]

    # Create mock issue manager
    mock_manager = Mock()
    mock_manager.add_labels = Mock()

    # Process issues
    results = process_issues(issues, labels_config, mock_manager, dry_run=False)

    # Both issues should be processed (no ignore labels defined)
    assert results["processed"] == 2
    assert results["skipped"] == 0
    assert 1 in results["initialized"]
    assert 2 in results["initialized"]


def test_process_issues_bot_busy_without_timeout() -> None:
    """Test process_issues with bot_busy label that has no timeout defined."""
    from workflows.validate_labels import process_issues

    # Create config with bot_busy label not in STALE_TIMEOUTS
    labels_config: dict[str, Any] = {
        "workflow_labels": [
            {
                "internal_id": "custom_busy",  # Not in STALE_TIMEOUTS
                "name": "status-99:custom-busy",
                "category": "bot_busy",
            }
        ],
        "ignore_labels": [],
    }

    # Create issue with this label
    issues: list[IssueData] = [
        cast(
            IssueData,
            {
                "number": 888,
                "title": "Test issue",
                "labels": ["status-99:custom-busy"],
            },
        )
    ]

    # Create mock issue manager
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock()  # Should not be called

    # Process issues
    results = process_issues(issues, labels_config, mock_manager, dry_run=False)

    # Should mark as OK since no timeout defined
    assert results["processed"] == 1
    assert results["ok"] == [888]
    assert len(results["warnings"]) == 0

    # get_issue_events should not be called (no timeout defined)
    mock_manager.get_issue_events.assert_not_called()


def test_check_stale_bot_process_with_api_exception() -> None:
    """Test check_stale_bot_process propagates API exceptions."""
    from github import GithubException

    # Create issue data
    issue_dict: dict[str, Any] = {
        "number": 777,
        "title": "Test issue",
        "labels": ["status-03:planning"],
    }

    # Create mock that raises exception
    mock_manager = Mock()
    mock_manager.get_issue_events = Mock(
        side_effect=GithubException(status=404, data={"message": "Not found"})
    )

    # Verify exception propagates (not caught)
    with pytest.raises(GithubException) as exc_info:
        check_stale_bot_process(
            cast(IssueData, issue_dict), "status-03:planning", "planning", mock_manager
        )

    assert exc_info.value.status == 404
