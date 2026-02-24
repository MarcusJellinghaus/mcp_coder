"""Tests for check_branch_status CLI integration functionality."""

import argparse
import sys
from unittest.mock import Mock, patch

import pytest

# Test-first approach: Try to import the module, skip dependent tests if not available
try:
    from mcp_coder.cli.commands.check_branch_status import execute_check_branch_status

    CHECK_BRANCH_STATUS_MODULE_AVAILABLE = True
except ImportError:
    CHECK_BRANCH_STATUS_MODULE_AVAILABLE = False


class TestCheckBranchStatusParserEnhancements:
    """Test new parser parameters for CI waiting and fix retry."""

    def test_ci_timeout_parameter_defaults_to_zero(self) -> None:
        """Test --ci-timeout parameter defaults to 0."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status"])

        assert args.ci_timeout == 0

    def test_ci_timeout_accepts_integer_value(self) -> None:
        """Test --ci-timeout accepts integer values."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--ci-timeout", "180"])

        assert args.ci_timeout == 180

    def test_ci_timeout_rejects_negative_values(self) -> None:
        """Test --ci-timeout rejects negative values."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        with pytest.raises(SystemExit):  # argparse exits on validation error
            parser.parse_args(["check", "branch-status", "--ci-timeout", "-60"])

    def test_fix_without_argument_defaults_to_one(self) -> None:
        """Test --fix without argument equals 1 (fix once)."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--fix"])

        assert args.fix == 1

    def test_fix_with_integer_argument(self) -> None:
        """Test --fix with integer argument."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--fix", "3"])

        assert args.fix == 3

    def test_fix_zero_means_no_fix(self) -> None:
        """Test --fix 0 means no fix (same as not providing --fix)."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--fix", "0"])

        assert args.fix == 0

    def test_fix_not_provided_defaults_to_zero(self) -> None:
        """Test --fix not provided defaults to 0 (no fix)."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status"])

        assert args.fix == 0

    def test_all_parameters_together(self) -> None:
        """Test --ci-timeout and --fix together."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "check",
                "branch-status",
                "--ci-timeout",
                "300",
                "--fix",
                "2",
                "--llm-truncate",
            ]
        )

        assert args.ci_timeout == 300
        assert args.fix == 2
        assert args.llm_truncate is True


class TestCheckBranchStatusCommandIntegration:
    """Test check_branch_status command CLI integration."""

    @patch("mcp_coder.cli.commands.check_branch_status.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check", "branch-status"])
    def test_check_branch_status_command_calls_function(
        self, mock_execute: Mock
    ) -> None:
        """Test that the check branch-status CLI command calls the execution function."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0  # Success

        result = main()

        assert result == 0
        mock_execute.assert_called_once()

        # Check that the function was called with proper arguments
        call_args = mock_execute.call_args[0][0]  # First positional argument (args)
        assert isinstance(call_args, argparse.Namespace)
        assert hasattr(call_args, "project_dir")
        assert hasattr(call_args, "fix")
        assert hasattr(call_args, "llm_truncate")

    @patch("mcp_coder.cli.commands.check_branch_status.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check", "branch-status", "--fix"])
    def test_check_branch_status_command_with_fix_flag(
        self, mock_execute: Mock
    ) -> None:
        """Test check branch-status command with --fix flag."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0  # Success

        result = main()

        assert result == 0
        mock_execute.assert_called_once()

        # Check that fix flag was parsed correctly
        call_args = mock_execute.call_args[0][0]
        assert call_args.fix == 1

    @patch("mcp_coder.cli.commands.check_branch_status.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check", "branch-status", "--llm-truncate"])
    def test_check_branch_status_command_with_llm_truncate_flag(
        self, mock_execute: Mock
    ) -> None:
        """Test check branch-status command with --llm-truncate flag."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0  # Success

        result = main()

        assert result == 0
        mock_execute.assert_called_once()

        # Check that llm_truncate flag was parsed correctly
        call_args = mock_execute.call_args[0][0]
        assert call_args.llm_truncate is True

    @patch("mcp_coder.cli.commands.check_branch_status.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check", "branch-status"])
    def test_check_branch_status_command_propagates_return_code(
        self, mock_execute: Mock
    ) -> None:
        """Test that check branch-status command propagates the return code."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 1  # Error

        result = main()

        assert result == 1
        mock_execute.assert_called_once()

    def test_check_branch_status_command_is_implemented(self) -> None:
        """Test that check branch-status command is implemented in main CLI.

        This test verifies that the check branch-status command has been successfully
        added to the CLI.
        """
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Check if check command exists in parser
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]

        assert subparsers_actions, "No subparsers found in CLI parser"

        subparser = subparsers_actions[0]
        # Check if 'check' is in the choices
        assert (
            "check" in subparser.choices
        ), "check command should be implemented in main.py"

        # Verify the check parser has branch-status subcommand
        check_parser = subparser.choices["check"]

        # Get the branch-status subparser
        check_subparsers = [
            action
            for action in check_parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        assert check_subparsers, "No subparsers found in check parser"

        branch_status_subparser = check_subparsers[0]
        assert (
            "branch-status" in branch_status_subparser.choices
        ), "branch-status subcommand should be implemented under check"

        # Parse test arguments to verify structure
        branch_status_parser = branch_status_subparser.choices["branch-status"]
        test_args = branch_status_parser.parse_args(["--fix", "--llm-truncate"])
        assert hasattr(test_args, "project_dir")
        assert hasattr(test_args, "fix")
        assert hasattr(test_args, "llm_truncate")
        assert test_args.fix == 1
        assert test_args.llm_truncate is True
