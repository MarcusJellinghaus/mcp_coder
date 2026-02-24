"""Tests for check_branch_status CI waiting functionality."""

import argparse
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
        """Should handle API errors gracefully by raising RuntimeError."""
        from mcp_coder.cli.commands.check_branch_status import (
            _wait_for_ci_completion,
        )

        mock_manager = Mock()
        mock_manager.get_latest_ci_status.side_effect = Exception("API Error")

        with pytest.raises(RuntimeError, match="API error during CI polling"):
            _wait_for_ci_completion(mock_manager, "branch", 30, True)

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

        sample_report = BranchStatusReport(
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
