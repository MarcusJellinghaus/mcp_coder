#!/usr/bin/env python3
"""Tests for claude_code_api module."""

import asyncio
import platform
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.llm_providers.claude.claude_code_api import (
    ClaudeAPIError,
    _ask_claude_code_api_async,
    _create_claude_client,
    ask_claude_code_api,
)


class TestCreateClaudeClient:
    """Test the _create_claude_client function."""

    @patch("mcp_coder.llm_providers.claude.claude_code_api.ClaudeCodeOptions")
    def test_create_claude_client_basic(self, mock_options_class: MagicMock) -> None:
        """Test that _create_claude_client creates basic options."""
        # Mock verification function - required on Linux/CI, helpful for isolation on Windows
        with patch(
            "mcp_coder.llm_providers.claude.claude_code_api._verify_claude_before_use"
        ) as mock_verify:
            # Use platform-appropriate mock paths
            if platform.system() == "Windows":
                mock_path = "C:\\Users\\user\\.local\\bin\\claude.exe"
            else:
                mock_path = "/usr/local/bin/claude"

            mock_verify.return_value = (True, mock_path, None)

            mock_options = MagicMock()
            mock_options_class.return_value = mock_options

            result = _create_claude_client()

            mock_verify.assert_called_once()
            mock_options_class.assert_called_once_with()
            assert result == mock_options

    @patch("mcp_coder.llm_providers.claude.claude_code_api._verify_claude_before_use")
    def test_create_claude_client_verification_fails(
        self, mock_verify: MagicMock
    ) -> None:
        """Test that _create_claude_client raises RuntimeError when verification fails."""
        # Mock failed verification
        mock_verify.return_value = (False, None, "Claude CLI not found")

        with pytest.raises(
            RuntimeError, match="Claude CLI verification failed: Claude CLI not found"
        ):
            _create_claude_client()

        mock_verify.assert_called_once()


