"""Tests for _redact_for_logging and log_function_call sensitive_fields."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.log_utils import (
    RedactableDict,
    _redact_for_logging,
    log_function_call,
)


class TestRedactForLogging:
    """Tests for the _redact_for_logging helper function."""

    def test_redact_flat_dict(self) -> None:
        """Test redaction of flat dictionary."""
        data: RedactableDict = {
            "token": "secret123",
            "username": "user",
        }
        result = _redact_for_logging(data, {"token"})

        assert result["token"] == "***"
        assert result["username"] == "user"
        # Original should be unchanged
        assert data["token"] == "secret123"

    def test_redact_nested_dict(self) -> None:
        """Test redaction of nested dictionary."""
        data: RedactableDict = {"outer": {"token": "secret", "safe": "visible"}}
        result = _redact_for_logging(data, {"token"})

        assert result["outer"]["token"] == "***"
        assert result["outer"]["safe"] == "visible"
        # Original should be unchanged
        assert data["outer"]["token"] == "secret"

    def test_redact_deeply_nested_dict(self) -> None:
        """Test redaction of deeply nested dictionary."""
        data: RedactableDict = {
            "github": {"token": "ghp_xxx"},
            "jenkins": {"api_token": "jenkins_xxx", "url": "http://example.com"},
        }
        result = _redact_for_logging(data, {"token", "api_token"})

        assert result["github"]["token"] == "***"
        assert result["jenkins"]["api_token"] == "***"
        assert result["jenkins"]["url"] == "http://example.com"
        # Original should be unchanged
        assert data["github"]["token"] == "ghp_xxx"
        assert data["jenkins"]["api_token"] == "jenkins_xxx"

    def test_redact_empty_sensitive_fields(self) -> None:
        """Test with empty sensitive_fields set."""
        data: RedactableDict = {"token": "secret", "name": "test"}
        result = _redact_for_logging(data, set())

        assert result["token"] == "secret"
        assert result["name"] == "test"

    def test_redact_non_matching_fields(self) -> None:
        """Test when no fields match sensitive_fields."""
        data: RedactableDict = {"name": "test", "value": 123}
        result = _redact_for_logging(data, {"token", "password"})

        assert result["name"] == "test"
        assert result["value"] == 123


class TestRedactForLoggingTupleKeys:
    """Tests for _redact_for_logging with tuple dictionary keys.

    Issue #327: get_config_values() returns dicts with tuple keys like
    ('github', 'token'). The redaction should check the last element
    of tuple keys against sensitive_fields.
    """

    def test_redact_tuple_key_matches_last_element(self) -> None:
        """Test that tuple keys are redacted when last element matches sensitive field."""
        data: RedactableDict = {
            ("github", "token"): "ghp_secret123",
            ("user", "name"): "john",
        }
        result = _redact_for_logging(data, {"token"})

        assert result[("github", "token")] == "***"
        assert result[("user", "name")] == "john"
        # Original unchanged
        assert data[("github", "token")] == "ghp_secret123"

    def test_redact_mixed_string_and_tuple_keys(self) -> None:
        """Test redaction works with both string and tuple keys in same dict."""
        data: RedactableDict = {
            "token": "direct_secret",
            ("github", "token"): "tuple_secret",
            "username": "user",
        }
        result = _redact_for_logging(data, {"token"})

        assert result["token"] == "***"
        assert result[("github", "token")] == "***"
        assert result["username"] == "user"

    def test_redact_tuple_key_no_match(self) -> None:
        """Test that tuple keys not matching sensitive fields are unchanged."""
        data: RedactableDict = {
            ("github", "username"): "user",
            ("jenkins", "url"): "http://example.com",
        }
        result = _redact_for_logging(data, {"token", "api_token"})

        assert result[("github", "username")] == "user"
        assert result[("jenkins", "url")] == "http://example.com"

    def test_redact_empty_tuple_key_unchanged(self) -> None:
        """Test that empty tuple keys are handled safely (no crash, no match)."""
        data: RedactableDict = {
            (): "empty_tuple_value",
            ("normal", "key"): "normal_value",
        }
        result = _redact_for_logging(data, {"token"})

        # Empty tuple should not crash and value should be unchanged
        assert result[()] == "empty_tuple_value"
        assert result[("normal", "key")] == "normal_value"


class TestLogFunctionCallWithSensitiveFields:
    """Tests for log_function_call decorator with sensitive_fields parameter."""

    def test_log_function_call_without_sensitive_fields(self) -> None:
        """Test that decorator works without sensitive_fields (backward compatible)."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call
            def simple_func(x: int) -> int:
                return x * 2

            result = simple_func(5)
            assert result == 10
            assert mock_logger.debug.call_count == 2

    def test_log_function_call_with_parentheses_no_args(self) -> None:
        """Test that decorator works with empty parentheses."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call()
            def simple_func(x: int) -> int:
                return x * 2

            result: int = simple_func(5)
            assert result == 10
            assert mock_logger.debug.call_count == 2

    def test_log_function_call_redacts_sensitive_params(self) -> None:
        """Test that sensitive parameter values are redacted in logs."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(sensitive_fields=["token", "password"])
            def auth_func(token: str, username: str) -> bool:
                return True

            auth_func(token="secret123", username="user")

            # Verify log contains "***" for token, but "user" for username
            first_call = mock_logger.debug.call_args_list[0]
            log_params = first_call[0][2]  # JSON string of parameters

            assert "***" in log_params
            assert "secret123" not in log_params
            assert "user" in log_params

    def test_log_function_call_redacts_sensitive_return_value(self) -> None:
        """Test that sensitive values in return dict are redacted in logs."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(sensitive_fields=["token"])
            def get_config() -> dict[str, str]:
                return {"token": "secret", "name": "test"}

            result: dict[str, str] = get_config()

            # Original return value should be unchanged
            assert result["token"] == "secret"
            assert result["name"] == "test"

            # Log should have redacted value
            second_call = mock_logger.debug.call_args_list[1]  # completion log
            result_str = str(second_call)

            assert "***" in result_str
            assert "secret" not in result_str
            assert "test" in result_str

    def test_log_function_call_redacts_nested_sensitive_values(self) -> None:
        """Test that nested sensitive values in return dict are redacted."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(sensitive_fields=["token", "api_token"])
            def load_config() -> dict[str, dict[str, str]]:
                return {
                    "github": {"token": "ghp_xxx"},
                    "jenkins": {
                        "api_token": "jenkins_xxx",
                        "url": "http://example.com",
                    },
                }

            result: dict[str, dict[str, str]] = load_config()

            # Original return value should be unchanged
            assert result["github"]["token"] == "ghp_xxx"
            assert result["jenkins"]["api_token"] == "jenkins_xxx"

            # Log should have redacted values
            second_call = mock_logger.debug.call_args_list[1]
            result_str = str(second_call)

            assert "ghp_xxx" not in result_str
            assert "jenkins_xxx" not in result_str
            assert "http://example.com" in result_str

    def test_log_function_call_non_dict_return_unchanged(self) -> None:
        """Test that non-dict return values work correctly with sensitive_fields."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            @log_function_call(sensitive_fields=["token"])
            def get_number() -> int:
                return 42

            result: int = get_number()
            assert result == 42
            assert mock_logger.debug.call_count == 2
