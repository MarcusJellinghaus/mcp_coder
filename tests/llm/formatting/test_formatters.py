"""Tests for response formatting functions."""

import argparse
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt


def _make_llm_response(
    raw_response: Dict[str, Any], text: str = "Response text."
) -> Dict[str, Any]:
    """Build a minimal LLMResponseDict wrapping the given raw_response."""
    return {
        "text": text,
        "session_id": raw_response.get("session_info", {}).get("session_id"),
        "version": "1.0",
        "timestamp": "2024-01-01T00:00:00",
        "method": "api",
        "provider": "claude",
        "raw_response": raw_response,
    }


class TestFormatVerboseResponse:
    """Tests for verbose response formatting via CLI."""

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_verbose_output(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test verbose output format with detailed tool interactions and metrics."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        raw = {
            "session_info": {
                "session_id": "verbose-session-456",
                "model": "claude-sonnet-4",
                "tools": ["file_reader", "file_writer", "code_executor"],
                "mcp_servers": [
                    {"name": "fs_server", "status": "connected"},
                    {"name": "code_server", "status": "connected"},
                ],
            },
            "result_info": {
                "duration_ms": 2340,
                "cost_usd": 0.0456,
                "usage": {"input_tokens": 25, "output_tokens": 18},
            },
            "raw_messages": [
                {"role": "user", "content": "How do I create a file?"},
                {
                    "role": "assistant",
                    "content": "Here's how to create a file with Python.",
                    "tool_calls": [
                        {
                            "name": "file_writer",
                            "parameters": {
                                "filename": "example.py",
                                "content": "print('hello')",
                            },
                        }
                    ],
                },
            ],
        }
        mock_prompt_llm.return_value = _make_llm_response(
            raw, text="Here's how to create a file with Python."
        )

        args = argparse.Namespace(prompt="How do I create a file?", verbosity="verbose")

        result = execute_prompt(args)

        assert result == 0

        captured = capsys.readouterr()
        captured_out: str = captured.out or ""

        assert "file_writer" in captured_out
        assert "example.py" in captured_out
        assert "2340" in captured_out or "2.34" in captured_out
        assert "0.0456" in captured_out
        assert "25" in captured_out
        assert "18" in captured_out
        assert "verbose-session-456" in captured_out
        assert "claude-sonnet-4" in captured_out
        assert "fs_server" in captured_out
        assert "connected" in captured_out


class TestFormatRawResponse:
    """Tests for raw response formatting via CLI."""

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_raw_output(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test raw output format with complete debug output including JSON structures."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        raw = {
            "session_info": {
                "session_id": "raw-debug-session-999",
                "model": "claude-sonnet-4",
                "tools": ["file_system", "code_analyzer", "debug_tool"],
                "mcp_servers": [
                    {"name": "fs_mcp", "status": "connected", "version": "1.0.0"},
                    {"name": "debug_mcp", "status": "connected", "version": "2.1.0"},
                ],
            },
            "result_info": {
                "duration_ms": 3450,
                "cost_usd": 0.0789,
                "usage": {"input_tokens": 42, "output_tokens": 28},
                "api_version": "2024-03-01",
            },
            "raw_messages": [
                {"role": "user", "content": "Debug this system"},
                {
                    "role": "assistant",
                    "content": "Here's the complete debugging information.",
                    "tool_calls": [
                        {
                            "id": "tool_call_123",
                            "name": "file_system",
                            "parameters": {
                                "action": "read",
                                "path": "/debug/logs.txt",
                                "options": {"encoding": "utf-8"},
                            },
                        }
                    ],
                },
            ],
            "api_metadata": {
                "request_id": "req_abc123xyz789",
                "endpoint": "https://api.anthropic.com/v1/messages",
                "headers": {"x-api-version": "2024-03-01"},
            },
        }
        mock_prompt_llm.return_value = _make_llm_response(
            raw, text="Here's the complete debugging information."
        )

        args = argparse.Namespace(prompt="Debug this system", verbosity="raw")

        result = execute_prompt(args)

        assert result == 0

        captured = capsys.readouterr()
        captured_out: str = captured.out or ""

        assert "Here's the complete debugging information." in captured_out
        assert "3450" in captured_out or "3.45" in captured_out
        assert "0.0789" in captured_out
        assert "42" in captured_out
        assert "28" in captured_out
        assert "raw-debug-session-999" in captured_out
        assert "claude-sonnet-4" in captured_out
        assert "fs_mcp" in captured_out
        assert "debug_mcp" in captured_out
        assert "connected" in captured_out
        assert "file_system" in captured_out
        assert "/debug/logs.txt" in captured_out
        assert "tool_call_123" in captured_out
        assert "req_abc123xyz789" in captured_out
        assert "api.anthropic.com" in captured_out
        assert "2024-03-01" in captured_out
        assert "utf-8" in captured_out
        for indicator in ["{", "}", '"', "[", "]"]:
            assert indicator in captured_out


