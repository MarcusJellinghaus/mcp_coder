#!/usr/bin/env python3
"""Tests for input validation across all LLM interface functions."""

from typing import Any, Callable

import pytest

from mcp_coder.llm.interface import ask_llm
from mcp_coder.llm.providers.claude.claude_code_api import (
    ask_claude_code_api,
    ask_claude_code_api_detailed_sync,
)
from mcp_coder.llm.providers.claude.claude_code_cli import ask_claude_code_cli
from mcp_coder.llm.providers.claude.claude_code_interface import ask_claude_code


class TestInputValidation:
    """Test input validation for all public functions."""

    @pytest.mark.parametrize(
        "_function_name,function",
        [
            ("ask_llm", ask_llm),
            ("ask_claude_code", ask_claude_code),
            ("ask_claude_code_cli", ask_claude_code_cli),
            ("ask_claude_code_api", ask_claude_code_api),
            ("ask_claude_code_api_detailed_sync", ask_claude_code_api_detailed_sync),
        ],
    )
    def test_empty_question_raises_error(
        self, _function_name: str, function: Callable[..., Any]
    ) -> None:
        """Test that empty questions raise ValueError."""
        with pytest.raises(
            ValueError, match="Question cannot be empty or whitespace only"
        ):
            function("")

    @pytest.mark.parametrize(
        "_function_name,function",
        [
            ("ask_llm", ask_llm),
            ("ask_claude_code", ask_claude_code),
            ("ask_claude_code_cli", ask_claude_code_cli),
            ("ask_claude_code_api", ask_claude_code_api),
            ("ask_claude_code_api_detailed_sync", ask_claude_code_api_detailed_sync),
        ],
    )
    def test_whitespace_only_question_raises_error(
        self, _function_name: str, function: Callable[..., Any]
    ) -> None:
        """Test that whitespace-only questions raise ValueError."""
        with pytest.raises(
            ValueError, match="Question cannot be empty or whitespace only"
        ):
            function("   \n\t  ")

    @pytest.mark.parametrize(
        "_function_name,function",
        [
            ("ask_llm", ask_llm),
            ("ask_claude_code", ask_claude_code),
            ("ask_claude_code_cli", ask_claude_code_cli),
            ("ask_claude_code_api", ask_claude_code_api),
            ("ask_claude_code_api_detailed_sync", ask_claude_code_api_detailed_sync),
        ],
    )
    def test_zero_timeout_raises_error(
        self, _function_name: str, function: Callable[..., Any]
    ) -> None:
        """Test that zero timeout raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be a positive number"):
            function("test question", timeout=0)

    @pytest.mark.parametrize(
        "_function_name,function",
        [
            ("ask_llm", ask_llm),
            ("ask_claude_code", ask_claude_code),
            ("ask_claude_code_cli", ask_claude_code_cli),
            ("ask_claude_code_api", ask_claude_code_api),
            ("ask_claude_code_api_detailed_sync", ask_claude_code_api_detailed_sync),
        ],
    )
    def test_negative_timeout_raises_error(
        self, _function_name: str, function: Callable[..., Any]
    ) -> None:
        """Test that negative timeout raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be a positive number"):
            function("test question", timeout=-1)

    def test_ask_llm_invalid_provider_raises_error(self) -> None:
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider: invalid"):
            ask_llm("test question", provider="invalid")

    def test_ask_claude_code_invalid_method_raises_error(self) -> None:
        """Test that invalid method raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported method: invalid"):
            ask_claude_code("test question", method="invalid")

    def test_ask_llm_invalid_method_raises_error(self) -> None:
        """Test that invalid method in ask_llm raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported method: invalid"):
            ask_llm("test question", method="invalid")
