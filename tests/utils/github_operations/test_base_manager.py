"""Unit tests for BaseGitHubManager error handling decorator."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import git
import pytest
from github.GithubException import GithubException

from mcp_coder.utils.github_operations.base_manager import (
    BaseGitHubManager,
    _handle_github_errors,
)


class TestHandleGitHubErrorsDecorator:
    """Unit tests for _handle_github_errors decorator."""

    def test_decorator_success_returns_value(self) -> None:
        """Test that decorator returns function value on success."""

        @_handle_github_errors(default_return={})
        def successful_function() -> dict[str, str]:
            return {"result": "success"}

        result = successful_function()
        assert result == {"result": "success"}

    def test_decorator_auth_error_401_raises(self) -> None:
        """Test that decorator re-raises 401 authentication errors."""

        @_handle_github_errors(default_return={})
        def function_with_auth_error() -> dict[str, str]:
            raise GithubException(401, {"message": "Bad credentials"}, None)

        with pytest.raises(GithubException) as exc_info:
            function_with_auth_error()

        assert exc_info.value.status == 401

    def test_decorator_auth_error_403_raises(self) -> None:
        """Test that decorator re-raises 403 permission errors."""

        @_handle_github_errors(default_return={})
        def function_with_permission_error() -> dict[str, str]:
            raise GithubException(403, {"message": "Forbidden"}, None)

        with pytest.raises(GithubException) as exc_info:
            function_with_permission_error()

        assert exc_info.value.status == 403

    def test_decorator_other_github_error_returns_default(self) -> None:
        """Test that decorator returns default for non-auth GitHub errors."""

        @_handle_github_errors(default_return={"error": "default"})
        def function_with_github_error() -> dict[str, str]:
            raise GithubException(404, {"message": "Not found"}, None)

        result = function_with_github_error()
        assert result == {"error": "default"}

    def test_decorator_generic_exception_returns_default(self) -> None:
        """Test that decorator returns default for generic exceptions."""

        @_handle_github_errors(default_return={"error": "default"})
        def function_with_generic_error() -> dict[str, str]:
            raise ValueError("Something went wrong")

        result = function_with_generic_error()
        assert result == {"error": "default"}

    def test_decorator_with_list_default_return(self) -> None:
        """Test that decorator works with list as default return value."""

        @_handle_github_errors(default_return=[])
        def function_returning_list() -> list[str]:
            raise GithubException(500, {"message": "Internal error"}, None)

        result = function_returning_list()
        assert result == []

    def test_decorator_with_bool_default_return(self) -> None:
        """Test that decorator works with bool as default return value."""

        @_handle_github_errors(default_return=False)
        def function_returning_bool() -> bool:
            raise GithubException(500, {"message": "Internal error"}, None)

        result = function_returning_bool()
        assert result is False

    def test_decorator_with_none_default_return(self) -> None:
        """Test that decorator works with None as default return value."""

        @_handle_github_errors(default_return=None)
        def function_returning_optional() -> str | None:
            raise ValueError("Error")

        result = function_returning_optional()
        assert result is None

    def test_decorator_preserves_function_args(self) -> None:
        """Test that decorator properly passes arguments to wrapped function."""

        @_handle_github_errors(default_return={})
        def function_with_args(a: int, b: str, c: bool = True) -> dict[str, object]:
            return {"a": a, "b": b, "c": c}

        result = function_with_args(42, "test", c=False)
        assert result == {"a": 42, "b": "test", "c": False}

    def test_decorator_preserves_function_name(self) -> None:
        """Test that decorator preserves function name via functools.wraps."""

        @_handle_github_errors(default_return={})
        def my_function() -> dict[str, str]:
            """My function docstring."""
            return {}

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My function docstring."

    def test_decorator_logs_auth_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test that decorator logs auth/permission errors before re-raising."""

        @_handle_github_errors(default_return={})
        def function_with_auth_error() -> dict[str, str]:
            raise GithubException(401, {"message": "Bad credentials"}, None)

        with pytest.raises(GithubException):
            function_with_auth_error()

        assert (
            "Authentication/permission error in function_with_auth_error" in caplog.text
        )

    def test_decorator_logs_github_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that decorator logs non-auth GitHub errors."""

        @_handle_github_errors(default_return={})
        def function_with_github_error() -> dict[str, str]:
            raise GithubException(404, {"message": "Not found"}, None)

        result = function_with_github_error()

        assert result == {}
        assert "GitHub API error in function_with_github_error" in caplog.text

    def test_decorator_logs_generic_error(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test that decorator logs generic exceptions."""

        @_handle_github_errors(default_return={})
        def function_with_generic_error() -> dict[str, str]:
            raise RuntimeError("Unexpected error")

        result = function_with_generic_error()

        assert result == {}
        assert "Unexpected error in function_with_generic_error" in caplog.text

    def test_decorator_with_method(self) -> None:
        """Test that decorator works with instance methods."""

        class MyManager:
            @_handle_github_errors(default_return={})
            def my_method(self, value: str) -> dict[str, str]:
                if value == "error":
                    raise ValueError("Error occurred")
                return {"value": value}

        manager = MyManager()

        # Success case
        result = manager.my_method("test")
        assert result == {"value": "test"}

        # Error case
        result = manager.my_method("error")
        assert result == {}

    def test_decorator_exception_propagation_for_auth_errors(self) -> None:
        """Test that only auth errors (401, 403) are propagated, others are not."""

        @_handle_github_errors(default_return={"status": "error"})
        def function_with_various_errors(status_code: int) -> dict[str, str]:
            raise GithubException(status_code, {"message": "Error"}, None)

        # Auth errors should be raised
        with pytest.raises(GithubException):
            function_with_various_errors(401)

        with pytest.raises(GithubException):
            function_with_various_errors(403)

        # Other errors should return default
        assert function_with_various_errors(400) == {"status": "error"}
        assert function_with_various_errors(404) == {"status": "error"}
        assert function_with_various_errors(500) == {"status": "error"}
        assert function_with_various_errors(502) == {"status": "error"}


