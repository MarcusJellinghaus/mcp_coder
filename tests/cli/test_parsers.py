"""Unit tests for HelpHintArgumentParser."""

from __future__ import annotations

import pytest

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
