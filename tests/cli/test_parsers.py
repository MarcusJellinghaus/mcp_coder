"""Unit tests for HelpHintArgumentParser and CLI parser flags."""

from __future__ import annotations

import argparse
import logging
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.main import create_parser, main
from mcp_coder.cli.parsers import HelpHintArgumentParser


@pytest.mark.parametrize(
    "argv",
    [
        ["prompt", "hi", "--execution-dir", "/tmp/x"],
        ["commit", "auto", "--execution-dir", "/tmp/x"],
        ["implement", "--execution-dir", "/tmp/x"],
        ["review-plan", "--execution-dir", "/tmp/x"],
        ["review-implementation", "--execution-dir", "/tmp/x"],
        ["create-plan", "123", "--execution-dir", "/tmp/x"],
        ["rebase", "--execution-dir", "/tmp/x"],
        ["create-pr", "--execution-dir", "/tmp/x"],
        ["check", "branch-status", "--execution-dir", "/tmp/x"],
        ["icoder", "--execution-dir", "/tmp/x"],
    ],
)
def test_execution_dir_flag_rejected(argv: list[str]) -> None:
    """The removed flag must fail loudly, not be silently ignored."""
    with pytest.raises(SystemExit):
        create_parser().parse_args(argv)


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
            ]
        )

        assert args.command == "check"
        assert args.check_subcommand == "branch-status"
        assert args.project_dir == "/path/to/project"
        assert args.fix == 1
        assert args.llm_truncate is True
        assert args.llm_method == "claude"
        assert args.mcp_config == ".mcp.test.json"

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


class TestHelpHintArgumentParser:
    """Tests for HelpHintArgumentParser.error() behavior."""

    def test_error_appends_help_hint(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Error output includes the 'Try ... --help' hint line."""
        parser = HelpHintArgumentParser(prog="mcp-coder")
        with pytest.raises(SystemExit):
            parser.error("unrecognized arguments: --foo")
        captured = capsys.readouterr()
        assert "Try 'mcp-coder --help' for more information." in captured.err

    def test_error_exits_with_code_2(self) -> None:
        """Parser errors exit with code 2 (POSIX/argparse convention)."""
        parser = HelpHintArgumentParser(prog="mcp-coder")
        with pytest.raises(SystemExit) as exc_info:
            parser.error("bad argument")
        assert exc_info.value.code == 2

    def test_error_includes_prog_name_in_hint(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The hint line uses the parser's prog name."""
        parser = HelpHintArgumentParser(prog="my-tool")
        with pytest.raises(SystemExit):
            parser.error("something wrong")
        captured = capsys.readouterr()
        assert "Try 'my-tool --help' for more information." in captured.err
        assert "my-tool: error: something wrong" in captured.err

    def test_subparser_inherits_help_hint_class(self) -> None:
        """Subparsers created via add_subparsers use HelpHintArgumentParser."""
        parser = HelpHintArgumentParser(prog="mcp-coder")
        subparsers = parser.add_subparsers(dest="command")
        sub = subparsers.add_parser("prompt")
        assert isinstance(sub, HelpHintArgumentParser)

    def test_subparser_error_uses_subcommand_prog(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Subparser error hint references the subcommand prog name."""
        parser = HelpHintArgumentParser(prog="mcp-coder")
        subparsers = parser.add_subparsers(dest="command")
        sub = subparsers.add_parser("prompt")
        with pytest.raises(SystemExit):
            sub.error("missing argument")
        captured = capsys.readouterr()
        assert "Try 'mcp-coder prompt --help' for more information." in captured.err


class TestCommitPushFlag:
    """Tests for --push flag on commit auto."""

    def _parse(self, *args: str) -> argparse.Namespace:
        """Parse CLI args using the full parser."""
        parser = create_parser()
        return parser.parse_args(list(args))

    def test_commit_auto_accepts_push_flag(self) -> None:
        """commit auto --push sets args.push=True."""
        args = self._parse("commit", "auto", "--push")
        assert args.push is True

    def test_commit_auto_push_default_false(self) -> None:
        """commit auto without --push defaults to False."""
        args = self._parse("commit", "auto")
        assert args.push is False


class TestLlmMethodCopilotChoice:
    """Tests for --llm-method copilot acceptance in parsers."""

    def _parse(self, *args: str) -> argparse.Namespace:
        """Parse CLI args using the full parser."""
        parser = create_parser()
        return parser.parse_args(list(args))

    def test_prompt_parser_accepts_copilot(self) -> None:
        """--llm-method copilot is accepted by prompt parser."""
        args = self._parse("prompt", "hello", "--llm-method", "copilot")
        assert args.llm_method == "copilot"

    def test_prompt_parser_rejects_invalid(self) -> None:
        """--llm-method invalid is rejected by prompt parser."""
        with pytest.raises(SystemExit):
            self._parse("prompt", "hello", "--llm-method", "invalid")

    def test_implement_parser_accepts_copilot(self) -> None:
        """--llm-method copilot is accepted by implement parser."""
        args = self._parse("implement", "--llm-method", "copilot")
        assert args.llm_method == "copilot"
