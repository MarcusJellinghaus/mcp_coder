"""Tests for create-pr command functionality.

This follows test-first development approach. Tests that require the create_pr module
are conditionally skipped if the module doesn't exist yet, while tests that can
run independently (like CLI integration checks) are always executed.
"""

import argparse
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Test-first approach: Try to import the module, skip dependent tests if not available
try:
    from mcp_coder.cli.commands.create_pr import (
        execute_create_pr,
    )

    CREATE_PR_MODULE_AVAILABLE = True
except Exception as e:
    import traceback

    print(f"\n\n*** IMPORT FAILED: {type(e).__name__}: {e} ***")
    traceback.print_exc()
    print("\n\n")
    CREATE_PR_MODULE_AVAILABLE = False

    # Create a mock for type checking in tests
    def execute_create_pr(*args, **kwargs):  # type: ignore
        pass


@pytest.mark.skipif(
    not CREATE_PR_MODULE_AVAILABLE, reason="create_pr module not yet implemented"
)
class TestExecuteCreatePr:
    """Tests for execute_create_pr function.

    These tests are skipped until src/mcp_coder/cli/commands/create_pr.py is created.
    This follows test-first development - tests are written before implementation.
    """

    @patch("mcp_coder.cli.commands.create_pr.resolve_project_dir")
    @patch("mcp_coder.cli.commands.create_pr.run_create_pr_workflow")
    @patch("mcp_coder.cli.commands.create_pr.parse_llm_method_from_args")
    def test_execute_create_pr_success(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful create-pr execution."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "cli")
        mock_run_workflow.return_value = 0

        args = argparse.Namespace(
            project_dir="/test/project", llm_method="claude_code_cli"
        )

        result = execute_create_pr(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_parse_llm.assert_called_once_with("claude_code_cli")
        mock_run_workflow.assert_called_once_with(project_dir, "claude", "cli")

    @patch("mcp_coder.cli.commands.create_pr.resolve_project_dir")
    @patch("mcp_coder.cli.commands.create_pr.run_create_pr_workflow")
    @patch("mcp_coder.cli.commands.create_pr.parse_llm_method_from_args")
    def test_execute_create_pr_with_custom_llm_method(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test execution with custom LLM method."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "api")
        mock_run_workflow.return_value = 0

        args = argparse.Namespace(
            project_dir="/test/project", llm_method="claude_code_api"
        )

        result = execute_create_pr(args)

        assert result == 0
        mock_parse_llm.assert_called_once_with("claude_code_api")
        mock_run_workflow.assert_called_once_with(project_dir, "claude", "api")

    @patch("mcp_coder.cli.commands.create_pr.resolve_project_dir")
    @patch("mcp_coder.cli.commands.create_pr.run_create_pr_workflow")
    @patch("mcp_coder.cli.commands.create_pr.parse_llm_method_from_args")
    def test_execute_create_pr_workflow_failure(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test handling of workflow failure (returns 1)."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "cli")
        mock_run_workflow.return_value = 1  # Workflow failure

        args = argparse.Namespace(
            project_dir="/test/project", llm_method="claude_code_cli"
        )

        result = execute_create_pr(args)

        assert result == 1
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_parse_llm.assert_called_once_with("claude_code_cli")
        mock_run_workflow.assert_called_once_with(project_dir, "claude", "cli")

    @patch("mcp_coder.cli.commands.create_pr.resolve_project_dir")
    def test_execute_create_pr_invalid_project_dir(
        self, mock_resolve_dir: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test handling of invalid project directory."""
        # Setup mocks - resolve_project_dir calls sys.exit(1) on failure
        mock_resolve_dir.side_effect = SystemExit(1)

        args = argparse.Namespace(
            project_dir="/invalid/path", llm_method="claude_code_cli"
        )

        with pytest.raises(SystemExit) as exc_info:
            execute_create_pr(args)

        assert exc_info.value.code == 1
        mock_resolve_dir.assert_called_once_with("/invalid/path")

    @patch("mcp_coder.cli.commands.create_pr.resolve_project_dir")
    @patch("mcp_coder.cli.commands.create_pr.run_create_pr_workflow")
    @patch("mcp_coder.cli.commands.create_pr.parse_llm_method_from_args")
    def test_execute_create_pr_none_project_dir(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test with None project_dir (uses current directory)."""
        # Setup mocks
        project_dir = Path.cwd()
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "cli")
        mock_run_workflow.return_value = 0

        args = argparse.Namespace(
            project_dir=None,  # Should use current directory
            llm_method="claude_code_cli",
        )

        result = execute_create_pr(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with(None)
        mock_parse_llm.assert_called_once_with("claude_code_cli")
        mock_run_workflow.assert_called_once_with(project_dir, "claude", "cli")

    @patch("mcp_coder.cli.commands.create_pr.resolve_project_dir")
    @patch("mcp_coder.cli.commands.create_pr.run_create_pr_workflow")
    @patch("mcp_coder.cli.commands.create_pr.parse_llm_method_from_args")
    def test_execute_create_pr_with_different_llm_methods(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test execution with different LLM methods."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_run_workflow.return_value = 0

        # Test with claude_code_cli
        mock_parse_llm.return_value = ("claude", "cli")
        args_cli = argparse.Namespace(
            project_dir="/test/project", llm_method="claude_code_cli"
        )
        result = execute_create_pr(args_cli)
        assert result == 0
        mock_parse_llm.assert_called_with("claude_code_cli")
        mock_run_workflow.assert_called_with(project_dir, "claude", "cli")

        # Reset mocks
        mock_resolve_dir.reset_mock()
        mock_run_workflow.reset_mock()
        mock_parse_llm.reset_mock()

        # Test with claude_code_api
        mock_parse_llm.return_value = ("claude", "api")
        args_api = argparse.Namespace(
            project_dir="/test/project", llm_method="claude_code_api"
        )
        result = execute_create_pr(args_api)
        assert result == 0
        mock_parse_llm.assert_called_with("claude_code_api")
        mock_run_workflow.assert_called_with(project_dir, "claude", "api")

    @patch("mcp_coder.cli.commands.create_pr.resolve_project_dir")
    @patch("mcp_coder.cli.commands.create_pr.run_create_pr_workflow")
    @patch("mcp_coder.cli.commands.create_pr.parse_llm_method_from_args")
    def test_execute_create_pr_keyboard_interrupt(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling of keyboard interrupt."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "cli")
        mock_run_workflow.side_effect = KeyboardInterrupt()

        args = argparse.Namespace(
            project_dir="/test/project", llm_method="claude_code_cli"
        )

        result = execute_create_pr(args)

        assert result == 1
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Operation cancelled by user." in captured_out

    @patch("mcp_coder.cli.commands.create_pr.resolve_project_dir")
    @patch("mcp_coder.cli.commands.create_pr.run_create_pr_workflow")
    @patch("mcp_coder.cli.commands.create_pr.parse_llm_method_from_args")
    def test_execute_create_pr_unexpected_error(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test handling of unexpected errors."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "cli")
        mock_run_workflow.side_effect = RuntimeError("Unexpected error")

        args = argparse.Namespace(
            project_dir="/test/project", llm_method="claude_code_cli"
        )

        result = execute_create_pr(args)

        assert result == 1
        captured = capsys.readouterr()
        captured_err: str = captured.err or ""
        assert "Error during workflow execution: Unexpected error" in captured_err
