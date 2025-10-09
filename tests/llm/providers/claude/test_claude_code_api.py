#!/usr/bin/env python3
"""Tests for claude_code_api module."""

import asyncio
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from claude_code_sdk._errors import CLINotFoundError

from mcp_coder.llm.providers.claude.claude_code_api import (
    ClaudeAPIError,
    _ask_claude_code_api_async,
    _create_claude_client,
    ask_claude_code_api,
    create_api_response_dict,
)


class TestCreateClaudeClient:
    """Test the _create_claude_client function."""

    def test_create_claude_client_basic(self) -> None:
        """Test that _create_claude_client creates basic options WITHOUT preemptive verification."""
        # Use context managers for clearer mock control
        with (
            patch(
                "mcp_coder.llm.providers.claude.claude_code_api.ClaudeCodeOptions"
            ) as mock_options_class,
            patch(
                "mcp_coder.llm.providers.claude.claude_code_api._verify_claude_before_use"
            ) as mock_verify,
        ):

            # Setup
            mock_options = MagicMock()
            mock_options_class.return_value = mock_options

            # Execute
            result = _create_claude_client()

            # Verify
            mock_verify.assert_not_called()
            mock_options_class.assert_called_once_with(env={})
            assert result == mock_options

    def test_create_claude_client_sdk_failure_triggers_verification(self) -> None:
        """Test that SDK failure triggers verification for diagnostics."""
        # Use context managers for clearer mock control
        with (
            patch(
                "mcp_coder.llm.providers.claude.claude_code_api.ClaudeCodeOptions"
            ) as mock_options_class,
            patch(
                "mcp_coder.llm.providers.claude.claude_code_api._verify_claude_before_use"
            ) as mock_verify,
        ):

            # Setup - SDK raises CLINotFoundError
            mock_options_class.side_effect = CLINotFoundError("Claude Code not found")
            mock_verify.return_value = (False, None, "Claude CLI not found")

            # Execute & Verify
            with pytest.raises(
                RuntimeError,
                match="Claude CLI not found during verification: Claude CLI not found",
            ):
                _create_claude_client()

            mock_options_class.assert_called_once()
            mock_verify.assert_called_once()

    def test_create_claude_client_with_env(self) -> None:
        """Test that _create_claude_client passes env WITHOUT preemptive verification."""
        # Use context managers for clearer mock control
        with (
            patch(
                "mcp_coder.llm.providers.claude.claude_code_api.ClaudeCodeOptions"
            ) as mock_options_class,
            patch(
                "mcp_coder.llm.providers.claude.claude_code_api._verify_claude_before_use"
            ) as mock_verify,
        ):

            # Setup
            mock_options = MagicMock()
            mock_options_class.return_value = mock_options
            env_vars = {"MCP_CODER_PROJECT_DIR": "/test/project"}

            # Execute
            result = _create_claude_client(env=env_vars)

            # Verify
            mock_verify.assert_not_called()
            mock_options_class.assert_called_once_with(env=env_vars)
            assert result == mock_options


