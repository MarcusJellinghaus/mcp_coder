"""Tests for the high-level LLM interface."""

import asyncio
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from mcp_coder.llm.interface import LLMTimeoutError, prompt_llm, prompt_llm_stream
from mcp_coder.utils.subprocess_runner import TimeoutExpired

# prompt_llm normalises project_dir with Path(), so the expected cwd is the
# normalised form of whatever the test passes in.
PROJECT_DIR = str(Path("/test/project"))


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

        result = prompt_llm(
            "Test question", provider="claude", timeout=30, project_dir=PROJECT_DIR
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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

        result = prompt_llm("Test question", project_dir=PROJECT_DIR)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Default response"

    def test_prompt_llm_unsupported_provider_gpt(self) -> None:
        """Test that prompt_llm raises ValueError for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider: gpt"):
            prompt_llm("Test question", provider="gpt", project_dir=PROJECT_DIR)

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_passes_through_exceptions(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that prompt_llm passes through exceptions from underlying implementations."""
        mock_ask_claude_code_cli.side_effect = RuntimeError("Claude error")

        with pytest.raises(RuntimeError, match="Claude error"):
            prompt_llm("Test question", provider="claude", project_dir=PROJECT_DIR)

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

        result = prompt_llm("Test question", timeout=60, project_dir=PROJECT_DIR)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=60,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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
            project_dir=PROJECT_DIR,
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id="test-session-123",
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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

        result = prompt_llm("Test question", project_dir=PROJECT_DIR)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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

        response = prompt_llm(
            "Test", session_id="some-session", project_dir=PROJECT_DIR
        )

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
            project_dir=PROJECT_DIR,
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Response with env vars"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_timeout_expired_reraised(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that TimeoutExpired is re-raised as LLMTimeoutError from prompt_llm."""
        mock_ask_claude_code_cli.side_effect = TimeoutExpired(cmd="claude", timeout=30)

        with pytest.raises(LLMTimeoutError):
            prompt_llm(
                "Test question", provider="claude", timeout=30, project_dir=PROJECT_DIR
            )

    @patch("mcp_coder.llm.providers.langchain.ask_langchain")
    def test_prompt_llm_asyncio_timeout_reraised_for_langchain(
        self, mock_ask_langchain: MagicMock
    ) -> None:
        """asyncio.TimeoutError from langchain provider is re-raised as LLMTimeoutError."""
        mock_ask_langchain.side_effect = asyncio.TimeoutError()

        with pytest.raises(LLMTimeoutError):
            prompt_llm(
                "Test question",
                provider="langchain",
                timeout=30,
                project_dir=PROJECT_DIR,
            )


class TestLLMTimeoutErrorNormalization:
    """Tests for LLMTimeoutError normalization in prompt_llm."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_claude_timeout_raises_llm_timeout_error(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """TimeoutExpired from claude is normalized to LLMTimeoutError (also a TimeoutError)."""
        mock_ask_claude_code_cli.side_effect = TimeoutExpired(cmd="claude", timeout=30)

        with pytest.raises(LLMTimeoutError) as exc_info:
            prompt_llm(
                "Test question", provider="claude", timeout=30, project_dir=PROJECT_DIR
            )

        # LLMTimeoutError is also a TimeoutError
        assert isinstance(exc_info.value, TimeoutError)
        assert "30s" in str(exc_info.value)
        # Original exception is chained
        assert isinstance(exc_info.value.__cause__, TimeoutExpired)

    @patch("mcp_coder.llm.providers.langchain.ask_langchain")
    def test_prompt_llm_langchain_timeout_raises_llm_timeout_error(
        self, mock_ask_langchain: MagicMock
    ) -> None:
        """asyncio.TimeoutError from langchain is normalized to LLMTimeoutError."""
        mock_ask_langchain.side_effect = asyncio.TimeoutError()

        with pytest.raises(LLMTimeoutError) as exc_info:
            prompt_llm(
                "Test question",
                provider="langchain",
                timeout=60,
                project_dir=PROJECT_DIR,
            )

        # LLMTimeoutError is also a TimeoutError
        assert isinstance(exc_info.value, TimeoutError)
        assert "60s" in str(exc_info.value)
        # Original exception is chained
        assert isinstance(exc_info.value.__cause__, asyncio.TimeoutError)


class TestPromptLLMProjectDirRouting:
    """Tests for project_dir parameter routing in prompt_llm."""

    def test_project_dir_is_required(self) -> None:
        """prompt_llm without project_dir raises TypeError (no silent cwd fallback)."""
        with pytest.raises(TypeError):
            prompt_llm("hi")  # type: ignore[call-arg]  # pylint: disable=missing-kwoa

    def test_prompt_llm_stream_project_dir_is_required(self) -> None:
        """prompt_llm_stream without project_dir raises TypeError."""
        with pytest.raises(TypeError):
            list(prompt_llm_stream("hi"))  # type: ignore[call-arg]  # pylint: disable=missing-kwoa

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_project_dir_passed_to_provider(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """project_dir should be passed as cwd to provider."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with project_dir",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question",
            project_dir=str(Path("/custom/project/dir")),
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=str(Path("/custom/project/dir")),
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Response with project_dir"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_project_dir_accepts_path_object(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """project_dir accepts a Path and is normalised to a str cwd."""
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
            project_dir=Path("/home/user/workspace"),
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=str(Path("/home/user/workspace")),
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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

        result = prompt_llm(
            "Integration test question",
            provider="claude",
            timeout=25,
            project_dir=PROJECT_DIR,
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Integration test question",
            session_id=None,
            timeout=25,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Full chain response"

    def test_parameter_validation_propagation(self) -> None:
        """Test that parameter validation errors propagate correctly."""
        # Test invalid provider
        with pytest.raises(ValueError, match="Unsupported provider"):
            prompt_llm("Test", provider="invalid", project_dir=PROJECT_DIR)

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
            project_dir=PROJECT_DIR,
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Integration test with session",
            session_id="integration-session-789",
            timeout=25,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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

        result = prompt_llm("Test question", project_dir=PROJECT_DIR)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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

        result = prompt_llm(
            "Follow up", session_id="existing-session", project_dir=PROJECT_DIR
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Follow up",
            session_id="existing-session",
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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

        result = prompt_llm("Test", project_dir=PROJECT_DIR)

        assert result["raw_response"]["duration_ms"] == 2801
        assert result["raw_response"]["cost_usd"] == 0.058

    def test_prompt_llm_unsupported_provider(self) -> None:
        """Test error for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            prompt_llm("Test", provider="gpt", project_dir=PROJECT_DIR)

    def test_prompt_llm_empty_question(self) -> None:
        """Test validation for empty question."""
        with pytest.raises(ValueError, match="cannot be empty"):
            prompt_llm("", project_dir=PROJECT_DIR)

    def test_prompt_llm_whitespace_only_question(self) -> None:
        """Test validation for whitespace-only question."""
        with pytest.raises(ValueError, match="cannot be empty"):
            prompt_llm("   ", project_dir=PROJECT_DIR)

    def test_prompt_llm_invalid_timeout(self) -> None:
        """Test validation for invalid timeout."""
        with pytest.raises(ValueError, match="positive number"):
            prompt_llm("Test", timeout=0, project_dir=PROJECT_DIR)

    def test_prompt_llm_negative_timeout(self) -> None:
        """Test validation for negative timeout."""
        with pytest.raises(ValueError, match="positive number"):
            prompt_llm("Test", timeout=-5, project_dir=PROJECT_DIR)

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

        result = prompt_llm("Test", timeout=60, project_dir=PROJECT_DIR)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test",
            session_id=None,
            timeout=60,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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

        result = prompt_llm("Test question", project_dir=PROJECT_DIR)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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

        result = prompt_llm(
            "Test question", env_vars=test_env_vars, project_dir=PROJECT_DIR
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "CLI response with env vars"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_timeout_expired_logged_and_reraised(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that TimeoutExpired is re-raised as LLMTimeoutError from prompt_llm."""
        mock_ask_claude_code_cli.side_effect = TimeoutExpired(cmd="claude", timeout=30)

        with pytest.raises(LLMTimeoutError):
            prompt_llm(
                "Test question", provider="claude", timeout=30, project_dir=PROJECT_DIR
            )

    @patch("mcp_coder.llm.providers.langchain.ask_langchain")
    def test_prompt_llm_asyncio_timeout_logged_and_reraised(
        self, mock_ask_langchain: MagicMock
    ) -> None:
        """asyncio.TimeoutError from langchain is re-raised as LLMTimeoutError."""
        mock_ask_langchain.side_effect = asyncio.TimeoutError()

        with pytest.raises(LLMTimeoutError):
            prompt_llm(
                "Test question",
                provider="langchain",
                timeout=30,
                project_dir=PROJECT_DIR,
            )


class TestPromptLLMProjectDir:
    """Tests for project_dir parameter in prompt_llm."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_project_dir_with_cli(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """project_dir should be passed to CLI provider."""
        mock_response = {
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "text": "CLI response with project_dir",
            "session_id": "cli-exec-123",
            "provider": "claude",
            "raw_response": {},
        }
        mock_ask_claude_code_cli.return_value = mock_response

        result = prompt_llm(
            "Test question",
            project_dir=str(Path("/custom/project/path")),
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=str(Path("/custom/project/path")),
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "CLI response with project_dir"


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

        result = prompt_llm(
            "Test question", env_vars=test_env_vars, project_dir=PROJECT_DIR
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=str(Path("/home/user/mcp-coder") / "logs"),
            append_system_prompt=None,
            system_prompt_replace=None,
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

        result = prompt_llm(
            "Test question", env_vars=test_env_vars, project_dir=PROJECT_DIR
        )

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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

        result = prompt_llm("Test question", env_vars=None, project_dir=PROJECT_DIR)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert result["text"] == "Response with no env vars"


class TestPromptLLMStreamLogsDirDerivation:
    """Tests for logs_dir derivation from env_vars in prompt_llm_stream."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_logs_dir_derived_from_env_vars_project_dir(
        self, mock_stream: MagicMock
    ) -> None:
        """When env_vars has MCP_CODER_PROJECT_DIR, logs_dir is derived and passed."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])
        test_env_vars = {"MCP_CODER_PROJECT_DIR": "/home/user/mcp-coder"}

        list(
            prompt_llm_stream(
                "Test question", env_vars=test_env_vars, project_dir=PROJECT_DIR
            )
        )

        mock_stream.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=str(Path("/home/user/mcp-coder") / "logs"),
            append_system_prompt=None,
            system_prompt_replace=None,
        )

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_logs_dir_none_when_env_vars_missing_project_dir(
        self, mock_stream: MagicMock
    ) -> None:
        """When env_vars lacks MCP_CODER_PROJECT_DIR, logs_dir=None."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])
        test_env_vars = {"OTHER_VAR": "some_value"}

        list(
            prompt_llm_stream(
                "Test question", env_vars=test_env_vars, project_dir=PROJECT_DIR
            )
        )

        mock_stream.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=test_env_vars,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_logs_dir_none_when_env_vars_is_none(self, mock_stream: MagicMock) -> None:
        """When env_vars is None, logs_dir=None (backward compat)."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])

        list(prompt_llm_stream("Test question", env_vars=None, project_dir=PROJECT_DIR))

        mock_stream.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )


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

    def _make_claude_response(self, text: str = "claude reply") -> dict[str, object]:
        from datetime import datetime

        return {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "session_id": "uuid-claude-session",
            "provider": "claude",
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

            result = prompt_llm("Hello", provider="langchain", project_dir=PROJECT_DIR)

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
                project_dir=PROJECT_DIR,
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
            prompt_llm("Hello", provider="unsupported_xyz", project_dir=PROJECT_DIR)
        assert "langchain" in str(exc_info.value)

    def test_unsupported_provider_error_mentions_copilot(self) -> None:
        """The ValueError for unsupported providers lists 'copilot' as supported."""
        from mcp_coder.llm.interface import prompt_llm

        with pytest.raises(ValueError) as exc_info:
            prompt_llm("Hello", provider="unsupported_xyz", project_dir=PROJECT_DIR)
        assert "copilot" in str(exc_info.value)

    def test_explicit_provider_beats_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicitly passed provider wins over MCP_CODER_LLM_PROVIDER."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        expected = self._make_langchain_response()
        with (
            patch(
                "mcp_coder.llm.providers.langchain.ask_langchain",
                return_value=expected,
            ) as mock_langchain,
            patch(
                "mcp_coder.llm.interface.ask_claude_code_cli",
                return_value=self._make_claude_response(),
            ) as mock_claude,
        ):
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", provider="claude", project_dir=PROJECT_DIR)

        mock_langchain.assert_not_called()
        mock_claude.assert_called_once()
        assert result["provider"] == "claude"

    def test_env_var_used_when_provider_omitted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_LLM_PROVIDER applies when no provider argument is given."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ) as mock_langchain:
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", project_dir=PROJECT_DIR)

        mock_langchain.assert_called_once()
        assert result["provider"] == "langchain"

    def test_defaults_to_claude_when_provider_and_env_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With no provider argument and no env var, claude is used."""
        monkeypatch.delenv("MCP_CODER_LLM_PROVIDER", raising=False)
        with patch(
            "mcp_coder.llm.interface.ask_claude_code_cli",
            return_value=self._make_claude_response(),
        ) as mock_claude:
            from mcp_coder.llm.interface import prompt_llm

            result = prompt_llm("Hello", project_dir=PROJECT_DIR)

        mock_claude.assert_called_once()
        assert result["provider"] == "claude"

    def test_unsupported_provider_still_raises_after_resolution(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicit unsupported provider raises even with a valid env var set."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        from mcp_coder.llm.interface import prompt_llm

        with pytest.raises(ValueError, match="Unsupported provider: unsupported_xyz"):
            prompt_llm("Hello", provider="unsupported_xyz", project_dir=PROJECT_DIR)

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
                project_dir=PROJECT_DIR,
            )

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs.get("mcp_config") == "/path/to/mcp.json"

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
                project_dir=PROJECT_DIR,
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

            result = prompt_llm("Hello", provider="langchain", project_dir=PROJECT_DIR)

        call_kwargs = mock_ask.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs.get("mcp_config") is None
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

            result = prompt_llm("Hello", provider="langchain", project_dir=PROJECT_DIR)
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
            project_dir="/work",
            branch_name="main",
        )

        mock_mlflow_cm.assert_called_once_with(
            "hello",
            "claude",
            "s1",
            {"branch_name": "main", "working_directory": str(Path("/work"))},
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

        result = prompt_llm(
            "hello", provider="langchain", session_id="lc-s1", project_dir=PROJECT_DIR
        )

        mock_mlflow_cm.assert_called_once_with(
            "hello",
            "langchain",
            "lc-s1",
            {"branch_name": None, "working_directory": PROJECT_DIR},
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

        with pytest.raises(LLMTimeoutError):
            prompt_llm("hello", provider="claude", timeout=30, project_dir=PROJECT_DIR)

        # Context manager __exit__ was called (exception propagated through it)
        mock_mlflow_cm.return_value.__exit__.assert_called_once()
        exit_args = mock_mlflow_cm.return_value.__exit__.call_args[0]
        assert exit_args[0] is LLMTimeoutError

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    def test_mlflow_conversation_not_called_for_unsupported_provider(
        self, mock_mlflow_cm: MagicMock
    ) -> None:
        """ValueError for unsupported provider is raised before context manager."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            prompt_llm("hello", provider="gpt", project_dir=PROJECT_DIR)

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
            project_dir="/my/dir",
            branch_name="feat-x",
        )

        _, args, _ = mock_mlflow_cm.mock_calls[0]
        metadata = args[3]
        assert metadata == {
            "branch_name": "feat-x",
            "working_directory": str(Path("/my/dir")),
        }

    @patch("mcp_coder.llm.interface.mlflow_conversation")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_metadata_branch_name_defaults_to_none(
        self, mock_cli: MagicMock, mock_mlflow_cm: MagicMock
    ) -> None:
        """When branch_name is not provided it is None; working_directory is project_dir."""
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

        prompt_llm("q", project_dir=PROJECT_DIR)

        _, args, _ = mock_mlflow_cm.mock_calls[0]
        metadata = args[3]
        assert metadata["branch_name"] is None
        assert metadata["working_directory"] == PROJECT_DIR


class TestPromptLlmStream:
    """Tests for prompt_llm_stream() function."""

    def test_prompt_llm_stream_validates_empty_question(self) -> None:
        """prompt_llm_stream raises ValueError for empty question."""
        with pytest.raises(ValueError, match="cannot be empty"):
            list(prompt_llm_stream("", project_dir=PROJECT_DIR))

    def test_prompt_llm_stream_validates_whitespace_question(self) -> None:
        """prompt_llm_stream raises ValueError for whitespace-only question."""
        with pytest.raises(ValueError, match="cannot be empty"):
            list(prompt_llm_stream("   ", project_dir=PROJECT_DIR))

    def test_prompt_llm_stream_validates_timeout_zero(self) -> None:
        """prompt_llm_stream raises ValueError for timeout <= 0."""
        with pytest.raises(ValueError, match="positive number"):
            list(prompt_llm_stream("Test", timeout=0, project_dir=PROJECT_DIR))

    def test_prompt_llm_stream_validates_timeout_negative(self) -> None:
        """prompt_llm_stream raises ValueError for negative timeout."""
        with pytest.raises(ValueError, match="positive number"):
            list(prompt_llm_stream("Test", timeout=-5, project_dir=PROJECT_DIR))

    def test_prompt_llm_stream_validates_provider(self) -> None:
        """prompt_llm_stream raises ValueError for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            list(prompt_llm_stream("Test", provider="gpt", project_dir=PROJECT_DIR))

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_prompt_llm_stream_routes_to_claude(self, mock_stream: MagicMock) -> None:
        """prompt_llm_stream routes to ask_claude_code_cli_stream for claude provider."""
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )

        events = list(
            prompt_llm_stream("Hello", provider="claude", project_dir=PROJECT_DIR)
        )

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
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

        events = list(
            prompt_llm_stream("Hello", provider="langchain", project_dir=PROJECT_DIR)
        )

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            mcp_config=None,
            env_vars=None,
            tools=None,
            system_prompt=None,
            project_prompt=None,
        )
        assert len(events) == 2

    def test_prompt_llm_stream_explicit_provider_beats_env_var(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicitly passed provider wins over MCP_CODER_LLM_PROVIDER."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        with (
            patch(
                "mcp_coder.llm.providers.langchain.ask_langchain_stream",
                return_value=iter([{"type": "done", "usage": {}}]),
            ) as mock_langchain,
            patch(
                "mcp_coder.llm.providers.claude.claude_code_cli_streaming."
                "ask_claude_code_cli_stream",
                return_value=iter([{"type": "done", "usage": {}}]),
            ) as mock_claude,
        ):
            events = list(
                prompt_llm_stream("Hello", provider="claude", project_dir=PROJECT_DIR)
            )

        mock_langchain.assert_not_called()
        mock_claude.assert_called_once()
        assert len(events) == 1

    def test_prompt_llm_stream_env_var_used_when_provider_omitted(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """MCP_CODER_LLM_PROVIDER applies when no provider argument is given."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain_stream",
            return_value=iter([{"type": "done", "usage": {}}]),
        ) as mock_langchain:
            events = list(prompt_llm_stream("Hello", project_dir=PROJECT_DIR))

        mock_langchain.assert_called_once()
        assert len(events) == 1

    def test_prompt_llm_stream_defaults_to_claude_without_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With no provider argument and no env var, claude is used."""
        monkeypatch.delenv("MCP_CODER_LLM_PROVIDER", raising=False)
        with patch(
            "mcp_coder.llm.providers.claude.claude_code_cli_streaming."
            "ask_claude_code_cli_stream",
            return_value=iter([{"type": "done", "usage": {}}]),
        ) as mock_claude:
            events = list(prompt_llm_stream("Hello", project_dir=PROJECT_DIR))

        mock_claude.assert_called_once()
        assert len(events) == 1

    def test_prompt_llm_stream_unsupported_provider_still_raises(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An explicit unsupported provider raises even with a valid env var set."""
        monkeypatch.setenv("MCP_CODER_LLM_PROVIDER", "langchain")
        with pytest.raises(ValueError, match="Unsupported provider: unsupported_xyz"):
            list(
                prompt_llm_stream(
                    "Hello", provider="unsupported_xyz", project_dir=PROJECT_DIR
                )
            )

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
                project_dir="/work",
                mcp_config="/mcp.json",
                branch_name="main",
            )
        )

        mock_stream.assert_called_once_with(
            "Q",
            session_id="sid",
            timeout=60,
            env_vars={"K": "V"},
            cwd=str(Path("/work")),
            mcp_config="/mcp.json",
            settings_file=None,
            branch_name="main",
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )


class TestPromptLlmStreamToolsParam:
    """Tests for tools parameter threading in prompt_llm_stream()."""

    @patch("mcp_coder.llm.providers.langchain.ask_langchain_stream")
    def test_prompt_llm_stream_passes_tools_to_langchain(
        self, mock_stream: MagicMock
    ) -> None:
        """prompt_llm_stream forwards tools= to ask_langchain_stream for langchain provider."""
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )
        fake_tools: list[Any] = [MagicMock(), MagicMock()]

        events = list(
            prompt_llm_stream(
                "Hello",
                provider="langchain",
                tools=fake_tools,
                project_dir=PROJECT_DIR,
            )
        )

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            mcp_config=None,
            env_vars=None,
            tools=fake_tools,
            system_prompt=None,
            project_prompt=None,
        )
        assert len(events) == 2

    @patch("mcp_coder.llm.providers.langchain.ask_langchain_stream")
    def test_prompt_llm_stream_passes_none_tools_by_default(
        self, mock_stream: MagicMock
    ) -> None:
        """prompt_llm_stream passes tools=None when no tools argument given."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])

        list(prompt_llm_stream("Hello", provider="langchain", project_dir=PROJECT_DIR))

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            mcp_config=None,
            env_vars=None,
            tools=None,
            system_prompt=None,
            project_prompt=None,
        )

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_prompt_llm_stream_claude_ignores_tools(
        self, mock_stream: MagicMock
    ) -> None:
        """Claude path works fine with tools param present (tools not forwarded to claude)."""
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )

        events = list(
            prompt_llm_stream(
                "Hello",
                provider="claude",
                tools=[MagicMock()],
                project_dir=PROJECT_DIR,
            )
        )

        # Claude provider call should NOT include tools kwarg
        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )
        assert len(events) == 2


