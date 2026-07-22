"""Tests for the review-plan / review-implementation CLI commands.

These verify the thin command layer over ``run_review_workflow``: both verbs
delegate to a shared ``_execute_review`` that resolves args exactly like
``execute_implement`` and forwards the right :class:`ReviewConfig` plus resolved
params, propagating the workflow return code.
"""

import argparse
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.review import (
    execute_review_implementation,
    execute_review_plan,
)
from mcp_coder.cli.main import create_parser
from mcp_coder.workflows.review.config import REVIEW_IMPLEMENTATION, REVIEW_PLAN


def _make_args() -> argparse.Namespace:
    """Build a fake ``args`` namespace with the review command flags."""
    return argparse.Namespace(
        project_dir="/test/project",
        llm_method="claude",
        execution_dir=None,
        mcp_config=None,
        settings=None,
        update_issue_labels=None,
        post_issue_comments=None,
    )


class TestExecuteReview:
    """Tests for execute_review_plan / execute_review_implementation."""

    @patch("mcp_coder.cli.commands.review.resolve_issue_interaction_flags")
    @patch("mcp_coder.cli.commands.review.resolve_claude_settings_path")
    @patch("mcp_coder.cli.commands.review.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.review.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.review.resolve_project_dir")
    @patch("mcp_coder.cli.commands.review.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.review.resolve_llm_method")
    @patch("mcp_coder.cli.commands.review.run_review_workflow")
    def test_execute_review_plan_forwards_config_and_params(
        self,
        mock_run_workflow: Mock,
        mock_resolve_llm: Mock,
        mock_parse_llm: Mock,
        mock_resolve_dir: Mock,
        mock_resolve_exec: Mock,
        mock_resolve_mcp: Mock,
        mock_resolve_settings: Mock,
        mock_resolve_flags: Mock,
    ) -> None:
        """review-plan passes REVIEW_PLAN and resolved params; return propagates."""
        project_dir = Path("/test/project")
        execution_dir = Path.cwd()
        mock_resolve_dir.return_value = project_dir
        mock_resolve_exec.return_value = execution_dir
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_resolve_mcp.return_value = None
        mock_resolve_settings.return_value = None
        mock_resolve_flags.return_value = (False, False)
        mock_run_workflow.return_value = 0

        args = _make_args()
        result = execute_review_plan(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_resolve_exec.assert_called_once_with(None)
        mock_parse_llm.assert_called_once_with("claude")
        mock_resolve_flags.assert_called_once_with(args, project_dir)
        mock_run_workflow.assert_called_once_with(
            REVIEW_PLAN,
            project_dir,
            "claude",
            None,
            None,
            execution_dir,
            False,
            False,
        )

    @patch("mcp_coder.cli.commands.review.resolve_issue_interaction_flags")
    @patch("mcp_coder.cli.commands.review.resolve_claude_settings_path")
    @patch("mcp_coder.cli.commands.review.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.review.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.review.resolve_project_dir")
    @patch("mcp_coder.cli.commands.review.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.review.resolve_llm_method")
    @patch("mcp_coder.cli.commands.review.run_review_workflow")
    def test_execute_review_implementation_forwards_config(
        self,
        mock_run_workflow: Mock,
        mock_resolve_llm: Mock,
        mock_parse_llm: Mock,
        mock_resolve_dir: Mock,
        mock_resolve_exec: Mock,
        mock_resolve_mcp: Mock,
        mock_resolve_settings: Mock,
        mock_resolve_flags: Mock,
    ) -> None:
        """review-implementation passes REVIEW_IMPLEMENTATION; return propagates."""
        project_dir = Path("/test/project")
        execution_dir = Path.cwd()
        mock_resolve_dir.return_value = project_dir
        mock_resolve_exec.return_value = execution_dir
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_resolve_mcp.return_value = None
        mock_resolve_settings.return_value = None
        mock_resolve_flags.return_value = (True, True)
        mock_run_workflow.return_value = 1

        args = _make_args()
        args.update_issue_labels = True
        args.post_issue_comments = True

        result = execute_review_implementation(args)

        assert result == 1
        mock_run_workflow.assert_called_once_with(
            REVIEW_IMPLEMENTATION,
            project_dir,
            "claude",
            None,
            None,
            execution_dir,
            True,
            True,
        )

    @patch("mcp_coder.cli.commands.review.enable_crash_logging")
    @patch("mcp_coder.cli.commands.review.resolve_issue_interaction_flags")
    @patch("mcp_coder.cli.commands.review.resolve_claude_settings_path")
    @patch("mcp_coder.cli.commands.review.resolve_mcp_config_path")
    @patch("mcp_coder.cli.commands.review.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.review.resolve_project_dir")
    @patch("mcp_coder.cli.commands.review.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.review.resolve_llm_method")
    @patch("mcp_coder.cli.commands.review.run_review_workflow")
    def test_enable_crash_logging_uses_command_name(
        self,
        mock_run_workflow: Mock,
        mock_resolve_llm: Mock,
        mock_parse_llm: Mock,
        mock_resolve_dir: Mock,
        mock_resolve_exec: Mock,
        mock_resolve_mcp: Mock,
        mock_resolve_settings: Mock,
        mock_resolve_flags: Mock,
        mock_crash_logging: Mock,
    ) -> None:
        """Crash logging is tagged with the review verb name."""
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_resolve_exec.return_value = Path.cwd()
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_resolve_mcp.return_value = None
        mock_resolve_settings.return_value = None
        mock_resolve_flags.return_value = (False, False)
        mock_run_workflow.return_value = 0

        execute_review_plan(_make_args())

        mock_crash_logging.assert_called_once_with(project_dir, "review-plan")

    @patch("mcp_coder.cli.commands.review.resolve_project_dir")
    @patch("mcp_coder.cli.commands.review.resolve_llm_method")
    @patch("mcp_coder.cli.commands.review.parse_llm_method_from_args")
    @patch("mcp_coder.cli.commands.review.run_review_workflow")
    def test_execute_review_exception_handling(
        self,
        mock_run_workflow: Mock,
        mock_parse_llm: Mock,
        mock_resolve_llm: Mock,
        mock_resolve_dir: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An unexpected error is caught and returns exit code 1."""
        mock_resolve_dir.return_value = Path("/test/project")
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_run_workflow.side_effect = Exception("boom")

        with caplog.at_level(logging.DEBUG):
            result = execute_review_plan(_make_args())

        assert result == 1
        assert "boom" in caplog.text

    @patch("mcp_coder.cli.commands.review.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.review.resolve_project_dir")
    def test_invalid_execution_dir_returns_error(
        self,
        mock_resolve_dir: Mock,
        mock_resolve_exec: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An invalid execution dir (ValueError) returns exit code 1."""
        mock_resolve_dir.return_value = Path("/test/project")
        mock_resolve_exec.side_effect = ValueError("Directory does not exist")

        with caplog.at_level(logging.DEBUG):
            result = execute_review_implementation(_make_args())

        assert result == 1
        assert "Directory does not exist" in caplog.text


class TestReviewParsers:
    """Tests for the review-plan / review-implementation argument parsers."""

    def _parse(self, *args: str) -> argparse.Namespace:
        """Parse CLI args using the full parser."""
        parser = create_parser()
        return parser.parse_args(list(args))

    def test_review_plan_parses(self) -> None:
        """`mcp-coder review-plan` parses with the shared defaults."""
        args = self._parse("review-plan")
        assert args.command == "review-plan"
        assert args.project_dir is None
        assert args.llm_method is None
        assert args.update_issue_labels is None
        assert args.post_issue_comments is None

    def test_review_implementation_parses(self) -> None:
        """`mcp-coder review-implementation` parses with the shared defaults."""
        args = self._parse("review-implementation")
        assert args.command == "review-implementation"
        assert args.update_issue_labels is None
        assert args.post_issue_comments is None

    def test_no_update_issue_labels_flag(self) -> None:
        """--no-update-issue-labels sets the flag to False."""
        args = self._parse("review-plan", "--no-update-issue-labels")
        assert args.update_issue_labels is False

    def test_post_issue_comments_flag(self) -> None:
        """--post-issue-comments sets the flag to True."""
        args = self._parse("review-implementation", "--post-issue-comments")
        assert args.post_issue_comments is True

    def test_review_verbs_have_no_issue_positional(self) -> None:
        """The review verbs take no issue_number positional (branch-derived)."""
        with pytest.raises(SystemExit):
            self._parse("review-plan", "42")

    def test_shared_args_present(self) -> None:
        """Both verbs expose the shared project/llm/mcp/settings/exec args."""
        for verb in ("review-plan", "review-implementation"):
            args = self._parse(verb, "--llm-method", "claude")
            assert args.llm_method == "claude"
            assert hasattr(args, "project_dir")
            assert hasattr(args, "mcp_config")
            assert hasattr(args, "settings")
            assert hasattr(args, "execution_dir")
