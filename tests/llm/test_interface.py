"""Tests for the high-level LLM interface."""

from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import ask_llm, prompt_llm
from mcp_coder.llm.providers.claude.claude_code_interface import ask_claude_code


class TestAskLLM:
    """Test the main ask_llm function."""

    @patch("mcp_coder.llm.interface.ask_claude_code")
    def test_ask_llm_routes_to_claude_code(
        self, mock_ask_claude_code: MagicMock
    ) -> None:
        """Test that ask_llm routes to ask_claude_code for claude provider."""
        mock_ask_claude_code.return_value = "Test response from Claude"

        result = ask_llm("Test question", provider="claude", method="cli", timeout=30)

        mock_ask_claude_code.assert_called_once_with(
            "Test question",
            method="cli",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
        )
        assert result == "Test response from Claude"

    @patch("mcp_coder.llm.interface.ask_claude_code")
    def test_ask_llm_default_parameters(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that ask_llm uses correct default parameters."""
        mock_ask_claude_code.return_value = "Default response"

        result = ask_llm("Test question")

        mock_ask_claude_code.assert_called_once_with(
            "Test question",
            method="cli",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
        )
        assert result == "Default response"

    def test_ask_llm_unsupported_provider(self) -> None:
        """Test that ask_llm raises ValueError for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider: gpt"):
            ask_llm("Test question", provider="gpt")

    @patch("mcp_coder.llm.interface.ask_claude_code")
    def test_ask_llm_passes_through_exceptions(
        self, mock_ask_claude_code: MagicMock
    ) -> None:
        """Test that ask_llm passes through exceptions from underlying implementations."""
        mock_ask_claude_code.side_effect = RuntimeError("Claude error")

        with pytest.raises(RuntimeError, match="Claude error"):
            ask_llm("Test question", provider="claude")

    @patch("mcp_coder.llm.interface.ask_claude_code")
    def test_ask_llm_custom_timeout(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that ask_llm passes through custom timeout."""
        mock_ask_claude_code.return_value = "Timeout response"

        result = ask_llm("Test question", timeout=60)

        mock_ask_claude_code.assert_called_once_with(
            "Test question",
            method="cli",
            session_id=None,
            timeout=60,
            env_vars=None,
            cwd=None,
        )
        assert result == "Timeout response"

    @patch("mcp_coder.llm.interface.ask_claude_code")
    def test_ask_llm_custom_method(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that ask_llm passes through custom method."""
        mock_ask_claude_code.return_value = "Method response"

        result = ask_llm(
            "Test question", method="api"
        )  # Even though not implemented yet

        mock_ask_claude_code.assert_called_once_with(
            "Test question",
            method="api",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
        )
        assert result == "Method response"

    @patch("mcp_coder.llm.interface.ask_claude_code")
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
            env_vars=None,
            cwd=None,
        )
        assert result == "Response with session"

    @patch("mcp_coder.llm.interface.ask_claude_code")
    def test_ask_llm_without_session_id(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that session_id is optional and defaults to None."""
        mock_ask_claude_code.return_value = "Response without session"

        # Should work without session_id (backward compatible)
        result = ask_llm("Test question")

        mock_ask_claude_code.assert_called_once_with(
            "Test question",
            method="cli",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
        )
        assert result == "Response without session"

    @patch("mcp_coder.llm.interface.ask_claude_code")
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
            env_vars=None,
            cwd=None,
            mcp_config=None,
        )
        assert result == "API response with session"

    @patch("mcp_coder.llm.interface.ask_claude_code")
    def test_ask_llm_returns_string_only(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that ask_llm returns string, not dict."""
        mock_ask_claude_code.return_value = "Just the text"

        response = ask_llm("Test", session_id="some-session")

        # Should return string only
        assert isinstance(response, str)
        assert response == "Just the text"

    @patch("mcp_coder.llm.interface.ask_claude_code")
    def test_ask_llm_with_env_vars(self, mock_ask_claude_code: MagicMock) -> None:
        """Test that ask_llm passes env_vars to ask_claude_code."""
        mock_ask_claude_code.return_value = "Response with env vars"
        test_env_vars = {"VAR1": "value1", "VAR2": "value2"}

        result = ask_llm(
            "Test question",
            provider="claude",
            method="cli",
            env_vars=test_env_vars,
        )

        mock_ask_claude_code.assert_called_once_with(
            "Test question",
            method="cli",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=None,
            mcp_config=None,
        )
        assert result == "Response with env vars"


class TestAskClaudeCode:
    """Test the Claude-specific routing function."""

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
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
            "Test question", session_id=None, timeout=30, env_vars=None, cwd=None
        )
        assert result == "CLI response"

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
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
            "Test question", session_id=None, timeout=30, env_vars=None, cwd=None
        )
        assert result == "Default CLI response"

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_api")
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
            "Test question", session_id=None, timeout=30, env_vars=None, cwd=None
        )
        assert result == "API response"

    def test_ask_claude_code_unsupported_method(self) -> None:
        """Test that ask_claude_code raises ValueError for unsupported method."""
        with pytest.raises(ValueError, match="Unsupported method: invalid"):
            ask_claude_code("Test question", method="invalid")

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
    def test_ask_claude_code_passes_through_exceptions(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that ask_claude_code passes through exceptions from CLI implementation."""
        mock_ask_claude_code_cli.side_effect = FileNotFoundError("Claude CLI not found")

        with pytest.raises(FileNotFoundError, match="Claude CLI not found"):
            ask_claude_code("Test question", method="cli")

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
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
            "Test question", session_id=None, timeout=45, env_vars=None, cwd=None
        )
        assert result == "Custom timeout response"


class TestIntegration:
    """Integration tests for the full routing chain."""

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
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
            "Integration test question",
            session_id=None,
            timeout=25,
            env_vars=None,
            cwd=None,
            mcp_config=None,
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

    @patch("mcp_coder.llm.providers.claude.claude_code_interface.ask_claude_code_cli")
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
            env_vars=None,
            cwd=None,
        )
        assert result == "Full chain response with session"


# Real integration tests for LLM interface are removed
# These are redundant with the critical path tests in test_claude_integration.py
# The interface routing and functionality is covered by the streamlined integration tests


class TestPromptLLM:
    """Tests for the prompt_llm function."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_returns_typed_dict_cli(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that prompt_llm returns LLMResponseDict with CLI."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "CLI response",
            "session_id": "cli-123",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Test question", method="cli")

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question", session_id=None, timeout=30, env_vars=None, cwd=None
        )
        assert isinstance(result, dict)
        assert result["version"] == "1.0"
        assert result["text"] == "CLI response"
        assert result["session_id"] == "cli-123"
        assert result["method"] == "cli"
        assert result["provider"] == "claude"

    @patch("mcp_coder.llm.interface.ask_claude_code_api")
    def test_prompt_llm_returns_typed_dict_api(
        self, mock_ask_claude_code_api: MagicMock
    ) -> None:
        """Test that prompt_llm returns LLMResponseDict with API."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "API response",
            "session_id": "api-456",
            "method": "api",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_api.return_value = mock_response

        result = prompt_llm("Test question", method="api")

        mock_ask_claude_code_api.assert_called_once_with(
            "Test question", session_id=None, timeout=30, env_vars=None, cwd=None
        )
        assert isinstance(result, dict)
        assert result["method"] == "api"
        assert result["session_id"] == "api-456"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_with_session_id_cli(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test session continuity with CLI."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Continued response",
            "session_id": "existing-session",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Follow up", method="cli", session_id="existing-session")

        mock_ask_claude_code_cli.assert_called_once_with(
            "Follow up",
            session_id="existing-session",
            timeout=30,
            env_vars=None,
            cwd=None,
        )
        assert result["session_id"] == "existing-session"

    @patch("mcp_coder.llm.interface.ask_claude_code_api")
    def test_prompt_llm_with_session_id_api(
        self, mock_ask_claude_code_api: MagicMock
    ) -> None:
        """Test session continuity with API."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Continued API response",
            "session_id": "api-session",
            "method": "api",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_api.return_value = mock_response

        result = prompt_llm("Follow up", method="api", session_id="api-session")

        mock_ask_claude_code_api.assert_called_once_with(
            "Follow up", session_id="api-session", timeout=30, env_vars=None, cwd=None
        )
        assert result["session_id"] == "api-session"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_preserves_metadata(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that metadata is preserved in response."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Response with metadata",
            "session_id": "meta-test",
            "method": "cli",
            "provider": "claude",
            "raw_response": {
                "duration_ms": 2801,
                "cost_usd": 0.058,
                "usage": {"input_tokens": 100},
            },
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Test")

        assert result["raw_response"]["duration_ms"] == 2801
        assert result["raw_response"]["cost_usd"] == 0.058

    def test_prompt_llm_unsupported_provider(self) -> None:
        """Test error for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            prompt_llm("Test", provider="gpt")

    def test_prompt_llm_unsupported_method(self) -> None:
        """Test error for unsupported method."""
        with pytest.raises(ValueError, match="Unsupported method"):
            prompt_llm("Test", method="unknown")

    def test_prompt_llm_empty_question(self) -> None:
        """Test validation for empty question."""
        with pytest.raises(ValueError, match="cannot be empty"):
            prompt_llm("")

    def test_prompt_llm_whitespace_only_question(self) -> None:
        """Test validation for whitespace-only question."""
        with pytest.raises(ValueError, match="cannot be empty"):
            prompt_llm("   ")

    def test_prompt_llm_invalid_timeout(self) -> None:
        """Test validation for invalid timeout."""
        with pytest.raises(ValueError, match="positive number"):
            prompt_llm("Test", timeout=0)

    def test_prompt_llm_negative_timeout(self) -> None:
        """Test validation for negative timeout."""
        with pytest.raises(ValueError, match="positive number"):
            prompt_llm("Test", timeout=-5)

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_custom_timeout(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that custom timeout is passed through."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Response with custom timeout",
            "session_id": "timeout-test",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Test", timeout=60)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test", session_id=None, timeout=60, env_vars=None, cwd=None
        )
        assert result["text"] == "Response with custom timeout"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_default_parameters(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that default parameters are correctly applied."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Response with defaults",
            "session_id": "defaults-test",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Test question")

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question", session_id=None, timeout=30, env_vars=None, cwd=None
        )
        assert result["provider"] == "claude"
        assert result["method"] == "cli"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_with_env_vars(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that prompt_llm passes env_vars to CLI provider."""
        test_env_vars = {"VAR1": "value1", "VAR2": "value2"}
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "CLI response with env vars",
            "session_id": "env-test",
            "method": "cli",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Test question", method="cli", env_vars=test_env_vars)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=None,
        )
        assert result["text"] == "CLI response with env vars"

    @patch("mcp_coder.llm.interface.ask_claude_code_api")
    def test_prompt_llm_with_env_vars_api(
        self, mock_ask_claude_code_api: MagicMock
    ) -> None:
        """Test that prompt_llm passes env_vars to API provider."""
        test_env_vars = {"VAR1": "value1", "VAR2": "value2"}
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "API response with env vars",
            "session_id": "api-env-test",
            "method": "api",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_api.return_value = mock_response

        result = prompt_llm("Test question", method="api", env_vars=test_env_vars)

        mock_ask_claude_code_api.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=None,
        )
        assert result["text"] == "API response with env vars"
