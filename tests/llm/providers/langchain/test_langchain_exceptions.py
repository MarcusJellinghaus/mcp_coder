"""Tests for mcp_coder.llm.providers.langchain._exceptions.

Tests custom exception classes, error tuples, message helpers,
and Google auth error detection.
"""

import ssl
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.langchain import _handle_provider_error
from mcp_coder.llm.providers.langchain._exceptions import (
    ANTHROPIC_AUTH_ERRORS,
    CONNECTION_ERRORS,
    GOOGLE_CLIENT_ERRORS,
    OPENAI_AUTH_ERRORS,
    LLMAuthError,
    LLMConnectionError,
    LLMMCPLaunchError,
    is_google_auth_error,
    raise_auth_error,
    raise_connection_error,
)


class TestLLMConnectionError:
    """Tests for LLMConnectionError exception class."""

    def test_is_subclass_of_connection_error(self) -> None:
        """LLMConnectionError inherits from ConnectionError."""
        assert issubclass(LLMConnectionError, ConnectionError)

    def test_can_be_caught_as_connection_error(self) -> None:
        """except ConnectionError catches LLMConnectionError."""
        with pytest.raises(ConnectionError):
            raise LLMConnectionError("test")


class TestLLMAuthError:
    """Tests for LLMAuthError exception class."""

    def test_is_subclass_of_exception(self) -> None:
        """LLMAuthError inherits from Exception."""
        assert issubclass(LLMAuthError, Exception)

    def test_not_subclass_of_connection_error(self) -> None:
        """LLMAuthError is separate from ConnectionError."""
        assert not issubclass(LLMAuthError, ConnectionError)


class TestRaiseConnectionError:
    """Tests for raise_connection_error helper."""

    def test_raises_llm_connection_error(self) -> None:
        """raise_connection_error raises LLMConnectionError."""
        with pytest.raises(LLMConnectionError):
            raise_connection_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=OSError("connection refused"),
            )

    def test_message_contains_provider_and_original(self) -> None:
        """Error message includes provider name and original error text."""
        with pytest.raises(LLMConnectionError, match="OpenAI") as exc_info:
            raise_connection_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=OSError("connection refused"),
            )
        assert "connection refused" in str(exc_info.value)

    def test_message_contains_env_var_hint(self) -> None:
        """Error message includes the environment variable name."""
        with pytest.raises(LLMConnectionError) as exc_info:
            raise_connection_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=OSError("fail"),
            )
        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_message_contains_ssl_hint(self) -> None:
        """Error message includes unquoted SSL/truststore hint for SSL errors."""
        with pytest.raises(LLMConnectionError) as exc_info:
            raise_connection_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=ssl.SSLError("certificate verify failed"),
            )
        message = str(exc_info.value)
        assert "truststore" in message
        assert "SSL_CERT_FILE" in message
        # Hint must be pastable in cmd.exe / PowerShell / bash — no single quotes
        # around the package spec.
        assert "pip install mcp-coder[truststore]" in message
        assert "'mcp-coder[truststore]'" not in message

    def test_no_ssl_hint_for_non_ssl_error(self) -> None:
        """Error message omits SSL hint when the cause is not an SSL error."""
        with pytest.raises(LLMConnectionError) as exc_info:
            raise_connection_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=ConnectionRefusedError("refused"),
            )
        assert "truststore" not in str(exc_info.value)

    def test_message_contains_endpoint_hint_when_provided(self) -> None:
        """Error message includes endpoint hint when provided."""
        with pytest.raises(LLMConnectionError) as exc_info:
            raise_connection_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=OSError("fail"),
                endpoint_hint="https://custom.example.com",
            )
        assert "https://custom.example.com" in str(exc_info.value)

    def test_message_omits_endpoint_hint_when_empty(self) -> None:
        """Error message has no endpoint line when not provided."""
        with pytest.raises(LLMConnectionError) as exc_info:
            raise_connection_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=OSError("fail"),
            )
        assert "endpoint" not in str(exc_info.value).lower().split("check:")[0]

    def test_chains_original_exception(self) -> None:
        """__cause__ is set to the original exception."""
        original = OSError("connection refused")
        with pytest.raises(LLMConnectionError) as exc_info:
            raise_connection_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=original,
            )
        assert exc_info.value.__cause__ is original


