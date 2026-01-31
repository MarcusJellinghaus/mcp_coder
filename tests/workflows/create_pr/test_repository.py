"""Tests for create_PR workflow repository management functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.workflows.create_pr.core import cleanup_repository, create_pull_request


class TestCleanupRepository:
    """Test cleanup_repository function."""

    @patch("mcp_coder.workflows.create_pr.core.clean_profiler_output")
    @patch("mcp_coder.workflows.create_pr.core.delete_pr_info_directory")
    def test_cleanup_repository_success(
        self,
        mock_delete_pr_info: MagicMock,
        mock_clean_profiler: MagicMock,
    ) -> None:
        """Test successful repository cleanup."""
        mock_delete_pr_info.return_value = True
        mock_clean_profiler.return_value = True

        result = cleanup_repository(Path("/test/project"))

        assert result is True
        mock_delete_pr_info.assert_called_once_with(Path("/test/project"))
        mock_clean_profiler.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.create_pr.core.clean_profiler_output")
    @patch("mcp_coder.workflows.create_pr.core.delete_pr_info_directory")
    def test_cleanup_repository_delete_pr_info_fails(
        self,
        mock_delete_pr_info: MagicMock,
        mock_clean_profiler: MagicMock,
    ) -> None:
        """Test repository cleanup when delete_pr_info_directory fails."""
        mock_delete_pr_info.return_value = False
        mock_clean_profiler.return_value = True

        result = cleanup_repository(Path("/test/project"))

        assert result is False
        mock_delete_pr_info.assert_called_once_with(Path("/test/project"))
        # Should still call clean_profiler even if delete fails
        mock_clean_profiler.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.create_pr.core.clean_profiler_output")
    @patch("mcp_coder.workflows.create_pr.core.delete_pr_info_directory")
    def test_cleanup_repository_clean_profiler_fails(
        self,
        mock_delete_pr_info: MagicMock,
        mock_clean_profiler: MagicMock,
    ) -> None:
        """Test repository cleanup when clean_profiler_output fails."""
        mock_delete_pr_info.return_value = True
        mock_clean_profiler.return_value = False

        result = cleanup_repository(Path("/test/project"))

        assert result is False
        mock_delete_pr_info.assert_called_once_with(Path("/test/project"))
        mock_clean_profiler.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.create_pr.core.clean_profiler_output")
    @patch("mcp_coder.workflows.create_pr.core.delete_pr_info_directory")
    def test_cleanup_repository_both_fail(
        self,
        mock_delete_pr_info: MagicMock,
        mock_clean_profiler: MagicMock,
    ) -> None:
        """Test repository cleanup when both operations fail."""
        mock_delete_pr_info.return_value = False
        mock_clean_profiler.return_value = False

        result = cleanup_repository(Path("/test/project"))

        assert result is False
        mock_delete_pr_info.assert_called_once_with(Path("/test/project"))
        mock_clean_profiler.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.create_pr.core.clean_profiler_output")
    @patch("mcp_coder.workflows.create_pr.core.delete_pr_info_directory")
    def test_cleanup_repository_calls_both_cleanup_functions(
        self,
        mock_delete_pr_info: MagicMock,
        mock_clean_profiler: MagicMock,
    ) -> None:
        """Test that cleanup_repository calls both cleanup functions."""
        mock_delete_pr_info.return_value = True
        mock_clean_profiler.return_value = True

        result = cleanup_repository(Path("/test/project"))

        assert result is True
        # Verify both cleanup functions are called
        mock_delete_pr_info.assert_called_once_with(Path("/test/project"))
        mock_clean_profiler.assert_called_once_with(Path("/test/project"))

    @patch("mcp_coder.workflows.create_pr.core.clean_profiler_output")
    @patch("mcp_coder.workflows.create_pr.core.delete_pr_info_directory")
    def test_cleanup_repository_continues_on_first_failure(
        self,
        mock_delete_pr_info: MagicMock,
        mock_clean_profiler: MagicMock,
    ) -> None:
        """Test repository cleanup continues even when first operation fails."""
        mock_delete_pr_info.return_value = False
        mock_clean_profiler.return_value = True

        result = cleanup_repository(Path("/test/project"))

        assert result is False
        # Both functions should still be called even if first one fails
        mock_delete_pr_info.assert_called_once_with(Path("/test/project"))
        mock_clean_profiler.assert_called_once_with(Path("/test/project"))


class TestCreatePullRequest:
    """Test create_pull_request function."""

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.get_parent_branch_name")
    def test_create_pull_request_success(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_pr_manager: MagicMock,
    ) -> None:
        """Test successful pull request creation."""
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = "main"

        mock_manager_instance = MagicMock()
        mock_manager_instance.create_pull_request.return_value = {
            "number": 123,
            "url": "https://github.com/owner/repo/pull/123",
        }
        mock_pr_manager.return_value = mock_manager_instance

        result = create_pull_request(
            Path("/test/project"), "Test PR Title", "Test PR Body"
        )

        assert result is True
        mock_pr_manager.assert_called_once_with(Path("/test/project"))
        mock_manager_instance.create_pull_request.assert_called_once_with(
            title="Test PR Title",
            head_branch="feature-branch",
            base_branch="main",
            body="Test PR Body",
        )

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    def test_create_pull_request_no_current_branch(
        self, mock_current_branch: MagicMock
    ) -> None:
        """Test pull request creation when current branch is unknown."""
        mock_current_branch.return_value = None

        result = create_pull_request(
            Path("/test/project"), "Test PR Title", "Test PR Body"
        )

        assert result is False

    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.get_parent_branch_name")
    def test_create_pull_request_no_parent_branch(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
    ) -> None:
        """Test pull request creation when parent branch is unknown."""
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = None

        result = create_pull_request(
            Path("/test/project"), "Test PR Title", "Test PR Body"
        )

        assert result is False

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.get_parent_branch_name")
    def test_create_pull_request_manager_failure(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_pr_manager: MagicMock,
    ) -> None:
        """Test pull request creation when PullRequestManager fails."""
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = "main"

        mock_manager_instance = MagicMock()
        mock_manager_instance.create_pull_request.return_value = (
            {}
        )  # Empty dict indicates failure
        mock_pr_manager.return_value = mock_manager_instance

        result = create_pull_request(
            Path("/test/project"), "Test PR Title", "Test PR Body"
        )

        assert result is False

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.get_parent_branch_name")
    def test_create_pull_request_no_pr_number(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_pr_manager: MagicMock,
    ) -> None:
        """Test pull request creation when PR number is missing."""
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = "main"

        mock_manager_instance = MagicMock()
        mock_manager_instance.create_pull_request.return_value = {
            "url": "https://github.com/owner/repo/pull/123"
            # Missing "number" key
        }
        mock_pr_manager.return_value = mock_manager_instance

        result = create_pull_request(
            Path("/test/project"), "Test PR Title", "Test PR Body"
        )

        assert result is False

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.get_parent_branch_name")
    def test_create_pull_request_exception(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_pr_manager: MagicMock,
    ) -> None:
        """Test pull request creation when exception occurs."""
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = "main"

        mock_pr_manager.side_effect = Exception("GitHub API error")

        result = create_pull_request(
            Path("/test/project"), "Test PR Title", "Test PR Body"
        )

        assert result is False

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.get_parent_branch_name")
    def test_create_pull_request_success_with_url(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_pr_manager: MagicMock,
    ) -> None:
        """Test successful pull request creation with URL logging."""
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = "main"

        mock_manager_instance = MagicMock()
        mock_manager_instance.create_pull_request.return_value = {
            "number": 456,
            "url": "https://github.com/owner/repo/pull/456",
        }
        mock_pr_manager.return_value = mock_manager_instance

        result = create_pull_request(
            Path("/test/project"), "feat: Amazing feature", "Detailed description"
        )

        assert result is True
        mock_manager_instance.create_pull_request.assert_called_once_with(
            title="feat: Amazing feature",
            head_branch="feature-branch",
            base_branch="main",
            body="Detailed description",
        )

    @patch("mcp_coder.workflows.create_pr.core.PullRequestManager")
    @patch("mcp_coder.workflows.create_pr.core.get_current_branch_name")
    @patch("mcp_coder.workflows.create_pr.core.get_parent_branch_name")
    def test_create_pull_request_success_without_url(
        self,
        mock_parent_branch: MagicMock,
        mock_current_branch: MagicMock,
        mock_pr_manager: MagicMock,
    ) -> None:
        """Test successful pull request creation without URL in response."""
        mock_current_branch.return_value = "feature-branch"
        mock_parent_branch.return_value = "main"

        mock_manager_instance = MagicMock()
        mock_manager_instance.create_pull_request.return_value = {
            "number": 789
            # No "url" key
        }
        mock_pr_manager.return_value = mock_manager_instance

        result = create_pull_request(
            Path("/test/project"), "fix: Bug fix", "Fixed the bug"
        )

        assert result is True
