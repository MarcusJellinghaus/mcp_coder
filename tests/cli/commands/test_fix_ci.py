"""Tests for the fix-ci CLI command handler."""

import argparse
import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.fix_ci import execute_fix_ci


class TestExecuteFixCi:
    """Tests for execute_fix_ci function."""

    @patch("mcp_coder.cli.commands.fix_ci.resolve_issue_interaction_flags")
    @patch("mcp_coder.cli.commands.fix_ci.resolve_claude_cwd")
    @patch("mcp_coder.cli.commands.fix_ci.resolve_project_dir")
    @patch("mcp_coder.cli.commands.fix_ci.run_fix_ci_workflow")
    @patch("mcp_coder.cli.commands.fix_ci.resolve_llm_method")
    @patch("mcp_coder.cli.commands.fix_ci.parse_llm_method_from_args")
    def test_execute_fix_ci_success(
        self,
        mock_parse_llm: Mock,
        mock_resolve_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        mock_resolve_exec: Mock,
        mock_resolve_flags: Mock,
    ) -> None:
        """Resolves project dir and returns run_fix_ci_workflow's exit code."""
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_resolve_exec.return_value = project_dir
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_resolve_flags.return_value = (False, False)
        mock_run_workflow.return_value = 0

        args = argparse.Namespace(
            project_dir="/test/project",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            update_issue_labels=None,
            post_issue_comments=None,
        )

        result = execute_fix_ci(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_resolve_exec.assert_called_once_with(project_dir)
        mock_parse_llm.assert_called_once_with("claude")
        mock_resolve_flags.assert_called_once_with(args, project_dir)
        mock_run_workflow.assert_called_once_with(
            project_dir, "claude", None, None, False, False
        )

    @patch("mcp_coder.cli.commands.fix_ci.resolve_issue_interaction_flags")
    @patch("mcp_coder.cli.commands.fix_ci.resolve_claude_cwd")
    @patch("mcp_coder.cli.commands.fix_ci.resolve_project_dir")
    @patch("mcp_coder.cli.commands.fix_ci.run_fix_ci_workflow")
    @patch("mcp_coder.cli.commands.fix_ci.resolve_llm_method")
    @patch("mcp_coder.cli.commands.fix_ci.parse_llm_method_from_args")
    def test_execute_fix_ci_workflow_failure(
        self,
        mock_parse_llm: Mock,
        mock_resolve_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        mock_resolve_exec: Mock,
        mock_resolve_flags: Mock,
    ) -> None:
        """A non-zero workflow result is passed through."""
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_resolve_exec.return_value = project_dir
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_resolve_flags.return_value = (False, False)
        mock_run_workflow.return_value = 1

        args = argparse.Namespace(
            project_dir="/test/project",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            update_issue_labels=None,
            post_issue_comments=None,
        )

        result = execute_fix_ci(args)

        assert result == 1
        mock_run_workflow.assert_called_once_with(
            project_dir, "claude", None, None, False, False
        )

    @patch("mcp_coder.cli.commands.fix_ci.resolve_project_dir")
    def test_invalid_project_dir_returns_one(
        self,
        mock_resolve_dir: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A ValueError from directory resolution returns exit code 1."""
        mock_resolve_dir.side_effect = ValueError("Directory does not exist")

        args = argparse.Namespace(
            project_dir="/nonexistent",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            update_issue_labels=None,
            post_issue_comments=None,
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_fix_ci(args)

        assert result == 1
        assert "Directory does not exist" in caplog.text

    @patch("mcp_coder.cli.commands.fix_ci.resolve_project_dir")
    @patch("mcp_coder.cli.commands.fix_ci.run_fix_ci_workflow")
    @patch("mcp_coder.cli.commands.fix_ci.resolve_llm_method")
    @patch("mcp_coder.cli.commands.fix_ci.parse_llm_method_from_args")
    def test_keyboard_interrupt_returns_one(
        self,
        mock_parse_llm: Mock,
        mock_resolve_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """KeyboardInterrupt is handled gracefully and returns 1."""
        mock_resolve_dir.return_value = Path("/test/project")
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_run_workflow.side_effect = KeyboardInterrupt()

        args = argparse.Namespace(
            project_dir="/test/project",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            update_issue_labels=None,
            post_issue_comments=None,
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_fix_ci(args)

        assert result == 1
        assert "Operation cancelled by user." in caplog.text

    @patch("mcp_coder.cli.commands.fix_ci.resolve_project_dir")
    @patch("mcp_coder.cli.commands.fix_ci.run_fix_ci_workflow")
    @patch("mcp_coder.cli.commands.fix_ci.resolve_llm_method")
    @patch("mcp_coder.cli.commands.fix_ci.parse_llm_method_from_args")
    def test_unexpected_exception_returns_one(
        self,
        mock_parse_llm: Mock,
        mock_resolve_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An unexpected exception is logged with exc_info and returns 1."""
        mock_resolve_dir.return_value = Path("/test/project")
        mock_resolve_llm.return_value = ("claude", "cli argument")
        mock_parse_llm.return_value = "claude"
        mock_run_workflow.side_effect = RuntimeError("boom")

        args = argparse.Namespace(
            project_dir="/test/project",
            llm_method="claude",
            mcp_config=None,
            settings=None,
            update_issue_labels=None,
            post_issue_comments=None,
        )

        with caplog.at_level(logging.DEBUG):
            result = execute_fix_ci(args)

        assert result == 1
        assert "boom" in caplog.text


class TestFixCiCliIntegration:
    """Smoke tests for CLI parser registration."""

    def test_fix_ci_command_registered(self) -> None:
        """fix-ci command is registered in the CLI parser."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["fix-ci"])

        assert args.command == "fix-ci"

    def test_fix_ci_command_has_llm_arguments(self) -> None:
        """fix-ci has --project-dir plus the LLM-related arguments."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["fix-ci"])

        assert hasattr(args, "project_dir")
        assert hasattr(args, "llm_method")
        assert hasattr(args, "mcp_config")
        assert hasattr(args, "settings")