class TestPromptLlmInjectPrompts:
    """Tests for the inject_prompts switch in prompt_llm and prompt_llm_stream."""

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_no_inject_prompts_loads_nothing(
        self,
        mock_ask_claude_code_cli: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """With inject_prompts left at its default, no prompts are loaded."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        prompt_llm("Test question", project_dir=PROJECT_DIR)

        mock_load_prompts.assert_not_called()
        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=None,
            system_prompt_replace=None,
        )

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_prompt_llm_project_dir_loads_prompts(
        self,
        mock_ask_claude_code_cli: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """When project_dir is provided, load_prompts is called and results passed to provider."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "system prompt content",
            "project prompt content",
            mock_config,
        )
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with prompts",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question", project_dir="/my/project", inject_prompts=True
        )

        mock_load_prompts.assert_called_once_with(Path("/my/project"))
        expected_combined = (
            "## System Prompt\n\nsystem prompt content\n\n"
            "## Project Prompt\n\nproject prompt content"
        )
        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=str(Path("/my/project")),
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=expected_combined,
            system_prompt_replace=None,
        )
        assert result["text"] == "Response with prompts"

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.ask_claude_code_cli_stream"
    )
    def test_prompt_llm_stream_project_dir_loads_prompts(
        self,
        mock_stream: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """prompt_llm_stream with project_dir loads prompts and passes to provider."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "sys prompt",
            "proj prompt",
            mock_config,
        )
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )

        events = list(
            prompt_llm_stream(
                "Hello",
                provider="claude",
                project_dir="/my/project",
                inject_prompts=True,
            )
        )

        mock_load_prompts.assert_called_once_with(Path("/my/project"))
        expected_combined = (
            "## System Prompt\n\nsys prompt\n\n" + "## Project Prompt\n\nproj prompt"
        )
        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=str(Path("/my/project")),
            mcp_config=None,
            settings_file=None,
            branch_name=None,
            logs_dir=None,
            append_system_prompt=expected_combined,
            system_prompt_replace=None,
        )
        assert len(events) == 2

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.providers.langchain.ask_langchain")
    def test_prompt_llm_langchain_project_dir_loads_prompts(
        self,
        mock_ask_langchain: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """prompt_llm with langchain provider and project_dir passes prompts."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "sys prompt",
            "proj prompt",
            mock_config,
        )
        mock_ask_langchain.return_value = {
            "text": "langchain reply",
            "session_id": "lc-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "langchain",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question",
            provider="langchain",
            project_dir="/my/project",
            inject_prompts=True,
        )

        mock_load_prompts.assert_called_once_with(Path("/my/project"))
        call_kwargs = mock_ask_langchain.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs["system_prompt"] == "sys prompt"
        assert kwargs["project_prompt"] == "proj prompt"
        assert result["text"] == "langchain reply"


