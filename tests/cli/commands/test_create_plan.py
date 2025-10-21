"""Tests for create-plan CLI command handler."""

import argparse
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.create_plan import execute_create_plan


class TestExecuteCreatePlan:
    """Test execute_create_plan CLI command handler."""

    @patch("mcp_coder.workflows.create_plan.run_create_plan_workflow")
    @patch("mcp_coder.cli.utils.parse_llm_method_from_args")
    @patch("mcp_coder.workflows.utils.resolve_project_dir")
    def test_execute_create_plan_success(
        self,
        mock_resolve_dir: Mock,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
    ) -> None:
        """Test successful create-plan command execution."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "cli")
        mock_run_workflow.return_value = 0

        args = argparse.Namespace(
            issue_number=123,
            project_dir="/test/project",
            llm_method="claude_code_cli",
        )

        result = execute_create_plan(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_parse_llm.assert_called_once_with("claude_code_cli")
        mock_run_workflow.assert_called_once_with(123, project_dir, "claude", "cli")

    @patch("mcp_coder.workflows.create_plan.run_create_plan_workflow")
    @patch("mcp_coder.cli.utils.parse_llm_method_from_args")
    @patch("mcp_coder.workflows.utils.resolve_project_dir")
    def test_execute_create_plan_workflow_failure(
        self,
        mock_resolve_dir: Mock,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
    ) -> None:
        """Test create-plan execution with workflow failure."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "cli")
        mock_run_workflow.return_value = 1

        args = argparse.Namespace(
            issue_number=123,
            project_dir="/test/project",
            llm_method="claude_code_cli",
        )

        result = execute_create_plan(args)

        assert result == 1
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_parse_llm.assert_called_once_with("claude_code_cli")
        mock_run_workflow.assert_called_once_with(123, project_dir, "claude", "cli")

    @patch("mcp_coder.workflows.create_plan.run_create_plan_workflow")
    @patch("mcp_coder.cli.utils.parse_llm_method_from_args")
    @patch("mcp_coder.workflows.utils.resolve_project_dir")
    def test_execute_create_plan_exception_handling(
        self,
        mock_resolve_dir: Mock,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test create-plan execution with unexpected exception."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "cli")
        mock_run_workflow.side_effect = Exception("Unexpected error")

        args = argparse.Namespace(
            issue_number=123,
            project_dir="/test/project",
            llm_method="claude_code_cli",
        )

        result = execute_create_plan(args)

        assert result == 1
        captured = capsys.readouterr()
        captured_err: str = captured.err or ""
        assert "Error during workflow execution: Unexpected error" in captured_err

    @patch("mcp_coder.workflows.create_plan.run_create_plan_workflow")
    @patch("mcp_coder.cli.utils.parse_llm_method_from_args")
    @patch("mcp_coder.workflows.utils.resolve_project_dir")
    def test_execute_create_plan_keyboard_interrupt(
        self,
        mock_resolve_dir: Mock,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test create-plan execution with keyboard interrupt."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "cli")
        mock_run_workflow.side_effect = KeyboardInterrupt()

        args = argparse.Namespace(
            issue_number=123,
            project_dir="/test/project",
            llm_method="claude_code_cli",
        )

        result = execute_create_plan(args)

        assert result == 1
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Operation cancelled by user." in captured_out
