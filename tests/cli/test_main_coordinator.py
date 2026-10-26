from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.main import create_parser, main


class TestCoordinatorCommand:
    """Tests for coordinator command CLI integration."""

    def test_coordinator_dry_run_parsing(self) -> None:
        """Test that coordinator --dry-run command is parsed correctly."""
        # Setup
        parser = create_parser()

        # Execute
        args = parser.parse_args(
            [
                "coordinator",
                "--dry-run",
                "--repo",
                "mcp_coder",
                "--branch-name",
                "feature-x",
            ]
        )

        # Verify
        assert args.command == "coordinator"
        assert args.dry_run is True
        assert args.repo == "mcp_coder"
        assert args.branch_name == "feature-x"
        assert args.coordinator_log_level == "DEBUG"  # default

    @patch("mcp_coder.cli.main.execute_coordinator_test")
    def test_coordinator_dry_run_executes_handler(self, mock_execute: Mock) -> None:
        """Test that coordinator --dry-run calls execute_coordinator_test."""
        # Setup
        mock_execute.return_value = 0

        # Execute
        with patch(
            "sys.argv",
            [
                "mcp-coder",
                "coordinator",
                "--dry-run",
                "--repo",
                "mcp_coder",
                "--branch-name",
                "feature-x",
            ],
        ):
            result = main()

        # Verify
        assert result == 0
        mock_execute.assert_called_once()

        # Check args passed to handler
        call_args = mock_execute.call_args[0][0]
        assert call_args.repo_name == "mcp_coder"
        assert call_args.branch_name == "feature-x"

    @patch("mcp_coder.cli.main.execute_coordinator_test")
    def test_coordinator_dry_run_with_log_level(self, mock_execute: Mock) -> None:
        """Test coordinator --dry-run respects --log-level-coordinator flag."""
        # Setup
        mock_execute.return_value = 0

        # Execute
        with patch(
            "sys.argv",
            [
                "mcp-coder",
                "coordinator",
                "--dry-run",
                "--repo",
                "mcp_coder",
                "--branch-name",
                "feature-x",
                "--log-level-coordinator",
                "WARNING",
            ],
        ):
            result = main()

        # Verify
        assert result == 0
        mock_execute.assert_called_once()

        # Check args passed to handler - log_level is mapped from coordinator_log_level
        call_args = mock_execute.call_args[0][0]
        assert call_args.repo_name == "mcp_coder"
        assert call_args.branch_name == "feature-x"
        assert call_args.log_level == "WARNING"

    def test_coordinator_dry_run_without_repo_shows_error(self) -> None:
        """Test that --dry-run without --repo shows error."""
        with patch(
            "sys.argv",
            ["mcp-coder", "coordinator", "--dry-run", "--branch-name", "feature-x"],
        ):
            result = main()

        assert result == 1

    def test_coordinator_dry_run_without_branch_shows_error(self) -> None:
        """Test that --dry-run without --branch-name shows error."""
        with patch(
            "sys.argv",
            ["mcp-coder", "coordinator", "--dry-run", "--repo", "mcp_coder"],
        ):
            result = main()

        assert result == 1

    def test_coordinator_without_all_or_repo_shows_error(self) -> None:
        """Test that coordinator without --all or --repo shows error."""
        with patch("sys.argv", ["mcp-coder", "coordinator"]):
            result = main()

        assert result == 1


class TestCoordinatorRunCommand:
    """Tests for coordinator run CLI integration."""

    @patch("mcp_coder.cli.main.execute_coordinator_run")
    def test_coordinator_run_with_repo_argument(self, mock_execute: Mock) -> None:
        """Test CLI routing for --repo mode."""
        # Setup
        mock_execute.return_value = 0

        # Execute
        with patch(
            "sys.argv",
            ["mcp-coder", "coordinator", "--repo", "mcp_coder"],
        ):
            result = main()

        # Verify
        assert result == 0
        mock_execute.assert_called_once()

        # Check args passed to handler
        call_args = mock_execute.call_args[0][0]
        assert call_args.command == "coordinator"
        assert call_args.repo == "mcp_coder"
        assert call_args.all is False
        assert call_args.log_level is None  # default (resolved at runtime)

    @patch("mcp_coder.cli.main.execute_coordinator_run")
    def test_coordinator_run_with_all_argument(self, mock_execute: Mock) -> None:
        """Test CLI routing for --all mode."""
        # Setup
        mock_execute.return_value = 0

        # Execute
        with patch(
            "sys.argv",
            ["mcp-coder", "coordinator", "--all"],
        ):
            result = main()

        # Verify
        assert result == 0
        mock_execute.assert_called_once()

        # Check args passed to handler
        call_args = mock_execute.call_args[0][0]
        assert call_args.command == "coordinator"
        assert call_args.all is True
        assert call_args.repo is None
        assert call_args.log_level is None  # default (resolved at runtime)

    @patch("mcp_coder.cli.main.execute_coordinator_run")
    def test_coordinator_run_with_log_level(self, mock_execute: Mock) -> None:
        """Test log level pass-through."""
        # Setup
        mock_execute.return_value = 0

        # Execute
        with patch(
            "sys.argv",
            [
                "mcp-coder",
                "--log-level",
                "DEBUG",
                "coordinator",
                "--repo",
                "mcp_coder",
            ],
        ):
            result = main()

        # Verify
        assert result == 0
        mock_execute.assert_called_once()

        # Check args passed to handler
        call_args = mock_execute.call_args[0][0]
        assert call_args.command == "coordinator"
        assert call_args.repo == "mcp_coder"
        assert call_args.all is False
        assert call_args.log_level == "DEBUG"

    def test_coordinator_run_all_and_repo_mutually_exclusive(self) -> None:
        """Test error when both --all and --repo provided."""
        parser = create_parser()

        # Should raise SystemExit when both --all and --repo are provided
        with pytest.raises(SystemExit):
            parser.parse_args(["coordinator", "--all", "--repo", "mcp_coder"])