class TestBuildClaudeSystemPrompts:
    """Tests for _build_claude_system_prompts helper."""

    def test_append_mode_returns_combined_in_first_slot(self) -> None:
        """In append mode, combined prompt goes to append_system_prompt."""
        from mcp_coder.llm.interface import _build_claude_system_prompts
        from mcp_coder.utils.pyproject_config import PromptsConfig

        config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )

        append, replace = _build_claude_system_prompts(
            "System text", "Project text", config, "/fake/dir"
        )

        expected = (
            "## System Prompt\n\nSystem text\n\n" + "## Project Prompt\n\nProject text"
        )
        assert append == expected
        assert replace is None

    def test_replace_mode_returns_combined_in_second_slot(self) -> None:
        """In replace mode, combined prompt goes to system_prompt_replace."""
        from mcp_coder.llm.interface import _build_claude_system_prompts
        from mcp_coder.utils.pyproject_config import PromptsConfig

        config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="replace",
        )

        append, replace = _build_claude_system_prompts(
            "System text", "Project text", config, "/fake/dir"
        )

        expected = (
            "## System Prompt\n\nSystem text\n\n" + "## Project Prompt\n\nProject text"
        )
        assert append is None
        assert replace == expected

    @patch("mcp_coder.prompts.prompt_loader.is_claude_md", return_value=True)
    @patch(
        "mcp_coder.prompts.prompt_loader.get_project_prompt_path",
        return_value=Path("/fake/dir/CLAUDE.md"),
    )
    def test_skips_project_prompt_when_claude_md(
        self,
        _mock_path: MagicMock,
        _mock_is_claude: MagicMock,
    ) -> None:
        """Project prompt is skipped when pointing at CLAUDE.md."""
        from mcp_coder.llm.interface import _build_claude_system_prompts
        from mcp_coder.utils.pyproject_config import PromptsConfig

        config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )

        append, replace = _build_claude_system_prompts(
            "System text", "Project text", config, "/fake/dir"
        )

        assert append == "## System Prompt\n\nSystem text"
        assert replace is None

    def test_no_prompts_returns_none(self) -> None:
        """When both prompts are None, returns (None, None)."""
        from mcp_coder.llm.interface import _build_claude_system_prompts
        from mcp_coder.utils.pyproject_config import PromptsConfig

        config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )

        append, replace = _build_claude_system_prompts(None, None, config, None)

        assert append is None
        assert replace is None

    def test_only_system_prompt(self) -> None:
        """When only system_prompt is set, only system section present."""
        from mcp_coder.llm.interface import _build_claude_system_prompts
        from mcp_coder.utils.pyproject_config import PromptsConfig

        config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )

        append, replace = _build_claude_system_prompts(
            "System only", None, config, None
        )

        assert append == "## System Prompt\n\nSystem only"
        assert replace is None


