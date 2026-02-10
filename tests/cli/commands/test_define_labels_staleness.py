"""Tests for define_labels elapsed time and staleness detection.

Tests cover:
- Elapsed time calculations (calculate_elapsed_minutes function)
- Stale bot process detection (check_stale_bot_process function)
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from mcp_coder.cli.commands.define_labels import (
    calculate_elapsed_minutes,
    check_stale_bot_process,
)
from mcp_coder.utils.github_operations.issues import IssueData


class TestCalculateElapsedMinutes:
    """Test calculate_elapsed_minutes function."""

    def test_calculates_minutes_from_iso_timestamp(self) -> None:
        """Test that elapsed minutes are calculated correctly from ISO timestamp."""
        # Create a timestamp 30 minutes ago
        timestamp = datetime.now(timezone.utc) - timedelta(minutes=30)
        timestamp_str = timestamp.isoformat()

        result = calculate_elapsed_minutes(timestamp_str)

        # Allow 1 minute tolerance for test execution time
        assert 29 <= result <= 31

    def test_handles_z_suffix(self) -> None:
        """Test that Z suffix timestamps are handled correctly."""
        # Create a timestamp 60 minutes ago with Z suffix
        timestamp = datetime.now(timezone.utc) - timedelta(minutes=60)
        # Format with Z suffix instead of +00:00
        timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        result = calculate_elapsed_minutes(timestamp_str)

        # Allow 1 minute tolerance for test execution time
        assert 59 <= result <= 61

    def test_handles_timezone_offset(self) -> None:
        """Test that timezone offset in timestamps is handled correctly."""
        # Create a timestamp 15 minutes ago with explicit UTC offset
        timestamp = datetime.now(timezone.utc) - timedelta(minutes=15)
        timestamp_str = timestamp.isoformat()  # Will include +00:00

        result = calculate_elapsed_minutes(timestamp_str)

        # Allow 1 minute tolerance
        assert 14 <= result <= 16


class TestCheckStaleBotProcess:
    """Test check_stale_bot_process function."""

    def test_returns_false_when_under_threshold(self) -> None:
        """Test that returns False when elapsed time is under threshold."""
        issue: IssueData = {
            "number": 1,
            "title": "Test issue",
            "body": "",
            "state": "open",
            "labels": ["status-06:implementing"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }

        # Create event timestamp 10 minutes ago (under 120 min threshold)
        recent_timestamp = (
            datetime.now(timezone.utc) - timedelta(minutes=10)
        ).isoformat()

        mock_issue_manager = MagicMock()
        mock_issue_manager.get_issue_events.return_value = [
            {
                "event": "labeled",
                "label": "status-06:implementing",
                "created_at": recent_timestamp,
                "actor": "bot",
            }
        ]

        is_stale, elapsed = check_stale_bot_process(
            issue, "status-06:implementing", 120, mock_issue_manager
        )

        assert is_stale is False
        assert elapsed is not None
        assert 9 <= elapsed <= 11  # Allow 1 minute tolerance

    def test_returns_true_when_over_threshold(self) -> None:
        """Test that returns True when elapsed time is over threshold."""
        issue: IssueData = {
            "number": 2,
            "title": "Stale issue",
            "body": "",
            "state": "open",
            "labels": ["status-06:implementing"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }

        # Create event timestamp 150 minutes ago (over 120 min threshold)
        stale_timestamp = (
            datetime.now(timezone.utc) - timedelta(minutes=150)
        ).isoformat()

        mock_issue_manager = MagicMock()
        mock_issue_manager.get_issue_events.return_value = [
            {
                "event": "labeled",
                "label": "status-06:implementing",
                "created_at": stale_timestamp,
                "actor": "bot",
            }
        ]

        is_stale, elapsed = check_stale_bot_process(
            issue, "status-06:implementing", 120, mock_issue_manager
        )

        assert is_stale is True
        assert elapsed is not None
        assert 149 <= elapsed <= 151  # Allow 1 minute tolerance

    def test_returns_none_when_no_labeled_event(self) -> None:
        """Test that returns None when no matching labeled event found."""
        issue: IssueData = {
            "number": 3,
            "title": "Issue without events",
            "body": "",
            "state": "open",
            "labels": ["status-06:implementing"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }

        mock_issue_manager = MagicMock()
        mock_issue_manager.get_issue_events.return_value = []  # No events

        is_stale, elapsed = check_stale_bot_process(
            issue, "status-06:implementing", 120, mock_issue_manager
        )

        assert is_stale is False
        assert elapsed is None

    def test_returns_false_when_timeout_not_configured(self) -> None:
        """Test that returns False when timeout is None (not configured)."""
        issue: IssueData = {
            "number": 4,
            "title": "Issue with unconfigured timeout",
            "body": "",
            "state": "open",
            "labels": ["status-06:implementing"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }

        mock_issue_manager = MagicMock()

        is_stale, elapsed = check_stale_bot_process(
            issue, "status-06:implementing", None, mock_issue_manager
        )

        assert is_stale is False
        assert elapsed is None
        # API should not be called when timeout is None
        mock_issue_manager.get_issue_events.assert_not_called()