class TestBaseGitHubManagerWithProjectDir:
    """Test suite for BaseGitHubManager initialization with project_dir.

    Tests the existing behavior where BaseGitHubManager is initialized
    with a local git repository path (project_dir parameter).
    """

    def test_successful_initialization_with_project_dir(self) -> None:
        """Test successful initialization with valid project directory."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        mock_repo = Mock(spec=git.Repo)

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.git.Repo"
            ) as mock_repo_class,
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch(
                "mcp_coder.utils.github_operations.base_manager.Github"
            ) as mock_github_class,
        ):
            mock_repo_class.return_value = mock_repo

            manager = BaseGitHubManager(project_dir=mock_path)

            # Verify manager was initialized correctly
            assert manager.project_dir == mock_path
            assert manager._repo == mock_repo
            assert manager.github_token == "fake_token"
            assert manager._repository is None  # Not fetched yet
            # repo_url mode attributes should be None
            assert manager._repo_owner is None
            assert manager._repo_name is None
            assert manager._repo_full_name is None

            # Verify git.Repo was called with project_dir
            mock_repo_class.assert_called_once_with(mock_path)

            # Verify GitHub client was initialized
            mock_github_class.assert_called_once_with("fake_token")

    def test_initialization_fails_directory_not_exists(self) -> None:
        """Test initialization fails when directory does not exist."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = False

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch("mcp_coder.utils.github_operations.base_manager.Github"),
        ):
            with pytest.raises(ValueError) as exc_info:
                BaseGitHubManager(project_dir=mock_path)

            assert "does not exist" in str(exc_info.value)

    def test_initialization_fails_path_not_directory(self) -> None:
        """Test initialization fails when path is not a directory."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = False

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch("mcp_coder.utils.github_operations.base_manager.Github"),
        ):
            with pytest.raises(ValueError) as exc_info:
                BaseGitHubManager(project_dir=mock_path)

            assert "not a directory" in str(exc_info.value)

    def test_initialization_fails_not_git_repository(self) -> None:
        """Test initialization fails when directory is not a git repository."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.git.Repo",
                side_effect=git.InvalidGitRepositoryError("Not a git repository"),
            ),
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch("mcp_coder.utils.github_operations.base_manager.Github"),
        ):
            with pytest.raises(ValueError) as exc_info:
                BaseGitHubManager(project_dir=mock_path)

            assert "not a git repository" in str(exc_info.value)

    def test_initialization_fails_no_github_token(self) -> None:
        """Test initialization fails when GitHub token is not configured."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value=None,  # No token configured
            ),
            patch("mcp_coder.utils.github_operations.base_manager.Github"),
        ):
            with pytest.raises(ValueError) as exc_info:
                BaseGitHubManager(project_dir=mock_path)

            assert "GitHub token not found" in str(exc_info.value)

    def test_get_repository_with_project_dir_mode(self) -> None:
        """Test _get_repository() in project_dir mode extracts repo from git remote."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        mock_repo = Mock(spec=git.Repo)
        mock_remote = Mock()
        mock_remote.name = "origin"
        mock_remote.url = "https://github.com/test-owner/test-repo.git"
        mock_repo.remotes = [mock_remote]

        mock_github_repo = Mock()

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.git.Repo"
            ) as mock_repo_class,
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch(
                "mcp_coder.utils.github_operations.base_manager.Github"
            ) as mock_github_class,
        ):
            mock_repo_class.return_value = mock_repo
            mock_github_client = Mock()
            mock_github_client.get_repo.return_value = mock_github_repo
            mock_github_class.return_value = mock_github_client

            manager = BaseGitHubManager(project_dir=mock_path)

            # Call _get_repository
            result = manager._get_repository()

            # Verify result
            assert result == mock_github_repo
            assert manager._repository == mock_github_repo  # Cached

            # Verify get_repo was called with correct full name
            mock_github_client.get_repo.assert_called_once_with("test-owner/test-repo")

    def test_get_repository_caching(self) -> None:
        """Test _get_repository() caches the repository object."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        mock_repo = Mock(spec=git.Repo)
        mock_remote = Mock()
        mock_remote.name = "origin"
        mock_remote.url = "https://github.com/test-owner/test-repo.git"
        mock_repo.remotes = [mock_remote]

        mock_github_repo = Mock()

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.git.Repo"
            ) as mock_repo_class,
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch(
                "mcp_coder.utils.github_operations.base_manager.Github"
            ) as mock_github_class,
        ):
            mock_repo_class.return_value = mock_repo
            mock_github_client = Mock()
            mock_github_client.get_repo.return_value = mock_github_repo
            mock_github_class.return_value = mock_github_client

            manager = BaseGitHubManager(project_dir=mock_path)

            # Call _get_repository multiple times
            result1 = manager._get_repository()
            result2 = manager._get_repository()
            result3 = manager._get_repository()

            # Verify all results are the same
            assert result1 == result2 == result3 == mock_github_repo

            # Verify get_repo was called only once (caching works)
            mock_github_client.get_repo.assert_called_once()

    def test_get_repository_no_origin_remote(self) -> None:
        """Test _get_repository() returns None when no origin remote exists."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        mock_repo = Mock(spec=git.Repo)
        mock_remote = Mock()
        mock_remote.name = "upstream"  # Not "origin"
        mock_remote.url = "https://github.com/test-owner/test-repo.git"
        mock_repo.remotes = [mock_remote]

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.git.Repo"
            ) as mock_repo_class,
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch("mcp_coder.utils.github_operations.base_manager.Github"),
        ):
            mock_repo_class.return_value = mock_repo

            manager = BaseGitHubManager(project_dir=mock_path)

            # Call _get_repository
            result = manager._get_repository()

            # Verify result is None (no origin remote)
            assert result is None

    def test_get_repository_invalid_github_url(self) -> None:
        """Test _get_repository() returns None when remote URL is not a valid GitHub URL."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        mock_repo = Mock(spec=git.Repo)
        mock_remote = Mock()
        mock_remote.name = "origin"
        mock_remote.url = "https://gitlab.com/test-owner/test-repo.git"  # Not GitHub
        mock_repo.remotes = [mock_remote]

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.git.Repo"
            ) as mock_repo_class,
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch("mcp_coder.utils.github_operations.base_manager.Github"),
        ):
            mock_repo_class.return_value = mock_repo

            manager = BaseGitHubManager(project_dir=mock_path)

            # Call _get_repository
            result = manager._get_repository()

            # Verify result is None (invalid GitHub URL)
            assert result is None

    def test_get_repository_github_api_error(self) -> None:
        """Test _get_repository() returns None when GitHub API returns error."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        mock_repo = Mock(spec=git.Repo)
        mock_remote = Mock()
        mock_remote.name = "origin"
        mock_remote.url = "https://github.com/test-owner/test-repo.git"
        mock_repo.remotes = [mock_remote]

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.git.Repo"
            ) as mock_repo_class,
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch(
                "mcp_coder.utils.github_operations.base_manager.Github"
            ) as mock_github_class,
        ):
            mock_repo_class.return_value = mock_repo
            mock_github_client = Mock()
            mock_github_client.get_repo.side_effect = GithubException(
                404, {"message": "Not Found"}, None
            )
            mock_github_class.return_value = mock_github_client

            manager = BaseGitHubManager(project_dir=mock_path)

            # Call _get_repository
            result = manager._get_repository()

            # Verify result is None (API error)
            assert result is None

    def test_get_repository_generic_exception(self) -> None:
        """Test _get_repository() returns None on unexpected exceptions."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        mock_repo = Mock(spec=git.Repo)
        mock_remote = Mock()
        mock_remote.name = "origin"
        mock_remote.url = "https://github.com/test-owner/test-repo.git"
        mock_repo.remotes = [mock_remote]

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.git.Repo"
            ) as mock_repo_class,
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch(
                "mcp_coder.utils.github_operations.base_manager.Github"
            ) as mock_github_class,
        ):
            mock_repo_class.return_value = mock_repo
            mock_github_client = Mock()
            mock_github_client.get_repo.side_effect = RuntimeError("Unexpected error")
            mock_github_class.return_value = mock_github_client

            manager = BaseGitHubManager(project_dir=mock_path)

            # Call _get_repository
            result = manager._get_repository()

            # Verify result is None (generic exception)
            assert result is None

    def test_ssh_url_format_parsing(self) -> None:
        """Test _get_repository() correctly parses SSH URL format."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        mock_repo = Mock(spec=git.Repo)
        mock_remote = Mock()
        mock_remote.name = "origin"
        mock_remote.url = "git@github.com:test-owner/test-repo.git"  # SSH format
        mock_repo.remotes = [mock_remote]

        mock_github_repo = Mock()

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.git.Repo"
            ) as mock_repo_class,
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch(
                "mcp_coder.utils.github_operations.base_manager.Github"
            ) as mock_github_class,
        ):
            mock_repo_class.return_value = mock_repo
            mock_github_client = Mock()
            mock_github_client.get_repo.return_value = mock_github_repo
            mock_github_class.return_value = mock_github_client

            manager = BaseGitHubManager(project_dir=mock_path)

            # Call _get_repository
            result = manager._get_repository()

            # Verify result
            assert result == mock_github_repo

            # Verify get_repo was called with correct full name (SSH parsed correctly)
            mock_github_client.get_repo.assert_called_once_with("test-owner/test-repo")

    def test_https_url_without_git_extension(self) -> None:
        """Test _get_repository() handles HTTPS URL without .git extension."""
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.is_dir.return_value = True

        mock_repo = Mock(spec=git.Repo)
        mock_remote = Mock()
        mock_remote.name = "origin"
        mock_remote.url = "https://github.com/test-owner/test-repo"  # No .git
        mock_repo.remotes = [mock_remote]

        mock_github_repo = Mock()

        with (
            patch(
                "mcp_coder.utils.github_operations.base_manager.git.Repo"
            ) as mock_repo_class,
            patch(
                "mcp_coder.utils.github_operations.base_manager.user_config.get_config_value",
                return_value="fake_token",
            ),
            patch(
                "mcp_coder.utils.github_operations.base_manager.Github"
            ) as mock_github_class,
        ):
            mock_repo_class.return_value = mock_repo
            mock_github_client = Mock()
            mock_github_client.get_repo.return_value = mock_github_repo
            mock_github_class.return_value = mock_github_client

            manager = BaseGitHubManager(project_dir=mock_path)

            # Call _get_repository
            result = manager._get_repository()

            # Verify result
            assert result == mock_github_repo

            # Verify get_repo was called with correct full name
            mock_github_client.get_repo.assert_called_once_with("test-owner/test-repo")
