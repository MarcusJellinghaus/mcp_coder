"""Unit tests for IssueManager with mocked dependencies."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import git
import pytest
from github.GithubException import GithubException

from mcp_coder.utils.github_operations.issues import IssueManager
from mcp_coder.utils.github_operations.issues.base import (
    validate_comment_id,
    validate_issue_number,
)


@pytest.mark.git_integration
class TestIssueManagerUnit:
    """Unit tests for IssueManager with mocked dependencies."""

    def test_initialization_requires_project_dir(self) -> None:
        """Test that None project_dir raises ValueError."""
        with pytest.raises(
            ValueError, match="Exactly one of project_dir or repo_url must be provided"
        ):
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): None}
            with pytest.raises(ValueError, match="GitHub token not found"):
                IssueManager(git_dir)

    def test_validate_issue_number(self, tmp_path: Path) -> None:
        """Test issue number validation."""
        # Test standalone validation function
        assert validate_issue_number(1) is True
        assert validate_issue_number(123) is True
        assert validate_issue_number(0) is False
        assert validate_issue_number(-1) is False

    def test_validate_comment_id(self, tmp_path: Path) -> None:
        """Test comment ID validation."""
        # Test standalone validation function
        assert validate_comment_id(1) is True
        assert validate_comment_id(456) is True
        assert validate_comment_id(0) is False
        assert validate_comment_id(-1) is False

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_issue_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful issue retrieval with assignees."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock assignee objects
        mock_assignee1 = MagicMock()
        mock_assignee1.login = "user1"
        mock_assignee2 = MagicMock()
        mock_assignee2.login = "user2"

        # Mock label objects
        mock_label = MagicMock()
        mock_label.name = "bug"

        # Mock GitHub API response
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = [mock_label]
        mock_issue.assignees = [mock_assignee1, mock_assignee2]
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.get_issue(123)

            assert result["number"] == 123
            assert result["title"] == "Test Issue"
            assert result["body"] == "Test description"
            assert result["state"] == "open"
            assert result["labels"] == ["bug"]
            assert result["assignees"] == ["user1", "user2"]
            assert result["user"] == "testuser"
            assert result["url"] == "https://github.com/test/repo/issues/123"
            assert result["locked"] is False

            mock_repo.get_issue.assert_called_once_with(123)

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
        mock_issue.assignees = []
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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
        mock_issue.assignees = []
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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
        mock_issue.assignees = []
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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
        mock_issue.assignees = []
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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
        mock_issue.assignees = []
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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
        mock_issue.assignees = []
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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
        mock_issue.assignees = []
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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
        mock_issue.assignees = []
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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
        mock_issue.assignees = []
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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
        mock_issue.assignees = []
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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
        mock_issue.assignees = []
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
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

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.set_labels(123, "bug")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_add_comment_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful comment addition."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock GitHub API responses
        mock_comment = MagicMock()
        mock_comment.id = 456789
        mock_comment.body = "This is a test comment"
        mock_comment.user.login = "testuser"
        mock_comment.html_url = (
            "https://github.com/test/repo/issues/123#issuecomment-456789"
        )
        mock_comment.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_comment.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"

        mock_issue = MagicMock()
        mock_issue.create_comment.return_value = mock_comment

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.add_comment(123, "This is a test comment")

            assert result["id"] == 456789
            assert result["body"] == "This is a test comment"
            assert result["user"] == "testuser"
            assert (
                result["url"]
                == "https://github.com/test/repo/issues/123#issuecomment-456789"
            )

            mock_issue.create_comment.assert_called_once_with("This is a test comment")

    def test_add_comment_empty_body(self, tmp_path: Path) -> None:
        """Test that empty comment body returns empty dict."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.add_comment(123, "")
            assert not result or result["id"] == 0

            result = manager.add_comment(123, "   ")
            assert not result or result["id"] == 0

    def test_add_comment_invalid_issue_number(self, tmp_path: Path) -> None:
        """Test adding comment with invalid issue number."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.add_comment(0, "Test comment")
            assert not result or result["id"] == 0

            result = manager.add_comment(-1, "Test comment")
            assert not result or result["id"] == 0

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_add_comment_auth_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that auth errors are raised for add_comment."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.create_comment.side_effect = GithubException(
            403, {"message": "Forbidden"}, None
        )

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.add_comment(123, "Test comment")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_comments_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful retrieval of comments."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock comment objects
        mock_comment1 = MagicMock()
        mock_comment1.id = 111
        mock_comment1.body = "First comment"
        mock_comment1.user.login = "user1"
        mock_comment1.html_url = (
            "https://github.com/test/repo/issues/123#issuecomment-111"
        )
        mock_comment1.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_comment1.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"

        mock_comment2 = MagicMock()
        mock_comment2.id = 222
        mock_comment2.body = "Second comment"
        mock_comment2.user.login = "user2"
        mock_comment2.html_url = (
            "https://github.com/test/repo/issues/123#issuecomment-222"
        )
        mock_comment2.created_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        mock_comment2.updated_at.isoformat.return_value = "2023-01-02T00:00:00Z"

        mock_issue = MagicMock()
        mock_issue.get_comments.return_value = [mock_comment1, mock_comment2]

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.get_comments(123)

            assert len(result) == 2
            assert result[0]["id"] == 111
            assert result[0]["body"] == "First comment"
            assert result[0]["user"] == "user1"
            assert result[1]["id"] == 222
            assert result[1]["body"] == "Second comment"
            assert result[1]["user"] == "user2"

            mock_issue.get_comments.assert_called_once()

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_comments_empty_list(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test getting comments from issue with no comments."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.get_comments.return_value = []

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.get_comments(123)

            assert result == []
            mock_issue.get_comments.assert_called_once()

    def test_get_comments_invalid_issue_number(self, tmp_path: Path) -> None:
        """Test getting comments with invalid issue number."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.get_comments(0)
            assert result == []

            result = manager.get_comments(-1)
            assert result == []

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_comments_auth_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that auth errors are raised for get_comments."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.get_comments.side_effect = GithubException(
            401, {"message": "Unauthorized"}, None
        )

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.get_comments(123)

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_edit_comment_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful comment editing."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock GitHub API responses
        mock_comment = MagicMock()
        mock_comment.id = 456789
        mock_comment.body = "Updated comment text"
        mock_comment.user.login = "testuser"
        mock_comment.html_url = (
            "https://github.com/test/repo/issues/123#issuecomment-456789"
        )
        mock_comment.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_comment.updated_at.isoformat.return_value = "2023-01-01T01:00:00Z"

        mock_issue = MagicMock()
        mock_issue.get_comment.return_value = mock_comment

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.edit_comment(123, 456789, "Updated comment text")

            assert result["id"] == 456789
            assert result["body"] == "Updated comment text"
            assert result["user"] == "testuser"
            assert (
                result["url"]
                == "https://github.com/test/repo/issues/123#issuecomment-456789"
            )

            # Verify edit was called
            mock_comment.edit.assert_called_once_with("Updated comment text")
            # Verify we fetched fresh data after editing
            assert mock_issue.get_comment.call_count == 2

    def test_edit_comment_empty_body(self, tmp_path: Path) -> None:
        """Test that empty comment body returns empty dict."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.edit_comment(123, 456789, "")
            assert not result or result["id"] == 0

            result = manager.edit_comment(123, 456789, "   ")
            assert not result or result["id"] == 0

    def test_edit_comment_invalid_issue_number(self, tmp_path: Path) -> None:
        """Test editing comment with invalid issue number."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.edit_comment(0, 456789, "Updated text")
            assert not result or result["id"] == 0

            result = manager.edit_comment(-1, 456789, "Updated text")
            assert not result or result["id"] == 0

    def test_edit_comment_invalid_comment_id(self, tmp_path: Path) -> None:
        """Test editing comment with invalid comment ID."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.edit_comment(123, 0, "Updated text")
            assert not result or result["id"] == 0

            result = manager.edit_comment(123, -1, "Updated text")
            assert not result or result["id"] == 0

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_edit_comment_auth_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that auth errors are raised for edit_comment."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_comment = MagicMock()
        mock_comment.edit.side_effect = GithubException(
            403, {"message": "Forbidden"}, None
        )

        mock_issue = MagicMock()
        mock_issue.get_comment.return_value = mock_comment

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.edit_comment(123, 456789, "Updated text")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_delete_comment_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful comment deletion."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock GitHub API responses
        mock_comment = MagicMock()

        mock_issue = MagicMock()
        mock_issue.get_comment.return_value = mock_comment

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.delete_comment(123, 456789)

            assert result is True

            # Verify delete was called
            mock_comment.delete.assert_called_once()

    def test_delete_comment_invalid_issue_number(self, tmp_path: Path) -> None:
        """Test deleting comment with invalid issue number."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.delete_comment(0, 456789)
            assert result is False

            result = manager.delete_comment(-1, 456789)
            assert result is False

    def test_delete_comment_invalid_comment_id(self, tmp_path: Path) -> None:
        """Test deleting comment with invalid comment ID."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.delete_comment(123, 0)
            assert result is False

            result = manager.delete_comment(123, -1)
            assert result is False

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_delete_comment_auth_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that auth errors are raised for delete_comment."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_comment = MagicMock()
        mock_comment.delete.side_effect = GithubException(
            401, {"message": "Unauthorized"}, None
        )

        mock_issue = MagicMock()
        mock_issue.get_comment.return_value = mock_comment

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            with pytest.raises(GithubException):
                manager.delete_comment(123, 456789)

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_issues_default_parameters(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test list_issues with default parameters (open, no PRs)."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock label objects
        mock_label = MagicMock()
        mock_label.name = "bug"

        # Mock issue (not a PR)
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = [mock_label]
        mock_issue.assignees = []
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False
        mock_issue.pull_request = None  # Not a PR

        # Mock PR (should be filtered out)
        mock_pr = MagicMock()
        mock_pr.number = 124
        mock_pr.title = "Test PR"
        mock_pr.body = "PR description"
        mock_pr.state = "open"
        mock_pr.labels = []
        mock_pr.assignees = []
        mock_pr.html_url = "https://github.com/test/repo/pull/124"
        mock_pr.created_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        mock_pr.updated_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        mock_pr.user.login = "testuser"
        mock_pr.locked = False
        mock_pr.pull_request = MagicMock()  # This is a PR

        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = [mock_issue, mock_pr]

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.list_issues()

            assert len(result) == 1
            assert result[0]["number"] == 123
            assert result[0]["title"] == "Test Issue"
            assert result[0]["labels"] == ["bug"]

            mock_repo.get_issues.assert_called_once_with(state="open")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_issues_open_only(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test list_issues filters by state='open'."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock open issue
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Open Issue"
        mock_issue.body = "Description"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.assignees = []
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False
        mock_issue.pull_request = None

        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = [mock_issue]

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.list_issues(state="open")

            assert len(result) == 1
            assert result[0]["state"] == "open"

            mock_repo.get_issues.assert_called_once_with(state="open")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_issues_include_pull_requests(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test list_issues includes PRs when flag=True."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock issue
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Issue description"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.assignees = []
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False
        mock_issue.pull_request = None

        # Mock PR
        mock_pr = MagicMock()
        mock_pr.number = 124
        mock_pr.title = "Test PR"
        mock_pr.body = "PR description"
        mock_pr.state = "open"
        mock_pr.labels = []
        mock_pr.assignees = []
        mock_pr.html_url = "https://github.com/test/repo/pull/124"
        mock_pr.created_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        mock_pr.updated_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        mock_pr.user.login = "testuser"
        mock_pr.locked = False
        mock_pr.pull_request = MagicMock()  # This is a PR

        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = [mock_issue, mock_pr]

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.list_issues(include_pull_requests=True)

            assert len(result) == 2
            assert result[0]["number"] == 123
            assert result[1]["number"] == 124

            mock_repo.get_issues.assert_called_once_with(state="open")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_issues_pagination_handled(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test list_issues handles GitHub API pagination."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Create 35 mock issues to simulate pagination
        mock_issues = []
        for i in range(35):
            mock_issue = MagicMock()
            mock_issue.number = i + 1
            mock_issue.title = f"Issue {i + 1}"
            mock_issue.body = f"Description {i + 1}"
            mock_issue.state = "open"
            mock_issue.labels = []
            mock_issue.assignees = []
            mock_issue.html_url = f"https://github.com/test/repo/issues/{i + 1}"
            mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
            mock_issue.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
            mock_issue.user.login = "testuser"
            mock_issue.locked = False
            mock_issue.pull_request = None
            mock_issues.append(mock_issue)

        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = mock_issues

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.list_issues()

            assert len(result) == 35
            assert result[0]["number"] == 1
            assert result[34]["number"] == 35

            mock_repo.get_issues.assert_called_once_with(state="open")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_issues_empty_repository(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test list_issues returns empty list for repo with no issues."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = []

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.list_issues()

            assert result == []
            mock_repo.get_issues.assert_called_once_with(state="open")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_issues_github_error_handling(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test list_issues handles GitHub API errors gracefully."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_repo = MagicMock()
        mock_repo.get_issues.side_effect = GithubException(
            500, {"message": "Server error"}, None
        )

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            # Non-auth errors should be handled gracefully and return empty list
            result = manager.list_issues()
            assert result == []

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_issue_events_success(self, mock_github: Mock, tmp_path: Path) -> None:
        """Test successful event retrieval."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock event objects
        mock_event1 = MagicMock()
        mock_event1.event = "labeled"
        mock_event1.label.name = "bug"
        mock_event1.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_event1.actor.login = "user1"

        mock_event2 = MagicMock()
        mock_event2.event = "unlabeled"
        mock_event2.label.name = "enhancement"
        mock_event2.created_at.isoformat.return_value = "2023-01-01T01:00:00Z"
        mock_event2.actor.login = "user2"

        mock_event3 = MagicMock()
        mock_event3.event = "commented"
        mock_event3.created_at.isoformat.return_value = "2023-01-01T02:00:00Z"
        mock_event3.actor.login = "user3"
        # commented events don't have label attribute
        delattr(mock_event3, "label")

        mock_issue = MagicMock()
        mock_issue.get_events.return_value = [mock_event1, mock_event2, mock_event3]

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.get_issue_events(123)

            assert len(result) == 3
            assert result[0]["event"] == "labeled"
            assert result[0]["label"] == "bug"
            assert result[0]["created_at"] == "2023-01-01T00:00:00Z"
            assert result[0]["actor"] == "user1"

            assert result[1]["event"] == "unlabeled"
            assert result[1]["label"] == "enhancement"
            assert result[1]["created_at"] == "2023-01-01T01:00:00Z"
            assert result[1]["actor"] == "user2"

            assert result[2]["event"] == "commented"
            assert result[2]["label"] is None
            assert result[2]["created_at"] == "2023-01-01T02:00:00Z"
            assert result[2]["actor"] == "user3"

            mock_issue.get_events.assert_called_once()

    def test_get_issue_events_invalid_issue_number(self, tmp_path: Path) -> None:
        """Test with invalid issue number returns empty list."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.get_issue_events(0)
            assert result == []

            result = manager.get_issue_events(-1)
            assert result == []

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_issue_events_filter_label_events(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that filtering by IssueEventType.LABELED works correctly."""
        from mcp_coder.utils.github_operations.issues import IssueEventType

        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock event objects
        mock_labeled_event = MagicMock()
        mock_labeled_event.event = "labeled"
        mock_labeled_event.label.name = "bug"
        mock_labeled_event.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_labeled_event.actor.login = "user1"

        mock_unlabeled_event = MagicMock()
        mock_unlabeled_event.event = "unlabeled"
        mock_unlabeled_event.label.name = "enhancement"
        mock_unlabeled_event.created_at.isoformat.return_value = "2023-01-01T01:00:00Z"
        mock_unlabeled_event.actor.login = "user2"

        mock_closed_event = MagicMock()
        mock_closed_event.event = "closed"
        mock_closed_event.created_at.isoformat.return_value = "2023-01-01T02:00:00Z"
        mock_closed_event.actor.login = "user3"
        delattr(mock_closed_event, "label")

        mock_issue = MagicMock()
        mock_issue.get_events.return_value = [
            mock_labeled_event,
            mock_unlabeled_event,
            mock_closed_event,
        ]

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            # Filter for only labeled events
            result = manager.get_issue_events(123, IssueEventType.LABELED)

            assert len(result) == 1
            assert result[0]["event"] == "labeled"
            assert result[0]["label"] == "bug"
            assert result[0]["actor"] == "user1"

            mock_issue.get_events.assert_called_once()

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_issue_events_api_error_raises(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test that API errors are raised for get_issue_events."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.get_events.side_effect = GithubException(
            500, {"message": "Server error"}, None
        )

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            # Verify that GithubException is raised (not handled)
            with pytest.raises(GithubException):
                manager.get_issue_events(123)

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_issue_events_filter_unlabeled(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test filtering by IssueEventType.UNLABELED."""
        from mcp_coder.utils.github_operations.issues import IssueEventType

        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock event objects
        mock_labeled_event = MagicMock()
        mock_labeled_event.event = "labeled"
        mock_labeled_event.label.name = "bug"
        mock_labeled_event.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_labeled_event.actor.login = "user1"

        mock_unlabeled_event1 = MagicMock()
        mock_unlabeled_event1.event = "unlabeled"
        mock_unlabeled_event1.label.name = "enhancement"
        mock_unlabeled_event1.created_at.isoformat.return_value = "2023-01-01T01:00:00Z"
        mock_unlabeled_event1.actor.login = "user2"

        mock_unlabeled_event2 = MagicMock()
        mock_unlabeled_event2.event = "unlabeled"
        mock_unlabeled_event2.label.name = "wontfix"
        mock_unlabeled_event2.created_at.isoformat.return_value = "2023-01-01T02:00:00Z"
        mock_unlabeled_event2.actor.login = "user3"

        mock_issue = MagicMock()
        mock_issue.get_events.return_value = [
            mock_labeled_event,
            mock_unlabeled_event1,
            mock_unlabeled_event2,
        ]

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            # Filter for only unlabeled events
            result = manager.get_issue_events(123, IssueEventType.UNLABELED)

            assert len(result) == 2
            assert result[0]["event"] == "unlabeled"
            assert result[0]["label"] == "enhancement"
            assert result[1]["event"] == "unlabeled"
            assert result[1]["label"] == "wontfix"

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_get_issue_events_empty_events(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test with issue that has no events."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        mock_issue = MagicMock()
        mock_issue.get_events.return_value = []

        mock_repo = MagicMock()
        mock_repo.get_issue.return_value = mock_issue

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            result = manager.get_issue_events(123)

            assert result == []
            mock_issue.get_events.assert_called_once()

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_issues_with_since_parameter(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test list_issues with since parameter filters by update time."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock issue objects
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Recent Issue"
        mock_issue.body = "Recent description"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.assignees = []
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False
        mock_issue.pull_request = None

        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = [mock_issue]

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            # Test with since parameter
            since_time = datetime(2023, 1, 1)
            result = manager.list_issues(since=since_time)

            assert len(result) == 1
            assert result[0]["number"] == 123
            assert result[0]["title"] == "Recent Issue"

            # Verify get_issues was called with since parameter
            mock_repo.get_issues.assert_called_once_with(state="open", since=since_time)

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_issues_since_filters_pull_requests(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test list_issues with since parameter still filters out PRs by default."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock issue (not a PR)
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Recent Issue"
        mock_issue.body = "Issue description"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.assignees = []
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-02T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False
        mock_issue.pull_request = None

        # Mock PR (should be filtered out)
        mock_pr = MagicMock()
        mock_pr.number = 124
        mock_pr.title = "Recent PR"
        mock_pr.body = "PR description"
        mock_pr.state = "open"
        mock_pr.labels = []
        mock_pr.assignees = []
        mock_pr.html_url = "https://github.com/test/repo/pull/124"
        mock_pr.created_at.isoformat.return_value = "2023-01-02T01:00:00Z"
        mock_pr.updated_at.isoformat.return_value = "2023-01-02T01:00:00Z"
        mock_pr.user.login = "testuser"
        mock_pr.locked = False
        mock_pr.pull_request = MagicMock()  # This is a PR

        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = [mock_issue, mock_pr]

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            # Test with since parameter
            since_time = datetime(2023, 1, 1)
            result = manager.list_issues(since=since_time, include_pull_requests=False)

            # Should only return the issue, not the PR
            assert len(result) == 1
            assert result[0]["number"] == 123
            assert result[0]["title"] == "Recent Issue"

            # Verify get_issues was called with since parameter
            mock_repo.get_issues.assert_called_once_with(state="open", since=since_time)

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_issues_without_since_unchanged(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test list_issues without since parameter works as before (backward compatibility)."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Mock issue
        mock_issue = MagicMock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "Test description"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.assignees = []
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.created_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.updated_at.isoformat.return_value = "2023-01-01T00:00:00Z"
        mock_issue.user.login = "testuser"
        mock_issue.locked = False
        mock_issue.pull_request = None

        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = [mock_issue]

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            # Test without since parameter (existing behavior)
            result = manager.list_issues(state="open", include_pull_requests=False)

            assert len(result) == 1
            assert result[0]["number"] == 123
            assert result[0]["title"] == "Test Issue"

            # Verify get_issues was called without since parameter
            mock_repo.get_issues.assert_called_once_with(state="open")

    @patch("mcp_coder.utils.github_operations.base_manager.Github")
    def test_list_issues_since_pagination(
        self, mock_github: Mock, tmp_path: Path
    ) -> None:
        """Test list_issues with since parameter handles pagination correctly."""
        git_dir = tmp_path / "git_dir"
        git_dir.mkdir()
        repo = git.Repo.init(git_dir)
        repo.create_remote("origin", "https://github.com/test/repo.git")

        # Create multiple mock issues to simulate pagination
        mock_issues = []
        for i in range(10):
            mock_issue = MagicMock()
            mock_issue.number = i + 1
            mock_issue.title = f"Recent Issue {i + 1}"
            mock_issue.body = f"Description {i + 1}"
            mock_issue.state = "open"
            mock_issue.labels = []
            mock_issue.assignees = []
            mock_issue.html_url = f"https://github.com/test/repo/issues/{i + 1}"
            mock_issue.created_at.isoformat.return_value = "2023-01-02T00:00:00Z"
            mock_issue.updated_at.isoformat.return_value = "2023-01-02T00:00:00Z"
            mock_issue.user.login = "testuser"
            mock_issue.locked = False
            mock_issue.pull_request = None
            mock_issues.append(mock_issue)

        mock_repo = MagicMock()
        mock_repo.get_issues.return_value = mock_issues

        mock_github_client = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_github.return_value = mock_github_client

        with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
            mock_config.return_value = {("github", "token"): "dummy-token"}
            manager = IssueManager(git_dir)

            # Test with since parameter
            since_time = datetime(2023, 1, 1)
            result = manager.list_issues(since=since_time)

            # Should return all 10 issues
            assert len(result) == 10
            assert result[0]["number"] == 1
            assert result[9]["number"] == 10

            # Verify get_issues was called with since parameter
            mock_repo.get_issues.assert_called_once_with(state="open", since=since_time)


# ==============================================================================
# Tests for _parse_base_branch() function
# ==============================================================================
class TestParseBaseBranch:
    """Tests for _parse_base_branch() function."""

    # Valid base branches
    def test_parse_base_branch_with_h3_header(self) -> None:
        """Test parsing base branch with standard H3 header."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        body = "### Base Branch\n\nfeature/v2\n\n### Description\n\nContent"
        assert _parse_base_branch(body) == "feature/v2"

    def test_parse_base_branch_case_insensitive(self) -> None:
        """Test parsing base branch with lowercase header."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        body = "# base branch\n\nmain\n\n# Description"
        assert _parse_base_branch(body) == "main"

    def test_parse_base_branch_uppercase(self) -> None:
        """Test parsing base branch with uppercase header."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        body = "## BASE BRANCH\n\nrelease/2.0\n\n## Description"
        assert _parse_base_branch(body) == "release/2.0"

    def test_parse_base_branch_with_h1_header(self) -> None:
        """Test parsing base branch with H1 header."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        body = "# Base Branch\n\nhotfix/urgent\n\n# Other"
        assert _parse_base_branch(body) == "hotfix/urgent"

    # No base branch (returns None)
    def test_parse_base_branch_no_section(self) -> None:
        """Test returns None when no base branch section exists."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        body = "### Description\n\nNo base branch section here"
        assert _parse_base_branch(body) is None

    def test_parse_base_branch_empty_body(self) -> None:
        """Test returns None for empty body."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        assert _parse_base_branch("") is None

    def test_parse_base_branch_none_body(self) -> None:
        """Test returns None for None body."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        assert _parse_base_branch(None) is None  # type: ignore[arg-type]

    def test_parse_base_branch_empty_content(self) -> None:
        """Test returns None when section has no content."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        body = "### Base Branch\n\n\n\n### Description"
        assert _parse_base_branch(body) is None

    def test_parse_base_branch_whitespace_only(self) -> None:
        """Test returns None when section has only whitespace."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        body = "### Base Branch\n\n   \n\n### Description"
        assert _parse_base_branch(body) is None

    def test_parse_base_branch_at_end_of_body(self) -> None:
        """Test parsing base branch when section is at end without trailing header."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        body = "### Description\n\nContent\n\n### Base Branch\n\nfeature/final"
        assert _parse_base_branch(body) == "feature/final"

    # Error cases (raises ValueError)
    def test_parse_base_branch_multiline_raises_error(self) -> None:
        """Test raises ValueError for multi-line content."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        body = "### Base Branch\n\nline1\nline2\n\n### Description"
        with pytest.raises(ValueError, match="multiple lines"):
            _parse_base_branch(body)

    def test_parse_base_branch_multiline_with_spaces_raises_error(self) -> None:
        """Test raises ValueError for multi-line content with leading spaces."""
        from mcp_coder.utils.github_operations.issues import _parse_base_branch

        body = "### Base Branch\n\nbranch1\n  branch2\n\n### Description"
        with pytest.raises(ValueError, match="multiple lines"):
            _parse_base_branch(body)


class TestGetIssueBaseBranch:
    """Tests for base_branch field in get_issue()."""

    def test_get_issue_with_base_branch(self) -> None:
        """Issue with valid base branch returns it in IssueData."""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "### Base Branch\n\nfeature/v2\n\n### Description\n\nContent"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.assignees = []
        mock_issue.user = None
        mock_issue.created_at = None
        mock_issue.updated_at = None
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.locked = False

        with patch(
            "mcp_coder.utils.github_operations.base_manager.BaseGitHubManager._get_repository"
        ) as mock_get_repo:
            mock_repo = Mock()
            mock_repo.get_issue.return_value = mock_issue
            mock_get_repo.return_value = mock_repo

            with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
                mock_config.return_value = {("github", "token"): "test_token"}
                with patch("github.Github"):
                    manager = IssueManager(repo_url="https://github.com/test/repo.git")
                    result = manager.get_issue(123)

        assert result["base_branch"] == "feature/v2"

    def test_get_issue_without_base_branch(self) -> None:
        """Issue without base branch section returns None."""
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "### Description\n\nNo base branch here"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.assignees = []
        mock_issue.user = None
        mock_issue.created_at = None
        mock_issue.updated_at = None
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.locked = False

        with patch(
            "mcp_coder.utils.github_operations.base_manager.BaseGitHubManager._get_repository"
        ) as mock_get_repo:
            mock_repo = Mock()
            mock_repo.get_issue.return_value = mock_issue
            mock_get_repo.return_value = mock_repo

            with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
                mock_config.return_value = {("github", "token"): "test_token"}
                with patch("github.Github"):
                    manager = IssueManager(repo_url="https://github.com/test/repo.git")
                    result = manager.get_issue(123)

        assert result["base_branch"] is None

    def test_get_issue_with_malformed_base_branch_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Issue with multi-line base branch logs warning and returns None."""
        import logging

        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test Issue"
        mock_issue.body = "### Base Branch\n\nline1\nline2\n\n### Description"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.assignees = []
        mock_issue.user = None
        mock_issue.created_at = None
        mock_issue.updated_at = None
        mock_issue.html_url = "https://github.com/test/repo/issues/123"
        mock_issue.locked = False

        with patch(
            "mcp_coder.utils.github_operations.base_manager.BaseGitHubManager._get_repository"
        ) as mock_get_repo:
            mock_repo = Mock()
            mock_repo.get_issue.return_value = mock_issue
            mock_get_repo.return_value = mock_repo

            with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
                mock_config.return_value = {("github", "token"): "test_token"}
                with patch("github.Github"):
                    with caplog.at_level(logging.WARNING):
                        manager = IssueManager(
                            repo_url="https://github.com/test/repo.git"
                        )
                        result = manager.get_issue(123)

        assert result["base_branch"] is None
        assert "malformed base branch" in caplog.text.lower()


class TestListIssuesBaseBranch:
    """Tests for base_branch field in list_issues()."""

    def test_list_issues_includes_base_branch(self) -> None:
        """list_issues() includes base_branch in each IssueData."""
        mock_issue1 = Mock()
        mock_issue1.number = 1
        mock_issue1.title = "Issue 1"
        mock_issue1.body = "### Base Branch\n\nmain\n\n### Desc"
        mock_issue1.state = "open"
        mock_issue1.labels = []
        mock_issue1.assignees = []
        mock_issue1.user = None
        mock_issue1.created_at = None
        mock_issue1.updated_at = None
        mock_issue1.html_url = "https://github.com/test/repo/issues/1"
        mock_issue1.locked = False
        mock_issue1.pull_request = None

        mock_issue2 = Mock()
        mock_issue2.number = 2
        mock_issue2.title = "Issue 2"
        mock_issue2.body = "### Description\n\nNo base branch"
        mock_issue2.state = "open"
        mock_issue2.labels = []
        mock_issue2.assignees = []
        mock_issue2.user = None
        mock_issue2.created_at = None
        mock_issue2.updated_at = None
        mock_issue2.html_url = "https://github.com/test/repo/issues/2"
        mock_issue2.locked = False
        mock_issue2.pull_request = None

        with patch(
            "mcp_coder.utils.github_operations.base_manager.BaseGitHubManager._get_repository"
        ) as mock_get_repo:
            mock_repo = Mock()
            mock_repo.get_issues.return_value = [mock_issue1, mock_issue2]
            mock_get_repo.return_value = mock_repo

            with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
                mock_config.return_value = {("github", "token"): "test_token"}
                with patch("github.Github"):
                    manager = IssueManager(repo_url="https://github.com/test/repo.git")
                    results = manager.list_issues()

        assert len(results) == 2
        assert results[0]["base_branch"] == "main"
        assert results[1]["base_branch"] is None

    def test_list_issues_with_malformed_base_branch_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """list_issues() logs warning for malformed base branch."""
        import logging

        mock_issue = Mock()
        mock_issue.number = 1
        mock_issue.title = "Issue 1"
        mock_issue.body = "### Base Branch\n\nline1\nline2\n\n### Desc"
        mock_issue.state = "open"
        mock_issue.labels = []
        mock_issue.assignees = []
        mock_issue.user = None
        mock_issue.created_at = None
        mock_issue.updated_at = None
        mock_issue.html_url = "https://github.com/test/repo/issues/1"
        mock_issue.locked = False
        mock_issue.pull_request = None

        with patch(
            "mcp_coder.utils.github_operations.base_manager.BaseGitHubManager._get_repository"
        ) as mock_get_repo:
            mock_repo = Mock()
            mock_repo.get_issues.return_value = [mock_issue]
            mock_get_repo.return_value = mock_repo

            with patch("mcp_coder.utils.user_config.get_config_values") as mock_config:
                mock_config.return_value = {("github", "token"): "test_token"}
                with patch("github.Github"):
                    with caplog.at_level(logging.WARNING):
                        manager = IssueManager(
                            repo_url="https://github.com/test/repo.git"
                        )
                        results = manager.list_issues()

        assert len(results) == 1
        assert results[0]["base_branch"] is None
        assert "malformed base branch" in caplog.text.lower()
