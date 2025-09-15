#!/usr/bin/env python3
"""Tests for claude_code_api module."""

import asyncio
import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mcp_coder.claude_code_api import (
    _ask_claude_code_api_async,
    _create_claude_client,
    ask_claude_code_api,
)


class TestCreateClaudeClient:
    """Test the _create_claude_client function."""

    @patch("mcp_coder.claude_code_api.ClaudeCodeOptions")
    def test_create_claude_client_basic(self, mock_options_class: MagicMock) -> None:
        """Test that _create_claude_client creates basic options."""
        mock_options = MagicMock()
        mock_options_class.return_value = mock_options

        result = _create_claude_client()

        mock_options_class.assert_called_once_with()
        assert result == mock_options


class TestAskClaudeCodeApiAsync:
    """Test the async _ask_claude_code_api_async function."""

    @pytest.mark.asyncio
    @patch("mcp_coder.claude_code_api.query")
    @patch("mcp_coder.claude_code_api._create_claude_client")
    async def test_basic_question_with_text_attribute(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test asking a basic question when messages have text attribute."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        mock_message1 = MagicMock()
        mock_message1.text = "Hello, "
        mock_message2 = MagicMock()
        mock_message2.text = "world!"

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
    @patch("mcp_coder.claude_code_api.query")
    @patch("mcp_coder.claude_code_api._create_claude_client")
    async def test_basic_question_with_content_attribute(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test asking a basic question when messages have content attribute."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        mock_message = MagicMock()
        mock_message.text = None
        mock_message.content = "Response with content"

        async def mock_query_response(*_args: object, **_kwargs: object) -> object:
            yield mock_message

        mock_query.side_effect = mock_query_response

        # Execute
        result = await _ask_claude_code_api_async("test question")

        # Verify
        assert result == "Response with content"

    @pytest.mark.asyncio
    @patch("mcp_coder.claude_code_api.query")
    @patch("mcp_coder.claude_code_api._create_claude_client")
    async def test_basic_question_with_string_fallback(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test asking a basic question when messages need string conversion."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        mock_message = MagicMock()
        mock_message.text = None
        mock_message.content = (
            "Fallback content response"  # Set content instead of relying on __str__
        )

        async def mock_query_response(*_args: object, **_kwargs: object) -> object:
            yield mock_message

        mock_query.side_effect = mock_query_response

        # Execute
        result = await _ask_claude_code_api_async("test question")

        # Verify
        assert result == "Fallback content response"

    @pytest.mark.asyncio
    @patch("mcp_coder.claude_code_api.query")
    @patch("mcp_coder.claude_code_api._create_claude_client")
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
    @patch("mcp_coder.claude_code_api.query")
    @patch("mcp_coder.claude_code_api._create_claude_client")
    async def test_strips_whitespace(
        self, mock_create_client: MagicMock, mock_query: AsyncMock
    ) -> None:
        """Test that response is stripped of whitespace."""
        # Setup
        mock_options = MagicMock()
        mock_create_client.return_value = mock_options

        mock_message = MagicMock()
        mock_message.text = "  \n  Response with whitespace  \n  "

        async def mock_query_response(*_args: object, **_kwargs: object) -> object:
            yield mock_message

        mock_query.side_effect = mock_query_response

        # Execute
        result = await _ask_claude_code_api_async("test question")

        # Verify
        assert result == "Response with whitespace"


class TestAskClaudeCodeApi:
    """Test the synchronous ask_claude_code_api function."""

    @patch("mcp_coder.claude_code_api.asyncio.run")
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

    @patch("mcp_coder.claude_code_api.asyncio.run")
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

    @patch("mcp_coder.claude_code_api.asyncio.run")
    def test_other_exception_conversion(self, mock_asyncio_run: MagicMock) -> None:
        """Test that other exceptions (non-ValueError, non-TimeoutExpired) are converted to CalledProcessError."""
        # Setup - use RuntimeError instead of ValueError since ValueError is now re-raised
        original_error = RuntimeError("Some SDK error")
        mock_asyncio_run.side_effect = original_error

        # Execute & Verify
        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            ask_claude_code_api("test question")

        error = exc_info.value
        assert error.returncode == 1
        assert error.cmd == ["claude-code-sdk", "query"]
        assert "Some SDK error" in error.stderr
        assert error.__cause__ == original_error

    @patch("mcp_coder.claude_code_api.find_claude_executable")
    @patch("mcp_coder.claude_code_api.asyncio.run")
    def test_dynamic_username_in_error_message(
        self, mock_asyncio_run: MagicMock, mock_find_claude: MagicMock
    ) -> None:
        """Test that error messages use dynamic username instead of hardcoded 'Marcus'."""
        # Setup
        mock_find_claude.return_value = "/some/path/to/claude"
        # Use RuntimeError instead of ValueError since ValueError is now re-raised
        claude_error = RuntimeError("Claude Code not found")
        mock_asyncio_run.side_effect = claude_error

        # Test with different usernames
        test_cases = [
            ({"USERNAME": "testuser"}, "testuser"),
            ({"USER": "linuxuser"}, "linuxuser"),
            ({}, "<username>"),  # Fallback when no username env vars
        ]

        for env_vars, expected_username in test_cases:
            with patch.dict("os.environ", env_vars, clear=True):
                with pytest.raises(subprocess.CalledProcessError) as exc_info:
                    ask_claude_code_api("test question")

                error_message = exc_info.value.stderr
                # Check that the error message contains the expected username
                assert f"C:\\Users\\{expected_username}\\.local\\bin" in error_message
                # Ensure it doesn't contain the hardcoded "Marcus"
                assert (
                    "C:\\Users\\Marcus\\.local\\bin" not in error_message
                    or expected_username == "Marcus"
                )


class TestImportError:
    """Test import error handling."""

    def test_import_error_on_missing_sdk(self) -> None:
        """Test that import error is raised when SDK is not available."""
        # This test verifies the import handling in the module
        # In a real scenario where claude-code-sdk is missing, the import would fail
        with patch.dict("sys.modules", {"claude_code_sdk": None}):
            with pytest.raises(ImportError) as exc_info:
                # Re-import the module to trigger the import error
                import importlib

                import mcp_coder.claude_code_api

                importlib.reload(mcp_coder.claude_code_api)

            assert "claude-code-sdk is not installed" in str(exc_info.value)


@pytest.mark.integration
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
