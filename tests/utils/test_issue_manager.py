"""Unit tests for IssueManager with mocked dependencies."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import git
import pytest
from github.GithubException import GithubException

from mcp_coder.utils.github_operations.issue_manager import IssueManager


class TestIssueManagerUnit:
    """Unit tests for IssueManager with mocked dependencies."""

    def test_initialization_requires_project_dir(self) -> None:
        """Test that None project_dir raises ValueError."""
        with pytest.raises(ValueError, match="project_dir is required"):
            IssueManager(None)

    def test_initialization_requires_git_repository(self, tmp_path: Path) -> None:
        """Test that non-git directory raises ValueError."""
        regular_dir = tmp_path / "regular_dir"
        regular_dir.mkdir()

        with pytest.raises(ValueError, match="Directory is not a git repository"):
            IssueManager(regular_dir)

    def test_initialization_requires_github_token(self, tmp_path: Path) -> None:
        """Test that missing GitHub token raises ValueError."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = None
            with pytest.raises(ValueError, match="GitHub token not found"):
                IssueManager(git_dir)

    def test_validate_issue_number(self, tmp_path: Path) -> None:
        """Test issue number validation."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            assert manager._validate_issue_number(1) is True
            assert manager._validate_issue_number(123) is True
            assert manager._validate_issue_number(0) is False
            assert manager._validate_issue_number(-1) is False

    def test_validate_comment_id(self, tmp_path: Path) -> None:
        """Test comment ID validation."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            assert manager._validate_comment_id(1) is True
            assert manager._validate_comment_id(456) is True
            assert manager._validate_comment_id(0) is False
            assert manager._validate_comment_id(-1) is False

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_create_issue_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful issue creation."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock GitHub API responses
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False

        mock_repo = MagicMock()
        mock_repo.create_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.create_issue("Test Issue", "Test description")

            assert result["number"] == 123
            assert result["title"] == "Test Issue"
            assert result["body"] == "Test description"
            assert result["state"] == "open"
            assert result["url"] == "https://github.com/test/repo/issues/123"

            mock_repo.create_issue.assert_called_once_with(
                title="Test Issue", body="Test description", labels=[]
            )

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_create_issue_with_labels(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test issue creation with labels."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock label objects
        mock_label1 = MagicMock()
        mock_label1.name = "bug"
        mock_label2 = MagicMock()
        mock_label2.name = "high-priority"

        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Bug Report"
        mock_issue.body = "Bug description"
        mock_issue.state = "open"
        mock_issue.labels = [mock_label1, mock_label2]
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False

        mock_repo = MagicMock()
        mock_repo.create_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.create_issue(
                "Bug Report", "Bug description", labels=["bug", "high-priority"]
            )

            assert result["number"] == 123
            assert result["labels"] == ["bug", "high-priority"]

            mock_repo.create_issue.assert_called_once_with(
                title="Bug Report",
                body="Bug description",
                labels=["bug", "high-priority"],
            )

    def test_create_issue_empty_title(self, tmp_path: Path) -> None:
        """Test that empty title returns empty dict."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.create_issue("")
            assert not result or result["number"] == 0

            result = manager.create_issue("   ")
            assert not result or result["number"] == 0

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_close_issue_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful issue closing."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock GitHub API responses
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "closed"
        mock_issue.labels = []
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T01:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.close_issue(123)

            assert result["number"] == 123
            assert result["state"] == "closed"

            # Verify edit was called to close the issue
            mock_issue.edit.assert_called_once_with(state="closed")
            # Verify we fetched fresh data after closing
            assert mock_repo.get_issue.call_count == 2

    def test_close_issue_invalid_number(self, tmp_path: Path) -> None:
        """Test closing issue with invalid number."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.close_issue(0)
            assert not result or result["number"] == 0

            result = manager.close_issue(-1)
            assert not result or result["number"] == 0

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_reopen_issue_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful issue reopening."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock GitHub API responses
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T02:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.reopen_issue(123)

            assert result["number"] == 123
            assert result["state"] == "open"

            # Verify edit was called to reopen the issue
            mock_issue.edit.assert_called_once_with(state="open")
            # Verify we fetched fresh data after reopening
            assert mock_repo.get_issue.call_count == 2

    def test_reopen_issue_invalid_number(self, tmp_path: Path) -> None:
        """Test reopening issue with invalid number."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.reopen_issue(0)
            assert not result or result["number"] == 0

            result = manager.reopen_issue(-1)
            assert not result or result["number"] == 0

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_create_issue_auth_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that auth errors are raised for create_issue."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_repo = MagicMock()
        mock_repo.create_issue.side_effect = GithubException(
            401, {"message": "Bad credentials"}, None
        )

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.create_issue("Test Issue")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_close_issue_auth_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that auth errors are raised for close_issue."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.edit.side_effect = GithubException(
            403, {"message": "Forbidden"}, None
        )

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.close_issue(123)

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_reopen_issue_auth_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that auth errors are raised for reopen_issue."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.edit.side_effect = GithubException(
            401, {"message": "Unauthorized"}, None
        )

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.reopen_issue(123)

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_available_labels_success(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test successful retrieval of repository labels."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock label objects
        mock_label1 = MagicMock()
        mock_label1.name = "bug"
        mock_label1.color = "d73a4a"
        mock_label1.description = "Something isn't working"

        mock_label2 = MagicMock()
        mock_label2.name = "enhancement"
        mock_label2.color = "a2eeef"
        mock_label2.description = "New feature or request"

        mock_label3 = MagicMock()
        mock_label3.name = "documentation"
        mock_label3.color = "0075ca"
        mock_label3.description = None

        mock_repo = MagicMock()
        mock_repo.get_labels.return_value = [mock_label1, mock_label2, mock_label3]

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.get_available_labels()

            assert len(result) == 3
            assert result[0]["name"] == "bug"
            assert result[0]["color"] == "d73a4a"
            assert result[0]["description"] == "Something isn't working"
            assert result[1]["name"] == "enhancement"
            assert result[1]["color"] == "a2eeef"
            assert result[2]["name"] == "documentation"
            assert result[2]["description"] is None

            mock_repo.get_labels.assert_called_once()

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_available_labels_auth_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that auth errors are raised for get_available_labels."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_repo = MagicMock()
        mock_repo.get_labels.side_effect = GithubException(
            401, {"message": "Bad credentials"}, None
        )

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.get_available_labels()

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_add_labels_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful addition of labels to an issue."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock label objects
        mock_label1 = MagicMock()
        mock_label1.name = "bug"
        mock_label2 = MagicMock()
        mock_label2.name = "high-priority"

        # Mock GitHub API responses
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = [mock_label1, mock_label2]
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T01:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.add_labels(123, "bug", "high-priority")

            assert result["number"] == 123
            assert result["labels"] == ["bug", "high-priority"]

            # Verify add_to_labels was called with variadic args
            mock_issue.add_to_labels.assert_called_once_with("bug", "high-priority")
            # Verify we fetched fresh data after adding labels
            assert mock_repo.get_issue.call_count == 2

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_add_labels_single_label(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test adding a single label to an issue."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock label object
        mock_label = MagicMock()
        mock_label.name = "bug"

        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = [mock_label]
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.add_labels(123, "bug")

            assert result["number"] == 123
            assert result["labels"] == ["bug"]

            mock_issue.add_to_labels.assert_called_once_with("bug")

    def test_add_labels_invalid_issue_number(self, tmp_path: Path) -> None:
        """Test adding labels with invalid issue number."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.add_labels(0, "bug")
            assert not result or result["number"] == 0

            result = manager.add_labels(-1, "bug")
            assert not result or result["number"] == 0

    def test_add_labels_no_labels_provided(self, tmp_path: Path) -> None:
        """Test adding labels without providing any labels."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.add_labels(123)
            assert not result or result["number"] == 0

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_add_labels_auth_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that auth errors are raised for add_labels."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.add_to_labels.side_effect = GithubException(
            403, {"message": "Forbidden"}, None
        )

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.add_labels(123, "bug")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_remove_labels_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful removal of labels from an issue."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock label object (remaining label)
        mock_label = MagicMock()
        mock_label.name = "documentation"

        # Mock GitHub API responses
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = [mock_label]  # Only one label remaining after removal
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T01:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.remove_labels(123, "bug", "high-priority")

            assert result["number"] == 123
            assert result["labels"] == ["documentation"]

            # Verify remove_from_labels was called for each label
            assert mock_issue.remove_from_labels.call_count == 2
            mock_issue.remove_from_labels.assert_any_call("bug")
            mock_issue.remove_from_labels.assert_any_call("high-priority")
            # Verify we fetched fresh data after removing labels
            assert mock_repo.get_issue.call_count == 2

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_remove_labels_single_label(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test removing a single label from an issue."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = []  # All labels removed
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.remove_labels(123, "bug")

            assert result["number"] == 123
            assert result["labels"] == []

            mock_issue.remove_from_labels.assert_called_once_with("bug")

    def test_remove_labels_invalid_issue_number(self, tmp_path: Path) -> None:
        """Test removing labels with invalid issue number."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.remove_labels(0, "bug")
            assert not result or result["number"] == 0

            result = manager.remove_labels(-1, "bug")
            assert not result or result["number"] == 0

    def test_remove_labels_no_labels_provided(self, tmp_path: Path) -> None:
        """Test removing labels without providing any labels."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.remove_labels(123)
            assert not result or result["number"] == 0

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_remove_labels_auth_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that auth errors are raised for remove_labels."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.remove_from_labels.side_effect = GithubException(
            403, {"message": "Forbidden"}, None
        )

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.remove_labels(123, "bug")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_set_labels_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful setting of labels on an issue."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock label objects
        mock_label1 = MagicMock()
        mock_label1.name = "bug"
        mock_label2 = MagicMock()
        mock_label2.name = "high-priority"

        # Mock GitHub API responses
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = [mock_label1, mock_label2]
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T01:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.set_labels(123, "bug", "high-priority")

            assert result["number"] == 123
            assert result["labels"] == ["bug", "high-priority"]

            # Verify set_labels was called with variadic args
            mock_issue.set_labels.assert_called_once_with("bug", "high-priority")
            # Verify we fetched fresh data after setting labels
            assert mock_repo.get_issue.call_count == 2

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_set_labels_empty_to_clear_all(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test setting empty labels to clear all labels."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = []  # All labels removed
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.set_labels(123)

            assert result["number"] == 123
            assert result["labels"] == []

            # Verify set_labels was called with no args (clears all labels)
            mock_issue.set_labels.assert_called_once_with()

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_set_labels_single_label(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test setting a single label on an issue."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock label object
        mock_label = MagicMock()
        mock_label.name = "bug"

        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = [mock_label]
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.set_labels(123, "bug")

            assert result["number"] == 123
            assert result["labels"] == ["bug"]

            mock_issue.set_labels.assert_called_once_with("bug")

    def test_set_labels_invalid_issue_number(self, tmp_path: Path) -> None:
        """Test setting labels with invalid issue number."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            result = manager.set_labels(0, "bug")
            assert not result or result["number"] == 0

            result = manager.set_labels(-1, "bug")
            assert not result or result["number"] == 0

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_set_labels_auth_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that auth errors are raised for set_labels."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.set_labels.side_effect = GithubException(
            401, {"message": "Unauthorized"}, None
        )

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_value") as mock_config:
            mock_config.return_value = "dummy-token"
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.set_labels(123, "bug")
