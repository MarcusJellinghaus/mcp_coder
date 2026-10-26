import asyncio
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import LLMTimeoutError, prompt_llm
from mcp_coder.utils.subprocess_runner import TimeoutExpired
from tests.llm.test_interface import PROJECT_DIR


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
        mock_ask_langchain.side_effect = TimeoutError()

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
        mock_ask_langchain.side_effect = TimeoutError()

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
        mock_ask_langchain.side_effect = TimeoutError()

        with pytest.raises(LLMTimeoutError):
            prompt_llm(
                "Test question",
                provider="langchain",
                timeout=30,
                project_dir=PROJECT_DIR,
            )
