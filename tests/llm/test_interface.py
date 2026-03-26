"""Tests for the high-level LLM interface."""

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from mcp_coder.llm.interface import prompt_llm, prompt_llm_stream
from mcp_coder.utils.subprocess_runner import TimeoutExpired


class TestPromptLLMRouting:
    """Test prompt_llm routing to providers."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_routes_to_claude_code(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that prompt_llm routes to ask_claude_code_cli for claude provider."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Test response from Claude",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm("Test question", provider="claude", timeout=30)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Test response from Claude"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_routes_default_parameters(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that prompt_llm uses correct default parameters."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Default response",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm("Test question")

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Default response"

    def test_prompt_llm_unsupported_provider_gpt(self) -> None:
        """Test that prompt_llm raises ValueError for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider: gpt"):
            prompt_llm("Test question", provider="gpt")

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_passes_through_exceptions(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that prompt_llm passes through exceptions from underlying implementations."""
        mock_ask_claude_code_cli.side_effect = RuntimeError("Claude error")

        with pytest.raises(RuntimeError, match="Claude error"):
            prompt_llm("Test question", provider="claude")

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_routes_custom_timeout(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that prompt_llm passes through custom timeout."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Timeout response",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm("Test question", timeout=60)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=60,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Timeout response"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_routes_with_session_id(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that session_id is passed through to ask_claude_code_cli."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with session",
            "session_id": "test-session-123",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question",
            provider="claude",
            session_id="test-session-123",
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id="test-session-123",
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Response with session"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_routes_without_session_id(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that session_id is optional and defaults to None."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response without session",
            "session_id": "auto-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm("Test question")

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Response without session"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_returns_dict(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """Test that prompt_llm returns dict, not string."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Just the text",
            "session_id": "some-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        response = prompt_llm("Test", session_id="some-session")

        assert isinstance(response, dict)
        assert response["text"] == "Just the text"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_routes_with_env_vars(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that prompt_llm passes env_vars to ask_claude_code_cli."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with env vars",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }
        test_env_vars = {"VAR1": "value1", "VAR2": "value2"}

        result = prompt_llm(
            "Test question",
            provider="claude",
            env_vars=test_env_vars,
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Response with env vars"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_timeout_expired_reraised(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that TimeoutExpired is re-raised as-is (not wrapped) from prompt_llm."""
        mock_ask_claude_code_cli.side_effect = TimeoutExpired(cmd="claude", timeout=30)

        with pytest.raises(TimeoutExpired):
            prompt_llm("Test question", provider="claude", timeout=30)

    @patch("mcp_coder.llm.providers.langchain.ask_langchain")
    def test_prompt_llm_asyncio_timeout_reraised_for_langchain(
        self, mock_ask_langchain: MagicMock
    ) -> None:
        """asyncio.TimeoutError from langchain provider is re-raised."""
        mock_ask_langchain.side_effect = asyncio.TimeoutError()

        with pytest.raises(asyncio.TimeoutError):
            prompt_llm("Test question", provider="langchain", timeout=30)


class TestPromptLLMExecutionDirRouting:
    """Tests for execution_dir parameter routing in prompt_llm."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_execution_dir_passed_to_provider(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """execution_dir should be passed as cwd to provider."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with execution_dir",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question",
            execution_dir="/custom/execution/dir",
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd="/custom/execution/dir",
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Response with execution_dir"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_execution_dir_none_uses_default(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """execution_dir=None should let subprocess use CWD."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with default dir",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm("Test question", execution_dir=None)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Response with default dir"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_execution_dir_with_absolute_path(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """execution_dir with absolute path should be passed through."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with absolute path",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question",
            execution_dir="/home/user/workspace",
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd="/home/user/workspace",
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Response with absolute path"


class TestIntegration:
    """Integration tests for the full routing chain."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_full_routing_chain(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """Test the full routing chain from prompt_llm to ask_claude_code_cli."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Full chain response",
            "session_id": "chain-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm("Integration test question", provider="claude", timeout=25)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Integration test question",
            session_id=None,
            timeout=25,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Full chain response"

    def test_parameter_validation_propagation(self) -> None:
        """Test that parameter validation errors propagate correctly."""
        # Test invalid provider
        with pytest.raises(ValueError, match="Unsupported provider"):
            prompt_llm("Test", provider="invalid")

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_full_routing_chain_with_session_id(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test the full routing chain with session_id parameter."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Full chain response with session",
            "session_id": "integration-session-789",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "Integration test with session",
            provider="claude",
            session_id="integration-session-789",
            timeout=25,
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Integration test with session",
            session_id="integration-session-789",
            timeout=25,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Full chain response with session"


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
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Test question")

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert isinstance(result, dict)
        assert result["version"] == "1.0"
        assert result["text"] == "CLI response"
        assert result["session_id"] == "cli-123"
        assert result["provider"] == "claude"

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
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Follow up", session_id="existing-session")

        mock_ask_claude_code_cli.assert_called_once_with(
            "Follow up",
            session_id="existing-session",
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["session_id"] == "existing-session"

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
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Test", timeout=60)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test",
            session_id=None,
            timeout=60,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
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
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Test question")

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["provider"] == "claude"

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
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Test question", env_vars=test_env_vars)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "CLI response with env vars"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_timeout_expired_logged_and_reraised(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that TimeoutExpired is re-raised as-is (not wrapped) from prompt_llm."""
        mock_ask_claude_code_cli.side_effect = TimeoutExpired(cmd="claude", timeout=30)

        with pytest.raises(TimeoutExpired):
            prompt_llm("Test question", provider="claude", timeout=30)

    @patch("mcp_coder.llm.providers.langchain.ask_langchain")
    def test_prompt_llm_asyncio_timeout_logged_and_reraised(
        self, mock_ask_langchain: MagicMock
    ) -> None:
        """asyncio.TimeoutError from langchain is re-raised with logging."""
        mock_ask_langchain.side_effect = asyncio.TimeoutError()

        with pytest.raises(asyncio.TimeoutError):
            prompt_llm("Test question", provider="langchain", timeout=30)


class TestPromptLLMExecutionDir:
    """Tests for execution_dir parameter in prompt_llm."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_execution_dir_with_cli(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """execution_dir should be passed to CLI provider."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "CLI response with execution_dir",
            "session_id": "cli-exec-123",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm(
            "Test question",
            execution_dir="/custom/execution/path",
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd="/custom/execution/path",
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "CLI response with execution_dir"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_execution_dir_none_defaults_to_cwd(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """execution_dir=None should pass None as cwd (subprocess uses CWD)."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "Response with default execution dir",
            "session_id": "default-exec-123",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm("Test question", execution_dir=None)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Response with default execution dir"


class TestPromptLLMLogsDirDerivation:
    """Tests for logs_dir derivation from env_vars in prompt_llm."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_logs_dir_derived_from_env_vars_project_dir(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """When env_vars has MCP_CODER_PROJECT_DIR, logs_dir is derived and passed."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with logs_dir",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }
        test_env_vars = {"MCP_CODER_PROJECT_DIR": "/home/user/mcp-coder"}

        result = prompt_llm("Test question", env_vars=test_env_vars)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=str(Path("/home/user/mcp-coder") / "logs"),
        )
        assert result["text"] == "Response with logs_dir"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_logs_dir_none_when_env_vars_missing_project_dir(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """When env_vars lacks MCP_CODER_PROJECT_DIR, logs_dir=None."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response without project dir",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }
        test_env_vars = {"OTHER_VAR": "some_value"}

        result = prompt_llm("Test question", env_vars=test_env_vars)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Response without project dir"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_logs_dir_none_when_env_vars_is_none(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """When env_vars is None, logs_dir=None (backward compat)."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with no env vars",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm("Test question", env_vars=None)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
            logs_dir=None,
        )
        assert result["text"] == "Response with no env vars"


class TestPromptLlmLangchainRouting:
    """Test that prompt_llm correctly routes to the langchain provider."""

    def _make_langchain_response(
        self, text: str = "langchain reply"
    ) -> dict[str, object]:
        from datetime import datetime

        return {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "session_id": "uuid-langchain-session",
            "provider": "langchain",
            "raw_response": {},
        }

    def test_routes_to_langchain_provider(self) -> None:
        """prompt_llm with provider='langchain' calls ask_langchain."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", provider="langchain")

        mock_ask.assert_called_once()
        assert result["provider"] == "langchain"
        assert result["text"] == "langchain reply"

    def test_passes_question_session_timeout(self) -> None:
        """prompt_llm passes question, session_id, timeout to ask_langchain."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm

            prompt_llm(
                "test question",
                provider="langchain",
                session_id="my-sid",
                timeout=60,
            )

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        args, kwargs = call_kwargs
        all_args = {
            **dict(zip(["question", "session_id", "timeout"], args)),
            **kwargs,
        }
        assert all_args.get("session_id") == "my-sid"
        assert all_args.get("timeout") == 60

    def test_unsupported_provider_error_mentions_langchain(self) -> None:
        """The ValueError for unsupported providers lists 'langchain' as supported."""
        from mcp_coder.llm.interface import prompt_llm

        with pytest.raises(ValueError) as exc_info:
            prompt_llm("Hello", provider="unsupported_xyz")
        assert "langchain" in str(exc_info.value)

    def test_env_var_overrides_provider_to_langchain(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_LLM_PROVIDER env var overrides the provider parameter."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ):
            from mcp_coder.llm.interface import prompt_llm

            # provider kwarg says "claude" but env var overrides to "langchain"
            result = prompt_llm("Hello", provider="claude")
        assert result["provider"] == "langchain"

    def test_passes_mcp_config_to_langchain(self) -> None:
        """mcp_config parameter is forwarded to ask_langchain()."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm

            prompt_llm(
                "Hello",
                provider="langchain",
                mcp_config="/path/to/mcp.json",
            )

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs.get("mcp_config") == "/path/to/mcp.json"

    def test_passes_execution_dir_to_langchain(self) -> None:
        """execution_dir parameter is forwarded to ask_langchain()."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm

            prompt_llm(
                "Hello",
                provider="langchain",
                execution_dir="/custom/dir",
            )

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs.get("execution_dir") == "/custom/dir"

    def test_passes_env_vars_to_langchain(self) -> None:
        """env_vars parameter is forwarded to ask_langchain()."""
        expected = self._make_langchain_response()
        test_env = {"KEY": "value"}
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm

            prompt_llm(
                "Hello",
                provider="langchain",
                env_vars=test_env,
            )

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs.get("env_vars") == {"KEY": "value"}

    def test_langchain_without_mcp_params_still_works(self) -> None:
        """Calling with provider=langchain and no MCP params works (backward compat)."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_ask:
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", provider="langchain")

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs.get("mcp_config") is None
        assert kwargs.get("execution_dir") is None
        assert kwargs.get("env_vars") is None
        assert result["text"] == "langchain reply"

    def test_prompt_llm_returns_full_response_for_langchain(self) -> None:
        """prompt_llm with provider='langchain' returns full dict response."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ):
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", provider="langchain")
        assert result["text"] == "langchain reply"
        assert result["provider"] == "langchain"


class TestMlflowConversationIntegration:
    """Tests for mlflow_conversation context manager wiring in prompt_llm."""

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_mlflow_conversation_called_for_claude(
        self, mock_cli: MagicMock, mock_mlflow_cm: MagicMock
    ) -> None:
        """prompt_llm wraps claude provider call with mlflow_conversation."""
        mock_ctx: dict[str, Any] = {"response_data": None, "error": None}
        mock_mlflow_cm.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_mlflow_cm.return_value.__exit__ = MagicMock(return_value=False)
        mock_cli.return_value = {
            "text": "reply",
            "session_id": "s1",
            "version": "1.0",
            "timestamp": "2025-01-01",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "hello",
            provider="claude",
            session_id="s1",
            execution_dir="/work",
            branch_name="main",
        )

        mock_mlflow_cm.assert_called_once_with(
            "hello",
            "claude",
            "s1",
            {"branch_name": "main", "working_directory": "/work"},
        )
        assert result["text"] == "reply"
        assert mock_ctx["response_data"] == mock_cli.return_value

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    @patch("mcp_coder.llm.providers.langchain.ask_langchain")
    def test_mlflow_conversation_called_for_langchain(
        self, mock_langchain: MagicMock, mock_mlflow_cm: MagicMock
    ) -> None:
        """prompt_llm wraps langchain provider call with mlflow_conversation."""
        mock_ctx: dict[str, Any] = {"response_data": None, "error": None}
        mock_mlflow_cm.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_mlflow_cm.return_value.__exit__ = MagicMock(return_value=False)
        mock_langchain.return_value = {
            "text": "lc reply",
            "session_id": "lc-s1",
            "version": "1.0",
            "timestamp": "2025-01-01",
            "provider": "langchain",
            "raw_response": {},
        }

        result = prompt_llm("hello", provider="langchain", session_id="lc-s1")

        mock_mlflow_cm.assert_called_once_with(
            "hello",
            "langchain",
            "lc-s1",
            {"branch_name": None, "working_directory": None},
        )
        assert result["text"] == "lc reply"
        assert mock_ctx["response_data"] == mock_langchain.return_value

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_mlflow_conversation_sees_timeout_exception(
        self, mock_cli: MagicMock, mock_mlflow_cm: MagicMock
    ) -> None:
        """TimeoutExpired propagates through context manager so Phase 2 logs error."""
        mock_ctx: dict[str, Any] = {"response_data": None, "error": None}
        mock_mlflow_cm.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_mlflow_cm.return_value.__exit__ = MagicMock(return_value=False)
        mock_cli.side_effect = TimeoutExpired(cmd="claude", timeout=30)

        with pytest.raises(TimeoutExpired):
            prompt_llm("hello", provider="claude", timeout=30)

        # Context manager __exit__ was called (exception propagated through it)
        mock_mlflow_cm.return_value.__exit__.assert_called_once()
        exit_args = mock_mlflow_cm.return_value.__exit__.call_args[0]
        assert exit_args[0] is TimeoutExpired

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    def test_mlflow_conversation_not_called_for_unsupported_provider(
        self, mock_mlflow_cm: MagicMock
    ) -> None:
        """ValueError for unsupported provider is raised before context manager."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            prompt_llm("hello", provider="gpt")

        mock_mlflow_cm.assert_not_called()

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_metadata_includes_branch_and_working_dir(
        self, mock_cli: MagicMock, mock_mlflow_cm: MagicMock
    ) -> None:
        """Metadata dict passed to mlflow_conversation contains branch_name and working_directory."""
        mock_ctx: dict[str, Any] = {"response_data": None, "error": None}
        mock_mlflow_cm.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_mlflow_cm.return_value.__exit__ = MagicMock(return_value=False)
        mock_cli.return_value = {
            "text": "r",
            "session_id": "s",
            "version": "1.0",
            "timestamp": "2025-01-01",
            "provider": "claude",
            "raw_response": {},
        }

        prompt_llm(
            "q",
            provider="claude",
            execution_dir="/my/dir",
            branch_name="feat-x",
        )

        _, args, _ = mock_mlflow_cm.mock_calls[0]
        metadata = args[3]
        assert metadata == {"branch_name": "feat-x", "working_directory": "/my/dir"}

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_metadata_defaults_to_none_values(
        self, mock_cli: MagicMock, mock_mlflow_cm: MagicMock
    ) -> None:
        """When branch_name and execution_dir not provided, metadata has None values."""
        mock_ctx: dict[str, Any] = {"response_data": None, "error": None}
        mock_mlflow_cm.return_value.__enter__ = MagicMock(return_value=mock_ctx)
        mock_mlflow_cm.return_value.__exit__ = MagicMock(return_value=False)
        mock_cli.return_value = {
            "text": "r",
            "session_id": "s",
            "version": "1.0",
            "timestamp": "2025-01-01",
            "provider": "claude",
            "raw_response": {},
        }

        prompt_llm("q")

        _, args, _ = mock_mlflow_cm.mock_calls[0]
        metadata = args[3]
        assert metadata == {"branch_name": None, "working_directory": None}


class TestPromptLlmStream:
    """Tests for prompt_llm_stream() function."""

    def test_prompt_llm_stream_validates_empty_question(self) -> None:
        """prompt_llm_stream raises ValueError for empty question."""
        with pytest.raises(ValueError, match="cannot be empty"):
            list(prompt_llm_stream(""))

    def test_prompt_llm_stream_validates_whitespace_question(self) -> None:
        """prompt_llm_stream raises ValueError for whitespace-only question."""
        with pytest.raises(ValueError, match="cannot be empty"):
            list(prompt_llm_stream("   "))

    def test_prompt_llm_stream_validates_timeout_zero(self) -> None:
        """prompt_llm_stream raises ValueError for timeout <= 0."""
        with pytest.raises(ValueError, match="positive number"):
            list(prompt_llm_stream("Test", timeout=0))

    def test_prompt_llm_stream_validates_timeout_negative(self) -> None:
        """prompt_llm_stream raises ValueError for negative timeout."""
        with pytest.raises(ValueError, match="positive number"):
            list(prompt_llm_stream("Test", timeout=-5))

    def test_prompt_llm_stream_validates_provider(self) -> None:
        """prompt_llm_stream raises ValueError for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            list(prompt_llm_stream("Test", provider="gpt"))

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_prompt_llm_stream_routes_to_claude(self, mock_stream: MagicMock) -> None:
        """prompt_llm_stream routes to ask_claude_code_cli_stream for claude provider."""
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )

        events = list(prompt_llm_stream("Hello", provider="claude"))

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
        )
        assert len(events) == 2
        assert events[0]["type"] == "text_delta"

    @patch("mcp_coder.llm.providers.langchain.ask_langchain_stream")
    def test_prompt_llm_stream_routes_to_langchain(
        self, mock_stream: MagicMock
    ) -> None:
        """prompt_llm_stream routes to ask_langchain_stream for langchain provider."""
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )

        events = list(prompt_llm_stream("Hello", provider="langchain"))

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            mcp_config=None,
            execution_dir=None,
            env_vars=None,
        )
        assert len(events) == 2

    def test_prompt_llm_stream_env_override(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_LLM_PROVIDER env var overrides provider parameter."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain_stream",
            return_value=iter([{"type": "done", "usage": {}}]),
        ) as mock_stream:
            events = list(prompt_llm_stream("Hello", provider="claude"))

        mock_stream.assert_called_once()
        assert len(events) == 1

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_prompt_llm_stream_passes_all_params(self, mock_stream: MagicMock) -> None:
        """prompt_llm_stream passes all parameters to the claude provider."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])

        list(
            prompt_llm_stream(
                "Q",
                provider="claude",
                session_id="sid",
                timeout=60,
                env_vars={"K": "V"},
                execution_dir="/work",
                mcp_config="/mcp.json",
                branch_name="main",
            )
        )

        mock_stream.assert_called_once_with(
            "Q",
            session_id="sid",
            timeout=60,
            env_vars={"K": "V"},
            cwd="/work",
            mcp_config="/mcp.json",
            branch_name="main",
        )
