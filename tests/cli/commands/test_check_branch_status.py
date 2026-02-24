"""Tests for check_branch_status command core functionality.

This follows test-first development approach. Tests that require the check_branch_status module
are conditionally skipped if the module doesn't exist yet, while tests that can
run independently (like CLI integration checks) are always executed.

Note: This file focuses on the main execution logic. Related test files:
- test_check_branch_status_ci_waiting.py: CI waiting and polling functionality
- test_check_branch_status_auto_fixes.py: Auto-fixes and retry logic
- test_check_branch_status_cli_integration.py: CLI parser and integration tests
"""

import argparse
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mcp_coder.checks.branch_status import BranchStatusReport

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
def sample_report() -> BranchStatusReport:
    """Create a sample BranchStatusReport for testing."""
    return BranchStatusReport(
        branch_name="feature/test-branch",
        base_branch="main",
        ci_status="PASSED",
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Branch is up to date with main",
        tasks_complete=True,
        current_github_label="status-implementation",
        recommendations=["Branch is ready for next workflow step"],
    )


@pytest.fixture
def failed_ci_report() -> BranchStatusReport:
    """Create a BranchStatusReport with failed CI for testing."""
    return BranchStatusReport(
        branch_name="feature/test-branch",
        base_branch="main",
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
            ci_timeout=0,
            fix=0,
            llm_truncate=False,
            llm_method="claude_code_cli",
            mcp_config=None,
            execution_dir=None,
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
            ci_timeout=0,
            fix=0,
            llm_truncate=True,
            llm_method="claude_code_cli",
            mcp_config=None,
            execution_dir=None,
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
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_execution_dir")
    def test_execute_check_branch_status_with_fixes_success(
        self,
        mock_resolve_exec: Mock,
        mock_run_fixes: Mock,
        mock_collect: Mock,
        mock_resolve_dir: Mock,
        failed_ci_report: BranchStatusReport,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test branch status check with --fix flag when fixes succeed."""
        # Setup mocks
        project_dir = Path("/test/project")
        exec_dir = Path.cwd()
        mock_resolve_dir.return_value = project_dir
        mock_resolve_exec.return_value = exec_dir
        mock_collect.return_value = failed_ci_report
        mock_run_fixes.return_value = True  # Fixes succeeded

        args = argparse.Namespace(
            project_dir="/test/project",
            ci_timeout=0,
            fix=1,
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
            project_dir,
            failed_ci_report,
            "claude",
            "api",
            None,
            exec_dir,
            fix_attempts=1,
            ci_timeout=0,
            llm_truncate=False,
        )

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    @patch("mcp_coder.cli.commands.check_branch_status._run_auto_fixes")
    @patch("mcp_coder.cli.commands.check_branch_status.resolve_execution_dir")
    def test_execute_check_branch_status_with_fixes_failure(
        self,
        mock_resolve_exec: Mock,
        mock_run_fixes: Mock,
        mock_collect: Mock,
        mock_resolve_dir: Mock,
        failed_ci_report: BranchStatusReport,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test branch status check with --fix flag when fixes fail."""
        # Setup mocks
        project_dir = Path("/test/project")
        exec_dir = Path.cwd()
        mock_resolve_dir.return_value = project_dir
        mock_resolve_exec.return_value = exec_dir
        mock_collect.return_value = failed_ci_report
        mock_run_fixes.return_value = False  # Fixes failed

        args = argparse.Namespace(
            project_dir="/test/project",
            ci_timeout=0,
            fix=1,
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
            ci_timeout=0,
            fix=0,
            llm_truncate=False,
            llm_method="claude_code_cli",
            mcp_config=None,
            execution_dir=None,
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
            ci_timeout=0,
            fix=0,
            llm_truncate=False,
            llm_method="claude_code_cli",
            mcp_config=None,
            execution_dir=None,
        )

        result = execute_check_branch_status(args)

        assert result == 2
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
            ci_timeout=0,
            fix=0,
            llm_truncate=False,
            llm_method="claude_code_cli",
            mcp_config=None,
            execution_dir=None,
        )

        result = execute_check_branch_status(args)

        assert result == 0
        mock_resolve_dir.assert_called_once_with(None)
        mock_collect.assert_called_once_with(project_dir, False)


# Note: CI waiting tests moved to test_check_branch_status_ci_waiting.py


# Note: Auto-fixes tests moved to test_check_branch_status_auto_fixes.py


# Note: Fix retry logic tests moved to test_check_branch_status_auto_fixes.py


# Note: CLI parser and integration tests moved to test_check_branch_status_cli_integration.py