class TestIsClaudeMd:
    """Tests for is_claude_md function."""

    def test_is_claude_md_true_root_level(self, tmp_path: Path) -> None:
        """Detects CLAUDE.md at project root."""
        from mcp_coder.prompts.prompt_loader import is_claude_md

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Instructions")

        assert is_claude_md(claude_md, str(tmp_path)) is True

    def test_is_claude_md_true_dot_claude_dir(self, tmp_path: Path) -> None:
        """Detects .claude/CLAUDE.md."""
        from mcp_coder.prompts.prompt_loader import is_claude_md

        dot_claude = tmp_path / ".claude"
        dot_claude.mkdir()
        claude_md = dot_claude / "CLAUDE.md"
        claude_md.write_text("# Instructions")

        assert is_claude_md(claude_md, str(tmp_path)) is True

    def test_is_claude_md_false_non_matching(self, tmp_path: Path) -> None:
        """Non-CLAUDE.md paths return False."""
        from mcp_coder.prompts.prompt_loader import is_claude_md

        custom = tmp_path / "my-prompt.md"
        custom.write_text("custom prompt")

        assert is_claude_md(custom, str(tmp_path)) is False

    def test_is_claude_md_parent_dir(self, tmp_path: Path) -> None:
        """Detects CLAUDE.md in parent directory."""
        from mcp_coder.prompts.prompt_loader import is_claude_md

        parent_claude = tmp_path / "CLAUDE.md"
        parent_claude.write_text("# Parent instructions")
        sub_project = tmp_path / "subproject"
        sub_project.mkdir()

        assert is_claude_md(parent_claude, str(sub_project)) is True

    def test_is_claude_md_none_path(self) -> None:
        """Returns False when path is None."""
        from mcp_coder.prompts.prompt_loader import is_claude_md

        assert is_claude_md(None, "/some/dir") is False

    def test_is_claude_md_none_project_dir(self, tmp_path: Path) -> None:
        """Returns False when project_dir is None."""
        from mcp_coder.prompts.prompt_loader import is_claude_md

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Instructions")

        assert is_claude_md(claude_md, None) is False