class TestAskClaudeCodeApiAsync:
    """Test the async _ask_claude_code_api_async function."""

    @pytest.mark.asyncio
    @patch("mcp_coder.llm_providers.claude.claude_code_api.query")
    @patch("mcp_coder.llm_providers.claude.claude_code_api._create_claude_client")
    async def test_multiple_text_blocks_concatenated(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test that multiple TextBlock messages are properly concatenated."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        # Import the real SDK classes to create proper mock objects
        from mcp_coder.llm_providers.claude.claude_code_api import (
            AssistantMessage,
            TextBlock,
        )

        # Create proper mock objects that will pass isinstance checks
        mock_text_block1 = MagicMock(spec=TextBlock)
        mock_text_block1.text = "Hello, "
        mock_text_block2 = MagicMock(spec=TextBlock)
        mock_text_block2.text = "world!"

        mock_message1 = MagicMock(spec=AssistantMessage)
        mock_message1.content = [mock_text_block1]
        mock_message2 = MagicMock(spec=AssistantMessage)
        mock_message2.content = [mock_text_block2]

        async def mock_query_response(*_args: object, **_kwargs: object) -> object:
            yield mock_message1
            yield mock_message2

        mock_query.side_effect = mock_query_response

        # Execute
        result = await _ask_claude_code_api_async("test question")

        # Verify
        assert result == "Hello, world!"
        mock_create_client.assert_called_once()
        mock_query.assert_called_once_with(prompt="test question", options=mock_options)

    @pytest.mark.asyncio
    @patch("mcp_coder.llm_providers.claude.claude_code_api.query")
    @patch("mcp_coder.llm_providers.claude.claude_code_api._create_claude_client")
    async def test_basic_question_with_assistant_message(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test asking a basic question with proper AssistantMessage types."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        # Import the real SDK classes to create proper mock objects
        from mcp_coder.llm_providers.claude.claude_code_api import (
            AssistantMessage,
            TextBlock,
        )

        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = "Response from TextBlock"

        mock_message = MagicMock(spec=AssistantMessage)
        mock_message.content = [mock_text_block]

        async def mock_query_response(*_args: object, **_kwargs: object) -> object:
            yield mock_message

        mock_query.side_effect = mock_query_response

        # Execute
        result = await _ask_claude_code_api_async("test question")

        # Verify
        assert result == "Response from TextBlock"

    @pytest.mark.asyncio
    @patch("mcp_coder.llm_providers.claude.claude_code_api.query")
    @patch("mcp_coder.llm_providers.claude.claude_code_api._create_claude_client")
    async def test_unknown_message_type_ignored(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test that unknown message types are simply ignored."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        # Import the real SDK classes to create proper mock objects
        from mcp_coder.llm_providers.claude.claude_code_api import (
            AssistantMessage,
            TextBlock,
        )

        # Create a message that doesn't match any known types
        mock_unknown_message = MagicMock()
        mock_unknown_message.some_attribute = "unknown"

        # Create a proper AssistantMessage that will pass isinstance checks
        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = "Real response"

        mock_assistant_message = MagicMock(spec=AssistantMessage)
        mock_assistant_message.content = [mock_text_block]

        async def mock_query_response(*_args: object, **_kwargs: object) -> object:
            yield mock_unknown_message  # This should be ignored
            yield mock_assistant_message  # This should be processed

        mock_query.side_effect = mock_query_response

        # Execute
        result = await _ask_claude_code_api_async("test question")

        # Verify - should only get response from the AssistantMessage
        assert result == "Real response"

    @pytest.mark.asyncio
    @patch("mcp_coder.llm_providers.claude.claude_code_api.query")
    @patch("mcp_coder.llm_providers.claude.claude_code_api._create_claude_client")
    async def test_timeout_handling(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test that timeout is properly handled."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        async def slow_query_response(*_args: object, **_kwargs: object) -> object:
            await asyncio.sleep(2)  # Simulate slow response
            yield MagicMock(text="Too late")

        mock_query.side_effect = slow_query_response

        # Execute & Verify
        with pytest.raises(subprocess.TimeoutExpired) as exc_info:
            await _ask_claude_code_api_async("test question", timeout=1)

        assert "timed out after 1 seconds" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("mcp_coder.llm_providers.claude.claude_code_api.query")
    @patch("mcp_coder.llm_providers.claude.claude_code_api._create_claude_client")
    async def test_strips_whitespace(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test that response is stripped of whitespace."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        # Import the real SDK classes to create proper mock objects
        from mcp_coder.llm_providers.claude.claude_code_api import (
            AssistantMessage,
            TextBlock,
        )

        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = "  \n  Response with whitespace  \n  "

        mock_message = MagicMock(spec=AssistantMessage)
        mock_message.content = [mock_text_block]

        async def mock_query_response(*_args: object, **_kwargs: object) -> object:
            yield mock_message

        mock_query.side_effect = mock_query_response

        # Execute
        result = await _ask_claude_code_api_async("test question")

        # Verify
        assert result == "Response with whitespace"


class TestAskClaudeCodeApi:
    """Test the synchronous ask_claude_code_api function."""

    @patch("mcp_coder.llm_providers.claude.claude_code_api.asyncio.run")
    def test_basic_question(self, mock_asyncio_run: MagicMock) -> None:
        """Test asking a basic question."""
        # Setup
        mock_asyncio_run.return_value = "Test response"

        # Execute
        result = ask_claude_code_api("test question", timeout=60)

        # Verify
        assert result == "Test response"
        mock_asyncio_run.assert_called_once()
        # The actual async function call is passed to asyncio.run
        args, _ = mock_asyncio_run.call_args
        assert len(args) == 1  # One positional argument (the coroutine)

    @patch("mcp_coder.llm_providers.claude.claude_code_api.asyncio.run")
    def test_timeout_exception_passthrough(self, mock_asyncio_run: MagicMock) -> None:
        """Test that TimeoutExpired exceptions are passed through."""
        # Setup
        timeout_error = subprocess.TimeoutExpired(
            ["claude-code-sdk", "query"], 30, "Timeout"
        )
        mock_asyncio_run.side_effect = timeout_error

        # Execute & Verify
        with pytest.raises(subprocess.TimeoutExpired):
            ask_claude_code_api("test question")

    @patch("mcp_coder.llm_providers.claude.claude_code_api.asyncio.run")
    def test_other_exception_conversion(self, mock_asyncio_run: MagicMock) -> None:
        """Test that other exceptions (non-ValueError, non-TimeoutExpired) are converted to ClaudeAPIError."""
        # Setup - use RuntimeError instead of ValueError since ValueError is now re-raised
        original_error = RuntimeError("Some SDK error")
        mock_asyncio_run.side_effect = original_error

        # Execute & Verify
        with pytest.raises(ClaudeAPIError) as exc_info:
            ask_claude_code_api("test question")

        error_msg = str(exc_info.value)
        assert "Some SDK error" in error_msg
        assert exc_info.value.__cause__ == original_error


# Note: ImportError tests removed since claude-code-sdk is now a required dependency
# Any import errors will occur at module load time if the dependency is missing


@pytest.mark.claude_api_integration
class TestClaudeCodeApiIntegration:
    """Integration tests for the Claude Code API implementation."""

    def test_api_method_available(self) -> None:
        """Test that the API implementation can be imported and called."""
        # This is a minimal integration test that doesn't require actual SDK
        # It just verifies the module structure is correct
        assert callable(ask_claude_code_api)
        print("✓ ask_claude_code_api function is callable")

        # Also verify helper function is available
        assert callable(_create_claude_client)
        print("✓ _create_claude_client helper function is callable")
