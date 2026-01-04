"""Tests for implement command functionality.

This follows test-first development approach. Tests that require the implement module
are conditionally skipped if the module doesn't exist yet, while tests that can
run independently (like CLI integration checks) are always executed.
"""

import argparse
import sys
from pathlib import Path
from unittest import mock
from unittest.mock import Mock, patch

import pytest

# Test-first approach: Try to import the module, skip dependent tests if not available
try:
    from mcp_coder.cli.commands.implement import execute_implement

    IMPLEMENT_MODULE_AVAILABLE = True
except ImportError:
    IMPLEMENT_MODULE_AVAILABLE = False

    # Create a mock for type checking in tests
    def execute_implement(*args, **kwargs):  # type: ignore
        pass


@pytest.mark.skipif(
    not IMPLEMENT_MODULE_AVAILABLE, reason="implement module not yet implemented"
)
class TestExecuteImplement:
    """Tests for execute_implement function.

    These tests are skipped until src/mcp_coder/cli/commands/implement.py is created.
    This follows test-first development - tests are written before implementation.
    """

    @patch("mcp_coder.cli.commands.implement.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.implement.resolve_project_dir")
    @patch("mcp_coder.cli.commands.implement.run_implement_workflow")
    @patch("mcp_coder.cli.commands.implement.parse_llm_method_from_args")
    def test_execute_implement_success(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        mock_resolve_exec: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful implement execution."""
        # Setup mocks
        project_dir = Path("/test/project")
        execution_dir = Path.cwd()
        mock_resolve_dir.return_value = project_dir
        mock_resolve_exec.return_value = str(execution_dir)
        mock_parse_llm.return_value = ("claude", "api")
        mock_run_workflow.return_value = 0

        args = argparse.Namespace(
            project_dir="/test/project",
            llm_method="claude_code_api",
            execution_dir=None,
            mcp_config=None,
        )

        result = execute_implement(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_resolve_exec.assert_called_once_with(None)
        mock_parse_llm.assert_called_once_with("claude_code_api")
        mock_run_workflow.assert_called_once_with(
            project_dir, "claude", "api", None, str(execution_dir), False
        )

    @patch("mcp_coder.cli.commands.implement.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.implement.resolve_project_dir")
    @patch("mcp_coder.cli.commands.implement.run_implement_workflow")
    @patch("mcp_coder.cli.commands.implement.parse_llm_method_from_args")
    def test_execute_implement_workflow_failure(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        mock_resolve_exec: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test implement execution with workflow failure."""
        # Setup mocks
        project_dir = Path("/test/project")
        execution_dir = Path.cwd()
        mock_resolve_dir.return_value = project_dir
        mock_resolve_exec.return_value = str(execution_dir)
        mock_parse_llm.return_value = ("claude", "api")
        mock_run_workflow.return_value = 1

        args = argparse.Namespace(
            project_dir="/test/project",
            llm_method="claude_code_api",
            execution_dir=None,
            mcp_config=None,
        )

        result = execute_implement(args)

        assert result == 1
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_resolve_exec.assert_called_once_with(None)
        mock_parse_llm.assert_called_once_with("claude_code_api")
        mock_run_workflow.assert_called_once_with(
            project_dir, "claude", "api", None, str(execution_dir), False
        )

    @patch("mcp_coder.cli.commands.implement.resolve_project_dir")
    def test_execute_implement_resolve_dir_failure(
        self, mock_resolve_dir: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test implement execution with directory resolution failure."""
        # Setup mocks - resolve_project_dir calls sys.exit(1) on failure
        mock_resolve_dir.side_effect = SystemExit(1)

        args = argparse.Namespace(
            project_dir="/invalid/path",
            llm_method="claude_code_api",
            execution_dir=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            execute_implement(args)

        assert exc_info.value.code == 1
        mock_resolve_dir.assert_called_once_with("/invalid/path")

    @patch("mcp_coder.cli.commands.implement.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.implement.resolve_project_dir")
    @patch("mcp_coder.cli.commands.implement.run_implement_workflow")
    @patch("mcp_coder.cli.commands.implement.parse_llm_method_from_args")
    def test_execute_implement_with_none_project_dir(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        mock_resolve_exec: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test implement execution with None project directory (uses current dir)."""
        # Setup mocks
        project_dir = Path.cwd()
        execution_dir = Path.cwd()
        mock_resolve_dir.return_value = project_dir
        mock_resolve_exec.return_value = str(execution_dir)
        mock_parse_llm.return_value = ("claude", "cli")
        mock_run_workflow.return_value = 0

        args = argparse.Namespace(
            project_dir=None,
            llm_method="claude_code_cli",
            execution_dir=None,
            mcp_config=None,
        )

        result = execute_implement(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with(None)
        mock_resolve_exec.assert_called_once_with(None)
        mock_parse_llm.assert_called_once_with("claude_code_cli")
        mock_run_workflow.assert_called_once_with(
            project_dir, "claude", "cli", None, str(execution_dir), False
        )

    @patch("mcp_coder.cli.commands.implement.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.implement.resolve_project_dir")
    @patch("mcp_coder.cli.commands.implement.run_implement_workflow")
    @patch("mcp_coder.cli.commands.implement.parse_llm_method_from_args")
    def test_execute_implement_with_different_llm_methods(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        mock_resolve_exec: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test implement execution with different LLM methods."""
        # Setup mocks
        project_dir = Path("/test/project")
        execution_dir = str(Path.cwd())
        mock_resolve_dir.return_value = project_dir
        mock_resolve_exec.return_value = execution_dir
        mock_run_workflow.return_value = 0

        # Test with claude_code_cli
        mock_parse_llm.return_value = ("claude", "cli")
        args_cli = argparse.Namespace(
            project_dir="/test/project",
            llm_method="claude_code_cli",
            execution_dir=None,
            mcp_config=None,
        )
        result = execute_implement(args_cli)
        assert result == 0
        mock_parse_llm.assert_called_with("claude_code_cli")
        mock_run_workflow.assert_called_with(
            project_dir, "claude", "cli", None, execution_dir, False
        )

        # Reset mocks
        mock_resolve_dir.reset_mock()
        mock_run_workflow.reset_mock()
        mock_parse_llm.reset_mock()

        # Test with claude_code_api
        mock_parse_llm.return_value = ("claude", "api")
        args_api = argparse.Namespace(
            project_dir="/test/project",
            llm_method="claude_code_api",
            execution_dir=None,
            mcp_config=None,
        )
        result = execute_implement(args_api)
        assert result == 0
        mock_parse_llm.assert_called_with("claude_code_api")
        mock_run_workflow.assert_called_with(
            project_dir, "claude", "api", None, execution_dir, False
        )

    @patch("mcp_coder.cli.commands.implement.resolve_project_dir")
    @patch("mcp_coder.cli.commands.implement.run_implement_workflow")
    @patch("mcp_coder.cli.commands.implement.parse_llm_method_from_args")
    def test_execute_implement_exception_handling(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test implement execution with unexpected exception."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "api")
        mock_run_workflow.side_effect = Exception("Unexpected error")

        args = argparse.Namespace(
            project_dir="/test/project",
            llm_method="claude_code_api",
            execution_dir=None,
        )

        result = execute_implement(args)

        assert result == 1
        captured = capsys.readouterr()
        captured_err: str = captured.err or ""
        assert "Error during workflow execution: Unexpected error" in captured_err

    @patch("mcp_coder.cli.commands.implement.resolve_project_dir")
    @patch("mcp_coder.cli.commands.implement.run_implement_workflow")
    @patch("mcp_coder.cli.commands.implement.parse_llm_method_from_args")
    def test_execute_implement_keyboard_interrupt(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_dir: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test implement execution with keyboard interrupt."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_parse_llm.return_value = ("claude", "api")
        mock_run_workflow.side_effect = KeyboardInterrupt()

        args = argparse.Namespace(
            project_dir="/test/project",
            llm_method="claude_code_api",
            execution_dir=None,
        )

        result = execute_implement(args)

        assert result == 1
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Operation cancelled by user." in captured_out


class TestImplementCommandError:
    """Test error handling scenarios for implement command."""

    def test_implement_command_is_implemented(self) -> None:
        """Test that implement command is now implemented in main CLI.

        This test verifies that the implement command has been successfully added to the CLI.
        """
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Check if implement subcommand exists in parser
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]

        assert subparsers_actions, "No subparsers found in CLI parser"

        subparser = subparsers_actions[0]
        # Check if 'implement' is in the choices
        assert (
            "implement" in subparser.choices
        ), "implement command should be implemented in main.py"

        # Verify the implement parser has the expected arguments
        implement_parser = subparser.choices["implement"]

        # Parse a test argument to verify structure
        test_args = implement_parser.parse_args(["--llm-method", "claude_code_api"])
        assert hasattr(test_args, "project_dir")
        assert hasattr(test_args, "llm_method")
        assert test_args.llm_method == "claude_code_api"

    @patch("mcp_coder.cli.commands.implement.resolve_project_dir")
    @patch("sys.argv", ["mcp-coder", "implement", "--project-dir", "/nonexistent"])
    def test_implement_command_with_invalid_project_dir(
        self, mock_resolve_dir: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that implement command with invalid project directory shows appropriate error.

        This test verifies error handling when implement command is called with invalid arguments.
        """
        from mcp_coder.cli.main import main

        # Mock resolve_project_dir to raise SystemExit for invalid path
        mock_resolve_dir.side_effect = SystemExit(1)

        with pytest.raises(SystemExit) as exc_info:
            main()

        # Should exit with code 1 for invalid project directory
        assert exc_info.value.code == 1

        mock_resolve_dir.assert_called_once_with("/nonexistent")


class TestImplementExecutionDir:
    """Tests for execution_dir handling in implement command."""

    @patch("mcp_coder.cli.commands.implement.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.implement.resolve_project_dir")
    @patch("mcp_coder.cli.commands.implement.run_implement_workflow")
    @patch("mcp_coder.cli.commands.implement.parse_llm_method_from_args")
    def test_default_execution_dir_uses_cwd(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_project: Mock,
        mock_resolve_exec: Mock,
    ) -> None:
        """Test default execution_dir should use current working directory."""
        project_dir = Path("/test/project")
        execution_dir = Path.cwd()
        mock_resolve_project.return_value = project_dir
        mock_resolve_exec.return_value = str(execution_dir)
        mock_parse_llm.return_value = ("claude", "api")
        mock_run_workflow.return_value = 0

        args = argparse.Namespace(
            project_dir="/test/project",
            execution_dir=None,  # No explicit execution_dir
            llm_method="claude_code_api",
            mcp_config=None,
        )

        result = execute_implement(args)

        assert result == 0
        mock_resolve_exec.assert_called_once_with(None)
        mock_run_workflow.assert_called_once_with(
            project_dir, "claude", "api", None, str(execution_dir), False
        )

    @patch("mcp_coder.cli.commands.implement.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.implement.resolve_project_dir")
    @patch("mcp_coder.cli.commands.implement.run_implement_workflow")
    @patch("mcp_coder.cli.commands.implement.parse_llm_method_from_args")
    def test_explicit_execution_dir_absolute(
        self,
        mock_parse_llm: Mock,
        mock_run_workflow: Mock,
        mock_resolve_project: Mock,
        mock_resolve_exec: Mock,
        tmp_path: Path,
    ) -> None:
        """Test explicit absolute execution_dir should be validated and used."""
        project_dir = Path("/test/project")
        execution_dir = tmp_path / "exec_dir"
        execution_dir.mkdir()

        mock_resolve_project.return_value = project_dir
        mock_resolve_exec.return_value = str(execution_dir)
        mock_parse_llm.return_value = ("claude", "api")
        mock_run_workflow.return_value = 0

        args = argparse.Namespace(
            project_dir="/test/project",
            execution_dir=str(execution_dir),
            llm_method="claude_code_api",
            mcp_config=None,
            update_labels=False,
        )

        result = execute_implement(args)

        assert result == 0
        mock_resolve_exec.assert_called_once_with(str(execution_dir))
        mock_run_workflow.assert_called_once_with(
            project_dir, "claude", "api", None, str(execution_dir), False
        )

    @patch("mcp_coder.cli.commands.implement.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.implement.resolve_project_dir")
    def test_invalid_execution_dir_returns_error(
        self,
        mock_resolve_project: Mock,
        mock_resolve_exec: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test invalid execution_dir should return error code 1."""
        project_dir = Path("/test/project")
        mock_resolve_project.return_value = project_dir
        mock_resolve_exec.side_effect = ValueError("Directory does not exist")

        args = argparse.Namespace(
            project_dir="/test/project",
            execution_dir="/nonexistent/invalid/path",
            llm_method="claude_code_api",
            mcp_config=None,
        )

        result = execute_implement(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "Directory does not exist" in captured.err
