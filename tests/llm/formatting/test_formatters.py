"""Tests for response formatting functions."""

import argparse
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt


class TestFormatVerboseResponse:
    """Tests for verbose response formatting via CLI."""

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    def test_verbose_output(
        self,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test verbose output format with detailed tool interactions and metrics."""
        # Setup enhanced mock response with rich tool interaction data
        mock_response = {
            "text": "Here's how to create a file with Python.",
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
                {
                    "role": "user",
                    "content": "How do I create a file?",
                },
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
        mock_ask_claude.return_value = mock_response

        # Create test arguments with verbose verbosity
        args = argparse.Namespace(prompt="How do I create a file?", verbosity="verbose")

        # Execute the prompt command
        result = execute_prompt(args)

        # Assert successful execution
        assert result == 0

        # Verify Claude API was called with correct prompt and session_id=None
        mock_ask_claude.assert_called_once_with("How do I create a file?", 30, None)

        # Capture output for verbose format verification
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""

        # Verify Claude response is present
        assert "Here's how to create a file with Python." in captured_out

        # Verify verbose-specific content is present
        # Tool interaction details
        assert "file_writer" in captured_out
        assert "example.py" in captured_out

        # Performance metrics
        assert (
            "2340" in captured_out or "2.34" in captured_out
        )  # Duration in ms or seconds
        assert "0.0456" in captured_out  # Cost
        assert "25" in captured_out  # Input tokens
        assert "18" in captured_out  # Output tokens

        # Session information
        assert "verbose-session-456" in captured_out
        assert "claude-sonnet-4" in captured_out

        # MCP server status
        assert "fs_server" in captured_out
        assert "connected" in captured_out


class TestFormatRawResponse:
    """Tests for raw response formatting via CLI."""

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    def test_raw_output(
        self,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test raw output format with complete debug output including JSON structures."""
        # Setup comprehensive mock response with complete JSON structures
        mock_response = {
            "text": "Here's the complete debugging information.",
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
                {
                    "role": "user",
                    "content": "Debug this system",
                },
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
        mock_ask_claude.return_value = mock_response

        # Create test arguments with raw verbosity
        args = argparse.Namespace(prompt="Debug this system", verbosity="raw")

        # Execute the prompt command
        result = execute_prompt(args)

        # Assert successful execution
        assert result == 0

        # Verify Claude API was called with correct prompt and session_id=None
        mock_ask_claude.assert_called_once_with("Debug this system", 30, None)

        # Capture output for raw format verification
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""

        # Verify Claude response is present
        assert "Here's the complete debugging information." in captured_out

        # Verify raw output contains everything from verbose level
        # Performance metrics
        assert (
            "3450" in captured_out or "3.45" in captured_out
        )  # Duration in ms or seconds
        assert "0.0789" in captured_out  # Cost
        assert "42" in captured_out  # Input tokens
        assert "28" in captured_out  # Output tokens

        # Session information
        assert "raw-debug-session-999" in captured_out
        assert "claude-sonnet-4" in captured_out

        # MCP server information
        assert "fs_mcp" in captured_out
        assert "debug_mcp" in captured_out
        assert "connected" in captured_out

        # Tool interactions
        assert "file_system" in captured_out
        assert "/debug/logs.txt" in captured_out

        # Verify raw-specific content (complete JSON structures)
        # Raw should contain JSON-like structures and complete API metadata
        assert "tool_call_123" in captured_out  # Tool call ID from raw messages
        assert "req_abc123xyz789" in captured_out  # Request ID from API metadata
        assert "api.anthropic.com" in captured_out  # API endpoint
        assert "2024-03-01" in captured_out  # API version
        assert "utf-8" in captured_out  # Deep parameter from tool call

        # Verify JSON structure patterns are present
        # Raw output should include complete JSON representations
        json_indicators = [
            "{",  # JSON opening brace
            "}",  # JSON closing brace
            '"',  # JSON string quotes
            "[",  # JSON array opening
            "]",  # JSON array closing
        ]
        for indicator in json_indicators:
            assert indicator in captured_out


class TestFormatterComparison:
    """Tests comparing different formatter outputs via CLI."""

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_verbose_vs_just_text_difference(
        self,
        mock_ask_llm: Mock,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that verbose output contains more detail than just-text output."""
        # Setup mock response for ask_claude_code_api_detailed_sync (verbose mode)
        mock_response = {
            "text": "Test response content.",
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
        mock_ask_claude.return_value = mock_response

        # Setup mock response for ask_llm (just-text mode)
        mock_ask_llm.return_value = "Test response content."

        # Test just-text output (default) - uses ask_llm
        args_just_text = argparse.Namespace(prompt="Test prompt")
        execute_prompt(args_just_text)
        just_text_output = capsys.readouterr().out or ""

        # Reset mock call count
        mock_ask_llm.reset_mock()
        mock_ask_claude.reset_mock()
        mock_ask_claude.return_value = mock_response

        # Test verbose output - uses ask_claude_code_api_detailed_sync
        args_verbose = argparse.Namespace(prompt="Test prompt", verbosity="verbose")
        execute_prompt(args_verbose)
        verbose_output = capsys.readouterr().out or ""

        # Verify both contain the basic response
        assert "Test response content." in just_text_output
        assert "Test response content." in verbose_output

        # Verify verbose contains additional details not in just-text
        assert len(verbose_output) > len(just_text_output)

        # Verbose should contain session details that just-text doesn't
        assert "comparison-session-789" in verbose_output
        assert "comparison-session-789" not in just_text_output

        # Verbose should contain performance metrics that just-text doesn't
        assert "1000" in verbose_output or "1.0" in verbose_output  # Duration
        assert "0.01" in verbose_output  # Cost
        assert (
            "1000" not in just_text_output
            and "1.0" not in just_text_output
            and "0.01" not in just_text_output
        )

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    def test_raw_vs_verbose_difference(
        self,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that raw output contains more detail than verbose output."""
        # Setup mock response with rich data for comparison
        mock_response = {
            "text": "Comparison test response.",
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
                {
                    "role": "user",
                    "content": "Compare verbosity levels",
                },
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
        mock_ask_claude.return_value = mock_response

        # Test verbose output
        args_verbose = argparse.Namespace(
            prompt="Compare verbosity levels", verbosity="verbose"
        )
        execute_prompt(args_verbose)
        verbose_output = capsys.readouterr().out or ""

        # Reset mock call count
        mock_ask_claude.reset_mock()
        mock_ask_claude.return_value = mock_response

        # Test raw output
        args_raw = argparse.Namespace(
            prompt="Compare verbosity levels", verbosity="raw"
        )
        execute_prompt(args_raw)
        raw_output = capsys.readouterr().out or ""

        # Verify both contain the basic response
        assert "Comparison test response." in verbose_output
        assert "Comparison test response." in raw_output

        # Verify both contain common verbose elements
        assert "comparison-raw-verbose-101" in verbose_output
        assert "comparison-raw-verbose-101" in raw_output
        assert "2000" in verbose_output or "2.0" in verbose_output
        assert "2000" in raw_output or "2.0" in raw_output

        # Verify raw contains additional details not in verbose
        assert len(raw_output) > len(verbose_output)

        # Raw should contain complete API metadata that verbose doesn't
        assert "unique_request_789" in raw_output
        assert "unique_request_789" not in verbose_output

        # Raw should contain detailed tool call IDs that verbose doesn't
        assert "unique_tool_id_456" in raw_output
        assert "unique_tool_id_456" not in verbose_output

        # Raw should contain API endpoint information that verbose doesn't
        assert "api.anthropic.com" in raw_output
        assert "api.anthropic.com" not in verbose_output
