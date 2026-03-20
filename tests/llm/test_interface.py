"""Tests for the high-level LLM interface."""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.interface import ask_llm, prompt_llm
from mcp_coder.utils.subprocess_runner import TimeoutExpired


class TestAskLLM:
    """Test the main ask_llm function."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_ask_llm_routes_to_claude_code(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that ask_llm routes to ask_claude_code_cli for claude provider."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Test response from Claude",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = ask_llm("Test question", provider="claude", timeout=30)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
        )
        assert result == "Test response from Claude"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_ask_llm_default_parameters(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that ask_llm uses correct default parameters."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Default response",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = ask_llm("Test question")

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
        )
        assert result == "Default response"

    def test_ask_llm_unsupported_provider(self) -> None:
        """Test that ask_llm raises ValueError for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported provider: gpt"):
            ask_llm("Test question", provider="gpt")

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_ask_llm_passes_through_exceptions(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that ask_llm passes through exceptions from underlying implementations."""
        mock_ask_claude_code_cli.side_effect = RuntimeError("Claude error")

        with pytest.raises(RuntimeError, match="Claude error"):
            ask_llm("Test question", provider="claude")

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_ask_llm_custom_timeout(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """Test that ask_llm passes through custom timeout."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Timeout response",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = ask_llm("Test question", timeout=60)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=60,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
        )
        assert result == "Timeout response"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_ask_llm_with_session_id(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """Test that session_id is passed through to ask_claude_code_cli."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with session",
            "session_id": "test-session-123",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = ask_llm(
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
        )
        assert result == "Response with session"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_ask_llm_without_session_id(
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

        # Should work without session_id (backward compatible)
        result = ask_llm("Test question")

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
        )
        assert result == "Response without session"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_ask_llm_returns_string_only(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that ask_llm returns string, not dict."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Just the text",
            "session_id": "some-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        response = ask_llm("Test", session_id="some-session")

        # Should return string only
        assert isinstance(response, str)
        assert response == "Just the text"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_ask_llm_with_env_vars(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """Test that ask_llm passes env_vars to ask_claude_code_cli."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Response with env vars",
            "session_id": "test-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }
        test_env_vars = {"VAR1": "value1", "VAR2": "value2"}

        result = ask_llm(
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
        )
        assert result == "Response with env vars"

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_ask_llm_timeout_expired_logged_and_reraised(
        self, mock_ask_claude_code_cli: MagicMock
    ) -> None:
        """Test that TimeoutExpired is re-raised as-is (not wrapped) from ask_llm."""
        mock_ask_claude_code_cli.side_effect = TimeoutExpired(cmd="claude", timeout=30)

        with pytest.raises(TimeoutExpired):
            ask_llm("Test question", provider="claude", timeout=30)

    @patch("mcp_coder.llm.providers.langchain.ask_langchain")
    def test_ask_llm_asyncio_timeout_reraised_for_langchain(
        self, mock_ask_langchain: MagicMock
    ) -> None:
        """asyncio.TimeoutError from langchain provider is re-raised."""
        mock_ask_langchain.side_effect = asyncio.TimeoutError()

        with pytest.raises(asyncio.TimeoutError):
            ask_llm("Test question", provider="langchain", timeout=30)


class TestAskLLMExecutionDir:
    """Tests for execution_dir parameter in ask_llm."""

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

        result = ask_llm(
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
        )
        assert result == "Response with execution_dir"

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

        result = ask_llm("Test question", execution_dir=None)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Test question",
            session_id=None,
            timeout=30,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
        )
        assert result == "Response with default dir"

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

        result = ask_llm(
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
        )
        assert result == "Response with absolute path"


class TestIntegration:
    """Integration tests for the full routing chain."""

    @patch("mcp_coder.llm.interface.ask_claude_code_cli")
    def test_full_routing_chain(self, mock_ask_claude_code_cli: MagicMock) -> None:
        """Test the full routing chain from ask_llm to ask_claude_code_cli."""
        mock_ask_claude_code_cli.return_value = {
            "text": "Full chain response",
            "session_id": "chain-session",
            "version": "1.0",
            "timestamp": "2025-10-01T10:30:00",
            "provider": "claude",
            "raw_response": {},
        }

        result = ask_llm("Integration test question", provider="claude", timeout=25)

        mock_ask_claude_code_cli.assert_called_once_with(
            "Integration test question",
            session_id=None,
            timeout=25,
            env_vars=None,
            cwd=None,
            mcp_config=None,
            branch_name=None,
        )
        assert result == "Full chain response"

    def test_parameter_validation_propagation(self) -> None:
        """Test that parameter validation errors propagate correctly."""
        # Test invalid provider
        with pytest.raises(ValueError, match="Unsupported provider"):
            ask_llm("Test", provider="invalid")

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

        result = ask_llm(
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
        )
        assert result["text"] == "Response with default execution dir"


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

    def test_ask_llm_delegates_to_prompt_llm_for_langchain(self) -> None:
        """ask_llm with provider='langchain' also routes correctly."""
        expected = self._make_langchain_response()
        with patch(
            "mcp_coder.llm.providers.langchain.ask_langchain",
            return_value=expected,
        ):
            from mcp_coder.llm.interface import ask_llm

            result = ask_llm("Hello", provider="langchain")
        assert result == "langchain reply"
