"""Tests for CLI main entry point."""

import argparse
import logging
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.main import (
    _resolve_log_level,
    create_parser,
    main,
)


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
        # --version triggers SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(["--version"])

    def test_parser_help_flag_stored_as_bool(self) -> None:
        """Test --help is stored as boolean, not intercepted by argparse."""
        parser = create_parser()
        args = parser.parse_args(["--help"])
        assert args.help is True

    def test_parser_h_flag_stored_as_bool(self) -> None:
        """Test -h is stored as boolean, not intercepted by argparse."""
        parser = create_parser()
        args = parser.parse_args(["-h"])
        assert args.help is True

    def test_parser_no_help_flag_default_false(self) -> None:
        """Test help defaults to False when not provided."""
        parser = create_parser()
        args = parser.parse_args([])
        assert args.help is False

    def test_parser_has_subparsers(self) -> None:
        """Test parser has subcommand structure."""
        parser = create_parser()
        # Check that subparsers exist (they should be accessible via _subparsers)
        assert hasattr(parser, "_subparsers")

    def test_parser_has_log_level_argument(self) -> None:
        """Test parser includes log level argument."""
        parser = create_parser()
        # Test parsing with log level
        args = parser.parse_args(["--log-level", "DEBUG", "init"])
        assert args.log_level == "DEBUG"
        assert args.command == "init"

    def test_parser_log_level_default(self) -> None:
        """Test log level has correct default value."""
        parser = create_parser()
        args = parser.parse_args(["init"])
        assert args.log_level is None

    def test_parser_log_level_choices(self) -> None:
        """Test log level validates choices."""
        parser = create_parser()
        # Valid choices should work
        for level in ["DEBUG", "INFO", "OUTPUT", "WARNING", "ERROR", "CRITICAL"]:
            args = parser.parse_args(["--log-level", level, "init"])
            assert args.log_level == level

        # Invalid choice should raise SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(["--log-level", "INVALID", "init"])


class TestLogLevelResolution:
    """Tests for _resolve_log_level function."""

    def test_log_level_default_is_none(self) -> None:
        """Test that parser default for --log-level is None."""
        parser = create_parser()
        args = parser.parse_args(["help"])
        assert args.log_level is None

    def test_resolve_log_level_coordinator_defaults_info(self) -> None:
        """Test that coordinator command defaults to INFO."""
        args = argparse.Namespace(command="coordinator", log_level=None)
        assert _resolve_log_level(args) == "INFO"

    def test_resolve_log_level_vscodeclaude_launch_default_output(self) -> None:
        """Test that vscodeclaude launch defaults to OUTPUT."""
        args = argparse.Namespace(
            command="vscodeclaude", log_level=None, vscodeclaude_subcommand="launch"
        )
        assert _resolve_log_level(args) == "OUTPUT"

    def test_resolve_log_level_vscodeclaude_status_default_output(self) -> None:
        """Test that vscodeclaude status defaults to OUTPUT."""
        args = argparse.Namespace(
            command="vscodeclaude", log_level=None, vscodeclaude_subcommand="status"
        )
        assert _resolve_log_level(args) == "OUTPUT"

    def test_resolve_log_level_other_commands_default_output(self) -> None:
        """Test that non-workflow commands default to OUTPUT."""
        for cmd in [
            "help",
            "verify",
            "check",
            "gh-tool",
            "git-tool",
            "commit",
            "init",
            "prompt",
            "create-plan",
            "implement",
            "create-pr",
            "vscodeclaude",
        ]:
            args = argparse.Namespace(command=cmd, log_level=None)
            assert _resolve_log_level(args) == "OUTPUT", f"Expected OUTPUT for {cmd}"

    def test_resolve_log_level_explicit_overrides_default(self) -> None:
        """Test that explicit --log-level always wins."""
        args = argparse.Namespace(command="help", log_level="DEBUG")
        assert _resolve_log_level(args) == "DEBUG"

        args = argparse.Namespace(command="implement", log_level="WARNING")
        assert _resolve_log_level(args) == "WARNING"

    def test_resolve_log_level_none_command(self) -> None:
        """Test that None command (no command provided) defaults to OUTPUT."""
        args = argparse.Namespace(command=None, log_level=None)
        assert _resolve_log_level(args) == "OUTPUT"


