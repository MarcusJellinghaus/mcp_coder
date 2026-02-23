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


@pytest.mark.skipif(
    not CHECK_BRANCH_STATUS_MODULE_AVAILABLE,
    reason="check_branch_status module not yet implemented",
)
class TestCIWaitingLogic:
    """Test CI waiting and polling functionality."""

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_timeout_zero_returns_immediately(
        self, mock_sleep: Mock
    ) -> None:
        """With timeout=0, should return immediately without polling."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )

        mock_manager = Mock()

        # Should not be called with timeout=0
        result = _wait_for_ci_completion(mock_manager, "branch", 0, False)

        assert result == (None, True)  # Graceful exit
        mock_sleep.assert_not_called()
        mock_manager.get_latest_ci_status.assert_not_called()

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_polls_until_completion(self, mock_sleep: Mock) -> None:
        """Should poll every 15 seconds until CI completes."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )

        mock_manager = Mock()
        # First call: in progress, Second call: completed
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"status": "in_progress"}, "jobs": []},
            {
                "run": {"status": "completed", "conclusion": "success"},
                "jobs": [],
            },
        ]

        ci_status, success = _wait_for_ci_completion(mock_manager, "branch", 60, True)

        assert success is True
        assert ci_status is not None
        assert ci_status["run"]["conclusion"] == "success"
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(15)

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_respects_timeout(self, mock_sleep: Mock) -> None:
        """Should respect timeout and return after max attempts."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )

        mock_manager = Mock()
        # Always return in_progress (never completes)
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"status": "in_progress"},
            "jobs": [],
        }

        # 45 second timeout = 3 attempts (45/15)
        ci_status, success = _wait_for_ci_completion(mock_manager, "branch", 45, True)

        assert success is False  # Timeout
        assert mock_sleep.call_count == 3

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_shows_progress_in_human_mode(
        self, mock_sleep: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Should show progress dots in human mode."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )

        mock_manager = Mock()
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"status": "in_progress"}, "jobs": []},
            {
                "run": {"status": "completed", "conclusion": "success"},
                "jobs": [],
            },
        ]

        _wait_for_ci_completion(mock_manager, "branch", 30, llm_mode=False)

        captured = capsys.readouterr()
        assert "Waiting for CI" in captured.out
        assert "." in captured.out  # Progress dots

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_silent_in_llm_mode(
        self, mock_sleep: Mock, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Should be silent in LLM mode."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )

        mock_manager = Mock()
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "success"},
            "jobs": [],
        }

        _wait_for_ci_completion(mock_manager, "branch", 30, llm_mode=True)

        captured = capsys.readouterr()
        assert captured.out == ""  # No output in LLM mode

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_early_exit_on_completion(self, mock_sleep: Mock) -> None:
        """Should exit immediately when CI completes."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )

        mock_manager = Mock()
        # CI already completed on first check
        mock_manager.get_latest_ci_status.return_value = {
            "run": {"status": "completed", "conclusion": "success"},
            "jobs": [],
        }

        ci_status, success = _wait_for_ci_completion(mock_manager, "branch", 300, True)

        assert success is True
        assert mock_sleep.call_count == 0  # No waiting needed
        assert mock_manager.get_latest_ci_status.call_count == 1

    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_wait_for_ci_handles_api_errors_gracefully(self, mock_sleep: Mock) -> None:
        """Should handle API errors gracefully and return success."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )

        mock_manager = Mock()
        mock_manager.get_latest_ci_status.side_effect = Exception("API Error")

        ci_status, success = _wait_for_ci_completion(mock_manager, "branch", 30, True)

        assert ci_status is None
        assert success is False  # Technical error on API error

    @patch("mcp_coder.cli.commands.check_branch_status.resolve_project_dir")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    @patch("mcp_coder.cli.commands.check_branch_status.collect_branch_status")
    def test_execute_with_ci_timeout_waits_before_display(
        self,
        mock_collect: Mock,
        mock_wait: Mock,
        mock_branch: Mock,
        mock_ci_manager: Mock,
        mock_resolve: Mock,
        sample_report: BranchStatusReport,
    ) -> None:
        """Test execute_check_branch_status calls wait before display."""
        from mcp_coder.cli.commands.check_branch_status import (
            execute_check_branch_status,
        )

        project_dir = Path("/test/project")
        mock_resolve.return_value = project_dir
        mock_branch.return_value = "feature-branch"
        mock_wait.return_value = (
            {"run": {"status": "completed", "conclusion": "success"}},
            True,
        )
        mock_collect.return_value = sample_report

        args = argparse.Namespace(
            project_dir="/test/project",
            ci_timeout=180,
            fix=0,
            llm_truncate=False,
        )

        result = execute_check_branch_status(args)

        assert result == 0
        mock_wait.assert_called_once()
        mock_collect.assert_called_once()


@pytest.mark.skipif(
    not CHECK_BRANCH_STATUS_MODULE_AVAILABLE,
    reason="check_branch_status module not yet implemented",
)
class TestRunAutoFixes:
    """Tests for _run_auto_fixes function."""

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    def test_run_auto_fixes_ci_only_success(
        self,
        mock_check_ci: Mock,
        mock_get_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Test auto-fixes that only handles CI failures."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        # Setup mocks
        project_dir = Path("/test/project")
        exec_dir = Path.cwd()
        mock_get_branch.return_value = "feature/test-branch"
        mock_check_ci.return_value = True  # Success

        result = _run_auto_fixes(
            project_dir, failed_ci_report, "claude", "api", None, exec_dir
        )

        assert result is True
        mock_check_ci.assert_called_once_with(
            project_dir, "feature/test-branch", "claude", "api", None, exec_dir
        )

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    def test_run_auto_fixes_ci_failure(
        self,
        mock_check_ci: Mock,
        mock_get_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Test auto-fixes when CI fix fails."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        # Setup mocks
        project_dir = Path("/test/project")
        exec_dir = Path.cwd()
        mock_get_branch.return_value = "feature/test-branch"
        mock_check_ci.return_value = False  # Failure

        result = _run_auto_fixes(
            project_dir, failed_ci_report, "claude", "api", None, exec_dir
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

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    def test_run_auto_fixes_exception_handling(
        self,
        mock_check_ci: Mock,
        mock_get_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Test auto-fixes with exception during CI fix."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        # Setup mocks
        project_dir = Path("/test/project")
        exec_dir = Path.cwd()
        mock_get_branch.return_value = "feature/test-branch"
        mock_check_ci.side_effect = Exception("Unexpected CI error")

        result = _run_auto_fixes(
            project_dir, failed_ci_report, "claude", "api", None, exec_dir
        )

        assert result is False


@pytest.mark.skipif(
    not CHECK_BRANCH_STATUS_MODULE_AVAILABLE,
    reason="check_branch_status module not yet implemented",
)
class TestFixRetryLogic:
    """Test fix retry logic with multiple attempts."""

    def test_fix_zero_means_no_fix(self, failed_ci_report: BranchStatusReport) -> None:
        """With fix_attempts=0, should return True without attempting any fixes."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=0,  # No fix
            ci_timeout=180,
            llm_truncate=False,
        )

        assert result is True  # Should succeed without doing anything

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    def test_fix_once_does_not_wait_for_recheck(
        self,
        mock_wait: Mock,
        mock_ci_manager: Mock,
        mock_check_ci: Mock,
        mock_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """With fix_attempts=1, should not wait for recheck (current behavior)."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        mock_branch.return_value = "feature-branch"
        mock_check_ci.return_value = True

        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=1,  # No retry
            ci_timeout=180,
            llm_truncate=False,
        )

        assert result is True
        mock_check_ci.assert_called_once()
        mock_wait.assert_not_called()  # No recheck

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_fix_twice_waits_after_first_attempt(
        self,
        mock_sleep: Mock,
        mock_wait: Mock,
        mock_ci_manager: Mock,
        mock_check_ci: Mock,
        mock_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """With fix_attempts=2, should wait after first attempt."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        mock_branch.return_value = "feature-branch"
        mock_check_ci.return_value = True  # Fix succeeds

        # Setup CI manager to return different statuses
        mock_manager = Mock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"id": 1}},  # Old run
            {"run": {"id": 2}},  # New run detected
            {"run": {"id": 2, "status": "completed", "conclusion": "success"}},
        ]

        # First wait: still failed, Second wait: passed
        mock_wait.side_effect = [
            ({"run": {"conclusion": "failure"}}, False),  # After attempt 1
            ({"run": {"conclusion": "success"}}, True),  # After attempt 2
        ]

        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=2,  # Retry enabled
            ci_timeout=180,
            llm_truncate=False,
        )

        assert result is True
        assert mock_check_ci.call_count == 2
        assert mock_wait.call_count == 2

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_fix_stops_early_when_ci_passes(
        self,
        mock_sleep: Mock,
        mock_wait: Mock,
        mock_ci_manager: Mock,
        mock_check_ci: Mock,
        mock_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Should stop early if CI passes before all attempts used."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        mock_branch.return_value = "feature-branch"
        mock_check_ci.return_value = True

        mock_manager = Mock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"id": 1}},  # Old run
            {"run": {"id": 2}},  # New run
        ]

        # CI passes after first attempt
        mock_wait.return_value = (
            {"run": {"conclusion": "success"}},
            True,
        )

        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=3,  # 3 attempts available
            ci_timeout=180,
            llm_truncate=False,
        )

        assert result is True
        assert mock_check_ci.call_count == 1  # Only 1 attempt used
        assert mock_wait.call_count == 1

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_fix_exhausts_all_attempts_on_failure(
        self,
        mock_sleep: Mock,
        mock_wait: Mock,
        mock_ci_manager: Mock,
        mock_check_ci: Mock,
        mock_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Should use all attempts if CI keeps failing."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        mock_branch.return_value = "feature-branch"
        mock_check_ci.return_value = True

        mock_manager = Mock()
        mock_ci_manager.return_value = mock_manager
        # Different run IDs for each attempt
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"id": 1}},
            {"run": {"id": 2}},  # Attempt 1
            {"run": {"id": 2}},
            {"run": {"id": 3}},  # Attempt 2
            {"run": {"id": 3}},
            {"run": {"id": 4}},  # Attempt 3
        ]

        # CI always fails
        mock_wait.return_value = (
            {"run": {"conclusion": "failure"}},
            False,
        )

        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=3,
            ci_timeout=180,
            llm_truncate=False,
        )

        assert result is False  # All attempts exhausted
        assert mock_check_ci.call_count == 3
        assert mock_wait.call_count == 3

    @patch("mcp_coder.cli.commands.check_branch_status.get_current_branch_name")
    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.CIResultsManager")
    @patch("mcp_coder.cli.commands.check_branch_status._wait_for_ci_completion")
    @patch("mcp_coder.cli.commands.check_branch_status.time.sleep")
    def test_fix_handles_wait_timeout_gracefully(
        self,
        mock_sleep: Mock,
        mock_wait: Mock,
        mock_ci_manager: Mock,
        mock_check_ci: Mock,
        mock_branch: Mock,
        failed_ci_report: BranchStatusReport,
    ) -> None:
        """Should handle CI wait timeout gracefully."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        mock_branch.return_value = "feature-branch"
        mock_check_ci.return_value = True

        mock_manager = Mock()
        mock_ci_manager.return_value = mock_manager
        mock_manager.get_latest_ci_status.side_effect = [
            {"run": {"id": 1}},
            {"run": {"id": 2}},
        ]

        # Wait times out (ci_status=None, success=False)
        mock_wait.return_value = (None, False)

        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
            "api",
            None,
            None,
            fix_attempts=2,
            ci_timeout=30,
            llm_truncate=False,
        )

        assert result is False  # Timeout counts as failure


class TestCheckBranchStatusParserEnhancements:
    """Test new parser parameters for CI waiting and fix retry."""

    def test_ci_timeout_parameter_defaults_to_zero(self) -> None:
        """Test --ci-timeout parameter defaults to 0."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status"])

        assert args.ci_timeout == 0

    def test_ci_timeout_accepts_integer_value(self) -> None:
        """Test --ci-timeout accepts integer values."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--ci-timeout", "180"])

        assert args.ci_timeout == 180

    def test_ci_timeout_rejects_negative_values(self) -> None:
        """Test --ci-timeout rejects negative values."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        with pytest.raises(SystemExit):  # argparse exits on validation error
            parser.parse_args(["check", "branch-status", "--ci-timeout", "-60"])

    def test_fix_without_argument_defaults_to_one(self) -> None:
        """Test --fix without argument equals 1 (fix once)."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--fix"])

        assert args.fix == 1

    def test_fix_with_integer_argument(self) -> None:
        """Test --fix with integer argument."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--fix", "3"])

        assert args.fix == 3

    def test_fix_zero_means_no_fix(self) -> None:
        """Test --fix 0 means no fix (same as not providing --fix)."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status", "--fix", "0"])

        assert args.fix == 0

    def test_fix_not_provided_defaults_to_zero(self) -> None:
        """Test --fix not provided defaults to 0 (no fix)."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(["check", "branch-status"])

        assert args.fix == 0

    def test_all_parameters_together(self) -> None:
        """Test --ci-timeout and --fix together."""
        from mcp_coder.cli.main import create_parser

        parser = create_parser()
        args = parser.parse_args(
            [
                "check",
                "branch-status",
                "--ci-timeout",
                "300",
                "--fix",
                "2",
                "--llm-truncate",
            ]
        )

        assert args.ci_timeout == 300
        assert args.fix == 2
        assert args.llm_truncate is True


