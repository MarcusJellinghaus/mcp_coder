"""CLI tests for coordinator/issue_stats.py - Argument parsing and execute function.

Tests cover:
- Argument parsing for issue-stats subcommand
- execute_coordinator_issue_stats function
"""

import argparse
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest


class TestParseArguments:
    """Test argument parsing for issue-stats."""

    def test_default_values(self) -> None:
        """Test that default values are correctly set."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["coordinator", "issue-stats"])

        assert args.command == "coordinator"
        assert args.coordinator_subcommand == "issue-stats"
        assert args.filter == "all"
        assert args.details is False
        assert args.project_dir is None

    def test_filter_human(self) -> None:
        """Test --filter human argument."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["coordinator", "issue-stats", "--filter", "human"])

        assert args.filter == "human"

    def test_filter_bot(self) -> None:
        """Test --filter bot argument."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["coordinator", "issue-stats", "--filter", "bot"])

        assert args.filter == "bot"

    def test_filter_case_insensitive(self) -> None:
        """Test --filter is case insensitive."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Test uppercase
        args = parser.parse_args(["coordinator", "issue-stats", "--filter", "HUMAN"])
        assert args.filter == "human"

        # Test mixed case
        args = parser.parse_args(["coordinator", "issue-stats", "--filter", "Bot"])
        assert args.filter == "bot"

    def test_details_flag(self) -> None:
        """Test --details flag."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["coordinator", "issue-stats", "--details"])

        assert args.details is True

    def test_project_dir_argument(self) -> None:
        """Test --project-dir argument."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(
            ["coordinator", "issue-stats", "--project-dir", "/path/to/project"]
        )

        assert args.project_dir == "/path/to/project"

    def test_combined_arguments(self) -> None:
        """Test combining multiple arguments."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "coordinator",
                "issue-stats",
                "--filter",
                "bot",
                "--details",
                "--project-dir",
                "/my/repo",
            ]
        )

        assert args.filter == "bot"
        assert args.details is True
        assert args.project_dir == "/my/repo"


class TestExecuteCoordinatorIssueStats:
    """Test execute_coordinator_issue_stats function."""

    @pytest.fixture
    def test_labels_config(self) -> dict[str, Any]:
        """Create a test labels configuration."""
        return {
            "workflow_labels": [
                {
                    "name": "status-01:created",
                    "category": "human_action",
                    "internal_id": "created",
                },
                {
                    "name": "status-04:plan-review",
                    "category": "human_action",
                    "internal_id": "plan_review",
                },
                {
                    "name": "status-02:awaiting-planning",
                    "category": "bot_pickup",
                    "internal_id": "awaiting_planning",
                },
                {
                    "name": "status-06:implementing",
                    "category": "bot_busy",
                    "internal_id": "implementing",
                },
            ],
            "ignore_labels": ["on hold", "wontfix"],
        }

    def test_returns_zero_on_success(
        self, tmp_path: Path, test_labels_config: dict[str, Any]
    ) -> None:
        """Test that function returns 0 on success."""
        from mcp_coder.cli.commands.coordinator.issue_stats import (
            execute_coordinator_issue_stats,
        )

        # Create a mock git repository
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            filter="all",
            details=False,
        )

        # Mock the dependencies
        with (
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.get_github_repository_url"
            ) as mock_get_url,
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.get_labels_config_path"
            ) as mock_config_path,
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.load_labels_config"
            ) as mock_load_config,
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.IssueManager"
            ) as mock_issue_manager,
        ):
            mock_get_url.return_value = "https://github.com/owner/repo"
            mock_config_path.return_value = Path("/fake/labels.json")
            mock_load_config.return_value = test_labels_config
            mock_issue_manager.return_value.list_issues.return_value = []

            result = execute_coordinator_issue_stats(args)

            assert result == 0

    def test_returns_one_on_error(self, tmp_path: Path) -> None:
        """Test that function returns 1 on error."""
        from mcp_coder.cli.commands.coordinator.issue_stats import (
            execute_coordinator_issue_stats,
        )

        # Non-existent directory
        args = argparse.Namespace(
            project_dir=str(tmp_path / "nonexistent"),
            filter="all",
            details=False,
        )

        result = execute_coordinator_issue_stats(args)

        assert result == 1

    def test_applies_filter_argument(
        self, tmp_path: Path, test_labels_config: dict[str, Any]
    ) -> None:
        """Test that filter argument is applied correctly."""
        from mcp_coder.cli.commands.coordinator.issue_stats import (
            execute_coordinator_issue_stats,
        )

        # Create a mock git repository
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            filter="human",
            details=False,
        )

        with (
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.get_github_repository_url"
            ) as mock_get_url,
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.get_labels_config_path"
            ) as mock_config_path,
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.load_labels_config"
            ) as mock_load_config,
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.IssueManager"
            ) as mock_issue_manager,
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.display_statistics"
            ) as mock_display,
        ):
            mock_get_url.return_value = "https://github.com/owner/repo"
            mock_config_path.return_value = Path("/fake/labels.json")
            mock_load_config.return_value = test_labels_config
            mock_issue_manager.return_value.list_issues.return_value = []

            execute_coordinator_issue_stats(args)

            # Verify display_statistics was called with correct filter
            mock_display.assert_called_once()
            call_kwargs = mock_display.call_args
            assert call_kwargs[1]["filter_category"] == "human"

    def test_applies_details_argument(
        self, tmp_path: Path, test_labels_config: dict[str, Any]
    ) -> None:
        """Test that details argument is applied correctly."""
        from mcp_coder.cli.commands.coordinator.issue_stats import (
            execute_coordinator_issue_stats,
        )

        # Create a mock git repository
        git_dir = tmp_path / ".git"
        git_dir.mkdir()

        args = argparse.Namespace(
            project_dir=str(tmp_path),
            filter="all",
            details=True,
        )

        with (
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.get_github_repository_url"
            ) as mock_get_url,
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.get_labels_config_path"
            ) as mock_config_path,
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.load_labels_config"
            ) as mock_load_config,
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.IssueManager"
            ) as mock_issue_manager,
            patch(
                "mcp_coder.cli.commands.coordinator.issue_stats.display_statistics"
            ) as mock_display,
        ):
            mock_get_url.return_value = "https://github.com/owner/repo"
            mock_config_path.return_value = Path("/fake/labels.json")
            mock_load_config.return_value = test_labels_config
            mock_issue_manager.return_value.list_issues.return_value = []

            execute_coordinator_issue_stats(args)

            # Verify display_statistics was called with details=True
            mock_display.assert_called_once()
            call_kwargs = mock_display.call_args
            assert call_kwargs[1]["show_details"] is True
