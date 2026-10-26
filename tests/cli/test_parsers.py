"""Unit tests for HelpHintArgumentParser and CLI parser flags."""

from __future__ import annotations

import argparse

import pytest

from mcp_coder.cli.main import create_parser
from mcp_coder.cli.parsers import HelpHintArgumentParser


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
