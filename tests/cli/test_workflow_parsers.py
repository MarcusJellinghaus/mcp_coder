from __future__ import annotations

import argparse

import pytest

from mcp_coder.cli.main import create_parser


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
            assert hasattr(args, "update_issue_labels"), (
                f"{cmd_args[0]} missing update_issue_labels"
            )
            assert hasattr(args, "post_issue_comments"), (
                f"{cmd_args[0]} missing post_issue_comments"
            )
            assert args.update_issue_labels is None
            assert args.post_issue_comments is None


class TestFixConflictParser:
    """Tests for the fix-conflict subparser wiring."""

    def _parse(self, *args: str) -> argparse.Namespace:
        """Parse CLI args using the full parser."""
        parser = create_parser()
        return parser.parse_args(list(args))

    def test_fix_conflict_parses_with_project_dir_only(self) -> None:
        """fix-conflict has --project-dir and no LLM-related arguments."""
        args = self._parse("fix-conflict")
        assert args.command == "fix-conflict"
        assert hasattr(args, "project_dir")
        assert not hasattr(args, "llm_method")


class TestFixCiParser:
    """Tests for the fix-ci subparser wiring."""

    def _parse(self, *args: str) -> argparse.Namespace:
        """Parse CLI args using the full parser."""
        parser = create_parser()
        return parser.parse_args(list(args))

    def test_fix_ci_parses_with_llm_arguments(self) -> None:
        """fix-ci has --project-dir and the LLM-related arguments."""
        args = self._parse("fix-ci")
        assert args.command == "fix-ci"
        assert hasattr(args, "project_dir")
        assert hasattr(args, "llm_method") is True
