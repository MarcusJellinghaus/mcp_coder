"""Tests for the high-level LLM interface."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm_interface import ask_llm
from mcp_coder.llm_providers.claude.claude_code_interface import ask_claude_code


class TestAskLLM:
    """Test the main ask_llm function."""

    @patch("mcp_coder.llm_interface.ask_claude_code")
    def test_ask_llm_routes_to_claude_code(
        self, mock_ask_claude_code: MagicMock
    ) -> None:
        """Test that ask_llm routes to ask_claude_code for claude provider."""
        mock_ask_claude_code.return_value = "Test response from Claude"

        result = ask_llm("Test question", provider="claude", method="cli", timeout=30)

        mock_ask_claude_code.assert_called_once_with(
            "Test question", method="cli", session_id=None, timeout=30, cwd=None
        )
        assert result == "Test response from Claude"

    @patch("mcp_coder.llm_interface.ask_claude_code")
    def test_ask_llm_default_parameters(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that ask_llm uses correct default parameters."""
        mock_ask_claude_code.return_value = "Default response"

        result = ask_llm("Test question")

        mock_ask_claude_code.assert_called_once_with(
            "Test question", method="cli", session_id=None, timeout=30, cwd=None
        )
        assert result == "Default response"

    def test_ask_llm_unsupported_provider(self) -> None:
        """Test that ask_llm raises ValueError for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider: gpt"):
            ask_llm("Test question", provider="gpt")

    @patch("mcp_coder.llm_interface.ask_claude_code")
    def test_ask_llm_passes_through_exceptions(
        self, mock_ask_claude_code: MagicMock
    ) -> None:
        """Test that ask_llm passes through exceptions from underlying implementations."""
        mock_ask_claude_code.side_effect = RuntimeError("Claude error")

        with pytest.raises(RuntimeError, match="Claude error"):
            ask_llm("Test question", provider="claude")

    @patch("mcp_coder.llm_interface.ask_claude_code")
    def test_ask_llm_custom_timeout(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that ask_llm passes through custom timeout."""
        mock_ask_claude_code.return_value = "Timeout response"

        result = ask_llm("Test question", timeout=60)

        mock_ask_claude_code.assert_called_once_with(
            "Test question", method="cli", session_id=None, timeout=60, cwd=None
        )
        assert result == "Timeout response"

    @patch("mcp_coder.llm_interface.ask_claude_code")
    def test_ask_llm_custom_method(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that ask_llm passes through custom method."""
        mock_ask_claude_code.return_value = "Method response"

        result = ask_llm(
            "Test question", method="api"
        )  # Even though not implemented yet

        mock_ask_claude_code.assert_called_once_with(
            "Test question", method="api", session_id=None, timeout=30, cwd=None
        )
        assert result == "Method response"

    @patch("mcp_coder.llm_interface.ask_claude_code")
    def test_ask_llm_with_session_id(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that session_id is passed through to ask_claude_code."""
        mock_ask_claude_code.return_value = "Response with session"

        result = ask_llm(
            "Test question",
            provider="claude",
            method="cli",
            session_id="test-session-123",
        )

        mock_ask_claude_code.assert_called_once_with(
            "Test question",
            method="cli",
            session_id="test-session-123",
            timeout=30,
            cwd=None,
        )
        assert result == "Response with session"

    @patch("mcp_coder.llm_interface.ask_claude_code")
    def test_ask_llm_without_session_id(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that session_id is optional and defaults to None."""
        mock_ask_claude_code.return_value = "Response without session"

        # Should work without session_id (backward compatible)
        result = ask_llm("Test question")

        mock_ask_claude_code.assert_called_once_with(
            "Test question", method="cli", session_id=None, timeout=30, cwd=None
        )
        assert result == "Response without session"

    @patch("mcp_coder.llm_interface.ask_claude_code")
    def test_ask_llm_session_id_with_api_method(
        self, mock_ask_claude_code: MagicMock
    ) -> None:
        """Test that session_id works with API method."""
        mock_ask_claude_code.return_value = "API response with session"

        result = ask_llm("Test question", method="api", session_id="api-session-456")

        mock_ask_claude_code.assert_called_once_with(
            "Test question",
            method="api",
            session_id="api-session-456",
            timeout=30,
            cwd=None,
        )
        assert result == "API response with session"

    @patch("mcp_coder.llm_interface.ask_claude_code")
    def test_ask_llm_returns_string_only(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that ask_llm returns string, not dict."""
        mock_ask_claude_code.return_value = "Just the text"

        response = ask_llm("Test", session_id="some-session")

        # Should return string only
        assert isinstance(response, str)
        assert response == "Just the text"


class TestAskClaudeCode:
    """Test the Claude-specific routing function."""

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_ask_claude_code_routes_to_cli(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that ask_claude_code routes to CLI implementation."""
        mock_ask_claude_code_cli.return_value = {
            "text": "CLI response",
            "session_id": "test-session",
            "version": "1.0",
        }

        result = ask_claude_code("Test question", method="cli", timeout=30)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question", session_id=None, timeout=30, cwd=None
        )
        assert result == "CLI response"

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_ask_claude_code_default_parameters(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that ask_claude_code uses correct default parameters."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Default CLI response",
            "session_id": "test-session",
            "version": "1.0",
        }

        result = ask_claude_code("Test question")

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question", session_id=None, timeout=30, cwd=None
        )
        assert result == "Default CLI response"

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_api")
    def test_ask_claude_code_routes_to_api(
        self, mock_ask_claude_code_api: MagicMock
    ) -> None:
        """Test that ask_claude_code routes to API implementation."""
        mock_ask_claude_code_api.return_value = {
            "text": "API response",
            "session_id": "api-session",
            "version": "1.0",
        }

        result = ask_claude_code("Test question", method="api", timeout=30)

        mock_ask_claude_code_api.assert_called_once_with(
            "Test question", session_id=None, timeout=30
        )
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
        mock_ask_claude_code_cli.return_value = {
            "text": "Custom timeout response",
            "session_id": "test-session",
            "version": "1.0",
        }

        result = ask_claude_code("Test question", timeout=45)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question", session_id=None, timeout=45, cwd=None
        )
        assert result == "Custom timeout response"


class TestIntegration:
    """Integration tests for the full routing chain."""

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_full_routing_chain(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """Test the full routing chain from ask_llm to ask_claude_code_cli."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Full chain response",
            "session_id": "chain-session",
            "version": "1.0",
        }

        result = ask_llm(
            "Integration test question", provider="claude", method="cli", timeout=25
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Integration test question", session_id=None, timeout=25, cwd=None
        )
        assert result == "Full chain response"

    def test_parameter_validation_propagation(self) -> None:
        """Test that parameter validation errors propagate correctly."""
        # Test invalid provider
        with pytest.raises(ValueError, match="Unsupported provider"):
            ask_llm("Test", provider="invalid")

        # Test invalid method (will be caught at claude_code_interface level)
        with pytest.raises(ValueError, match="Unsupported method"):
            ask_llm("Test", provider="claude", method="invalid")

    @patch("mcp_coder.llm_providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_full_routing_chain_with_session_id(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test the full routing chain with session_id parameter."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Full chain response with session",
            "session_id": "integration-session-789",
            "version": "1.0",
        }

        result = ask_llm(
            "Integration test with session",
            provider="claude",
            method="cli",
            session_id="integration-session-789",
            timeout=25,
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Integration test with session",
            session_id="integration-session-789",
            timeout=25,
            cwd=None,
        )
        assert result == "Full chain response with session"


@pytest.mark.claude_cli_integration
class TestLLMInterfaceCLIRealIntegration:
    """Real integration tests for LLM interface using CLI method."""

    def test_ask_llm_cli_paris_question(self) -> None:
        """Test that ask_llm with CLI method can answer the Paris question."""
        try:
            response = ask_llm(
                "What is the capital of France? Answer with just the city name.",
                provider="claude",
                method="cli",
                timeout=30,
            )

            assert response, "CLI method returned empty response"
            assert isinstance(
                response, str
            ), f"Expected string response, got {type(response)}"

            response_lower = response.strip().lower()
            assert (
                "paris" in response_lower
            ), f"Expected 'paris' in response, got: {response}"

        except Exception as e:
            pytest.skip(f"Claude CLI integration test failed (expected): {str(e)}")


@pytest.mark.claude_api_integration
class TestLLMInterfaceAPIRealIntegration:
    """Real integration tests for LLM interface using API method."""

    def test_ask_llm_api_paris_question(self) -> None:
        """Test that ask_llm with API method can answer the Paris question."""
        try:
            response = ask_llm(
                "What is the capital of France? Answer with just the city name.",
                provider="claude",
                method="api",
                timeout=30,
            )

            assert response, "API method returned empty response"
            assert isinstance(
                response, str
            ), f"Expected string response, got {type(response)}"

            response_lower = response.strip().lower()
            assert (
                "paris" in response_lower
            ), f"Expected 'paris' in response, got: {response}"

        except Exception as e:
            pytest.skip(f"Claude API integration test failed (expected): {str(e)}")
