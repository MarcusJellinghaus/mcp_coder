"""Unit tests for define_labels validation and staleness detection.

Tests cover:
- Stale timeout configuration validation
- Status label checking
- Issue initialization
- Elapsed time calculations
- Stale bot process detection
- Issue validation
- Validation summary formatting
"""

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.define_labels import (
    ValidationResults,
    calculate_elapsed_minutes,
    check_stale_bot_process,
    check_status_labels,
    execute_define_labels,
    format_validation_summary,
    initialize_issues,
    validate_issues,
)
from mcp_coder.utils.github_operations.issue_manager import IssueData
from mcp_coder.utils.github_operations.label_config import load_labels_config


class TestStaleTimeoutConfiguration:
    """Test stale_timeout_minutes field in labels configuration."""

    def test_bot_busy_labels_have_stale_timeout(self, labels_config_path: Path) -> None:
        """Test that all bot_busy labels have stale_timeout_minutes field."""
        labels_config = load_labels_config(labels_config_path)

        bot_busy_labels = [
            label
            for label in labels_config["workflow_labels"]
            if label.get("category") == "bot_busy"
        ]

        # Ensure we have bot_busy labels to test
        assert len(bot_busy_labels) > 0, "Should have at least one bot_busy label"

        for label in bot_busy_labels:
            assert (
                "stale_timeout_minutes" in label
            ), f"bot_busy label '{label['name']}' should have stale_timeout_minutes field"

    def test_stale_timeout_values_are_positive_integers(
        self, labels_config_path: Path
    ) -> None:
        """Test that stale_timeout_minutes values are positive integers."""
        labels_config = load_labels_config(labels_config_path)

        bot_busy_labels = [
            label
            for label in labels_config["workflow_labels"]
            if label.get("category") == "bot_busy"
        ]

        for label in bot_busy_labels:
            timeout = label.get("stale_timeout_minutes")
            assert isinstance(
                timeout, int
            ), f"stale_timeout_minutes for '{label['name']}' should be an integer"
            assert (
                timeout > 0
            ), f"stale_timeout_minutes for '{label['name']}' should be positive"

    def test_expected_timeout_values(self, labels_config_path: Path) -> None:
        """Test specific timeout values match requirements."""
        labels_config = load_labels_config(labels_config_path)

        # Build lookup by internal_id
        labels_by_id = {
            label["internal_id"]: label for label in labels_config["workflow_labels"]
        }

        # Expected timeout values per spec
        expected_timeouts = {
            "planning": 15,
            "implementing": 120,
            "pr_creating": 15,
        }

        for internal_id, expected_timeout in expected_timeouts.items():
            assert (
                internal_id in labels_by_id
            ), f"Label with internal_id '{internal_id}' should exist"
            label = labels_by_id[internal_id]
            actual_timeout = label.get("stale_timeout_minutes")
            assert actual_timeout == expected_timeout, (
                f"stale_timeout_minutes for '{internal_id}' should be {expected_timeout}, "
                f"got {actual_timeout}"
            )


