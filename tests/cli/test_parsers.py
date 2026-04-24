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


class TestICoderSessionArgs:
    """Tests for icoder session continuation arguments."""

    def _parse(self, *args: str) -> argparse.Namespace:
        """Parse CLI args using the full parser."""
        parser = create_parser()
        return parser.parse_args(list(args))

    def test_icoder_parser_continue_session_flag(self) -> None:
        """icoder --continue-session sets continue_session=True."""
        args = self._parse("icoder", "--continue-session")
        assert args.continue_session is True

    def test_icoder_parser_continue_session_from(self) -> None:
        """icoder --continue-session-from sets the file path."""
        args = self._parse("icoder", "--continue-session-from", "/path/to/file")
        assert args.continue_session_from == "/path/to/file"

    def test_icoder_parser_session_id(self) -> None:
        """icoder --session-id sets the session ID."""
        args = self._parse("icoder", "--session-id", "abc123")
        assert args.session_id == "abc123"

    def test_icoder_parser_default_no_continuation(self) -> None:
        """icoder with no flags has continuation defaults."""
        args = self._parse("icoder")
        assert args.continue_session is False
        assert args.session_id is None

    def test_icoder_parser_timeout_default(self) -> None:
        """icoder with no --timeout flag defaults to 300."""
        args = self._parse("icoder")
        assert args.timeout == 300

    def test_icoder_parser_timeout_custom(self) -> None:
        """icoder --timeout 600 sets timeout=600."""
        args = self._parse("icoder", "--timeout", "600")
        assert args.timeout == 600

    def test_icoder_parser_continue_flags_mutually_exclusive(self) -> None:
        """--continue-session and --continue-session-from are mutually exclusive."""
        with pytest.raises(SystemExit):
            self._parse(
                "icoder", "--continue-session", "--continue-session-from", "/path"
            )


class TestDefineLabelsParser:
    """Tests for define-labels CLI flags."""

    def _parse(self, *args: str) -> argparse.Namespace:
        """Parse CLI args using the full parser."""
        parser = create_parser()
        return parser.parse_args(list(args))

    def test_default_flags_are_false(self) -> None:
        """All optional flags default to False/None."""
        args = self._parse("gh-tool", "define-labels")
        assert args.init is False
        assert args.validate is False
        assert args.config is None
        assert args.generate_github_actions is False
        assert args.all is False

    def test_init_flag(self) -> None:
        """--init sets args.init=True."""
        args = self._parse("gh-tool", "define-labels", "--init")
        assert args.init is True

    def test_validate_flag(self) -> None:
        """--validate sets args.validate=True."""
        args = self._parse("gh-tool", "define-labels", "--validate")
        assert args.validate is True

    def test_config_flag(self) -> None:
        """--config path/to/config.json sets args.config."""
        args = self._parse(
            "gh-tool", "define-labels", "--config", "path/to/config.json"
        )
        assert args.config == "path/to/config.json"

    def test_generate_github_actions_flag(self) -> None:
        """--generate-github-actions sets args.generate_github_actions=True."""
        args = self._parse("gh-tool", "define-labels", "--generate-github-actions")
        assert args.generate_github_actions is True

    def test_all_flag(self) -> None:
        """--all sets args.all=True."""
        args = self._parse("gh-tool", "define-labels", "--all")
        assert args.all is True

    def test_combined_flags(self) -> None:
        """Multiple flags can be combined."""
        args = self._parse(
            "gh-tool",
            "define-labels",
            "--init",
            "--validate",
            "--config",
            "my.json",
            "--generate-github-actions",
            "--all",
        )
        assert args.init is True
        assert args.validate is True
        assert args.config == "my.json"
        assert args.generate_github_actions is True
        assert args.all is True


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


class TestCommitPushFlag:
    """Tests for --push flag on commit auto and commit clipboard."""

    def _parse(self, *args: str) -> argparse.Namespace:
        """Parse CLI args using the full parser."""
        parser = create_parser()
        return parser.parse_args(list(args))

    def test_commit_auto_accepts_push_flag(self) -> None:
        """commit auto --push sets args.push=True."""
        args = self._parse("commit", "auto", "--push")
        assert args.push is True

    def test_commit_clipboard_accepts_push_flag(self) -> None:
        """commit clipboard --push sets args.push=True."""
        args = self._parse("commit", "clipboard", "--push")
        assert args.push is True

    def test_commit_auto_push_default_false(self) -> None:
        """commit auto without --push defaults to False."""
        args = self._parse("commit", "auto")
        assert args.push is False

    def test_commit_clipboard_push_default_false(self) -> None:
        """commit clipboard without --push defaults to False."""
        args = self._parse("commit", "clipboard")
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