class TestFormatterComparison:
    """Tests comparing different formatter outputs via CLI."""

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_verbose_vs_just_text_difference(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that verbose output contains more detail than just-text output."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        raw = {
            "session_info": {
                "session_id": "comparison-session-789",
                "model": "claude-sonnet-4",
                "tools": ["test_tool"],
                "mcp_servers": [{"name": "test_server", "status": "connected"}],
            },
            "result_info": {
                "duration_ms": 1000,
                "cost_usd": 0.01,
                "usage": {"input_tokens": 5, "output_tokens": 3},
            },
            "raw_messages": [],
        }
        mock_prompt_llm.return_value = _make_llm_response(
            raw, text="Test response content."
        )

        # Test just-text output
        args_just_text = argparse.Namespace(prompt="Test prompt")
        execute_prompt(args_just_text)
        just_text_output = capsys.readouterr().out or ""

        mock_prompt_llm.reset_mock()
        mock_prompt_llm.return_value = _make_llm_response(
            raw, text="Test response content."
        )

        # Test verbose output
        args_verbose = argparse.Namespace(prompt="Test prompt", verbosity="verbose")
        execute_prompt(args_verbose)
        verbose_output = capsys.readouterr().out or ""

        assert "Test response content." in just_text_output
        assert len(verbose_output) > len(just_text_output)
        assert "comparison-session-789" in verbose_output
        assert "comparison-session-789" not in just_text_output
        assert "1000" in verbose_output or "1.0" in verbose_output
        assert "0.01" in verbose_output

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm")
    def test_raw_vs_verbose_difference(
        self,
        mock_prompt_llm: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that raw output contains more detail than verbose output."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        raw = {
            "session_info": {
                "session_id": "comparison-raw-verbose-101",
                "model": "claude-sonnet-4",
                "tools": ["comparison_tool"],
                "mcp_servers": [{"name": "comp_server", "status": "connected"}],
            },
            "result_info": {
                "duration_ms": 2000,
                "cost_usd": 0.02,
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
            "raw_messages": [
                {"role": "user", "content": "Compare verbosity levels"},
                {
                    "role": "assistant",
                    "content": "Comparison test response.",
                    "tool_calls": [
                        {
                            "id": "unique_tool_id_456",
                            "name": "comparison_tool",
                            "parameters": {"mode": "test"},
                        }
                    ],
                },
            ],
            "api_metadata": {
                "request_id": "unique_request_789",
                "endpoint": "https://api.anthropic.com/v1/messages",
            },
        }
        mock_prompt_llm.return_value = _make_llm_response(
            raw, text="Comparison test response."
        )

        args_verbose = argparse.Namespace(
            prompt="Compare verbosity levels", verbosity="verbose"
        )
        execute_prompt(args_verbose)
        verbose_output = capsys.readouterr().out or ""

        mock_prompt_llm.reset_mock()
        mock_prompt_llm.return_value = _make_llm_response(
            raw, text="Comparison test response."
        )

        args_raw = argparse.Namespace(
            prompt="Compare verbosity levels", verbosity="raw"
        )
        execute_prompt(args_raw)
        raw_output = capsys.readouterr().out or ""

        assert "Comparison test response." in raw_output
        assert "comparison-raw-verbose-101" in verbose_output
        assert "comparison-raw-verbose-101" in raw_output
        assert "2000" in verbose_output or "2.0" in verbose_output
        assert "2000" in raw_output or "2.0" in raw_output
        assert len(raw_output) > len(verbose_output)
        assert "unique_request_789" in raw_output
        assert "unique_request_789" not in verbose_output
        assert "unique_tool_id_456" in raw_output
        assert "unique_tool_id_456" not in verbose_output
        assert "api.anthropic.com" in raw_output
        assert "api.anthropic.com" not in verbose_output
