"""Tests for the Claude Code interface routing functionality."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm_providers.claude.claude_code_interface import ask_claude_code


class TestAskClaudeCode:
    """Test the Claude Code interface routing function."""

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_ask_claude_code_routes_to_cli(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that ask_claude_code routes to CLI implementation."""
        mock_ask_claude_code_cli.return_value = "CLI response"

        result = ask_claude_code("Test question", method="cli", timeout=30)

        mock_ask_claude_code_cli.assert_called_once_with("Test question", timeout=30)
        assert result == "CLI response"

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_ask_claude_code_default_parameters(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that ask_claude_code uses correct default parameters."""
        mock_ask_claude_code_cli.return_value = "Default CLI response"

        result = ask_claude_code("Test question")

        mock_ask_claude_code_cli.assert_called_once_with("Test question", timeout=30)
        assert result == "Default CLI response"

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_api")
    def test_ask_claude_code_routes_to_api(
        self, mock_ask_claude_code_api: MagicMock
    ) -> None:
        """Test that ask_claude_code routes to API implementation."""
        mock_ask_claude_code_api.return_value = "API response"

        result = ask_claude_code("Test question", method="api", timeout=30)

        mock_ask_claude_code_api.assert_called_once_with("Test question", timeout=30)
        assert result == "API response"

    def test_ask_claude_code_unsupported_method(self) -> None:
        """Test that ask_claude_code raises ValueError for unsupported method."""
        with pytest.raises(ValueError, match="Unsupported method: invalid"):
            ask_claude_code("Test question", method="invalid")

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_ask_claude_code_passes_through_exceptions(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that ask_claude_code passes through exceptions from CLI implementation."""
        mock_ask_claude_code_cli.side_effect = FileNotFoundError("Claude CLI not found")

        with pytest.raises(FileNotFoundError, match="Claude CLI not found"):
            ask_claude_code("Test question", method="cli")

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_ask_claude_code_custom_timeout(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that ask_claude_code passes through custom timeout."""
        mock_ask_claude_code_cli.return_value = "Custom timeout response"

        result = ask_claude_code("Test question", timeout=45)

        mock_ask_claude_code_cli.assert_called_once_with("Test question", timeout=45)
        assert result == "Custom timeout response"

    def test_ask_claude_code_empty_question(self) -> None:
        """Test that ask_claude_code raises ValueError for empty question."""
        with pytest.raises(ValueError, match="Question cannot be empty"):
            ask_claude_code("")

        with pytest.raises(ValueError, match="Question cannot be empty"):
            ask_claude_code("   ")

    def test_ask_claude_code_invalid_timeout(self) -> None:
        """Test that ask_claude_code raises ValueError for invalid timeout."""
        with pytest.raises(ValueError, match="Timeout must be a positive number"):
            ask_claude_code("Test question", timeout=0)

        with pytest.raises(ValueError, match="Timeout must be a positive number"):
            ask_claude_code("Test question", timeout=-1)

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_api")
    def test_ask_claude_code_api_method_timeout(
        self, mock_ask_claude_code_api: MagicMock
    ) -> None:
        """Test that ask_claude_code passes timeout to API method."""
        mock_ask_claude_code_api.return_value = "API timeout response"

        result = ask_claude_code("Test question", method="api", timeout=60)

        mock_ask_claude_code_api.assert_called_once_with("Test question", timeout=60)
        assert result == "API timeout response"


class TestParameterValidation:
    """Test parameter validation in ask_claude_code."""

    def test_question_validation(self) -> None:
        """Test various invalid question inputs."""
        invalid_questions = ["", "   ", "\t", "\n", "  \n\t  "]
        
        for invalid_question in invalid_questions:
            with pytest.raises(ValueError, match="Question cannot be empty"):
                ask_claude_code(invalid_question)

    def test_timeout_validation(self) -> None:
        """Test various invalid timeout inputs."""
        invalid_timeouts = [0, -1, -10]
        
        for invalid_timeout in invalid_timeouts:
            with pytest.raises(ValueError, match="Timeout must be a positive number"):
                ask_claude_code("Valid question", timeout=invalid_timeout)

    def test_method_validation(self) -> None:
        """Test various invalid method inputs."""
        invalid_methods = ["invalid", "CLI", "API", "gpt", "", "openai"]
        
        for invalid_method in invalid_methods:
            with pytest.raises(ValueError, match="Unsupported method"):
                ask_claude_code("Valid question", method=invalid_method)

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_valid_inputs(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """Test that valid inputs work correctly."""
        mock_ask_claude_code_cli.return_value = "Valid response"
        
        # Valid question variations
        valid_questions = [
            "Simple question",
            "Question with numbers 123",
            "Question with special chars: !@#$%",
            "Multi-line\nquestion\nwith\nbreaks",
            "Question with   extra   spaces",
            "x",  # Single character
            "Q" * 1000,  # Long question
        ]
        
        for valid_question in valid_questions:
            result = ask_claude_code(valid_question)
            assert result == "Valid response"
            
        # Valid timeout variations
        valid_timeouts = [1, 30, 60, 120, 300, 3600]
        
        for valid_timeout in valid_timeouts:
            result = ask_claude_code("Test", timeout=valid_timeout)
            assert result == "Valid response"


class TestIntegration:
    """Integration tests for the routing functionality."""

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_cli")
    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_api")
    def test_method_routing_integration(
        self, mock_api: MagicMock, mock_cli: MagicMock
    ) -> None:
        """Test that both methods can be called and routed correctly."""
        mock_cli.return_value = "CLI integration response"
        mock_api.return_value = "API integration response"
        
        # Test CLI routing
        cli_result = ask_claude_code("CLI test", method="cli", timeout=25)
        assert cli_result == "CLI integration response"
        mock_cli.assert_called_once_with("CLI test", timeout=25)
        
        # Test API routing
        api_result = ask_claude_code("API test", method="api", timeout=35)
        assert api_result == "API integration response"
        mock_api.assert_called_once_with("API test", timeout=35)
        
        # Verify isolation
        assert mock_cli.call_count == 1
        assert mock_api.call_count == 1