class TestPromptLlmCopilotRouting:
    """Tests for copilot provider routing in prompt_llm and prompt_llm_stream."""

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_prompt_llm_routes_to_copilot(self, mock_ask_copilot: MagicMock) -> None:
        """prompt_llm routes to ask_copilot_cli for copilot provider."""
        mock_ask_copilot.return_value = {
            "text": "Copilot response",
            "session_id": "copilot-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "copilot",
            "raw_response": {},
        }

        result = prompt_llm(
            "Test question", provider="copilot", timeout=30, project_dir=PROJECT_DIR
        )

        mock_ask_copilot.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            logs_dir=None,
            branch_name=None,
            system_prompt=None,
        )
        assert result["text"] == "Copilot response"
        assert result["provider"] == "copilot"

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli_stream")
    def test_prompt_llm_stream_routes_to_copilot(self, mock_stream: MagicMock) -> None:
        """prompt_llm_stream routes to ask_copilot_cli_stream for copilot provider."""
        mock_stream.return_value = iter(
            [{"type": "text_delta", "text": "Hi"}, {"type": "done", "usage": {}}]
        )

        events = list(
            prompt_llm_stream("Hello", provider="copilot", project_dir=PROJECT_DIR)
        )

        mock_stream.assert_called_once_with(
            "Hello",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=PROJECT_DIR,
            logs_dir=None,
            branch_name=None,
            system_prompt=None,
        )
        assert len(events) == 2
        assert events[0]["type"] == "text_delta"