class TestCheckStatusLabels:
    """Test check_status_labels function."""

    def test_no_status_labels_returns_zero(self) -> None:
        """Test that issues without status labels return count of 0."""
        issue: IssueData = {
            "number": 1,
            "title": "Test issue",
            "body": "",
            "state": "open",
            "labels": ["bug", "enhancement"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        workflow_label_names = {
            "status-01:created",
            "status-02:awaiting-planning",
            "status-03:planning",
        }

        count, found_labels = check_status_labels(issue, workflow_label_names)

        assert count == 0
        assert found_labels == []

    def test_single_status_label_returns_one(self) -> None:
        """Test that issues with one status label return count of 1."""
        issue: IssueData = {
            "number": 2,
            "title": "Test issue with label",
            "body": "",
            "state": "open",
            "labels": ["bug", "status-01:created", "enhancement"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        workflow_label_names = {
            "status-01:created",
            "status-02:awaiting-planning",
            "status-03:planning",
        }

        count, found_labels = check_status_labels(issue, workflow_label_names)

        assert count == 1
        assert found_labels == ["status-01:created"]

    def test_multiple_status_labels_returns_count(self) -> None:
        """Test that issues with multiple status labels return correct count."""
        issue: IssueData = {
            "number": 3,
            "title": "Test issue with multiple labels",
            "body": "",
            "state": "open",
            "labels": ["status-01:created", "status-02:awaiting-planning"],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        workflow_label_names = {
            "status-01:created",
            "status-02:awaiting-planning",
            "status-03:planning",
        }

        count, found_labels = check_status_labels(issue, workflow_label_names)

        assert count == 2
        assert set(found_labels) == {"status-01:created", "status-02:awaiting-planning"}

    def test_ignores_non_workflow_labels(self) -> None:
        """Test that non-workflow labels are ignored in the count."""
        issue: IssueData = {
            "number": 4,
            "title": "Test issue with mixed labels",
            "body": "",
            "state": "open",
            "labels": [
                "bug",
                "status-01:created",
                "enhancement",
                "priority-high",
                "documentation",
            ],
            "assignees": [],
            "user": None,
            "created_at": None,
            "updated_at": None,
            "url": "",
            "locked": False,
        }
        workflow_label_names = {
            "status-01:created",
            "status-02:awaiting-planning",
            "status-03:planning",
        }

        count, found_labels = check_status_labels(issue, workflow_label_names)

        assert count == 1
        assert found_labels == ["status-01:created"]


class TestInitializeIssues:
    """Test initialize_issues function."""

    def test_initializes_issues_without_labels(self) -> None:
        """Test that issues without status labels are initialized."""
        issues: list[IssueData] = [
            {
                "number": 1,
                "title": "Issue without labels",
                "body": "",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
            {
                "number": 2,
                "title": "Another issue without labels",
                "body": "",
                "state": "open",
                "labels": [],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
        ]
        workflow_label_names = {"status-01:created", "status-02:awaiting-planning"}
        created_label_name = "status-01:created"

        mock_issue_manager = MagicMock()
        mock_issue_manager.add_labels.return_value = {
            "number": 1,
            "labels": ["status-01:created"],
        }

        result = initialize_issues(
            issues,
            workflow_label_names,
            created_label_name,
            mock_issue_manager,
            dry_run=False,
        )

        assert result == [1, 2]
        assert mock_issue_manager.add_labels.call_count == 2
        mock_issue_manager.add_labels.assert_any_call(1, "status-01:created")
        mock_issue_manager.add_labels.assert_any_call(2, "status-01:created")

    def test_skips_issues_with_labels(self) -> None:
        """Test that issues with status labels are skipped."""
        issues: list[IssueData] = [
            {
                "number": 1,
                "title": "Issue with status label",
                "body": "",
                "state": "open",
                "labels": ["status-02:awaiting-planning"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
            {
                "number": 2,
                "title": "Issue without labels",
                "body": "",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
        ]
        workflow_label_names = {"status-01:created", "status-02:awaiting-planning"}
        created_label_name = "status-01:created"

        mock_issue_manager = MagicMock()
        mock_issue_manager.add_labels.return_value = {"number": 2, "labels": []}

        result = initialize_issues(
            issues,
            workflow_label_names,
            created_label_name,
            mock_issue_manager,
            dry_run=False,
        )

        # Only issue 2 should be initialized
        assert result == [2]
        assert mock_issue_manager.add_labels.call_count == 1
        mock_issue_manager.add_labels.assert_called_once_with(2, "status-01:created")

    def test_dry_run_does_not_call_api(self) -> None:
        """Test that dry-run mode does not call the API."""
        issues: list[IssueData] = [
            {
                "number": 1,
                "title": "Issue without labels",
                "body": "",
                "state": "open",
                "labels": [],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
        ]
        workflow_label_names = {"status-01:created"}
        created_label_name = "status-01:created"

        mock_issue_manager = MagicMock()

        result = initialize_issues(
            issues,
            workflow_label_names,
            created_label_name,
            mock_issue_manager,
            dry_run=True,
        )

        # Issue should be in result but API should NOT be called
        assert result == [1]
        mock_issue_manager.add_labels.assert_not_called()

    def test_returns_initialized_issue_numbers(self) -> None:
        """Test that the function returns the correct list of issue numbers."""
        issues: list[IssueData] = [
            {
                "number": 10,
                "title": "Issue 10",
                "body": "",
                "state": "open",
                "labels": [],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
            {
                "number": 20,
                "title": "Issue 20",
                "body": "",
                "state": "open",
                "labels": ["status-01:created"],  # Has label, skip
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
            {
                "number": 30,
                "title": "Issue 30",
                "body": "",
                "state": "open",
                "labels": ["bug"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
        ]
        workflow_label_names = {"status-01:created", "status-02:awaiting-planning"}
        created_label_name = "status-01:created"

        mock_issue_manager = MagicMock()
        mock_issue_manager.add_labels.return_value = {"number": 0, "labels": []}

        result = initialize_issues(
            issues,
            workflow_label_names,
            created_label_name,
            mock_issue_manager,
            dry_run=False,
        )

        # Only issues 10 and 30 should be initialized (20 already has a label)
        assert result == [10, 30]


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


class TestValidateIssues:
    """Test validate_issues function."""

    @pytest.fixture
    def sample_labels_config(self) -> dict[str, Any]:
        """Create a sample labels config for testing."""
        return {
            "workflow_labels": [
                {
                    "name": "status-01:created",
                    "internal_id": "created",
                    "category": "human_action",
                    "color": "10b981",
                    "description": "Fresh issue",
                },
                {
                    "name": "status-03:planning",
                    "internal_id": "planning",
                    "category": "bot_busy",
                    "color": "a7f3d0",
                    "description": "Planning in progress",
                    "stale_timeout_minutes": 15,
                },
                {
                    "name": "status-06:implementing",
                    "internal_id": "implementing",
                    "category": "bot_busy",
                    "color": "bfdbfe",
                    "description": "Implementation in progress",
                    "stale_timeout_minutes": 120,
                },
            ]
        }

    def test_detects_multiple_status_labels_as_errors(
        self, sample_labels_config: dict[str, Any]
    ) -> None:
        """Test that issues with multiple status labels are reported as errors."""
        issues: list[IssueData] = [
            {
                "number": 23,
                "title": "Issue with multiple labels",
                "body": "",
                "state": "open",
                "labels": ["status-01:created", "status-03:planning"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            }
        ]

        mock_issue_manager = MagicMock()

        result = validate_issues(
            issues, sample_labels_config, mock_issue_manager, dry_run=False
        )

        assert len(result["errors"]) == 1
        assert result["errors"][0]["issue"] == 23
        assert set(result["errors"][0]["labels"]) == {
            "status-01:created",
            "status-03:planning",
        }
        assert len(result["ok"]) == 0
        assert len(result["warnings"]) == 0

    def test_detects_stale_bot_process_as_warning(
        self, sample_labels_config: dict[str, Any]
    ) -> None:
        """Test that stale bot_busy processes are reported as warnings."""
        issues: list[IssueData] = [
            {
                "number": 78,
                "title": "Stale implementing issue",
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
        ]

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

        result = validate_issues(
            issues, sample_labels_config, mock_issue_manager, dry_run=False
        )

        assert len(result["warnings"]) == 1
        assert result["warnings"][0]["issue"] == 78
        assert result["warnings"][0]["label"] == "status-06:implementing"
        assert result["warnings"][0]["threshold"] == 120
        assert 149 <= result["warnings"][0]["elapsed"] <= 151
        assert len(result["errors"]) == 0
        assert len(result["ok"]) == 0

    def test_marks_valid_issues_as_ok(
        self, sample_labels_config: dict[str, Any]
    ) -> None:
        """Test that valid issues are marked as OK."""
        issues: list[IssueData] = [
            {
                "number": 1,
                "title": "Valid issue with human_action label",
                "body": "",
                "state": "open",
                "labels": ["status-01:created"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
            {
                "number": 2,
                "title": "Valid issue with fresh bot_busy label",
                "body": "",
                "state": "open",
                "labels": ["status-06:implementing"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
        ]

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

        result = validate_issues(
            issues, sample_labels_config, mock_issue_manager, dry_run=False
        )

        assert result["ok"] == [1, 2]
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0

    def test_runs_staleness_check_in_dry_run(
        self, sample_labels_config: dict[str, Any]
    ) -> None:
        """Test that staleness checks run even in dry-run mode."""
        issues: list[IssueData] = [
            {
                "number": 100,
                "title": "Stale issue in dry run",
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
        ]

        # Create stale timestamp
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

        result = validate_issues(
            issues, sample_labels_config, mock_issue_manager, dry_run=True
        )

        # Staleness check should run and report warning even in dry-run
        assert len(result["warnings"]) == 1
        assert result["warnings"][0]["issue"] == 100
        mock_issue_manager.get_issue_events.assert_called_once()

    def test_handles_missing_timeout_gracefully(
        self, sample_labels_config: dict[str, Any]
    ) -> None:
        """Test that missing timeout configuration is handled gracefully."""
        # Add a bot_busy label without stale_timeout_minutes
        sample_labels_config["workflow_labels"].append(
            {
                "name": "status-09:pr-creating",
                "internal_id": "pr_creating",
                "category": "bot_busy",
                "color": "fed7aa",
                "description": "Creating PR",
                # Note: no stale_timeout_minutes
            }
        )

        issues: list[IssueData] = [
            {
                "number": 50,
                "title": "Issue with unconfigured timeout",
                "body": "",
                "state": "open",
                "labels": ["status-09:pr-creating"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            }
        ]

        mock_issue_manager = MagicMock()

        result = validate_issues(
            issues, sample_labels_config, mock_issue_manager, dry_run=False
        )

        # Should be marked as OK (staleness check skipped)
        assert result["ok"] == [50]
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
        # API should not be called when timeout is not configured
        mock_issue_manager.get_issue_events.assert_not_called()


class TestFormatValidationSummary:
    """Test format_validation_summary function."""

    def test_includes_label_sync_counts(self) -> None:
        """Test that summary includes label sync counts."""
        label_changes = {
            "created": ["status-01:created", "status-02:awaiting-planning"],
            "updated": ["status-03:planning"],
            "deleted": [],
            "unchanged": [
                "status-04:plan-review",
                "status-05:plan-ready",
                "status-06:implementing",
            ],
        }
        validation_results: ValidationResults = {
            "initialized": [],
            "errors": [],
            "warnings": [],
            "ok": [],
            "skipped": 0,
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(label_changes, validation_results, repo_url)

        assert "Created=2" in result
        assert "Updated=1" in result
        assert "Deleted=0" in result
        assert "Unchanged=3" in result

    def test_includes_initialized_issues(self) -> None:
        """Test that summary includes initialized issue count."""
        label_changes = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        validation_results: ValidationResults = {
            "initialized": [12, 45, 78],
            "errors": [],
            "warnings": [],
            "ok": [],
            "skipped": 0,
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(label_changes, validation_results, repo_url)

        assert "Issues initialized: 3" in result

    def test_includes_error_details(self) -> None:
        """Test that summary includes error details with issue numbers and labels."""
        label_changes = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        validation_results: ValidationResults = {
            "initialized": [],
            "errors": [
                {
                    "issue": 45,
                    "labels": ["status-01:created", "status-03:planning"],
                }
            ],
            "warnings": [],
            "ok": [],
            "skipped": 0,
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(label_changes, validation_results, repo_url)

        assert "Errors (multiple status labels): 1" in result
        assert "#45" in result
        assert "status-01:created" in result
        assert "status-03:planning" in result

    def test_includes_warning_with_threshold(self) -> None:
        """Test that summary includes warning details with elapsed and threshold."""
        label_changes = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        validation_results: ValidationResults = {
            "initialized": [],
            "errors": [],
            "warnings": [
                {
                    "issue": 78,
                    "label": "status-06:implementing",
                    "elapsed": 150,
                    "threshold": 120,
                }
            ],
            "ok": [],
            "skipped": 0,
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(label_changes, validation_results, repo_url)

        assert "Warnings (stale bot processes): 1" in result
        assert "#78" in result
        assert "status-06:implementing" in result
        assert "150 minutes" in result
        assert "threshold: 120" in result

    def test_no_errors_or_warnings_shows_clean_summary(self) -> None:
        """Test that clean summary shows success when no errors or warnings."""
        label_changes = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }
        validation_results: ValidationResults = {
            "initialized": [],
            "errors": [],
            "warnings": [],
            "ok": [1, 2, 3],
            "skipped": 0,
        }
        repo_url = "https://github.com/owner/repo"

        result = format_validation_summary(label_changes, validation_results, repo_url)

        # Should not contain error or warning sections
        assert "Errors" not in result
        assert "Warnings" not in result


class TestExecuteDefineLabelsExitCodes:
    """Test exit codes from execute_define_labels."""

    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_returns_zero_on_success(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test successful execution returns 0."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "name": "status-01:created",
                    "internal_id": "created",
                    "category": "human_action",
                    "color": "10b981",
                    "description": "Test",
                }
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created"],
        }

        # Setup mock issue manager to return no issues
        mock_issue_manager = MagicMock()
        mock_issue_manager.list_issues.return_value = []
        mock_issue_manager_class.return_value = mock_issue_manager

        args = argparse.Namespace(
            project_dir=str(project_dir),
            dry_run=False,
        )

        result = execute_define_labels(args)

        assert result == 0

    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_returns_one_on_errors(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test execution with errors returns 1."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "name": "status-01:created",
                    "internal_id": "created",
                    "category": "human_action",
                    "color": "10b981",
                    "description": "Test",
                },
                {
                    "name": "status-03:planning",
                    "internal_id": "planning",
                    "category": "bot_busy",
                    "color": "a7f3d0",
                    "description": "Planning",
                    "stale_timeout_minutes": 15,
                },
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-01:created", "status-03:planning"],
        }

        # Setup mock issue manager to return an issue with multiple labels (error)
        mock_issue_manager = MagicMock()
        mock_issue_manager.list_issues.return_value = [
            {
                "number": 45,
                "title": "Issue with multiple labels",
                "body": "",
                "state": "open",
                "labels": ["status-01:created", "status-03:planning"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            }
        ]
        mock_issue_manager_class.return_value = mock_issue_manager

        args = argparse.Namespace(
            project_dir=str(project_dir),
            dry_run=False,
        )

        result = execute_define_labels(args)

        assert result == 1

    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_returns_two_on_warnings_only(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test execution with warnings only returns 2."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "name": "status-06:implementing",
                    "internal_id": "implementing",
                    "category": "bot_busy",
                    "color": "bfdbfe",
                    "description": "Implementing",
                    "stale_timeout_minutes": 120,
                },
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": ["status-06:implementing"],
        }

        # Create stale timestamp (150 minutes ago, over 120 min threshold)
        stale_timestamp = (
            datetime.now(timezone.utc) - timedelta(minutes=150)
        ).isoformat()

        # Setup mock issue manager to return an issue with stale bot_busy label
        mock_issue_manager = MagicMock()
        mock_issue_manager.list_issues.return_value = [
            {
                "number": 78,
                "title": "Stale implementing issue",
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
        ]
        mock_issue_manager.get_issue_events.return_value = [
            {
                "event": "labeled",
                "label": "status-06:implementing",
                "created_at": stale_timestamp,
                "actor": "bot",
            }
        ]
        mock_issue_manager_class.return_value = mock_issue_manager

        args = argparse.Namespace(
            project_dir=str(project_dir),
            dry_run=False,
        )

        result = execute_define_labels(args)

        assert result == 2

    @patch("mcp_coder.cli.commands.define_labels.IssueManager")
    @patch("mcp_coder.cli.commands.define_labels.apply_labels")
    @patch("mcp_coder.cli.commands.define_labels.load_labels_config")
    @patch("mcp_coder.cli.commands.define_labels.get_labels_config_path")
    @patch("mcp_coder.cli.commands.define_labels.resolve_project_dir")
    def test_errors_take_precedence_over_warnings(
        self,
        mock_resolve_dir: MagicMock,
        mock_get_config_path: MagicMock,
        mock_load_config: MagicMock,
        mock_apply_labels: MagicMock,
        mock_issue_manager_class: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test that errors (exit code 1) take precedence over warnings (exit code 2)."""
        # Setup mocks
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        mock_resolve_dir.return_value = project_dir
        mock_get_config_path.return_value = project_dir / "config" / "labels.json"
        mock_load_config.return_value = {
            "workflow_labels": [
                {
                    "name": "status-01:created",
                    "internal_id": "created",
                    "category": "human_action",
                    "color": "10b981",
                    "description": "Test",
                },
                {
                    "name": "status-03:planning",
                    "internal_id": "planning",
                    "category": "bot_busy",
                    "color": "a7f3d0",
                    "description": "Planning",
                    "stale_timeout_minutes": 15,
                },
                {
                    "name": "status-06:implementing",
                    "internal_id": "implementing",
                    "category": "bot_busy",
                    "color": "bfdbfe",
                    "description": "Implementing",
                    "stale_timeout_minutes": 120,
                },
            ]
        }
        mock_apply_labels.return_value = {
            "created": [],
            "updated": [],
            "deleted": [],
            "unchanged": [
                "status-01:created",
                "status-03:planning",
                "status-06:implementing",
            ],
        }

        # Create stale timestamp for warning
        stale_timestamp = (
            datetime.now(timezone.utc) - timedelta(minutes=150)
        ).isoformat()

        # Setup mock issue manager with both error and warning issues
        mock_issue_manager = MagicMock()
        mock_issue_manager.list_issues.return_value = [
            # Issue with multiple labels (error)
            {
                "number": 45,
                "title": "Issue with multiple labels",
                "body": "",
                "state": "open",
                "labels": ["status-01:created", "status-03:planning"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
            # Stale issue (warning)
            {
                "number": 78,
                "title": "Stale implementing issue",
                "body": "",
                "state": "open",
                "labels": ["status-06:implementing"],
                "assignees": [],
                "user": None,
                "created_at": None,
                "updated_at": None,
                "url": "",
                "locked": False,
            },
        ]
        mock_issue_manager.get_issue_events.return_value = [
            {
                "event": "labeled",
                "label": "status-06:implementing",
                "created_at": stale_timestamp,
                "actor": "bot",
            }
        ]
        mock_issue_manager_class.return_value = mock_issue_manager

        args = argparse.Namespace(
            project_dir=str(project_dir),
            dry_run=False,
        )

        result = execute_define_labels(args)

        # Errors take precedence, so should return 1 not 2
        assert result == 1
