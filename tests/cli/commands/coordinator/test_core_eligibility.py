from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_coder.cli.commands.coordinator import (
    get_cached_eligible_issues,
    get_eligible_issues,
)
from mcp_coder.mcp_workspace_github import IssueData, RepoIdentifier
from tests.github_factories import make_issue_data


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
        assert len(result) == 2
        assert result[0]["number"] == 4  # status-08 has highest priority
        assert result[1]["number"] == 1  # status-02 has lower priority

        # Verify IssueManager.list_issues was called with correct params
        mock_issue_manager.list_issues.assert_called_once_with(
            state="open", include_pull_requests=False
        )


class TestGetCachedEligibleIssues:
    """Tests for get_cached_eligible_issues wrapper function.

    Note: get_cached_eligible_issues is now a thin wrapper that:
    1. Calls get_all_cached_issues() from issues.cache module
    2. Filters results using _filter_eligible_issues()
    3. Falls back to get_eligible_issues() on errors

    These tests verify the wrapper behavior, not the underlying cache operations
    (which are tested in tests/utils/github_operations/test_issues.cache.py).
    """

    @pytest.fixture
    def sample_issue(self) -> IssueData:
        """Sample issue data for testing."""
        return make_issue_data(
            number=123,
            labels=["status-02:awaiting-planning"],
            updated_at="2025-12-31T09:00:00Z",
            url="https://github.com/test/repo/issues/123",
            title="Test issue",
            body="Test issue body",
            user="testuser",
            created_at="2025-12-31T08:00:00Z",
        )

    @pytest.fixture
    def mock_issue_manager(self) -> Mock:
        """Mock IssueManager for testing."""
        manager = Mock()
        manager.list_issues.return_value = []
        return manager

    def test_get_cached_eligible_issues_calls_get_all_cached_issues(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test that wrapper calls get_all_cached_issues and filters results."""
        with (
            patch(
                "mcp_coder.cli.commands.coordinator.core.get_all_cached_issues"
            ) as mock_get_all,
            patch(
                "mcp_coder.cli.commands.coordinator.core._filter_eligible_issues"
            ) as mock_filter,
        ):
            mock_get_all.return_value = [sample_issue]
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            assert result == [sample_issue]
            mock_get_all.assert_called_once_with(
                RepoIdentifier.from_full_name("owner/repo"),
                issue_manager=mock_issue_manager,
                force_refresh=False,
                cache_refresh_minutes=1440,
            )
            mock_filter.assert_called_once_with([sample_issue])

    def test_get_cached_eligible_issues_passes_force_refresh(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test that force_refresh parameter is passed through."""
        with (
            patch(
                "mcp_coder.cli.commands.coordinator.core.get_all_cached_issues"
            ) as mock_get_all,
            patch(
                "mcp_coder.cli.commands.coordinator.core._filter_eligible_issues"
            ) as mock_filter,
        ):
            mock_get_all.return_value = [sample_issue]
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues(
                "owner/repo", mock_issue_manager, force_refresh=True
            )

            assert result == [sample_issue]
            mock_get_all.assert_called_once_with(
                RepoIdentifier.from_full_name("owner/repo"),
                issue_manager=mock_issue_manager,
                force_refresh=True,
                cache_refresh_minutes=1440,
            )

    def test_get_cached_eligible_issues_passes_cache_refresh_minutes(
        self, mock_issue_manager: Mock, sample_issue: IssueData
    ) -> None:
        """Test that cache_refresh_minutes parameter is passed through."""
        with (
            patch(
                "mcp_coder.cli.commands.coordinator.core.get_all_cached_issues"
            ) as mock_get_all,
            patch(
                "mcp_coder.cli.commands.coordinator.core._filter_eligible_issues"
            ) as mock_filter,
        ):
            mock_get_all.return_value = [sample_issue]
            mock_filter.return_value = [sample_issue]

            result = get_cached_eligible_issues(
                "owner/repo", mock_issue_manager, cache_refresh_minutes=720
            )

            assert result == [sample_issue]
            mock_get_all.assert_called_once_with(
                RepoIdentifier.from_full_name("owner/repo"),
                issue_manager=mock_issue_manager,
                force_refresh=False,
                cache_refresh_minutes=720,
            )

    def test_get_cached_eligible_issues_fallback_on_error(
        self, mock_issue_manager: Mock
    ) -> None:
        """Test graceful fallback when cache operations fail."""
        with (
            patch(
                "mcp_coder.cli.commands.coordinator.core.get_all_cached_issues",
                side_effect=ValueError("Cache error"),
            ),
            patch(
                "mcp_coder.cli.commands.coordinator.core.get_eligible_issues"
            ) as mock_fallback,
        ):
            mock_fallback.return_value = []

            result = get_cached_eligible_issues("owner/repo", mock_issue_manager)

            # Should fall back to get_eligible_issues
            assert result == []
            mock_fallback.assert_called_once_with(mock_issue_manager)
