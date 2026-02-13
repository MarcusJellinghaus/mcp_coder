"""Tests for define_labels status label checking and issue initialization.

Tests cover:
- Status label checking (check_status_labels function)
- Issue initialization (initialize_issues function)
"""

from unittest.mock import MagicMock

from mcp_coder.cli.commands.define_labels import (
    check_status_labels,
    initialize_issues,
)
from mcp_coder.utils.github_operations.issues import IssueData


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
