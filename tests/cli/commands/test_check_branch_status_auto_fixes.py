"""Tests for check_branch_status auto-fixes functionality."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from mcp_workspace.workflows.task_tracker import TaskTrackerStatus

from mcp_coder.checks.branch_status import BranchStatusReport, CIStatus
from mcp_coder.workflow_steps import commit
from tests.ci_fix_drive import patch_ci_fix_externals


@pytest.fixture
def failed_ci_report() -> BranchStatusReport:
    """Create a BranchStatusReport with failed CI for testing."""
    return BranchStatusReport(
        branch_name="feature/test-branch",
        base_branch="main",
        ci_status=CIStatus.FAILED,
        ci_details="Test failure: AssertionError in test_example",
        rebase_needed=False,
        rebase_reason="Branch is up to date with main",
        tasks_status=TaskTrackerStatus.COMPLETE,
        tasks_reason="All tasks complete",
        tasks_is_blocking=False,
        current_github_label="status-implementation",
        recommendations=[
            "Fix CI failures before proceeding",
            "Check CI error details above",
        ],
    )


@pytest.fixture
def sample_report() -> BranchStatusReport:
    """Create a sample BranchStatusReport for testing."""
    return BranchStatusReport(
        branch_name="feature/test-branch",
        base_branch="main",
        ci_status=CIStatus.PASSED,
        ci_details=None,
        rebase_needed=False,
        rebase_reason="Branch is up to date with main",
        tasks_status=TaskTrackerStatus.COMPLETE,
        tasks_reason="All tasks complete",
        tasks_is_blocking=False,
        current_github_label="status-implementation",
        recommendations=["Branch is ready for next workflow step"],
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
        mock_get_branch.return_value = "feature/test-branch"
        mock_check_ci.return_value = True  # Success

        result = _run_auto_fixes(project_dir, failed_ci_report, "claude", None)

        assert result is True
        mock_check_ci.assert_called_once_with(
            project_dir, "feature/test-branch", "claude", None, None
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
        mock_get_branch.return_value = "feature/test-branch"
        mock_check_ci.return_value = False  # Failure

        result = _run_auto_fixes(project_dir, failed_ci_report, "claude", None)

        assert result is False
        mock_check_ci.assert_called_once()

    def test_run_auto_fixes_no_fixes_needed(
        self, sample_report: BranchStatusReport
    ) -> None:
        """Test auto-fixes when no fixes are needed."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        project_dir = Path("/test/project")

        result = _run_auto_fixes(project_dir, sample_report, "claude", None, None)

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
        mock_get_branch.return_value = "feature/test-branch"
        mock_check_ci.side_effect = Exception("Unexpected CI error")

        result = _run_auto_fixes(project_dir, failed_ci_report, "claude", None)

        assert result is False

    @patch("mcp_coder.cli.commands.check_branch_status.check_and_fix_ci")
    @patch("mcp_coder.cli.commands.check_branch_status.check_formatter_config")
    def test_run_auto_fixes_formatter_config_error(
        self,
        mock_check_formatter: Mock,
        mock_check_ci: Mock,
        failed_ci_report: BranchStatusReport,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Unresolvable formatter → False, error logged, no CI fix."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        project_dir = Path("/test/project")
        mock_check_formatter.return_value = "No formatter declared: X"

        with caplog.at_level(logging.ERROR):
            result = _run_auto_fixes(project_dir, failed_ci_report, "claude", None)

        assert result is False
        mock_check_formatter.assert_called_once_with(project_dir, warn_legacy_key=True)
        assert any(
            r.levelno == logging.ERROR and r.getMessage() == "No formatter declared: X"
            for r in caplog.records
        )
        mock_check_ci.assert_not_called()

    @patch("mcp_coder.cli.commands.check_branch_status.check_formatter_config")
    def test_run_auto_fixes_ci_not_failed_skips_formatter_check(
        self, mock_check_formatter: Mock, sample_report: BranchStatusReport
    ) -> None:
        """CI not failed → formatter config is not checked."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        result = _run_auto_fixes(Path("/test/project"), sample_report, "claude", None)

        assert result is True
        mock_check_formatter.assert_not_called()


class TestFixRetryLogic:
    """Test fix retry logic with multiple attempts."""

    def test_fix_zero_means_no_fix(self, failed_ci_report: BranchStatusReport) -> None:
        """With fix_attempts=0, should return True without attempting any fixes."""
        from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

        result = _run_auto_fixes(
            Path("/test"),
            failed_ci_report,
            "claude",
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
            None,
            None,
            fix_attempts=2,
            ci_timeout=30,
            llm_truncate=False,
        )

        assert result is False  # Timeout counts as failure


def test_auto_fix_format_code_false_skips_formatter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failed_ci_report: BranchStatusReport,
) -> None:
    """``format_code = false`` → ``--fix`` commits without calling the formatter."""
    from mcp_coder.cli.commands.check_branch_status import _run_auto_fixes

    (tmp_path / "pyproject.toml").write_text(
        "[tool.mcp-coder]\nformat_code = false\n", encoding="utf-8"
    )
    commit_changes = patch_ci_fix_externals(monkeypatch)
    wrapper = MagicMock(return_value={})
    monkeypatch.setattr(commit, "run_format_code", wrapper)

    with patch(
        "mcp_coder.cli.commands.check_branch_status.get_current_branch_name",
        return_value="feature/test-branch",
    ):
        result = _run_auto_fixes(tmp_path, failed_ci_report, "claude", None)

    assert result is True
    commit_changes.assert_called_once()
    wrapper.assert_not_called()
