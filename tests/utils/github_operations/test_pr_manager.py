"""Comprehensive unit tests for PullRequestManager with mocked GitHub API.

This module focuses on testing our wrapper logic, validation, error handling,
and data transformation - NOT the PyGithub library itself.
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import git
import pytest
from github.GithubException import GithubException

from mcp_coder.utils.github_operations.pr_manager import PullRequestManager


@pytest.mark.git_integration
class TestPullRequestManagerUnit:
    """Unit tests for PullRequestManager with mocked dependencies."""

    # ========================================
    # Initialization Tests
    # ========================================

    def test_initialization_requires_project_dir(self) -> None:
        """Test that None project_dir raises ValueError."""
        with pytest.raises(ValueError, match="project_dir is required"):
            PullRequestManager(None)

    def test_initialization_requires_git_repository(self, tmp_path: Path) -> None:
        """Test that non-git directory raises ValueError."""
        regular_dir = tmp_path / "regular_dir"
        regular_dir.mkdir()

        with pytest.raises(ValueError, match="Directory is not a git repository"):
            PullRequestManager(regular_dir)

    def test_initialization_requires_github_remote(self, tmp_path: Path) -> None:
        """Test that git repo without GitHub remote raises ValueError."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        git.Repo.init(git_dir)  # No remote configured

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"  # Provide token to pass that check
            with pytest.raises(ValueError, match="Could not detect GitHub repository URL"):
                PullRequestManager(git_dir)

    def test_initialization_requires_github_token(self, tmp_path: Path) -> None:
        """Test that missing GitHub token raises ValueError."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = None
            with pytest.raises(ValueError, match="GitHub token not found"):
                PullRequestManager(git_dir)

    # ========================================
    # Validation Tests
    # ========================================

    def test_validate_pr_number(self, tmp_path: Path) -> None:
        """Test PR number validation logic."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            # Valid PR numbers
            assert manager._validate_pr_number(1) is True
            assert manager._validate_pr_number(123) is True
            assert manager._validate_pr_number(99999) is True

            # Invalid PR numbers
            assert manager._validate_pr_number(0) is False
            assert manager._validate_pr_number(-1) is False
            assert manager._validate_pr_number(-999) is False

    def test_validate_branch_name(self, tmp_path: Path) -> None:
        """Test branch name validation logic."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            # Valid branch names
            assert manager._validate_branch_name("main") is True
            assert manager._validate_branch_name("feature-branch") is True
            assert manager._validate_branch_name("feature/new-feature") is True
            assert manager._validate_branch_name("bugfix_123") is True

            # Invalid branch names - empty or whitespace
            assert manager._validate_branch_name("") is False
            assert manager._validate_branch_name("   ") is False

            # Invalid branch names - invalid characters
            assert manager._validate_branch_name("branch~name") is False
            assert manager._validate_branch_name("branch^name") is False
            assert manager._validate_branch_name("branch:name") is False
            assert manager._validate_branch_name("branch?name") is False
            assert manager._validate_branch_name("branch*name") is False
            assert manager._validate_branch_name("branch[name") is False

            # Invalid branch names - invalid start/end
            assert manager._validate_branch_name(".branch") is False
            assert manager._validate_branch_name("branch.") is False
            assert manager._validate_branch_name("branch.lock") is False

    # ========================================
    # Property Tests
    # ========================================

    def test_repository_name_property(self, tmp_path: Path) -> None:
        """Test repository_name property returns correct format."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/testuser/testrepo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "test-token"
            manager = PullRequestManager(git_dir)

            assert manager.repository_name == "testuser/testrepo"

    def test_repository_url_property(self, tmp_path: Path) -> None:
        """Test repository_url property is set correctly."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/testuser/testrepo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "test-token"
            manager = PullRequestManager(git_dir)

            assert manager.repository_url == "https://github.com/testuser/testrepo"

    # ========================================
    # Create Pull Request Tests
    # ========================================

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_create_pull_request_success(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test successful PR creation with mocked GitHub API."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock PR object
        mock_pr = MagicMock()
        mock_pr.number = 123
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.state = "open"
        mock_pr.head.ref = "feature-branch"
        mock_pr.base.ref = "main"
        mock_pr.html_url = "https://github.com/test/repo/pull/123"
        mock_pr.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_pr.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_pr.user.login = "testuser"
        mock_pr.mergeable = True
        mock_pr.merged = False
        mock_pr.draft = False

        mock_repo = MagicMock()
        mock_repo.create_pull.return_value = mock_pr

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            result = manager.create_pull_request(
                "Test PR", "feature-branch", "main", "Test description"
            )

            # Verify the result structure
            assert result["number"] == 123
            assert result["title"] == "Test PR"
            assert result["body"] == "Test description"
            assert result["state"] == "open"
            assert result["head_branch"] == "feature-branch"
            assert result["base_branch"] == "main"
            assert result["url"] == "https://github.com/test/repo/pull/123"

            # Verify GitHub API was called correctly
            mock_repo.create_pull.assert_called_once_with(
                title="Test PR",
                body="Test description",
                head="feature-branch",
                base="main",
            )

    def test_create_pull_request_empty_title(self, tmp_path: Path) -> None:
        """Test that empty title returns empty dict."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            # Empty title
            result = manager.create_pull_request("", "feature-branch", "main")
            assert not result

            # Whitespace-only title
            result = manager.create_pull_request("   ", "feature-branch", "main")
            assert not result

    def test_create_pull_request_invalid_head_branch(self, tmp_path: Path) -> None:
        """Test that invalid head branch returns empty dict."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            result = manager.create_pull_request(
                "Valid Title", "invalid~branch", "main"
            )
            assert not result

    def test_create_pull_request_invalid_base_branch(self, tmp_path: Path) -> None:
        """Test that invalid base branch returns empty dict."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            result = manager.create_pull_request(
                "Valid Title", "feature", "invalid^branch"
            )
            assert not result

    # ========================================
    # Get Pull Request Tests
    # ========================================

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_pull_request_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful PR retrieval."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock PR object
        mock_pr = MagicMock()
        mock_pr.number = 123
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.state = "open"
        mock_pr.head.ref = "feature-branch"
        mock_pr.base.ref = "main"
        mock_pr.html_url = "https://github.com/test/repo/pull/123"
        mock_pr.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_pr.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_pr.user.login = "testuser"
        mock_pr.mergeable = True
        mock_pr.merged = False
        mock_pr.draft = False

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            result = manager.get_pull_request(123)

            assert result["number"] == 123
            assert result["title"] == "Test PR"
            mock_repo.get_pull.assert_called_once_with(123)

    def test_get_pull_request_invalid_number(self, tmp_path: Path) -> None:
        """Test that invalid PR number returns empty dict."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            result = manager.get_pull_request(-1)
            assert not result

            result = manager.get_pull_request(0)
            assert not result

    # ========================================
    # List Pull Requests Tests
    # ========================================

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_pull_requests_data_transformation(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that our wrapper correctly transforms PyGithub objects to our format."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock multiple PR objects
        mock_pr1 = MagicMock()
        mock_pr1.number = 1
        mock_pr1.title = "First PR"
        mock_pr1.body = "First description"
        mock_pr1.state = "open"
        mock_pr1.head.ref = "feature-1"
        mock_pr1.base.ref = "main"
        mock_pr1.html_url = "https://github.com/test/repo/pull/1"
        mock_pr1.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_pr1.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_pr1.user.login = "user1"
        mock_pr1.mergeable = True
        mock_pr1.merged = False
        mock_pr1.draft = False

        mock_pr2 = MagicMock()
        mock_pr2.number = 2
        mock_pr2.title = "Second PR"
        mock_pr2.body = "Second description"
        mock_pr2.state = "open"
        mock_pr2.head.ref = "feature-2"
        mock_pr2.base.ref = "main"
        mock_pr2.html_url = "https://github.com/test/repo/pull/2"
        mock_pr2.created_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        mock_pr2.updated_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        mock_pr2.user.login = "user2"
        mock_pr2.mergeable = False
        mock_pr2.merged = False
        mock_pr2.draft = True

        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = [mock_pr1, mock_pr2]

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            result = manager.list_pull_requests(state="open")

            # Verify we got 2 PRs
            assert len(result) == 2

            # Verify data transformation is correct
            assert result[0]["number"] == 1
            assert result[0]["title"] == "First PR"
            assert result[0]["draft"] is False
            assert result[1]["number"] == 2
            assert result[1]["title"] == "Second PR"
            assert result[1]["draft"] is True

            # Verify API was called with correct parameters
            mock_repo.get_pulls.assert_called_once_with(state="open")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_pull_requests_with_base_branch_filter(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test listing PRs with base branch filter."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = []

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            manager.list_pull_requests(state="all", base_branch="develop")

            # Verify API was called with base branch parameter
            mock_repo.get_pulls.assert_called_once_with(state="all", base="develop")

    def test_list_pull_requests_invalid_base_branch(self, tmp_path: Path) -> None:
        """Test that invalid base branch returns empty list."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            result = manager.list_pull_requests(base_branch="invalid~branch")
            assert result == []

    # ========================================
    # Close Pull Request Tests
    # ========================================

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_close_pull_request_success(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test successful PR closing."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock PR object
        mock_pr = MagicMock()
        mock_pr.number = 123
        mock_pr.title = "Test PR"
        mock_pr.body = "Test description"
        mock_pr.state = "closed"
        mock_pr.head.ref = "feature-branch"
        mock_pr.base.ref = "main"
        mock_pr.html_url = "https://github.com/test/repo/pull/123"
        mock_pr.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_pr.updated_at.isoformat.return_value = "2023-01-01T01:00:00Z"
        mock_pr.user.login = "testuser"
        mock_pr.mergeable = True
        mock_pr.merged = False
        mock_pr.draft = False

        mock_repo = MagicMock()
        mock_repo.get_pull.return_value = mock_pr

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            result = manager.close_pull_request(123)

            assert result["number"] == 123
            assert result["state"] == "closed"

            # Verify edit was called to close the PR
            mock_pr.edit.assert_called_once_with(state="closed")
            # Verify we fetched fresh data after closing
            assert mock_repo.get_pull.call_count == 2

    def test_close_pull_request_invalid_number(self, tmp_path: Path) -> None:
        """Test closing PR with invalid number."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            result = manager.close_pull_request(0)
            assert not result

            result = manager.close_pull_request(-1)
            assert not result

    # ========================================
    # Error Handling Tests
    # ========================================

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_github_api_error_returns_empty(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that GitHub API errors are handled gracefully."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock API to raise error
        mock_repo = MagicMock()
        mock_repo.create_pull.side_effect = GithubException(
            404, {"message": "Not Found"}, None
        )

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = PullRequestManager(git_dir)

            # Errors should return empty dict
            result = manager.create_pull_request("Test PR", "feature", "main")
            assert not result
