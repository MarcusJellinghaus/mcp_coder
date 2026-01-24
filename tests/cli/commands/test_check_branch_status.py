"""Tests for check_branch_status command functionality.

This follows test-first development approach. Tests that require the check_branch_status module
are conditionally skipped if the module doesn't exist yet, while tests that can
run independently (like CLI integration checks) are always executed.
"""

import argparse
import sys
from pathlib import Path
from unittest import mock
from unittest.mock import Mock, patch

import pytest

from mcp_coder.utils.branch_status import BranchStatusReport

# Test-first approach: Try to import the module, skip dependent tests if not available
try:
    from mcp_coder.cli.commands.check_branch_status import execute_check_branch_status

    CHECK_BRANCH_STATUS_MODULE_AVAILABLE = True
except ImportError:
    CHECK_BRANCH_STATUS_MODULE_AVAILABLE = False

    # Create a mock for type checking in tests
    def execute_check_branch_status(*args, **kwargs):  # type: ignore
        pass


@pytest.fixture
def sample_report():
    """Create a sample BranchStatusReport for testing."""
    return BranchStatusReport(
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Branch is up to date with main",
        tasks_complete=True,
        current_github_label="status-implementation",
        recommendations=["Branch is ready for next workflow step"],
    )


@pytest.fixture
def failed_ci_report():
    """Create a BranchStatusReport with failed CI for testing."""
    return BranchStatusReport(
        ci_status="FAILED",
        ci_details="Test failure: AssertionError in test_example",
        rebase_needed=False,
        rebase_reason="Branch is up to date with main",
        tasks_complete=True,
        current_github_label="status-implementation",
        recommendations=[
            "Fix CI failures before proceeding",
            "Check CI error details above",
        ],
    )


@pytest.fixture
def rebase_needed_report():
    """Create a BranchStatusReport that needs rebase for testing."""
    return BranchStatusReport(
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=True,
        rebase_reason="Branch is behind main branch and needs rebase",
        tasks_complete=True,
        current_github_label="status-implementation",
        recommendations=["Rebase branch with main when tasks are complete"],
    )


