"""Tests for the fix-conflict CLI command handler."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.commands.fix_conflict import execute_fix_conflict


def _make_args() -> MagicMock:
    args = MagicMock()
    args.project_dir = "/test/project"
    return args


class TestExecuteFixConflict:
    """Tests for execute_fix_conflict."""

    @patch("mcp_coder.workflows.fix_conflict.core.run_fix_conflict_workflow")
    @patch("mcp_coder.cli.commands.fix_conflict.enable_crash_logging")
    @patch("mcp_coder.cli.commands.fix_conflict.log_command_startup")
    @patch("mcp_coder.cli.commands.fix_conflict.resolve_project_dir")
    def test_success_path(
        self,
        mock_resolve_dir: MagicMock,
        mock_log_startup: MagicMock,
        mock_crash_logging: MagicMock,
        mock_workflow: MagicMock,
    ) -> None:
        """Resolves project dir and returns run_fix_conflict_workflow's exit code."""
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_workflow.return_value = 0

        result = execute_fix_conflict(_make_args())

        assert result == 0
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_log_startup.assert_called_once_with("fix-conflict", project_dir)
        mock_crash_logging.assert_called_once_with(project_dir, "fix-conflict")
        mock_workflow.assert_called_once_with(project_dir)

    @patch("mcp_coder.workflows.fix_conflict.core.run_fix_conflict_workflow")
    @patch("mcp_coder.cli.commands.fix_conflict.enable_crash_logging")
    @patch("mcp_coder.cli.commands.fix_conflict.log_command_startup")
    @patch("mcp_coder.cli.commands.fix_conflict.resolve_project_dir")
    def test_workflow_failure_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        mock_log_startup: MagicMock,
        mock_crash_logging: MagicMock,
        mock_workflow: MagicMock,
    ) -> None:
        """A non-zero workflow result is passed through."""
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_workflow.return_value = 1

        result = execute_fix_conflict(_make_args())

        assert result == 1

    @patch("mcp_coder.cli.commands.fix_conflict.resolve_project_dir")
    def test_invalid_project_dir_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A ValueError from directory resolution returns exit code 1."""
        mock_resolve_dir.side_effect = ValueError("Directory does not exist")

        with caplog.at_level(logging.DEBUG):
            result = execute_fix_conflict(_make_args())

        assert result == 1
        assert "Directory does not exist" in caplog.text

    @patch("mcp_coder.workflows.fix_conflict.core.run_fix_conflict_workflow")
    @patch("mcp_coder.cli.commands.fix_conflict.enable_crash_logging")
    @patch("mcp_coder.cli.commands.fix_conflict.log_command_startup")
    @patch("mcp_coder.cli.commands.fix_conflict.resolve_project_dir")
    def test_keyboard_interrupt_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        mock_log_startup: MagicMock,
        mock_crash_logging: MagicMock,
        mock_workflow: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """KeyboardInterrupt is handled gracefully and returns 1."""
        mock_resolve_dir.return_value = Path("/test/project")
        mock_workflow.side_effect = KeyboardInterrupt()

        with caplog.at_level(logging.DEBUG):
            result = execute_fix_conflict(_make_args())

        assert result == 1
        assert "Operation cancelled by user." in caplog.text

    @patch("mcp_coder.workflows.fix_conflict.core.run_fix_conflict_workflow")
    @patch("mcp_coder.cli.commands.fix_conflict.enable_crash_logging")
    @patch("mcp_coder.cli.commands.fix_conflict.log_command_startup")
    @patch("mcp_coder.cli.commands.fix_conflict.resolve_project_dir")
    def test_unexpected_exception_returns_one(
        self,
        mock_resolve_dir: MagicMock,
        mock_log_startup: MagicMock,
        mock_crash_logging: MagicMock,
        mock_workflow: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """An unexpected exception is logged with exc_info and returns 1."""
        mock_resolve_dir.return_value = Path("/test/project")
        mock_workflow.side_effect = RuntimeError("boom")

        with caplog.at_level(logging.DEBUG):
            result = execute_fix_conflict(_make_args())

        assert result == 1
        assert "boom" in caplog.text


class TestFixConflictCliIntegration:
    """Smoke tests for CLI parser registration."""

    def test_fix_conflict_command_registered(self) -> None:
        """fix-conflict command is registered in the CLI parser."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["fix-conflict"])

        assert args.command == "fix-conflict"

    def test_fix_conflict_command_has_project_dir_only(self) -> None:
        """fix-conflict has --project-dir but no LLM-related arguments."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["fix-conflict"])

        assert hasattr(args, "project_dir")
        assert args.project_dir is None
        assert not hasattr(args, "llm_method")
        assert not hasattr(args, "mcp_config")
        assert not hasattr(args, "settings")