class TestNoCommandShowsHelp:
    """Test that no command shows unified help."""

    def test_no_command_prints_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that running with no command prints help text."""
        with patch("sys.argv", ["mcp-coder"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert (
            "mcp-coder - AI-powered software development automation toolkit"
            in captured.out
        )
        assert "commit" in captured.out


class TestMain:
    """Test main CLI entry point."""

    def test_main_no_args_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that main with no command prints unified help."""
        with patch("sys.argv", ["mcp-coder"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert (
            "mcp-coder - AI-powered software development automation toolkit"
            in captured.out
        )

    def test_main_help_command(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test 'mcp-coder help' command shows unified help."""
        with patch("sys.argv", ["mcp-coder", "help"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert (
            "mcp-coder - AI-powered software development automation toolkit"
            in captured.out
        )

    def test_main_help_flag_shows_help(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test 'mcp-coder --help' shows categorized help (not argparse)."""
        with patch("sys.argv", ["mcp-coder", "--help"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "SETUP" in captured.out
        assert "TOOLS" in captured.out
        assert "OPTIONS" in captured.out

    def test_main_h_flag_shows_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test 'mcp-coder -h' shows categorized help."""
        with patch("sys.argv", ["mcp-coder", "-h"]):
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "SETUP" in captured.out
        assert "TOOLS" in captured.out

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
            command=None, log_level="INFO", help=False
        )
        mock_create_parser.return_value = mock_parser

        # Patch get_help_text to raise KeyboardInterrupt
        with patch("mcp_coder.cli.main.get_help_text", side_effect=KeyboardInterrupt()):
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
            command=None, log_level="INFO", help=False
        )
        mock_create_parser.return_value = mock_parser

        # Patch get_help_text to raise an unexpected exception
        with patch(
            "mcp_coder.cli.main.get_help_text", side_effect=Exception("Test error")
        ):
            with patch("builtins.print"):
                result = main()

        assert result == 2
        mock_setup_logging.assert_called_once_with("INFO")

    @patch("mcp_coder.cli.main.setup_logging")
    @patch("mcp_coder.cli.main.create_parser")
    def test_main_custom_log_level(
        self,
        mock_create_parser: Mock,
        mock_setup_logging: Mock,
    ) -> None:
        """Test that main uses custom log level when provided."""
        mock_parser = Mock()
        mock_parser.parse_args.return_value = argparse.Namespace(
            command=None, log_level="DEBUG", help=False
        )
        mock_create_parser.return_value = mock_parser

        with patch("builtins.print"):
            result = main()

        assert result == 0
        mock_setup_logging.assert_called_once_with("DEBUG")

    @patch("mcp_coder.cli.main.setup_logging")
    @patch("mcp_coder.cli.main.create_parser")
    def test_main_error_log_level(
        self,
        mock_create_parser: Mock,
        mock_setup_logging: Mock,
    ) -> None:
        """Test that main works with ERROR log level."""
        mock_parser = Mock()
        mock_parser.parse_args.return_value = argparse.Namespace(
            command="help", log_level="ERROR", help=False
        )
        mock_create_parser.return_value = mock_parser

        with patch("builtins.print"):
            result = main()

        assert result == 0
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


class TestExecutionDirArgument:
    """Tests for --execution-dir CLI argument."""

    def test_execution_dir_defaults_to_none(self) -> None:
        """--execution-dir should default to None when not specified."""
        parser = create_parser()
        args = parser.parse_args(["prompt", "test prompt", "--project-dir", "."])
        assert args.execution_dir is None

    def test_execution_dir_accepts_absolute_path(self) -> None:
        """--execution-dir should accept absolute paths."""
        parser = create_parser()
        args = parser.parse_args(
            ["prompt", "test prompt", "--execution-dir", "/tmp/workspace"]
        )
        assert args.execution_dir == "/tmp/workspace"

    def test_execution_dir_accepts_relative_path(self) -> None:
        """--execution-dir should accept relative paths."""
        parser = create_parser()
        args = parser.parse_args(
            ["prompt", "test prompt", "--execution-dir", "./subdir"]
        )
        assert args.execution_dir == "./subdir"

    def test_execution_dir_on_prompt_command(self) -> None:
        """Verify --execution-dir works with prompt command."""
        parser = create_parser()
        args = parser.parse_args(
            ["prompt", "test prompt", "--execution-dir", "/workspace"]
        )
        assert args.command == "prompt"
        assert args.execution_dir == "/workspace"
        assert args.prompt == "test prompt"

    def test_execution_dir_on_commit_auto(self) -> None:
        """Verify --execution-dir works with commit auto command."""
        parser = create_parser()
        args = parser.parse_args(["commit", "auto", "--execution-dir", "/workspace"])
        assert args.command == "commit"
        assert args.commit_mode == "auto"
        assert args.execution_dir == "/workspace"

    def test_execution_dir_on_implement(self) -> None:
        """Verify --execution-dir works with implement command."""
        parser = create_parser()
        args = parser.parse_args(["implement", "--execution-dir", "/workspace"])
        assert args.command == "implement"
        assert args.execution_dir == "/workspace"

    def test_execution_dir_on_create_plan(self) -> None:
        """Verify --execution-dir works with create-plan command."""
        parser = create_parser()
        args = parser.parse_args(
            ["create-plan", "123", "--execution-dir", "/workspace"]
        )
        assert args.command == "create-plan"
        assert args.execution_dir == "/workspace"
        assert args.issue_number == 123

    def test_execution_dir_on_create_pr(self) -> None:
        """Verify --execution-dir works with create-pr command."""
        parser = create_parser()
        args = parser.parse_args(["create-pr", "--execution-dir", "/workspace"])
        assert args.command == "create-pr"
        assert args.execution_dir == "/workspace"


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


class TestCheckBranchStatusCommand:
    """Tests for check branch-status CLI integration."""

    def test_check_branch_status_parser_creation(self) -> None:
        """Test that check branch-status parser is created correctly."""
        parser = create_parser()

        # Test basic parsing with minimal args
        args = parser.parse_args(["check", "branch-status"])
        assert args.command == "check"
        assert args.check_subcommand == "branch-status"

    def test_check_branch_status_default_args(self) -> None:
        """Test check branch-status command with default arguments."""
        parser = create_parser()
        args = parser.parse_args(["check", "branch-status"])

        assert args.command == "check"
        assert args.check_subcommand == "branch-status"
        assert args.project_dir is None
        assert args.fix == 0
        assert args.llm_truncate is False
        assert args.llm_method is None  # None = resolve at runtime from config
        assert args.mcp_config is None
        assert args.execution_dir is None

    def test_check_branch_status_with_fix_flag(self) -> None:
        """Test check branch-status command with --fix flag."""
        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--fix"])

        assert args.command == "check"
        assert args.check_subcommand == "branch-status"
        assert args.fix == 1
        assert args.llm_truncate is False

    def test_check_branch_status_with_llm_truncate(self) -> None:
        """Test check branch-status command with --llm-truncate flag."""
        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--llm-truncate"])

        assert args.command == "check"
        assert args.check_subcommand == "branch-status"
        assert args.llm_truncate is True
        assert args.fix == 0

    def test_check_branch_status_with_project_dir(self) -> None:
        """Test check branch-status command with custom project directory."""
        parser = create_parser()
        args = parser.parse_args(
            ["check", "branch-status", "--project-dir", "/path/to/project"]
        )

        assert args.command == "check"
        assert args.check_subcommand == "branch-status"
        assert args.project_dir == "/path/to/project"

    def test_check_branch_status_with_llm_method(self) -> None:
        """Test check branch-status command with different LLM methods."""
        parser = create_parser()

        # Test claude
        args = parser.parse_args(["check", "branch-status", "--llm-method", "claude"])
        assert args.llm_method == "claude"

    def test_check_branch_status_with_mcp_config(self) -> None:
        """Test check branch-status command with MCP config path."""
        parser = create_parser()
        args = parser.parse_args(
            ["check", "branch-status", "--mcp-config", ".mcp.linux.json"]
        )

        assert args.command == "check"
        assert args.check_subcommand == "branch-status"
        assert args.mcp_config == ".mcp.linux.json"

    def test_check_branch_status_with_execution_dir(self) -> None:
        """Test check branch-status command with execution directory."""
        parser = create_parser()
        args = parser.parse_args(
            ["check", "branch-status", "--execution-dir", "/workspace"]
        )

        assert args.command == "check"
        assert args.check_subcommand == "branch-status"
        assert args.execution_dir == "/workspace"

    def test_check_branch_status_with_all_flags(self) -> None:
        """Test check branch-status command with all flags combined."""
        parser = create_parser()
        args = parser.parse_args(
            [
                "check",
                "branch-status",
                "--project-dir",
                "/path/to/project",
                "--fix",
                "--llm-truncate",
                "--llm-method",
                "claude",
                "--mcp-config",
                ".mcp.test.json",
                "--execution-dir",
                "/tmp/workspace",
            ]
        )

        assert args.command == "check"
        assert args.check_subcommand == "branch-status"
        assert args.project_dir == "/path/to/project"
        assert args.fix == 1
        assert args.llm_truncate is True
        assert args.llm_method == "claude"
        assert args.mcp_config == ".mcp.test.json"
        assert args.execution_dir == "/tmp/workspace"

    @patch("mcp_coder.cli.commands.check_branch_status.execute_check_branch_status")
    def test_check_branch_status_routing(self, mock_execute: Mock) -> None:
        """Test that check branch-status command routes to correct handler."""
        # Setup
        mock_execute.return_value = 0

        # Execute
        with patch("sys.argv", ["mcp-coder", "check", "branch-status"]):
            result = main()

        # Verify
        assert result == 0
        mock_execute.assert_called_once()

        # Check args passed to handler
        call_args = mock_execute.call_args[0][0]
        assert call_args.command == "check"
        assert call_args.check_subcommand == "branch-status"
        assert call_args.fix == 0
        assert call_args.llm_truncate is False

    @patch("mcp_coder.cli.commands.check_branch_status.execute_check_branch_status")
    def test_check_branch_status_routing_with_flags(self, mock_execute: Mock) -> None:
        """Test routing with all command flags."""
        # Setup
        mock_execute.return_value = 0

        # Execute
        with patch(
            "sys.argv",
            [
                "mcp-coder",
                "check",
                "branch-status",
                "--fix",
                "--llm-truncate",
                "--project-dir",
                "/test/path",
            ],
        ):
            result = main()

        # Verify
        assert result == 0
        mock_execute.assert_called_once()

        # Check args passed to handler
        call_args = mock_execute.call_args[0][0]
        assert call_args.command == "check"
        assert call_args.check_subcommand == "branch-status"
        assert call_args.fix == 1
        assert call_args.llm_truncate is True
        assert call_args.project_dir == "/test/path"

    def test_check_branch_status_invalid_llm_method(self) -> None:
        """Test error when invalid LLM method provided."""
        parser = create_parser()

        # Should raise SystemExit when invalid LLM method is provided
        with pytest.raises(SystemExit):
            parser.parse_args(
                ["check", "branch-status", "--llm-method", "invalid_method"]
            )

    def test_check_no_subcommand_shows_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that check without subcommand shows error and help hint."""
        with caplog.at_level(logging.DEBUG):
            with patch("sys.argv", ["mcp-coder", "check"]):
                result = main()

        assert result == 1
        assert "Please specify a check subcommand" in caplog.text
        assert "Try 'mcp-coder check --help' for more information." in caplog.text


class TestHelpHintIntegration:
    """Tests for help hint display on argument errors and manual error paths."""

    def test_unrecognized_arg_shows_help_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that unrecognized top-level args show help hint on stderr."""
        with patch("sys.argv", ["mcp-coder", "--resume-session"]):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "unrecognized arguments: --resume-session" in captured.err
        assert "Try 'mcp-coder --help' for more information." in captured.err

    def test_subcommand_unrecognized_arg_shows_help_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that unrecognized subcommand args show help hint."""
        with patch(
            "sys.argv", ["mcp-coder", "check", "branch-status", "--nonexistent"]
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        assert "unrecognized arguments: --nonexistent" in captured.err
        assert "--help' for more information." in captured.err

    def test_gh_tool_no_subcommand_shows_help_hint(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that gh-tool without subcommand shows help hint."""
        with caplog.at_level(logging.DEBUG):
            with patch("sys.argv", ["mcp-coder", "gh-tool"]):
                result = main()

        assert result == 1
        assert "Please specify a gh-tool subcommand" in caplog.text
        assert "Try 'mcp-coder gh-tool --help' for more information." in caplog.text

    def test_vscodeclaude_no_subcommand_shows_help_hint(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that vscodeclaude without subcommand shows help hint."""
        with caplog.at_level(logging.DEBUG):
            with patch("sys.argv", ["mcp-coder", "vscodeclaude"]):
                result = main()

        assert result == 1
        assert "Please specify a subcommand" in caplog.text
        assert (
            "Try 'mcp-coder vscodeclaude --help' for more information." in caplog.text
        )

    def test_git_tool_no_subcommand_shows_help_hint(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that git-tool without subcommand shows help hint."""
        with caplog.at_level(logging.DEBUG):
            with patch("sys.argv", ["mcp-coder", "git-tool"]):
                result = main()

        assert result == 1
        assert "Please specify a git-tool subcommand" in caplog.text
        assert "Try 'mcp-coder git-tool --help' for more information." in caplog.text

    @pytest.mark.parametrize(
        "argv,expected_error",
        [
            (
                ["mcp-coder", "coordinator", "--dry-run", "--branch-name", "feat-x"],
                "--dry-run requires --repo NAME",
            ),
            (
                ["mcp-coder", "coordinator", "--dry-run", "--repo", "mcp_coder"],
                "--dry-run requires --branch-name BRANCH",
            ),
            (
                ["mcp-coder", "coordinator"],
                "Either --all or --repo must be specified",
            ),
        ],
        ids=[
            "dry-run-requires-repo",
            "dry-run-requires-branch-name",
            "either-all-or-repo",
        ],
    )
    def test_coordinator_no_flags_shows_help_hint(
        self,
        argv: list[str],
        expected_error: str,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Test that coordinator error paths show help hint."""
        with caplog.at_level(logging.DEBUG):
            with patch("sys.argv", argv):
                result = main()

        assert result == 1
        assert expected_error in caplog.text
        assert "Try 'mcp-coder coordinator --help' for more information." in caplog.text

    def test_commit_no_subcommand_shows_help_hint(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that commit without subcommand shows help hint."""
        with caplog.at_level(logging.DEBUG):
            with patch("sys.argv", ["mcp-coder", "commit"]):
                result = main()

        assert result == 1
        assert "is not yet implemented" in caplog.text
        assert "Try 'mcp-coder commit --help' for more information." in caplog.text