class TestCopilotSystemPromptHandling:
    """Tests for system prompt handling in copilot provider."""

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_copilot_system_prompt_passed_on_new_session(
        self,
        mock_ask_copilot: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """No session_id → system_prompt forwarded to copilot."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "system prompt content",
            "project prompt content",
            mock_config,
        )
        mock_ask_copilot.return_value = {
            "text": "Copilot reply",
            "session_id": "new-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "copilot",
            "raw_response": {},
        }

        prompt_llm(
            "Test question",
            provider="copilot",
            project_dir="/my/project",
            inject_prompts=True,
        )

        call_kwargs = mock_ask_copilot.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs["system_prompt"] == "system prompt content"

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_copilot_system_prompt_skipped_on_resume(
        self,
        mock_ask_copilot: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """session_id set → system_prompt=None for copilot."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "system prompt content",
            "project prompt content",
            mock_config,
        )
        mock_ask_copilot.return_value = {
            "text": "Copilot reply",
            "session_id": "existing-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "copilot",
            "raw_response": {},
        }

        prompt_llm(
            "Test question",
            provider="copilot",
            session_id="existing-session",
            project_dir="/my/project",
            inject_prompts=True,
        )

        call_kwargs = mock_ask_copilot.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert kwargs["system_prompt"] is None

    @patch("mcp_coder.prompts.prompt_loader.load_prompts")
    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_copilot_project_prompt_always_skipped(
        self,
        mock_ask_copilot: MagicMock,
        mock_load_prompts: MagicMock,
    ) -> None:
        """project_prompt is never forwarded to copilot (reads CLAUDE.md natively)."""
        from mcp_coder.utils.pyproject_config import PromptsConfig

        mock_config = PromptsConfig(
            system_prompt=None,
            project_prompt=None,
            claude_system_prompt_mode="append",
        )
        mock_load_prompts.return_value = (
            "system prompt",
            "project prompt that should NOT appear",
            mock_config,
        )
        mock_ask_copilot.return_value = {
            "text": "Copilot reply",
            "session_id": "session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "copilot",
            "raw_response": {},
        }

        prompt_llm(
            "Test question",
            provider="copilot",
            project_dir="/my/project",
            inject_prompts=True,
        )

        call_kwargs = mock_ask_copilot.call_args
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        # system_prompt should be present but project_prompt should NOT
        assert kwargs["system_prompt"] == "system prompt"
        # ask_copilot_cli has no project_prompt parameter
        assert "project_prompt" not in kwargs


