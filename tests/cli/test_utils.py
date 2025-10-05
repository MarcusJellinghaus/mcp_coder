"""Tests for CLI utility functions."""

from typing import Tuple
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.cli.utils import parse_llm_method_from_args


class TestParseLLMMethodFromArgs:
    """Test cases for parse_llm_method_from_args function."""

    @patch("mcp_coder.cli.utils.parse_llm_method")
    def test_parse_llm_method_from_args_api(self, mock_parse: MagicMock) -> None:
        """Test parsing API method parameter."""
        mock_parse.return_value = ("claude", "api")

        result = parse_llm_method_from_args("claude_code_api")

        assert result == ("claude", "api")
        mock_parse.assert_called_once_with("claude_code_api")

    @patch("mcp_coder.cli.utils.parse_llm_method")
    def test_parse_llm_method_from_args_cli(self, mock_parse: MagicMock) -> None:
        """Test parsing CLI method parameter."""
        mock_parse.return_value = ("claude", "cli")

        result = parse_llm_method_from_args("claude_code_cli")

        assert result == ("claude", "cli")
        mock_parse.assert_called_once_with("claude_code_cli")

    @patch("mcp_coder.cli.utils.parse_llm_method")
    def test_parse_llm_method_from_args_invalid(self, mock_parse: MagicMock) -> None:
        """Test error handling for invalid method."""
        mock_parse.side_effect = ValueError("Unsupported llm_method: invalid_method")

        with pytest.raises(ValueError, match="Unsupported llm_method: invalid_method"):
            parse_llm_method_from_args("invalid_method")

        mock_parse.assert_called_once_with("invalid_method")

    @patch("mcp_coder.cli.utils.parse_llm_method")
    def test_parse_llm_method_from_args_empty_string(
        self, mock_parse: MagicMock
    ) -> None:
        """Test error handling for empty string."""
        mock_parse.side_effect = ValueError("Unsupported llm_method: ")

        with pytest.raises(ValueError, match="Unsupported llm_method: "):
            parse_llm_method_from_args("")

        mock_parse.assert_called_once_with("")

    @patch("mcp_coder.cli.utils.parse_llm_method")
    def test_parse_llm_method_from_args_delegates_to_original(
        self, mock_parse: MagicMock
    ) -> None:
        """Test that function properly delegates to underlying parse_llm_method."""
        expected_result = ("test_provider", "test_method")
        mock_parse.return_value = expected_result

        result = parse_llm_method_from_args("test_input")

        assert result == expected_result
        mock_parse.assert_called_once_with("test_input")

    def test_parse_llm_method_from_args_integration_api(self) -> None:
        """Integration test for API method without mocking."""
        provider, method = parse_llm_method_from_args("claude_code_api")

        assert provider == "claude"
        assert method == "api"

    def test_parse_llm_method_from_args_integration_cli(self) -> None:
        """Integration test for CLI method without mocking."""
        provider, method = parse_llm_method_from_args("claude_code_cli")

        assert provider == "claude"
        assert method == "cli"

    def test_parse_llm_method_from_args_integration_invalid(self) -> None:
        """Integration test for invalid method without mocking."""
        with pytest.raises(ValueError, match="Unsupported llm_method: invalid"):
            parse_llm_method_from_args("invalid")
