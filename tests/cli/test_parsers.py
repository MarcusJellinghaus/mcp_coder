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


class TestBooleanOptionalFlags:
    """Tests for --update-issue-labels and --post-issue-comments flags."""

    def _parse(self, *args: str) -> argparse.Namespace:
        """Parse CLI args using the full parser."""
        parser = create_parser()
        return parser.parse_args(list(args))

    def test_update_issue_labels_default_none(self) -> None:
        """implement with no flag gives update_issue_labels=None."""
        args = self._parse("implement")
        assert args.update_issue_labels is None

    def test_update_issue_labels_true(self) -> None:
        """--update-issue-labels sets True."""
        args = self._parse("implement", "--update-issue-labels")
        assert args.update_issue_labels is True

    def test_update_issue_labels_false(self) -> None:
        """--no-update-issue-labels sets False."""
        args = self._parse("implement", "--no-update-issue-labels")
        assert args.update_issue_labels is False

    def test_post_issue_comments_default_none(self) -> None:
        """implement with no flag gives post_issue_comments=None."""
        args = self._parse("implement")
        assert args.post_issue_comments is None

    def test_post_issue_comments_true(self) -> None:
        """--post-issue-comments sets True."""
        args = self._parse("implement", "--post-issue-comments")
        assert args.post_issue_comments is True

    def test_post_issue_comments_false(self) -> None:
        """--no-post-issue-comments sets False."""
        args = self._parse("implement", "--no-post-issue-comments")
        assert args.post_issue_comments is False

    def test_old_update_labels_flag_removed(self) -> None:
        """--update-labels is no longer recognized."""
        with pytest.raises(SystemExit):
            self._parse("implement", "--update-labels")

    def test_flags_present_on_all_three_parsers(self) -> None:
        """implement, create-plan, and create-pr all have both flags."""
        for cmd_args in (
            ["implement"],
            ["create-plan", "42"],
            ["create-pr"],
        ):
            args = self._parse(*cmd_args)
            assert hasattr(
                args, "update_issue_labels"
            ), f"{cmd_args[0]} missing update_issue_labels"
            assert hasattr(
                args, "post_issue_comments"
            ), f"{cmd_args[0]} missing post_issue_comments"
            assert args.update_issue_labels is None
            assert args.post_issue_comments is None