class TestCopilotTimeoutHandling:
    """Tests for copilot timeout error normalization."""

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_copilot_timeout_raises_llm_timeout_error(
        self, mock_ask_copilot: MagicMock
    ) -> None:
        """TimeoutExpired from copilot is normalized to LLMTimeoutError."""
        mock_ask_copilot.side_effect = TimeoutExpired(cmd="copilot", timeout=30)

        with pytest.raises(LLMTimeoutError) as exc_info:
            prompt_llm(
                "Test question", provider="copilot", timeout=30, project_dir=PROJECT_DIR
            )

        assert isinstance(exc_info.value, TimeoutError)
        assert "30s" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, TimeoutExpired)


class TestCopilotProviderValidation:
    """Tests that copilot is accepted as a valid provider."""

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli")
    def test_prompt_llm_accepts_copilot_provider(
        self, mock_ask_copilot: MagicMock
    ) -> None:
        """No ValueError for provider='copilot'."""
        mock_ask_copilot.return_value = {
            "text": "ok",
            "session_id": "s",
            "version": "1.0",
            "timestamp": "2025-01-01",
            "provider": "copilot",
            "raw_response": {},
        }

        # Should not raise
        result = prompt_llm("Test", provider="copilot", project_dir=PROJECT_DIR)
        assert result["text"] == "ok"

    @patch("mcp_coder.llm.providers.copilot.ask_copilot_cli_stream")
    def test_prompt_llm_stream_accepts_copilot_provider(
        self, mock_stream: MagicMock
    ) -> None:
        """No ValueError for provider='copilot' in stream mode."""
        mock_stream.return_value = iter([{"type": "done", "usage": {}}])

        # Should not raise
        events = list(
            prompt_llm_stream("Test", provider="copilot", project_dir=PROJECT_DIR)
        )
        assert len(events) == 1


class TestUnsupportedProviderListsAllProviders:
    """Test that unsupported provider error message lists all providers."""

    def test_unsupported_provider_error_lists_all_providers(self) -> None:
        """Error message includes 'copilot', 'claude', 'langchain'."""
        with pytest.raises(ValueError) as exc_info:
            prompt_llm("Test", provider="invalid", project_dir=PROJECT_DIR)

        error_msg = str(exc_info.value)
        assert "copilot" in error_msg
        assert "claude" in error_msg
        assert "langchain" in error_msg

    def test_unsupported_provider_stream_error_lists_all_providers(self) -> None:
        """Stream error message includes 'copilot', 'claude', 'langchain'."""
        with pytest.raises(ValueError) as exc_info:
            list(prompt_llm_stream("Test", provider="invalid", project_dir=PROJECT_DIR))

        error_msg = str(exc_info.value)
        assert "copilot" in error_msg
        assert "claude" in error_msg
        assert "langchain" in error_msg
