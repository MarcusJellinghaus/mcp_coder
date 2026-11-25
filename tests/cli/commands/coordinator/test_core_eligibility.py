from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    PRIORITY_ORDER,
    _filter_eligible_issues,
    get_eligible_issues,
)
from mcp_coder.cli.commands.coordinator.core import stage_index
from tests.github_factories import make_issue_data


class TestStageIndex:
    """stage_index ranks issues in reverse pipeline order."""

    @pytest.mark.parametrize(
        ("label", "expected"),
        [
            ("status-81:failing-ci", 0),
            ("status-71:merge-conflict", 1),
            ("status-08:ready-pr", 2),
            ("status-17:code-review-bot", 3),
            ("status-05:plan-ready", 4),
            ("status-14:plan-review-bot", 5),
            ("status-02:awaiting-planning", 6),
        ],
    )
    def test_stage_label_maps_to_position(self, label: str, expected: int) -> None:
        issue = make_issue_data(labels=["enhancement", label])
        assert stage_index(issue) == expected

    def test_issue_without_stage_label_sorts_last(self) -> None:
        issue = make_issue_data(labels=["bug", "status-01:created"])
        assert stage_index(issue) == len(PRIORITY_ORDER)


class TestFilterEligibleIssues:
    """_filter_eligible_issues keeps input order."""

    @patch("mcp_coder.cli.commands.coordinator.core.load_labels_config")
    def test_keeps_input_order(self, mock_load_config: MagicMock) -> None:
        mock_load_config.return_value = {
            "workflow_labels": [
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
            ],
            "ignore_labels": [],
        }
        issues = [
            make_issue_data(number=1, labels=["status-02:awaiting-planning"]),
            make_issue_data(number=2, labels=["status-08:ready-pr"]),
        ]

        result = _filter_eligible_issues(issues)

        assert [issue["number"] for issue in result] == [1, 2]


class TestGetEligibleIssues:
    """Tests for get_eligible_issues function."""

    @patch("mcp_coder.cli.commands.coordinator.core.IssueManager")
    @patch("mcp_coder.cli.commands.coordinator.core.load_labels_config")
    def test_get_eligible_issues_filters_by_bot_pickup_labels(
        self, mock_load_config: MagicMock, mock_issue_manager_class: MagicMock
    ) -> None:
        """Test filtering issues by bot_pickup labels."""
        # Setup - Mock label configuration
        mock_load_config.return_value = {
            "workflow_labels": [
                {"name": "status-01:created", "category": "human_action"},
                {"name": "status-02:awaiting-planning", "category": "bot_pickup"},
                {"name": "status-05:plan-ready", "category": "bot_pickup"},
                {"name": "status-08:ready-pr", "category": "bot_pickup"},
                {"name": "status-03:planning", "category": "bot_busy"},
            ],
            "ignore_labels": ["Overview"],
        }

        # Setup - Mock IssueManager instance
        mock_issue_manager = MagicMock()
        mock_issue_manager_class.return_value = mock_issue_manager

        # Mock issue list with mixed labels
        mock_issue_manager.list_issues.return_value = [
            # Issue with valid bot_pickup label - should be included
            make_issue_data(
                labels=["status-02:awaiting-planning", "enhancement"],
                url="https://github.com/user/repo/issues/1",
            ),
            # Issue with no bot_pickup label - should be excluded
            make_issue_data(
                number=2,
                labels=["status-01:created", "bug"],
                url="https://github.com/user/repo/issues/2",
            ),
            # Another valid issue with bot_pickup label - should be included
            make_issue_data(
                number=4,
                labels=["status-08:ready-pr"],
                url="https://github.com/user/repo/issues/4",
            ),
        ]

        # Execute
        result = get_eligible_issues(mock_issue_manager)

        # Verify - only issues with exactly one bot_pickup label
        # Input order is kept; the coordinator sorts globally
        assert [issue["number"] for issue in result] == [1, 4]

        # Verify IssueManager.list_issues was called with correct params
        mock_issue_manager.list_issues.assert_called_once_with(
            state="open", include_pull_requests=False
        )