class TestAskClaudeCodeApiAsync:
    """Test the async _ask_claude_code_api_async function."""

    @pytest.mark.asyncio
    @patch("mcp_coder.llm.providers.claude.claude_code_api.query")
    @patch("mcp_coder.llm.providers.claude.claude_code_api._create_claude_client")
    async def test_multiple_text_blocks_concatenated(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test that multiple TextBlock messages are properly concatenated."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        # Import the real SDK classes to create proper mock objects
        from mcp_coder.llm.providers.claude.claude_code_api import (
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
    @patch("mcp_coder.llm.providers.claude.claude_code_api.query")
    @patch("mcp_coder.llm.providers.claude.claude_code_api._create_claude_client")
    async def test_basic_question_with_assistant_message(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test asking a basic question with proper AssistantMessage types."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        # Import the real SDK classes to create proper mock objects
        from mcp_coder.llm.providers.claude.claude_code_api import (
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
    @patch("mcp_coder.llm.providers.claude.claude_code_api.query")
    @patch("mcp_coder.llm.providers.claude.claude_code_api._create_claude_client")
    async def test_unknown_message_type_ignored(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test that unknown message types are simply ignored."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        # Import the real SDK classes to create proper mock objects
        from mcp_coder.llm.providers.claude.claude_code_api import (
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
    @patch("mcp_coder.llm.providers.claude.claude_code_api.query")
    @patch("mcp_coder.llm.providers.claude.claude_code_api._create_claude_client")
    async def test_timeout_handling(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test that timeout is properly handled."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        async def slow_query_response(*_args: object, **_kwargs: object) -> object:
            await asyncio.sleep(0.6)  # Simulate slow response
            yield MagicMock(text="Too late")

        mock_query.side_effect = slow_query_response

        # Execute & Verify - timeout must be less than sleep time to trigger
        with pytest.raises(subprocess.TimeoutExpired) as exc_info:
            await _ask_claude_code_api_async("test question", timeout=0.3)

        assert "timed out after 0.3 seconds" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("mcp_coder.llm.providers.claude.claude_code_api.query")
    @patch("mcp_coder.llm.providers.claude.claude_code_api._create_claude_client")
    async def test_strips_whitespace(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test that response is stripped of whitespace."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        # Import the real SDK classes to create proper mock objects
        from mcp_coder.llm.providers.claude.claude_code_api import (
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
    """Test the synchronous ask_claude_code_api function (legacy tests for old string return)."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync"
    )
    def test_basic_question(self, mock_detailed_sync: MagicMock) -> None:
        """Test asking a basic question returns LLMResponseDict."""
        # Setup - mock the detailed sync function
        mock_detailed_sync.return_value = {
            "text": "Test response",
            "session_info": {"session_id": "test-123"},
            "result_info": {},
            "raw_messages": [],
        }

        # Execute
        result = ask_claude_code_api("test question", timeout=60)

        # Verify - now returns dict, not string
        assert isinstance(result, dict)
        assert result["text"] == "Test response"
        mock_detailed_sync.assert_called_once_with("test question", 60, None, None)

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync"
    )
    def test_timeout_exception_passthrough(self, mock_detailed_sync: MagicMock) -> None:
        """Test that TimeoutExpired exceptions are passed through."""
        # Setup
        timeout_error = subprocess.TimeoutExpired(
            ["claude-code-sdk", "query"], 30, "Timeout"
        )
        mock_detailed_sync.side_effect = timeout_error

        # Execute & Verify
        with pytest.raises(subprocess.TimeoutExpired):
            ask_claude_code_api("test question")

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync"
    )
    def test_other_exception_conversion(self, mock_detailed_sync: MagicMock) -> None:
        """Test that other exceptions are converted to ClaudeAPIError."""
        # Setup - use RuntimeError
        original_error = RuntimeError("Some SDK error")
        mock_detailed_sync.side_effect = original_error

        # Execute & Verify
        with pytest.raises(ClaudeAPIError) as exc_info:
            ask_claude_code_api("test question")

        error_msg = str(exc_info.value)
        assert "Claude API Error" in error_msg
        assert exc_info.value.__cause__ == original_error

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync"
    )
    def test_ask_claude_code_api_with_env_vars(
        self, mock_detailed_sync: MagicMock
    ) -> None:
        """Test that env_vars are passed through to detailed_sync."""
        # Setup
        mock_detailed_sync.return_value = {
            "text": "Response with env",
            "session_info": {"session_id": "env-test"},
            "result_info": {},
            "raw_messages": [],
        }

        env_vars = {"MCP_CODER_PROJECT_DIR": "/test/project"}

        # Execute
        result = ask_claude_code_api("test question", env_vars=env_vars)

        # Verify
        assert result["text"] == "Response with env"
        mock_detailed_sync.assert_called_once_with(
            "test question", 30.0, None, env_vars
        )


# Note: ImportError tests removed since claude-code-sdk is now a required dependency
# Any import errors will occur at module load time if the dependency is missing


class TestCreateApiResponseDict:
    """Test the create_api_response_dict helper function."""

    def test_create_api_response_dict_structure(self) -> None:
        """Test API response dict creation with all required fields."""
        detailed = {
            "text": "API response",
            "session_info": {"session_id": "api-123", "model": "claude-sonnet-4"},
            "result_info": {"cost_usd": 0.058, "duration_ms": 2801},
            "raw_messages": [],
        }

        result = create_api_response_dict("API response", "api-123", detailed)

        assert result["text"] == "API response"
        assert result["session_id"] == "api-123"
        assert result["method"] == "api"
        assert result["provider"] == "claude"
        assert "version" in result
        assert "timestamp" in result
        assert result["raw_response"]["session_info"]["session_id"] == "api-123"  # type: ignore[index]
        assert result["raw_response"]["result_info"]["cost_usd"] == 0.058  # type: ignore[index]

    def test_create_api_response_dict_none_session(self) -> None:
        """Test API response dict creation with None session_id."""
        detailed = {
            "text": "Response without session",
            "session_info": {},
            "result_info": {},
            "raw_messages": [],
        }

        result = create_api_response_dict("Response without session", None, detailed)

        assert result["session_id"] is None
        assert result["text"] == "Response without session"


class TestAskClaudeCodeApiTypedDict:
    """Test ask_claude_code_api returns LLMResponseDict."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync"
    )
    def test_ask_claude_code_api_returns_typed_dict(
        self, mock_detailed_sync: MagicMock
    ) -> None:
        """Test that API method returns complete LLMResponseDict."""
        mock_detailed_sync.return_value = {
            "text": "Test response",
            "session_info": {"session_id": "test-123", "model": "claude-sonnet-4"},
            "result_info": {"cost_usd": 0.05, "duration_ms": 1500},
            "raw_messages": [],
        }

        result = ask_claude_code_api("Test question")

        # Check all required fields
        assert isinstance(result, dict)
        required_fields = [
            "version",
            "timestamp",
            "text",
            "session_id",
            "method",
            "provider",
            "raw_response",
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Verify content
        assert result["text"] == "Test response"
        assert result["method"] == "api"
        assert result["provider"] == "claude"

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_api.ask_claude_code_api_detailed_sync"
    )
    def test_ask_claude_code_api_extracts_session_from_detailed(
        self, mock_detailed_sync: MagicMock
    ) -> None:
        """Test session_id extraction from detailed response."""
        mock_detailed_sync.return_value = {
            "text": "Response text",
            "session_info": {
                "session_id": "extracted-session",
                "model": "claude",
            },
            "result_info": {"cost_usd": 0.05},
            "raw_messages": [],
        }

        result = ask_claude_code_api("Test")

        assert result["session_id"] == "extracted-session"
        assert (
            result["raw_response"]["session_info"]["session_id"]  # type: ignore[index]
            == "extracted-session"
        )


class TestAskClaudeCodeApiDetailed:
    """Test ask_claude_code_api_detailed and detailed_sync with env_vars."""

    @pytest.mark.asyncio
    @patch("mcp_coder.llm.providers.claude.claude_code_api.query")
    @patch("mcp_coder.llm.providers.claude.claude_code_api._create_claude_client")
    async def test_ask_claude_code_api_detailed_with_env_vars(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test that env_vars are passed to _create_claude_client in detailed."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        from mcp_coder.llm.providers.claude.claude_code_api import (
            AssistantMessage,
            TextBlock,
            ask_claude_code_api_detailed,
        )

        mock_text_block = MagicMock(spec=TextBlock)
        mock_text_block.text = "Response"
        mock_message = MagicMock(spec=AssistantMessage)
        mock_message.content = [mock_text_block]

        async def mock_query_response(*_args: object, **_kwargs: object) -> object:
            yield mock_message

        mock_query.side_effect = mock_query_response

        env_vars = {"MCP_CODER_PROJECT_DIR": "/test/project"}

        # Execute
        result = await ask_claude_code_api_detailed(
            "test question", timeout=30.0, env_vars=env_vars
        )

        # Verify
        assert result["text"] == "Response"
        mock_create_client.assert_called_once_with(None, env=env_vars)


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
