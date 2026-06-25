"""Tests for the Claude provider error types."""

import pytest

from mcp_coder.llm.providers.claude.errors import ClaudeAPIError


def test_claude_api_error_is_exception() -> None:
    assert issubclass(ClaudeAPIError, Exception)


def test_claude_api_error_raises_with_message() -> None:
    with pytest.raises(ClaudeAPIError, match="boom"):
        raise ClaudeAPIError("boom")