class TestCheckBranchStatusCommandIntegration:
    """Test check_branch_status command CLI integration."""

    @patch("mcp_coder.cli.commands.check_branch_status.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check", "branch-status"])
    def test_check_branch_status_command_calls_function(
        self, mock_execute: Mock
    ) -> None:
        """Test that the check branch-status CLI command calls the execution function."""
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

    @patch("mcp_coder.cli.commands.check_branch_status.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check", "branch-status", "--fix"])
    def test_check_branch_status_command_with_fix_flag(
        self, mock_execute: Mock
    ) -> None:
        """Test check branch-status command with --fix flag."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0  # Success

        result = main()

        assert result == 0
        mock_execute.assert_called_once()

        # Check that fix flag was parsed correctly
        call_args = mock_execute.call_args[0][0]
        assert call_args.fix == 1

    @patch("mcp_coder.cli.commands.check_branch_status.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check", "branch-status", "--llm-truncate"])
    def test_check_branch_status_command_with_llm_truncate_flag(
        self, mock_execute: Mock
    ) -> None:
        """Test check branch-status command with --llm-truncate flag."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 0  # Success

        result = main()

        assert result == 0
        mock_execute.assert_called_once()

        # Check that llm_truncate flag was parsed correctly
        call_args = mock_execute.call_args[0][0]
        assert call_args.llm_truncate is True

    @patch("mcp_coder.cli.commands.check_branch_status.execute_check_branch_status")
    @patch("sys.argv", ["mcp-coder", "check", "branch-status"])
    def test_check_branch_status_command_propagates_return_code(
        self, mock_execute: Mock
    ) -> None:
        """Test that check branch-status command propagates the return code."""
        from mcp_coder.cli.main import main

        mock_execute.return_value = 1  # Error

        result = main()

        assert result == 1
        mock_execute.assert_called_once()

    def test_check_branch_status_command_is_implemented(self) -> None:
        """Test that check branch-status command is implemented in main CLI.

        This test verifies that the check branch-status command has been successfully
        added to the CLI.
        """
        from mcp_coder.cli.main import create_parser

        parser = create_parser()

        # Check if check command exists in parser
        subparsers_actions = [
            action
            for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]

        assert subparsers_actions, "No subparsers found in CLI parser"

        subparser = subparsers_actions[0]
        # Check if 'check' is in the choices
        assert (
            "check" in subparser.choices
        ), "check command should be implemented in main.py"

        # Verify the check parser has branch-status subcommand
        check_parser = subparser.choices["check"]

        # Get the branch-status subparser
        check_subparsers = [
            action
            for action in check_parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        assert check_subparsers, "No subparsers found in check parser"

        branch_status_subparser = check_subparsers[0]
        assert (
            "branch-status" in branch_status_subparser.choices
        ), "branch-status subcommand should be implemented under check"

        # Parse test arguments to verify structure
        branch_status_parser = branch_status_subparser.choices["branch-status"]
        test_args = branch_status_parser.parse_args(["--fix", "--llm-truncate"])
        assert hasattr(test_args, "project_dir")
        assert hasattr(test_args, "fix")
        assert hasattr(test_args, "llm_truncate")
        assert test_args.fix == 1
        assert test_args.llm_truncate is True