class TestRaiseAuthError:
    """Tests for raise_auth_error helper."""

    def test_raises_llm_auth_error(self) -> None:
        """raise_auth_error raises LLMAuthError."""
        with pytest.raises(LLMAuthError):
            raise_auth_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=Exception("401 Unauthorized"),
            )

    def test_message_contains_provider_and_original(self) -> None:
        """Error message includes provider name and original error text."""
        with pytest.raises(LLMAuthError, match="Anthropic") as exc_info:
            raise_auth_error(
                provider="Anthropic",
                env_var="ANTHROPIC_API_KEY",
                original=Exception("401 Unauthorized"),
            )
        assert "401 Unauthorized" in str(exc_info.value)

    def test_message_contains_env_var_hint(self) -> None:
        """Error message includes the environment variable name."""
        with pytest.raises(LLMAuthError) as exc_info:
            raise_auth_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=Exception("auth fail"),
            )
        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_message_does_not_contain_ssl_hint(self) -> None:
        """Auth errors should not mention SSL/truststore."""
        with pytest.raises(LLMAuthError) as exc_info:
            raise_auth_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=Exception("auth fail"),
            )
        assert "truststore" not in str(exc_info.value)
        assert "SSL_CERT_FILE" not in str(exc_info.value)

    def test_chains_original_exception(self) -> None:
        """__cause__ is set to the original exception."""
        original = Exception("401 Unauthorized")
        with pytest.raises(LLMAuthError) as exc_info:
            raise_auth_error(
                provider="OpenAI",
                env_var="OPENAI_API_KEY",
                original=original,
            )
        assert exc_info.value.__cause__ is original


class TestIsGoogleAuthError:
    """Tests for is_google_auth_error helper."""

    def test_returns_true_for_401(self) -> None:
        """Returns True for ClientError with code=401."""
        exc = MagicMock()
        exc.code = 401
        with patch(
            "mcp_coder.llm.providers.langchain._exceptions.GOOGLE_CLIENT_ERRORS",
            (type(exc),),
        ):
            assert is_google_auth_error(exc) is True

    def test_returns_true_for_403(self) -> None:
        """Returns True for ClientError with code=403."""
        exc = MagicMock()
        exc.code = 403
        with patch(
            "mcp_coder.llm.providers.langchain._exceptions.GOOGLE_CLIENT_ERRORS",
            (type(exc),),
        ):
            assert is_google_auth_error(exc) is True

    def test_returns_false_for_other_codes(self) -> None:
        """Returns False for ClientError with non-auth codes."""
        exc = MagicMock()
        exc.code = 500
        with patch(
            "mcp_coder.llm.providers.langchain._exceptions.GOOGLE_CLIENT_ERRORS",
            (type(exc),),
        ):
            assert is_google_auth_error(exc) is False

    def test_returns_false_for_non_client_error(self) -> None:
        """Returns False for plain Exception."""
        exc = Exception("not a client error")
        assert is_google_auth_error(exc) is False

    def test_returns_false_when_google_not_installed(self) -> None:
        """Returns False when GOOGLE_CLIENT_ERRORS is empty."""
        exc = MagicMock()
        exc.code = 401
        with patch(
            "mcp_coder.llm.providers.langchain._exceptions.GOOGLE_CLIENT_ERRORS",
            (),
        ):
            assert is_google_auth_error(exc) is False


class TestErrorTuples:
    """Tests for module-level error tuples."""

    def test_connection_errors_excludes_oserror(self) -> None:
        """OSError is deliberately excluded so local MCP launch failures
        (FileNotFoundError / PermissionError) are not reclassified as
        remote connection errors."""
        assert OSError not in CONNECTION_ERRORS
        assert ConnectionError in CONNECTION_ERRORS

    def test_connection_errors_contains_httpx_connect_error(self) -> None:
        """httpx transport types are included when httpx is installed."""
        try:
            import httpx
        except ImportError:
            pytest.skip("httpx not installed")
        assert httpx.ConnectError in CONNECTION_ERRORS

    def test_openai_auth_tuple_is_tuple(self) -> None:
        """OPENAI_AUTH_ERRORS is a tuple."""
        assert isinstance(OPENAI_AUTH_ERRORS, tuple)

    def test_anthropic_auth_tuple_is_tuple(self) -> None:
        """ANTHROPIC_AUTH_ERRORS is a tuple."""
        assert isinstance(ANTHROPIC_AUTH_ERRORS, tuple)

    def test_google_client_tuple_is_tuple(self) -> None:
        """GOOGLE_CLIENT_ERRORS is a tuple."""
        assert isinstance(GOOGLE_CLIENT_ERRORS, tuple)


class TestLLMMCPLaunchError:
    """Tests for LLMMCPLaunchError exception class."""

    def test_llm_mcp_launch_error_hierarchy(self) -> None:
        """LLMMCPLaunchError is a plain Exception, not a ConnectionError,
        and is not treated as a connection error by the provider helpers."""
        assert issubclass(LLMMCPLaunchError, Exception)
        assert not issubclass(LLMMCPLaunchError, ConnectionError)
        assert LLMMCPLaunchError not in CONNECTION_ERRORS


class TestHandleProviderErrorLocalLaunchFailures:
    """_handle_provider_error must not rewrap local MCP launch errors."""

    def test_handle_provider_error_passes_through_filenotfound(self) -> None:
        """FileNotFoundError from a local launch is not rewrapped."""
        # Implicit assertion: no exception raised. The helper returns None
        # via fall-through; the meaningful behavior is that it does not
        # raise LLMConnectionError.
        _handle_provider_error(FileNotFoundError("nope"), "openai")

    def test_handle_provider_error_passes_through_permission_error(self) -> None:
        """PermissionError from a local launch is not rewrapped."""
        _handle_provider_error(PermissionError("denied"), "openai")
