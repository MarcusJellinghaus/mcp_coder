"""Tests for CLI main entry point."""

import argparse
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.main import create_parser, handle_no_command, main


class TestCreateParser:
    """Test argument parser creation."""

    def test_create_parser_returns_argumentparser(self) -> None:
        """Test that create_parser returns ArgumentParser instance."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)

    def test_parser_has_correct_prog_name(self) -> None:
        """Test parser program name is set correctly."""
        parser = create_parser()
        assert parser.prog == "mcp-coder"

    def test_parser_has_version_action(self) -> None:
        """Test parser includes version argument."""
        parser = create_parser()
        # Check if version action exists by trying to parse --version
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_parser_has_subparsers(self) -> None:
        """Test parser has subcommand structure."""
        parser = create_parser()
        # Check that subparsers exist (they should be accessible via _subparsers)
        assert hasattr(parser, "_subparsers")

    def test_parser_has_log_level_argument(self) -> None:
        """Test parser includes log level argument."""
        parser = create_parser()
        # Test parsing with log level
        args = parser.parse_args(["--log-level", "DEBUG", "help"])
        assert args.log_level == "DEBUG"
        assert args.command == "help"

    def test_parser_log_level_default(self) -> None:
        """Test log level has correct default value."""
        parser = create_parser()
        args = parser.parse_args(["help"])
        assert args.log_level == "INFO"

    def test_parser_log_level_choices(self) -> None:
        """Test log level validates choices."""
        parser = create_parser()
        # Valid choices should work
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            args = parser.parse_args(["--log-level", level, "help"])
            assert args.log_level == level

        # Invalid choice should raise SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(["--log-level", "INVALID", "help"])


class TestHandleNoCommand:
    """Test handling when no command is provided."""

    @patch("builtins.print")
    def test_handle_no_command_prints_help(self, mock_print: Mock) -> None:
        """Test that handle_no_command prints help information."""
        args = argparse.Namespace(command=None)
        result = handle_no_command(args)

        assert result == 1
        # Verify help text was printed
        mock_print.assert_called()
        call_args = [call[0][0] for call in mock_print.call_args_list]
        help_text = " ".join(call_args)
        assert "mcp-coder" in help_text
        assert "help" in help_text
        assert "commit" in help_text

    @patch("mcp_coder.cli.main.logger")
    def test_handle_no_command_logs_info(self, mock_logger: Mock) -> None:
        """Test that handle_no_command logs appropriate message."""
        args = argparse.Namespace(command=None)
        handle_no_command(args)

        mock_logger.info.assert_called_with("No command provided, showing help")


class TestMain:
    """Test main CLI entry point."""

    @patch("mcp_coder.cli.main.setup_logging")
    @patch("mcp_coder.cli.main.handle_no_command")
    @patch("mcp_coder.cli.main.create_parser")
    def test_main_no_args_calls_handle_no_command(
        self,
        mock_create_parser: Mock,
        mock_handle_no_command: Mock,
        mock_setup_logging: Mock,
    ) -> None:
        """Test that main calls handle_no_command when no command provided."""
        mock_parser = Mock()
        mock_parser.parse_args.return_value = argparse.Namespace(
            command=None, log_level="INFO"
        )
        mock_create_parser.return_value = mock_parser
        mock_handle_no_command.return_value = 1

        result = main()

        assert result == 1
        mock_handle_no_command.assert_called_once()
        mock_setup_logging.assert_called_once_with("INFO")

    @patch("mcp_coder.cli.main.setup_logging")
    @patch("mcp_coder.cli.main.execute_help")
    @patch("mcp_coder.cli.main.create_parser")
    def test_main_help_command(
        self,
        mock_create_parser: Mock,
        mock_execute_help: Mock,
        mock_setup_logging: Mock,
    ) -> None:
        """Test 'mcp-coder help' command works."""
        mock_parser = Mock()
        mock_parser.parse_args.return_value = argparse.Namespace(
            command="help", log_level="INFO"
        )
        mock_create_parser.return_value = mock_parser
        mock_execute_help.return_value = 0

        result = main()

        assert result == 0
        mock_execute_help.assert_called_once()
        mock_setup_logging.assert_called_once_with("INFO")

    @patch("mcp_coder.cli.main.setup_logging")
    @patch("mcp_coder.cli.main.create_parser")
    @patch("builtins.print")
    def test_main_unknown_command_returns_error(
        self, mock_print: Mock, mock_create_parser: Mock, mock_setup_logging: Mock
    ) -> None:
        """Test that main returns error for unknown commands."""
        mock_parser = Mock()
        mock_parser.parse_args.return_value = argparse.Namespace(
            command="unknown", log_level="INFO"
        )
        mock_create_parser.return_value = mock_parser

        result = main()

        assert result == 1
        mock_print.assert_called()
        mock_setup_logging.assert_called_once_with("INFO")

    @patch("mcp_coder.cli.main.setup_logging")
    @patch("mcp_coder.cli.main.create_parser")
    def test_main_keyboard_interrupt_returns_1(
        self, mock_create_parser: Mock, mock_setup_logging: Mock
    ) -> None:
        """Test that main handles KeyboardInterrupt gracefully."""
        mock_parser = Mock()
        # For KeyboardInterrupt, the exception occurs before we get log_level,
        # so we need to mock the args parsing to succeed first
        mock_parser.parse_args.return_value = argparse.Namespace(
            command=None, log_level="INFO"
        )
        mock_create_parser.return_value = mock_parser

        # Patch the handle_no_command to raise KeyboardInterrupt
        with patch(
            "mcp_coder.cli.main.handle_no_command", side_effect=KeyboardInterrupt()
        ):
            with patch("builtins.print"):
                result = main()

        assert result == 1
        mock_setup_logging.assert_called_once_with("INFO")

    @patch("mcp_coder.cli.main.setup_logging")
    @patch("mcp_coder.cli.main.create_parser")
    def test_main_unexpected_exception_returns_2(
        self, mock_create_parser: Mock, mock_setup_logging: Mock
    ) -> None:
        """Test that main handles unexpected exceptions."""
        mock_parser = Mock()
        # For unexpected exceptions, the exception occurs after we get log_level,
        # so we need args parsing to succeed first
        mock_parser.parse_args.return_value = argparse.Namespace(
            command=None, log_level="INFO"
        )
        mock_create_parser.return_value = mock_parser

        # Patch the handle_no_command to raise an unexpected exception
        with patch(
            "mcp_coder.cli.main.handle_no_command", side_effect=Exception("Test error")
        ):
            with patch("builtins.print"):
                result = main()

        assert result == 2
        mock_setup_logging.assert_called_once_with("INFO")

    @patch("mcp_coder.cli.main.setup_logging")
    @patch("mcp_coder.cli.main.handle_no_command")
    @patch("mcp_coder.cli.main.create_parser")
    def test_main_custom_log_level(
        self,
        mock_create_parser: Mock,
        mock_handle_no_command: Mock,
        mock_setup_logging: Mock,
    ) -> None:
        """Test that main uses custom log level when provided."""
        mock_parser = Mock()
        mock_parser.parse_args.return_value = argparse.Namespace(
            command=None, log_level="DEBUG"
        )
        mock_create_parser.return_value = mock_parser
        mock_handle_no_command.return_value = 1

        result = main()

        assert result == 1
        mock_handle_no_command.assert_called_once()
        mock_setup_logging.assert_called_once_with("DEBUG")

    @patch("mcp_coder.cli.main.setup_logging")
    @patch("mcp_coder.cli.main.execute_help")
    @patch("mcp_coder.cli.main.create_parser")
    def test_main_error_log_level(
        self,
        mock_create_parser: Mock,
        mock_execute_help: Mock,
        mock_setup_logging: Mock,
    ) -> None:
        """Test that main works with ERROR log level."""
        mock_parser = Mock()
        mock_parser.parse_args.return_value = argparse.Namespace(
            command="help", log_level="ERROR"
        )
        mock_create_parser.return_value = mock_parser
        mock_execute_help.return_value = 0

        result = main()

        assert result == 0
        mock_execute_help.assert_called_once()
        mock_setup_logging.assert_called_once_with("ERROR")


class TestCLIEntryPoint:
    """Test CLI entry point configuration."""

    def test_cli_entry_point_exists(self) -> None:
        """Test that CLI entry point is properly configured."""
        # Main already imported at module level - verify it's callable
        assert callable(main)

    def test_main_can_be_imported_from_cli_module(self) -> None:
        """Test that main can be imported from CLI module."""
        # Main already imported at module level - verify it's callable
        assert callable(main)


class TestCoordinatorCommand:
    """Tests for coordinator command CLI integration."""

    def test_coordinator_test_command_parsing(self) -> None:
        """Test that coordinator test command is parsed correctly."""
        # Setup
        parser = create_parser()

        # Execute
        args = parser.parse_args(
            ["coordinator", "test", "mcp_coder", "--branch-name", "feature-x"]
        )

        # Verify
        assert args.command == "coordinator"
        assert args.coordinator_subcommand == "test"
        assert args.repo_name == "mcp_coder"
        assert args.branch_name == "feature-x"
        assert args.log_level == "INFO"  # default

    def test_coordinator_test_requires_branch_name(self) -> None:
        """Test that --branch-name is required."""
        parser = create_parser()

        # Should raise SystemExit when --branch-name is missing
        with pytest.raises(SystemExit):
            parser.parse_args(["coordinator", "test", "mcp_coder"])

    @patch("mcp_coder.cli.main.execute_coordinator_test")
    def test_coordinator_test_executes_handler(self, mock_execute: Mock) -> None:
        """Test that coordinator test calls execute_coordinator_test."""
        # Setup
        mock_execute.return_value = 0

        # Execute
        with patch(
            "sys.argv",
            [
                "mcp-coder",
                "coordinator",
                "test",
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
    def test_coordinator_test_with_log_level(self, mock_execute: Mock) -> None:
        """Test coordinator test respects --log-level flag."""
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
                "test",
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
        assert call_args.log_level == "DEBUG"

    @patch("mcp_coder.cli.main.logger")
    @patch("builtins.print")
    def test_coordinator_no_subcommand_shows_error(
        self, mock_print: Mock, mock_logger: Mock
    ) -> None:
        """Test that coordinator without subcommand shows error."""
        # Execute
        with patch("sys.argv", ["mcp-coder", "coordinator"]):
            result = main()

        # Verify
        assert result == 1
        mock_logger.error.assert_called_with("Coordinator subcommand required")
        mock_print.assert_called_with(
            "Error: Please specify a coordinator subcommand (e.g., 'test', 'run')"
        )


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
            ["mcp-coder", "coordinator", "run", "--repo", "mcp_coder"],
        ):
            result = main()

        # Verify
        assert result == 0
        mock_execute.assert_called_once()

        # Check args passed to handler
        call_args = mock_execute.call_args[0][0]
        assert call_args.command == "coordinator"
        assert call_args.coordinator_subcommand == "run"
        assert call_args.repo == "mcp_coder"
        assert call_args.all is False
        assert call_args.log_level == "INFO"  # default

    @patch("mcp_coder.cli.main.execute_coordinator_run")
    def test_coordinator_run_with_all_argument(self, mock_execute: Mock) -> None:
        """Test CLI routing for --all mode."""
        # Setup
        mock_execute.return_value = 0

        # Execute
        with patch(
            "sys.argv",
            ["mcp-coder", "coordinator", "run", "--all"],
        ):
            result = main()

        # Verify
        assert result == 0
        mock_execute.assert_called_once()

        # Check args passed to handler
        call_args = mock_execute.call_args[0][0]
        assert call_args.command == "coordinator"
        assert call_args.coordinator_subcommand == "run"
        assert call_args.all is True
        assert call_args.repo is None
        assert call_args.log_level == "INFO"  # default

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
                "run",
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
        assert call_args.coordinator_subcommand == "run"
        assert call_args.repo == "mcp_coder"
        assert call_args.all is False
        assert call_args.log_level == "DEBUG"
