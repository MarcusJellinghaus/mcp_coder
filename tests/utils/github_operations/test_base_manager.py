"""Unit tests for BaseGitHubManager error handling decorator."""

from unittest.mock import MagicMock

import pytest
from github.GithubException import GithubException

from mcp_coder.utils.github_operations.base_manager import _handle_github_errors


class TestHandleGitHubErrorsDecorator:
    """Unit tests for _handle_github_errors decorator."""

    def test_decorator_success_returns_value(self) -> None:
        """Test that decorator returns function value on success."""

        @_handle_github_errors(default_return={})
        def successful_function() -> dict[str, str]:
            return {"result": "success"}

        result = successful_function()
        assert result == {"result": "success"}

    def test_decorator_auth_error_401_returns_default(self) -> None:
        """Test that decorator returns default for 401 authentication errors."""

        @_handle_github_errors(default_return={"error": "default"})
        def function_with_auth_error() -> dict[str, str]:
            raise GithubException(401, {"message": "Bad credentials"}, None)

        result = function_with_auth_error()
        assert result == {"error": "default"}

    def test_decorator_auth_error_403_returns_default(self) -> None:
        """Test that decorator returns default for 403 permission errors."""

        @_handle_github_errors(default_return={"error": "default"})
        def function_with_permission_error() -> dict[str, str]:
            raise GithubException(403, {"message": "Forbidden"}, None)

        result = function_with_permission_error()
        assert result == {"error": "default"}

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
        """Test that decorator logs auth/permission errors."""

        @_handle_github_errors(default_return={})
        def function_with_auth_error() -> dict[str, str]:
            raise GithubException(401, {"message": "Bad credentials"}, None)

        result = function_with_auth_error()

        assert result == {}
        assert "GitHub API error in function_with_auth_error" in caplog.text

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

    def test_decorator_handles_all_github_errors(self) -> None:
        """Test that decorator returns default for all GitHub errors."""

        @_handle_github_errors(default_return={"status": "error"})
        def function_with_various_errors(status_code: int) -> dict[str, str]:
            raise GithubException(status_code, {"message": "Error"}, None)

        # All errors should return default
        assert function_with_various_errors(400) == {"status": "error"}
        assert function_with_various_errors(401) == {"status": "error"}
        assert function_with_various_errors(403) == {"status": "error"}
        assert function_with_various_errors(404) == {"status": "error"}
        assert function_with_various_errors(500) == {"status": "error"}
        assert function_with_various_errors(502) == {"status": "error"}