@pytest.mark.skipif(
    not CHECK_BRANCH_STATUS_MODULE_AVAILABLE,
    reason="check_branch_status module not yet implemented",
)
class TestExecuteCheckBranchStatus:
    """Tests for execute_check_branch_status function.

    These tests are skipped until src/mcp_coder/cli/commands/check_branch_status.py is created.
    This follows test-first development - tests are written before implementation.
    """

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    def test_execute_check_branch_status_read_only_success(
        self,
        mock_collect: Mock,
        mock_resolve_dir: Mock,
        sample_report: BranchStatusReport,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful read-only branch status check."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_collect.return_value = sample_report

        args = argparse.Namespace(
            project_dir="/test/project",
            fix=False,
            llm_truncate=False,
        )

        result = execute_check_branch_status(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_collect.assert_called_once_with(project_dir, False)

        # Check output contains human-formatted report
        captured = capsys.readouterr()
        assert "Branch Status Report" in captured.out
        assert "CI Status: ✅ PASSED" in captured.out

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    def test_execute_check_branch_status_llm_mode(
        self,
        mock_collect: Mock,
        mock_resolve_dir: Mock,
        sample_report: BranchStatusReport,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test branch status check with LLM output format."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_collect.return_value = sample_report

        args = argparse.Namespace(
            project_dir="/test/project",
            fix=False,
            llm_truncate=True,
        )

        result = execute_check_branch_status(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_collect.assert_called_once_with(project_dir, True)

        # Check output contains LLM-formatted report
        captured = capsys.readouterr()
        assert "Branch Status: CI=PASSED" in captured.out

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    @patch("mcp_coder.cli.commands.check_branch_status._run_auto_fixes")
    def test_execute_check_branch_status_with_fixes_success(
        self,
        mock_run_fixes: Mock,
        mock_collect: Mock,
        mock_resolve_dir: Mock,
        failed_ci_report: BranchStatusReport,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test branch status check with --fix flag when fixes succeed."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_collect.return_value = failed_ci_report
        mock_run_fixes.return_value = True  # Fixes succeeded

        args = argparse.Namespace(
            project_dir="/test/project",
            fix=True,
            llm_truncate=False,
            llm_method="claude_code_api",
            mcp_config=None,
            execution_dir=None,
        )

        result = execute_check_branch_status(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_collect.assert_called_once_with(project_dir, False)
        mock_run_fixes.assert_called_once_with(
            project_dir, failed_ci_report, "claude", "api", None, None
        )

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    @patch("mcp_coder.cli.commands.check_branch_status._run_auto_fixes")
    def test_execute_check_branch_status_with_fixes_failure(
        self,
        mock_run_fixes: Mock,
        mock_collect: Mock,
        mock_resolve_dir: Mock,
        failed_ci_report: BranchStatusReport,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test branch status check with --fix flag when fixes fail."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_collect.return_value = failed_ci_report
        mock_run_fixes.return_value = False  # Fixes failed

        args = argparse.Namespace(
            project_dir="/test/project",
            fix=True,
            llm_truncate=False,
            llm_method="claude_code_api",
            mcp_config=None,
            execution_dir=None,
        )

        result = execute_check_branch_status(args)

        assert result == 1
        mock_resolve_dir.assert_called_once_with("/test/project")
        mock_collect.assert_called_once_with(project_dir, False)
        mock_run_fixes.assert_called_once()

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    def test_execute_check_branch_status_resolve_dir_failure(
        self, mock_resolve_dir: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test check_branch_status execution with directory resolution failure."""
        # Setup mocks - resolve_project_dir calls sys.exit(1) on failure
        mock_resolve_dir.side_effect = SystemExit(1)

        args = argparse.Namespace(
            project_dir="/invalid/path",
            fix=False,
            llm_truncate=False,
        )

        with pytest.raises(SystemExit) as exc_info:
            execute_check_branch_status(args)

        assert exc_info.value.code == 1
        mock_resolve_dir.assert_called_once_with("/invalid/path")

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    def test_execute_check_branch_status_collection_exception(
        self,
        mock_collect: Mock,
        mock_resolve_dir: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test check_branch_status execution with status collection failure."""
        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_dir.return_value = project_dir
        mock_collect.side_effect = Exception("Git error")

        args = argparse.Namespace(
            project_dir="/test/project",
            fix=False,
            llm_truncate=False,
        )

        result = execute_check_branch_status(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error collecting branch status: Git error" in captured.err

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    @patch("mcp_coder.cli.commands.check_branch_status.parse_llm_method_from_args")
    def test_execute_check_branch_status_with_none_project_dir(
        self,
        mock_parse_llm: Mock,
        mock_collect: Mock,
        mock_resolve_dir: Mock,
        sample_report: BranchStatusReport,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test check_branch_status execution with None project directory (uses current dir)."""
        # Setup mocks
        project_dir = Path.cwd()
        mock_resolve_dir.return_value = project_dir
        mock_collect.return_value = sample_report
        mock_parse_llm.return_value = ("claude", "cli")

        args = argparse.Namespace(
            project_dir=None,
            fix=False,
            llm_truncate=False,
        )

        result = execute_check_branch_status(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with(None)
        mock_collect.assert_called_once_with(project_dir, False)


@pytest.mark.skipif(
    not CHECK_BRANCH_STATUS_MODULE_AVAILABLE,
    reason="check_branch_status module not yet implemented",
)
class TestRunAutoFixes:
    """Tests for _run_auto_fixes function."""

    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_mcp_config_path")
    def test_run_auto_fixes_ci_only_success(
        self,
        mock_resolve_mcp: Mock,
        mock_resolve_exec: Mock,
        mock_check_ci: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Test auto-fixes that only handles CI failures."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_mcp.return_value = None
        mock_resolve_exec.return_value = Path.cwd()
        mock_check_ci.return_value = 0  # Success

        result = _run_auto_fixes(
            project_dir, failed_ci_report, "claude", "api", None, None
        )

        assert result is True
        mock_check_ci.assert_called_once_with(
            project_dir, "claude", "api", None, str(Path.cwd())
        )

    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_mcp_config_path")
    def test_run_auto_fixes_ci_failure(
        self,
        mock_resolve_mcp: Mock,
        mock_resolve_exec: Mock,
        mock_check_ci: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Test auto-fixes when CI fix fails."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_mcp.return_value = None
        mock_resolve_exec.return_value = Path.cwd()
        mock_check_ci.return_value = 1  # Failure

        result = _run_auto_fixes(
            project_dir, failed_ci_report, "claude", "api", None, None
        )

        assert result is False
        mock_check_ci.assert_called_once()

    def test_run_auto_fixes_no_fixes_needed(
        self, sample_report: BranchStatusReport
    ) -> None:
        """Test auto-fixes when no fixes are needed."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        project_dir = Path("/test/project")

        result = _run_auto_fixes(
            project_dir, sample_report, "claude", "api", None, None
        )

        assert result is True  # Success when no fixes needed

    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_execution_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_mcp_config_path")
    def test_run_auto_fixes_exception_handling(
        self,
        mock_resolve_mcp: Mock,
        mock_resolve_exec: Mock,
        mock_check_ci: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Test auto-fixes with exception during CI fix."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        # Setup mocks
        project_dir = Path("/test/project")
        mock_resolve_mcp.return_value = None
        mock_resolve_exec.return_value = Path.cwd()
        mock_check_ci.side_effect = Exception("Unexpected CI error")

        result = _run_auto_fixes(
            project_dir, failed_ci_report, "claude", "api", None, None
        )

        assert result is False


@pytest.mark.skipif(
    not CHECK_BRANCH_STATUS_MODULE_AVAILABLE,
    reason="check_branch_status module not yet implemented",
)
class TestPromptForMajorOperations:
    """Tests for _prompt_for_major_operations function."""

    @patch("builtins.input", return_value="y")
    def test_prompt_for_major_operations_user_confirms(
        self, mock_input: Mock, rebase_needed_report: BranchStatusReport
    ) -> None:
        """Test prompt when user confirms major operations."""
        from mcp_coder.cli.commands.check_branch_status import (
            _prompt_for_major_operations,
        )

        result = _prompt_for_major_operations(rebase_needed_report)

        assert result is True
        mock_input.assert_called_once()

    @patch("builtins.input", return_value="n")
    def test_prompt_for_major_operations_user_declines(
        self, mock_input: Mock, rebase_needed_report: BranchStatusReport
    ) -> None:
        """Test prompt when user declines major operations."""
        from mcp_coder.cli.commands.check_branch_status import (
            _prompt_for_major_operations,
        )

        result = _prompt_for_major_operations(rebase_needed_report)

        assert result is False
        mock_input.assert_called_once()

    @patch("builtins.input", side_effect=KeyboardInterrupt())
    def test_prompt_for_major_operations_keyboard_interrupt(
        self, mock_input: Mock, rebase_needed_report: BranchStatusReport
    ) -> None:
        """Test prompt with keyboard interrupt."""
        from mcp_coder.cli.commands.check_branch_status import (
            _prompt_for_major_operations,
        )

        result = _prompt_for_major_operations(rebase_needed_report)

        assert result is False

    def test_prompt_for_major_operations_no_major_ops_needed(
        self, sample_report: BranchStatusReport
    ) -> None:
        """Test prompt when no major operations are needed."""
        from mcp_coder.cli.commands.check_branch_status import (
            _prompt_for_major_operations,
        )

        result = _prompt_for_major_operations(sample_report)

        assert result is True  # No prompt needed, so approve


class TestCheckBranchStatusCommandIntegration:
    """Test check_branch_status command CLI integration."""

    @patch("mcp_coder.cli.main.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check-branch-status"])
    def test_check_branch_status_command_calls_function(
        self, mock_execute: Mock
    ) -> None:
        """Test that the check-branch-status CLI command calls the execution function."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0  # Success

        result = main()

        assert result == 0
        mock_execute.assert_called_once()

        # Check that the function was called with proper arguments
        call_args = mock_execute.call_args[0][0]  # First positional argument (args)
        assert isinstance(call_args, argparse.Namespace)
        assert hasattr(call_args, "project_dir")
        assert hasattr(call_args, "fix")
        assert hasattr(call_args, "llm_truncate")

    @patch("mcp_coder.cli.main.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check-branch-status", "--fix"])
    def test_check_branch_status_command_with_fix_flag(
        self, mock_execute: Mock
    ) -> None:
        """Test check-branch-status command with --fix flag."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0  # Success

        result = main()

        assert result == 0
        mock_execute.assert_called_once()

        # Check that fix flag was parsed correctly
        call_args = mock_execute.call_args[0][0]
        assert call_args.fix is True

    @patch("mcp_coder.cli.main.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check-branch-status", "--llm-truncate"])
    def test_check_branch_status_command_with_llm_truncate_flag(
        self, mock_execute: Mock
    ) -> None:
        """Test check-branch-status command with --llm-truncate flag."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0  # Success

        result = main()

        assert result == 0
        mock_execute.assert_called_once()

        # Check that llm_truncate flag was parsed correctly
        call_args = mock_execute.call_args[0][0]
        assert call_args.llm_truncate is True

    @patch("mcp_coder.cli.main.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check-branch-status"])
    def test_check_branch_status_command_propagates_return_code(
        self, mock_execute: Mock
    ) -> None:
        """Test that check-branch-status command propagates the return code."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 1  # Error

        result = main()

        assert result == 1
        mock_execute.assert_called_once()

    def test_check_branch_status_command_is_implemented(self) -> None:
        """Test that check-branch-status command is implemented in main CLI.

        This test verifies that the check-branch-status command has been successfully
        added to the CLI.
        """
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Check if check-branch-status subcommand exists in parser
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]

        assert subparsers_actions, "No subparsers found in CLI parser"

        subparser = subparsers_actions[0]
        # Check if 'check-branch-status' is in the choices
        assert (
            "check-branch-status" in subparser.choices
        ), "check-branch-status command should be implemented in main.py"

        # Verify the check-branch-status parser has the expected arguments
        check_parser = subparser.choices["check-branch-status"]

        # Parse test arguments to verify structure
        test_args = check_parser.parse_args(["--fix", "--llm-truncate"])
        assert hasattr(test_args, "project_dir")
        assert hasattr(test_args, "fix")
        assert hasattr(test_args, "llm_truncate")
        assert test_args.fix is True
        assert test_args.llm_truncate is True
