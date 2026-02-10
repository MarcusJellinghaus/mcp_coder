"""Tests for define_labels issue validation.

Tests cover:
- Issue validation (validate_issues function)
- Multiple status label detection
- Stale bot process warnings
"""

from datetime import datetime, timedelta, timezone
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp_coder.cli.commands.define_labels import validate_issues
from mcp_coder.utils.github_operations.issues import IssueData


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
