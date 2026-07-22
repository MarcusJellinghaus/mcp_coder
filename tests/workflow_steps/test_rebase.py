"""Tests for the rebase-and-push workflow step."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.workflow_steps.rebase import (
    _attempt_rebase_and_push,
    _get_rebase_target_branch,
)
from mcp_coder.workflows.implement.core import run_implement_workflow


class TestGetRebaseTargetBranch:
    """Tests for _get_rebase_target_branch function."""

    @patch("mcp_coder.workflow_steps.rebase.detect_base_branch")
    def test_returns_pr_base_branch(
        self, mock_detect_base: MagicMock, tmp_path: Path
    ) -> None:
        """Test returns base_branch when detect_base_branch finds a valid branch."""
        mock_detect_base.return_value = "develop"

        result = _get_rebase_target_branch(tmp_path)
        assert result == "develop"

    @patch("mcp_coder.workflow_steps.rebase.detect_base_branch")
    def test_returns_none_when_detection_fails(
        self, mock_detect_base: MagicMock, tmp_path: Path
    ) -> None:
        """Test returns None when detect_base_branch returns None."""
        mock_detect_base.return_value = None

        result = _get_rebase_target_branch(tmp_path)
        assert result is None

    @patch("mcp_coder.workflow_steps.rebase.detect_base_branch")
    def test_returns_valid_branch_from_detection(
        self, mock_detect_base: MagicMock, tmp_path: Path
    ) -> None:
        """Test returns the branch name when detect_base_branch returns a valid branch."""
        mock_detect_base.return_value = "main"

        result = _get_rebase_target_branch(tmp_path)
        assert result == "main"


class TestRebaseIntegration:
    """Tests for rebase integration in workflow."""

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_rebase_and_push_called_after_prerequisites(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test rebase is attempted after prerequisites pass."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop here
        mock_get_target.return_value = "main"
        mock_rebase.return_value = True  # Rebase succeeds
        mock_push.return_value = True  # Push succeeds

        run_implement_workflow(Path("/test"), "claude")

        mock_get_target.assert_called_once()
        mock_rebase.assert_called_once_with(Path("/test"), "main")

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_push_with_force_with_lease_after_successful_rebase(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test push is called with force_with_lease=True after successful rebase."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop here
        mock_get_target.return_value = "main"
        mock_rebase.return_value = True  # Rebase succeeds
        mock_push.return_value = True  # Push succeeds

        run_implement_workflow(Path("/test"), "claude")

        # Verify push was called with force_with_lease=True
        mock_push.assert_called_once_with(Path("/test"), force_with_lease=True)

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_workflow_continues_when_rebase_fails(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test workflow continues even when rebase returns False."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop workflow here to focus on rebase
        mock_get_target.return_value = "main"
        mock_rebase.return_value = False  # Rebase failed

        # Should not fail - workflow continues past rebase failure
        result = run_implement_workflow(Path("/test"), "claude", "cli")

        # Workflow should have continued to prepare_task_tracker
        mock_prepare.assert_called_once()
        # Push should not be called when rebase fails
        mock_push.assert_not_called()
        # Result is 1 because prepare_task_tracker returns False, not because of rebase
        assert result == 1

    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_rebase_skipped_when_no_target_branch(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
    ) -> None:
        """Test rebase is skipped when target branch cannot be detected."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = False  # Stop here
        mock_get_target.return_value = None  # No target detected

        run_implement_workflow(Path("/test"), "claude")

        mock_rebase.assert_not_called()

    @patch("mcp_coder.workflow_steps.rebase.push_changes")
    @patch("mcp_coder.workflow_steps.rebase.rebase_onto_branch")
    @patch("mcp_coder.workflow_steps.rebase._get_rebase_target_branch")
    @patch("mcp_coder.workflows.implement.core.prepare_task_tracker")
    @patch("mcp_coder.workflows.implement.core.check_prerequisites")
    @patch("mcp_coder.workflows.implement.core.check_main_branch")
    @patch("mcp_coder.workflows.implement.core.check_git_clean")
    def test_workflow_continues_when_push_after_rebase_fails(
        self,
        mock_clean: MagicMock,
        mock_branch: MagicMock,
        mock_prereq: MagicMock,
        mock_prepare: MagicMock,
        mock_get_target: MagicMock,
        mock_rebase: MagicMock,
        mock_push: MagicMock,
    ) -> None:
        """Test workflow continues even when push after rebase fails."""
        mock_clean.return_value = True
        mock_branch.return_value = True
        mock_prereq.return_value = True
        mock_prepare.return_value = False  # Stop workflow here
        mock_get_target.return_value = "main"
        mock_rebase.return_value = True  # Rebase succeeds
        mock_push.return_value = False  # Push fails

        # Should not fail - workflow continues past push failure
        result = run_implement_workflow(Path("/test"), "claude", "cli")

        # Workflow should have continued to prepare_task_tracker
        mock_prepare.assert_called_once()
        # Result is 1 because prepare_task_tracker returns False
        assert result == 1
