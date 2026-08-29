#!/usr/bin/env python3
"""Tests for input validation across all LLM interface functions."""

from typing import Any, Callable

import pytest

from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.providers.claude.claude_code_cli import ask_claude_code_cli

# prompt_llm requires a keyword-only project_dir, while ask_claude_code_cli names
# the same concept cwd - so the extra kwargs travel with each function.
VALIDATION_TARGETS = [
    ("prompt_llm", prompt_llm, {"project_dir": "."}),
    ("ask_claude_code_cli", ask_claude_code_cli, {"cwd": "."}),
]


class TestInputValidation:
    """Test input validation for all public functions."""

    @pytest.mark.parametrize("_function_name,function,extra_kwargs", VALIDATION_TARGETS)
    def test_empty_question_raises_error(
        self,
        _function_name: str,
        function: Callable[..., Any],
        extra_kwargs: dict[str, Any],
    ) -> None:
        """Test that empty questions raise ValueError."""
        with pytest.raises(
            ValueError, match="Question cannot be empty or whitespace only"
        ):
            function("", **extra_kwargs)

    @pytest.mark.parametrize("_function_name,function,extra_kwargs", VALIDATION_TARGETS)
    def test_whitespace_only_question_raises_error(
        self,
        _function_name: str,
        function: Callable[..., Any],
        extra_kwargs: dict[str, Any],
    ) -> None:
        """Test that whitespace-only questions raise ValueError."""
        with pytest.raises(
            ValueError, match="Question cannot be empty or whitespace only"
        ):
            function("   \n\t  ", **extra_kwargs)

    @pytest.mark.parametrize("_function_name,function,extra_kwargs", VALIDATION_TARGETS)
    def test_zero_timeout_raises_error(
        self,
        _function_name: str,
        function: Callable[..., Any],
        extra_kwargs: dict[str, Any],
    ) -> None:
        """Test that zero timeout raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be a positive number"):
            function("test question", timeout=0, **extra_kwargs)

    @pytest.mark.parametrize("_function_name,function,extra_kwargs", VALIDATION_TARGETS)
    def test_negative_timeout_raises_error(
        self,
        _function_name: str,
        function: Callable[..., Any],
        extra_kwargs: dict[str, Any],
    ) -> None:
        """Test that negative timeout raises ValueError."""
        with pytest.raises(ValueError, match="Timeout must be a positive number"):
            function("test question", timeout=-1, **extra_kwargs)

    def test_prompt_llm_invalid_provider_raises_error(self) -> None:
        """Test that invalid provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider: invalid"):
            prompt_llm("test question", provider="invalid", project_dir=".")
