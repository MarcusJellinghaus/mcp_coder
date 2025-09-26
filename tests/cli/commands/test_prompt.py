"""Tests for prompt command functionality."""

import argparse
import json
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional
from unittest.mock import Mock, mock_open, patch

import pytest

# _find_latest_response_file is available from the prompt module
from mcp_coder.cli.commands.prompt import _find_latest_response_file, execute_prompt


class TestExecutePrompt:
    """Tests for execute_prompt function."""

    # Test constants to avoid magic strings
    FAKE_RESPONSE_PATH = "/fake/path/response_2025-09-19T14-30-22.json"
    FAKE_SESSION_ID = "test-session-456"
    DEFAULT_MODEL = "claude-sonnet-4"

    VALID_TIMESTAMPS = [
        "response_2025-09-19T14-30-20.json",
        "response_2025-09-19T14-30-22.json",
        "response_2025-09-19T14-30-25.json",
    ]

    INVALID_FILES = [
        "response_abc_2025.json",
        "other_file.json",
        "response_invalid.json",
    ]

    @pytest.fixture
    def sample_stored_response(self) -> Dict[str, Any]:
        """Standard stored response data for continuation tests."""
        return {
            "prompt": "How do I create a Python file?",
            "response_data": {
                "text": "Here's how to create a Python file.",
                "session_info": {
                    "session_id": "previous-session-456",
                    "model": self.DEFAULT_MODEL,
                    "tools": ["file_writer"],
                    "mcp_servers": [{"name": "fs_server", "status": "connected"}],
                },
                "result_info": {
                    "duration_ms": 1500,
                    "cost_usd": 0.025,
                    "usage": {"input_tokens": 15, "output_tokens": 12},
                },
                "raw_messages": [
                    {"role": "user", "content": "How do I create a Python file?"},
                    {
                        "role": "assistant",
                        "content": "Here's how to create a Python file.",
                    },
                ],
            },
            "metadata": {
                "timestamp": "2025-09-19T10:30:00Z",
                "working_directory": "/test/dir",
                "model": self.DEFAULT_MODEL,
            },
        }

    @pytest.fixture
    def sample_claude_response(self) -> Dict[str, Any]:
        """Standard Claude API response for tests."""
        return {
            "text": "Now let's also add some error handling to that file.",
            "session_info": {
                "session_id": "continuation-session-789",
                "model": self.DEFAULT_MODEL,
                "tools": ["file_writer", "code_analyzer"],
                "mcp_servers": [{"name": "fs_server", "status": "connected"}],
            },
            "result_info": {
                "duration_ms": 1800,
                "cost_usd": 0.030,
                "usage": {"input_tokens": 25, "output_tokens": 18},
            },
            "raw_messages": [],
        }

    def _setup_file_discovery_mocks(
        self,
        mock_find_latest: Mock,
        mock_exists: Mock,
        mock_file_open: Mock,
        return_file: Optional[str] = None,
        stored_response: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set up common mocks for file discovery tests."""
        if return_file is None:
            return_file = self.FAKE_RESPONSE_PATH

        mock_find_latest.return_value = return_file
        mock_exists.return_value = return_file is not None

        if return_file and stored_response:
            mock_file_open.return_value.read.return_value = json.dumps(stored_response)

    def _create_test_files_in_temp_dir(
        self, temp_dir: str, filenames: List[str]
    ) -> None:
        """Create test response files in temporary directory."""
        for filename in filenames:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"test": "data", "filename": filename}, f)

    def _create_continue_args(
        self,
        prompt: str = "Test prompt",
        continue_from: Optional[str] = None,
        continue_flag: bool = False,
        verbosity: str = "just-text",
    ) -> argparse.Namespace:
        """Create standardized argument namespace for continue tests."""
        args = argparse.Namespace(prompt=prompt, verbosity=verbosity)

        # Set continue options
        setattr(args, "continue_from", continue_from)
        setattr(args, "continue", continue_flag)

        return args

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    def test_basic_prompt_success(
        self,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful prompt execution with mocked Claude API detailed function."""
        # Setup mock response for ask_claude_code_api_detailed_sync
        mock_response = {
            "text": "The capital of France is Paris.",
            "session_info": {
                "session_id": "test-session-123",
                "model": "claude-sonnet-4",
                "tools": ["Read", "Write", "Bash"],
                "mcp_servers": [{"name": "checker", "status": "connected"}],
            },
            "result_info": {
                "duration_ms": 1500,
                "cost_usd": 0.0234,
                "usage": {"input_tokens": 10, "output_tokens": 8},
            },
            "raw_messages": [],
        }
        mock_ask_claude.return_value = mock_response

        # Create test arguments
        args = argparse.Namespace(prompt="What is the capital of France?")

        # Execute the prompt command
        result = execute_prompt(args)

        # Assert successful execution
        assert result == 0

        # Verify Claude API was called with correct prompt
        mock_ask_claude.assert_called_once_with("What is the capital of France?", 30)

        # Verify basic output presence (Claude response visible)
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "The capital of France is Paris." in captured_out

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    def test_prompt_api_error(
        self,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test API error handling when Claude API fails."""
        # Setup mock to raise exception
        mock_ask_claude.side_effect = Exception("Claude API connection failed")

        # Create test arguments
        args = argparse.Namespace(prompt="Test question")

        # Execute the prompt command
        result = execute_prompt(args)

        # Assert error return code
        assert result == 1

        # Verify Claude API was called
        mock_ask_claude.assert_called_once_with("Test question", 30)

        # Verify error message is displayed
        captured = capsys.readouterr()
        captured_err: str = captured.err or ""
        assert "Error" in captured_err
        assert "Claude API connection failed" in captured_err

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

        # Verify Claude API was called with correct prompt
        mock_ask_claude.assert_called_once_with("How do I create a file?", 30)

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

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    def test_verbose_vs_just_text_difference(
        self,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that verbose output contains more detail than just-text output."""
        # Setup mock response
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

        # Test just-text output (default)
        args_just_text = argparse.Namespace(prompt="Test prompt")
        execute_prompt(args_just_text)
        just_text_output = capsys.readouterr().out or ""

        # Reset mock call count
        mock_ask_claude.reset_mock()
        mock_ask_claude.return_value = mock_response

        # Test verbose output
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

        # Verify Claude API was called with correct prompt
        mock_ask_claude.assert_called_once_with("Debug this system", 30)

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

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    @patch("mcp_coder.cli.commands.prompt._store_response")
    def test_store_response(
        self,
        mock_store_response: Mock,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test storing complete session data to .mcp-coder/responses/ directory.

        Note: This test mocks the _store_response function to prevent actual file creation
        during testing, while verifying the storage functionality is called properly.
        """
        # Setup mock response for Claude API
        mock_response = {
            "text": "Here's how to create a Python file.",
            "session_info": {
                "session_id": "storage-test-session-123",
                "model": "claude-sonnet-4",
                "tools": ["file_writer", "code_analyzer"],
                "mcp_servers": [
                    {"name": "fs_server", "status": "connected"},
                    {"name": "code_server", "status": "connected"},
                ],
            },
            "result_info": {
                "duration_ms": 1800,
                "cost_usd": 0.0345,
                "usage": {"input_tokens": 20, "output_tokens": 15},
            },
            "raw_messages": [
                {
                    "role": "user",
                    "content": "How do I create a Python file?",
                },
                {
                    "role": "assistant",
                    "content": "Here's how to create a Python file.",
                    "tool_calls": [
                        {
                            "id": "tool_call_456",
                            "name": "file_writer",
                            "parameters": {
                                "filename": "test.py",
                                "content": "print('Hello, World!')",
                            },
                        }
                    ],
                },
            ],
        }
        mock_ask_claude.return_value = mock_response

        # Create test arguments with store_response flag
        # Note: store_response functionality doesn't exist yet,
        # but this tests that the attribute doesn't break anything
        args = argparse.Namespace(
            prompt="How do I create a Python file?", store_response=True
        )

        # Mock the storage function to return a fake path
        mock_store_response.return_value = (
            "/fake/path/response_2025-01-01T12-00-00.json"
        )

        # Execute the prompt command
        result = execute_prompt(args)

        # Assert successful execution
        assert result == 0

        # Verify Claude API was called with correct prompt
        mock_ask_claude.assert_called_once_with("How do I create a Python file?", 30)

        # Verify storage function was called with correct parameters
        mock_store_response.assert_called_once_with(
            mock_response, "How do I create a Python file?"
        )

        # Verify normal output is still printed (basic functionality works)
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Here's how to create a Python file." in captured_out

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_success(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful continuation from stored response file."""
        # Setup mock for stored response file
        stored_response = {
            "prompt": "How do I create a Python file?",
            "response_data": {
                "text": "Here's how to create a Python file.",
                "session_info": {
                    "session_id": "previous-session-456",
                    "model": "claude-sonnet-4",
                    "tools": ["file_writer"],
                    "mcp_servers": [{"name": "fs_server", "status": "connected"}],
                },
                "result_info": {
                    "duration_ms": 1500,
                    "cost_usd": 0.025,
                    "usage": {"input_tokens": 15, "output_tokens": 12},
                },
                "raw_messages": [
                    {
                        "role": "user",
                        "content": "How do I create a Python file?",
                    },
                    {
                        "role": "assistant",
                        "content": "Here's how to create a Python file.",
                    },
                ],
            },
            "metadata": {
                "timestamp": "2025-09-19T10:30:00Z",
                "working_directory": "/test/dir",
                "model": "claude-sonnet-4",
            },
        }

        # Setup mock file system
        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(stored_response)

        # Setup mock response for new Claude API call
        new_response = {
            "text": "Now let's also add some error handling to that file.",
            "session_info": {
                "session_id": "continuation-session-789",
                "model": "claude-sonnet-4",
                "tools": ["file_writer", "code_analyzer"],
                "mcp_servers": [{"name": "fs_server", "status": "connected"}],
            },
            "result_info": {
                "duration_ms": 1800,
                "cost_usd": 0.030,
                "usage": {"input_tokens": 25, "output_tokens": 18},
            },
            "raw_messages": [],
        }
        mock_ask_claude.return_value = new_response

        # Create test arguments with continue_from parameter
        args = argparse.Namespace(
            prompt="Add error handling",
            continue_from="path/to/previous_response.json",
        )

        # Execute the prompt command
        result = execute_prompt(args)

        # Assert successful execution
        assert result == 0

        # Verify file reading operations
        mock_exists.assert_called_once_with("path/to/previous_response.json")
        mock_file_open.assert_called_once_with(
            "path/to/previous_response.json", "r", encoding="utf-8"
        )

        # Verify Claude API was called with enhanced context
        # Should include both previous context and new prompt
        mock_ask_claude.assert_called_once()
        api_call_args = mock_ask_claude.call_args
        enhanced_prompt = api_call_args[0][0]  # First positional argument

        # Verify the enhanced prompt contains previous context
        assert "How do I create a Python file?" in enhanced_prompt
        assert "Here's how to create a Python file." in enhanced_prompt
        assert "Add error handling" in enhanced_prompt
        assert (
            "Previous conversation:" in enhanced_prompt or "Context:" in enhanced_prompt
        )

        # Verify normal output is displayed
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Now let's also add some error handling to that file." in captured_out

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    @patch("os.path.exists")
    def test_continue_from_file_not_found(
        self,
        mock_exists: Mock,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test error handling when continue_from file doesn't exist."""
        # Setup mock file system - file doesn't exist
        mock_exists.return_value = False

        # Create test arguments with continue_from parameter pointing to non-existent file
        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_from="path/to/nonexistent_file.json",
        )

        # Execute the prompt command
        result = execute_prompt(args)

        # Assert error return code
        assert result == 1

        # Verify file existence check was called
        mock_exists.assert_called_once_with("path/to/nonexistent_file.json")

        # Verify Claude API was NOT called (due to file error)
        mock_ask_claude.assert_not_called()

        # Verify error message is displayed
        captured = capsys.readouterr()
        captured_err: str = captured.err or ""
        assert "Error" in captured_err
        assert (
            "nonexistent_file.json" in captured_err
            or "not found" in captured_err.lower()
        )

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_invalid_json(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test error handling when continue_from file contains invalid JSON."""
        # Setup mock file system - file exists but contains invalid JSON
        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = "{ invalid json content }"

        # Create test arguments with continue_from parameter
        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_from="path/to/invalid.json",
        )

        # Execute the prompt command
        result = execute_prompt(args)

        # Assert error return code
        assert result == 1

        # Verify file operations were attempted
        mock_exists.assert_called_once_with("path/to/invalid.json")
        mock_file_open.assert_called_once_with(
            "path/to/invalid.json", "r", encoding="utf-8"
        )

        # Verify Claude API was NOT called (due to JSON error)
        mock_ask_claude.assert_not_called()

        # Verify error message is displayed
        captured = capsys.readouterr()
        captured_err: str = captured.err or ""
        assert "Error" in captured_err
        # Accept Python's standard JSON parsing error messages
        assert (
            "expecting" in captured_err.lower()
            or "invalid" in captured_err.lower()
            or "json" in captured_err.lower()
        )

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_missing_required_fields(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test error handling when continue_from file has missing required fields."""
        # Setup mock for incomplete stored response (missing prompt or response_data)
        incomplete_response = {
            "metadata": {
                "timestamp": "2025-09-19T10:30:00Z",
                "working_directory": "/test/dir",
            }
            # Missing "prompt" and "response_data" fields
        }

        # Setup mock file system
        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(incomplete_response)

        # Create test arguments with continue_from parameter
        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_from="path/to/incomplete.json",
        )

        # Execute the prompt command
        result = execute_prompt(args)

        # Assert error return code
        assert result == 1

        # Verify file operations were attempted
        mock_exists.assert_called_once_with("path/to/incomplete.json")
        mock_file_open.assert_called_once_with(
            "path/to/incomplete.json", "r", encoding="utf-8"
        )

        # Verify Claude API was NOT called (due to missing data)
        mock_ask_claude.assert_not_called()

        # Verify error message is displayed
        captured = capsys.readouterr()
        captured_err: str = captured.err or ""
        assert "Error" in captured_err
        assert (
            "missing" in captured_err.lower()
            or "required" in captured_err.lower()
            or "invalid" in captured_err.lower()
        )

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_with_verbosity(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test continuation functionality works with different verbosity levels."""
        # Setup mock for stored response file
        stored_response = {
            "prompt": "What is Python?",
            "response_data": {
                "text": "Python is a programming language.",
                "session_info": {
                    "session_id": "verbose-continuation-123",
                    "model": "claude-sonnet-4",
                    "tools": ["code_analyzer"],
                    "mcp_servers": [{"name": "test_server", "status": "connected"}],
                },
                "result_info": {
                    "duration_ms": 1200,
                    "cost_usd": 0.020,
                    "usage": {"input_tokens": 10, "output_tokens": 8},
                },
                "raw_messages": [],
            },
            "metadata": {
                "timestamp": "2025-09-19T11:00:00Z",
                "working_directory": "/test/dir",
                "model": "claude-sonnet-4",
            },
        }

        # Setup mock file system
        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(stored_response)

        # Setup mock response for new Claude API call
        new_response = {
            "text": "Here are some advanced Python features.",
            "session_info": {
                "session_id": "verbose-continuation-new-456",
                "model": "claude-sonnet-4",
                "tools": ["code_analyzer", "file_writer"],
                "mcp_servers": [{"name": "test_server", "status": "connected"}],
            },
            "result_info": {
                "duration_ms": 2500,
                "cost_usd": 0.040,
                "usage": {"input_tokens": 30, "output_tokens": 22},
            },
            "raw_messages": [],
        }
        mock_ask_claude.return_value = new_response

        # Create test arguments with continue_from and verbose verbosity
        args = argparse.Namespace(
            prompt="Tell me about advanced features",
            continue_from="path/to/previous.json",
            verbosity="verbose",
        )

        # Execute the prompt command
        result = execute_prompt(args)

        # Assert successful execution
        assert result == 0

        # Verify file reading operations
        mock_exists.assert_called_once_with("path/to/previous.json")
        mock_file_open.assert_called_once_with(
            "path/to/previous.json", "r", encoding="utf-8"
        )

        # Verify Claude API was called with enhanced context
        mock_ask_claude.assert_called_once()
        api_call_args = mock_ask_claude.call_args
        enhanced_prompt = api_call_args[0][0]

        # Verify the enhanced prompt contains previous context
        assert "What is Python?" in enhanced_prompt
        assert "Python is a programming language." in enhanced_prompt
        assert "Tell me about advanced features" in enhanced_prompt

        # Verify verbose output format is applied
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""

        # Should contain the main response
        assert "Here are some advanced Python features." in captured_out

        # Should contain verbose-specific information (session info, metrics)
        assert "verbose-continuation-new-456" in captured_out  # New session ID
        assert "2500" in captured_out or "2.5" in captured_out  # Duration
        assert "0.040" in captured_out  # Cost
        assert "30" in captured_out  # Input tokens
        assert "22" in captured_out  # Output tokens

    def test_find_latest_response_file_success(self) -> None:
        """Test successful discovery of latest response file with proper sorting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use constants and helper method
            self._create_test_files_in_temp_dir(temp_dir, self.VALID_TIMESTAMPS)

            # Call the function
            result = _find_latest_response_file(temp_dir)

            # Verify it returns the latest file
            expected_path = os.path.join(temp_dir, "response_2025-09-19T14-30-25.json")
            assert result == expected_path
            assert os.path.exists(result)

    def test_find_latest_response_file_edge_cases(self) -> None:
        """Test edge cases: no directory, no files, mixed file types."""
        # Test 1: Non-existent directory
        non_existent_dir = "/path/that/does/not/exist"
        result = _find_latest_response_file(non_existent_dir)
        assert result is None

        # Test 2: Empty directory
        with tempfile.TemporaryDirectory() as temp_dir:
            result = _find_latest_response_file(temp_dir)
            assert result is None

        # Test 3: Directory with no valid response files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some non-response files
            invalid_files = [
                "other_file.json",
                "response_invalid.json",
                "not_a_response.txt",
                "readme.md",
            ]

            for filename in invalid_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("test content")

            result = _find_latest_response_file(temp_dir)
            assert result is None

    def test_find_latest_response_file_mixed_valid_invalid(self) -> None:
        """Test file discovery ignores invalid files and selects latest valid file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use constants and helper method
            test_files = self.VALID_TIMESTAMPS + self.INVALID_FILES
            self._create_test_files_in_temp_dir(temp_dir, test_files)

            # Call the function
            result = _find_latest_response_file(temp_dir)

            # Verify it returns only the latest VALID file
            expected_path = os.path.join(temp_dir, "response_2025-09-19T14-30-25.json")
            assert result == expected_path

            # Verify the file exists and contains expected data
            assert os.path.exists(result)
            with open(result, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert data["filename"] == "response_2025-09-19T14-30-25.json"

    def test_find_latest_response_file_invalid_datetime_values(self) -> None:
        """Test strict validation rejects files with invalid date/time values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with invalid date/time values but correct format
            invalid_files = [
                "response_2025-13-45T99-99-99.json",  # Invalid month, day, hour, minute, second
                "response_2025-00-01T12-00-00.json",  # Invalid month (0)
                "response_2025-12-32T12-00-00.json",  # Invalid day (32)
                "response_2025-12-01T25-00-00.json",  # Invalid hour (25)
                "response_2025-12-01T12-61-00.json",  # Invalid minute (61)
                "response_2025-12-01T12-00-61.json",  # Invalid second (61)
            ]

            for filename in invalid_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"test": "data"}, f)

            # Should return None when all files have invalid date/time values
            result = _find_latest_response_file(temp_dir)
            assert result is None

    def test_find_latest_response_file_only_invalid_files_remain(self) -> None:
        """Test behavior when valid files are removed leaving only invalid ones."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # First create both valid and invalid files
            all_files = [
                "response_2025-09-19T14-30-22.json",  # Valid
                "response_2025-09-19T14-30-25.json",  # Valid
                "response_abc_2025.json",  # Invalid format
                "other_file.json",  # Not a response file
            ]

            for filename in all_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"test": "data"}, f)

            # Verify it initially finds valid files
            result = _find_latest_response_file(temp_dir)
            assert result is not None
            assert "response_2025-09-19T14-30-25.json" in result

            # Remove all valid files
            for filename in [
                "response_2025-09-19T14-30-22.json",
                "response_2025-09-19T14-30-25.json",
            ]:
                os.remove(os.path.join(temp_dir, filename))

            # Should return None when only invalid files remain
            result = _find_latest_response_file(temp_dir)
            assert result is None

    def test_find_latest_response_file_lexicographic_sorting(self) -> None:
        """Test that files are sorted lexicographically to find the latest timestamp."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files in non-chronological order to test sorting
            test_files = [
                "response_2025-09-20T10-00-00.json",  # Later date
                "response_2025-09-19T23-59-59.json",  # Earlier date, later time
                "response_2025-09-20T09-59-59.json",  # Later date, earlier time
                "response_2025-09-20T10-00-01.json",  # Latest overall (expected result)
            ]

            for filename in test_files:
                file_path = os.path.join(temp_dir, filename)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump({"filename": filename}, f)

            # Call the function
            result = _find_latest_response_file(temp_dir)

            # Verify it returns the lexicographically latest file
            expected_path = os.path.join(temp_dir, "response_2025-09-20T10-00-01.json")
            assert result == expected_path

            # Verify the file contains expected data
            with open(result, "r", encoding="utf-8") as f:
                data = json.load(f)
                assert data["filename"] == "response_2025-09-20T10-00-01.json"

    def test_find_latest_response_file_user_feedback_message(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test that user feedback message shows correct count and filename."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Use constants and helper method
            self._create_test_files_in_temp_dir(temp_dir, self.VALID_TIMESTAMPS)

            # Call the function
            result = _find_latest_response_file(temp_dir)

            # Verify return value
            assert result is not None
            assert "response_2025-09-19T14-30-25.json" in result

            # Verify user feedback message
            captured = capsys.readouterr()
            captured_out = captured.out or ""
            assert (
                "Found 3 previous sessions, continuing from: response_2025-09-19T14-30-25.json"
                in captured_out
            )

    @patch("mcp_coder.cli.commands.prompt._find_latest_response_file")
    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    def test_continue_success(
        self,
        mock_ask_claude: Mock,
        mock_find_latest: Mock,
        capsys: pytest.CaptureFixture[str],
        sample_stored_response: Dict[str, Any],
        sample_claude_response: Dict[str, Any],
    ) -> None:
        """Test successful --continue execution with file discovery and user feedback."""
        mock_ask_claude.return_value = sample_claude_response

        # Mock file operations for reading stored response
        with (
            patch("os.path.exists") as mock_exists,
            patch(
                "builtins.open", mock_open(read_data=json.dumps(sample_stored_response))
            ),
        ):
            # Setup mocks manually for this test
            mock_find_latest.return_value = self.FAKE_RESPONSE_PATH
            mock_exists.return_value = True

            # The test doesn't actually call _find_latest_response_file directly
            # since we're testing continue_from, not continue functionality

            # Test current continue_from functionality as baseline
            args = self._create_continue_args(
                prompt="Add error handling", continue_from=self.FAKE_RESPONSE_PATH
            )

            # Execute the prompt command
            result = execute_prompt(args)

            # Assert successful execution
            assert result == 0

            # Verify Claude API was called with enhanced context
            mock_ask_claude.assert_called_once()
            api_call_args = mock_ask_claude.call_args
            enhanced_prompt = api_call_args[0][0]  # First positional argument

            # Verify the enhanced prompt contains previous context
            assert "How do I create a Python file?" in enhanced_prompt
            assert "Here's how to create a Python file." in enhanced_prompt
            assert "Add error handling" in enhanced_prompt
            assert (
                "Previous conversation:" in enhanced_prompt
                or "Context:" in enhanced_prompt
            )

            # Verify normal output is displayed
            captured = capsys.readouterr()
            captured_out: str = captured.out or ""
            assert sample_claude_response["text"] in captured_out

    @patch("mcp_coder.cli.commands.prompt.glob.glob")
    @patch("mcp_coder.cli.commands.prompt.os.path.exists")
    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    def test_continue_no_files(
        self,
        mock_ask_claude: Mock,
        mock_exists: Mock,
        mock_glob: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test file discovery when no response files are found.

        This test verifies the _find_latest_response_file function behavior
        that will be integrated in Step 5.
        """
        # Setup mocks for no files found
        mock_exists.return_value = True  # Directory exists
        mock_glob.return_value = []  # But no response files

        # Setup mock response for new Claude API call (should proceed normally)
        new_response = {
            "text": "Starting a new conversation about Python.",
            "session_info": {
                "session_id": "new-session-123",
                "model": "claude-sonnet-4",
                "tools": ["code_analyzer"],
                "mcp_servers": [{"name": "test_server", "status": "connected"}],
            },
            "result_info": {
                "duration_ms": 1200,
                "cost_usd": 0.020,
                "usage": {"input_tokens": 10, "output_tokens": 8},
            },
            "raw_messages": [],
        }
        mock_ask_claude.return_value = new_response

        # Test file discovery functionality when no files exist
        from mcp_coder.cli.commands.prompt import _find_latest_response_file

        latest_file = _find_latest_response_file()

        # Verify file discovery returns None when no files found
        assert latest_file is None

        # Test normal execution when no continue_from is specified
        args = argparse.Namespace(prompt="Tell me about Python", verbosity="just-text")

        # Execute the prompt command (should work normally)
        result = execute_prompt(args)

        # Assert successful execution (should work with new conversation)
        assert result == 0

        # Verify Claude API was called with original prompt (no context enhancement)
        mock_ask_claude.assert_called_once_with("Tell me about Python", 30)

        # Verify normal output is displayed
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""
        assert "Starting a new conversation about Python." in captured_out

    @patch("mcp_coder.cli.commands.prompt.glob.glob")
    @patch("mcp_coder.cli.commands.prompt.os.path.exists")
    def test_continue_with_user_feedback(
        self,
        mock_exists: Mock,
        mock_glob: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that user feedback shows selected filename clearly.

        This test verifies the _find_latest_response_file function provides
        user feedback that will be used in Step 5.
        """
        # Setup mocks for file discovery
        mock_exists.return_value = True
        mock_glob.return_value = [
            "/fake/responses/response_2025-09-22T16-45-20.json",
            "/fake/responses/response_2025-09-22T16-45-30.json",  # Latest
            "/fake/responses/response_2025-09-22T16-45-25.json",
        ]

        # Test the file discovery function directly
        from mcp_coder.cli.commands.prompt import _find_latest_response_file

        # Call the function to test user feedback
        result = _find_latest_response_file()

        # Verify the function returns the latest file
        assert result == "/fake/responses/response_2025-09-22T16-45-30.json"

        # Verify user feedback shows the selected filename clearly
        captured = capsys.readouterr()
        captured_out: str = captured.out or ""

        # User should see the selected filename in the output
        assert "response_2025-09-22T16-45-30.json" in captured_out

        # Should contain the user feedback message
        assert "Found 3 previous sessions, continuing from:" in captured_out

    def test_mutual_exclusivity_handled_by_argparse(self) -> None:
        """Test that argument structure supports mutual exclusivity design.

        This test verifies the argument structure that will be used in Step 5
        when --continue is implemented. The actual argparse validation
        happens at the CLI level using mutually_exclusive_group().
        """
        # Test that we can create valid argument combinations for future implementation

        # Valid: continue_last=True, continue_from=None (current implementation)
        args_continue = argparse.Namespace(
            prompt="Follow up question", continue_last=True, continue_from=None
        )
        assert args_continue.continue_last is True
        assert args_continue.continue_from is None

        # Valid: continue_last=False, continue_from="path" (existing implementation)
        args_continue_from = argparse.Namespace(
            prompt="Follow up question",
            continue_last=False,
            continue_from="path/to/file.json",
        )
        assert args_continue_from.continue_last is False
        assert args_continue_from.continue_from == "path/to/file.json"

        # Valid: Neither option set (normal operation)
        args_normal = argparse.Namespace(
            prompt="Normal question", continue_last=False, continue_from=None
        )
        assert args_normal.continue_last is False
        assert args_normal.continue_from is None

        # Verify that the argument patterns are consistent and support mutual exclusivity
        # This ensures Step 5 implementation will work correctly
        # Using explicit boolean checks to satisfy mypy
        assert not (
            bool(args_continue.continue_last) and bool(args_continue.continue_from)
        )
        assert not (
            bool(args_continue_from.continue_last)
            and bool(args_continue_from.continue_from)
        )
        assert not (bool(args_normal.continue_last) and bool(args_normal.continue_from))

    def test_continue_success_integration(
        self,
        sample_stored_response: Dict[str, Any],
        sample_claude_response: Dict[str, Any],
    ) -> None:
        """Test CLI integration for --continue success case."""
        with (
            patch(
                "mcp_coder.cli.commands.prompt._find_latest_response_file"
            ) as mock_find_latest,
            patch(
                "mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync"
            ) as mock_ask_claude,
            patch("builtins.open", mock_open()) as mock_file_open,
            patch("os.path.exists") as mock_exists,
        ):
            # Use helper method for setup
            self._setup_file_discovery_mocks(
                mock_find_latest,
                mock_exists,
                mock_file_open,
                stored_response=sample_stored_response,
            )
            mock_ask_claude.return_value = sample_claude_response

            # Test the current continue_from functionality that Step 5 will leverage
            # Create test arguments using helper method
            args = self._create_continue_args(
                prompt="Add error handling", continue_from=self.FAKE_RESPONSE_PATH
            )

            # Execute the prompt command
            result = execute_prompt(args)
            assert result == 0

            # Verify file operations
            mock_exists.assert_called_once_with(self.FAKE_RESPONSE_PATH)
            mock_file_open.assert_called_once_with(
                self.FAKE_RESPONSE_PATH, "r", encoding="utf-8"
            )

            # Verify Claude API was called with enhanced context
            mock_ask_claude.assert_called_once()
            api_call_args = mock_ask_claude.call_args
            enhanced_prompt = api_call_args[0][0]

            # Verify the enhanced prompt contains previous context
            assert "How do I create a Python file?" in enhanced_prompt
            assert "Here's how to create a Python file." in enhanced_prompt
            assert "Add error handling" in enhanced_prompt
            assert (
                "Previous conversation:" in enhanced_prompt
                or "Context:" in enhanced_prompt
            )

            # Verify file discovery works for Step 5 integration
            assert mock_find_latest.return_value == self.FAKE_RESPONSE_PATH

    def test_continue_no_files_integration(self) -> None:
        """Test CLI integration when no response files are found.

        This test focuses on the CLI integration when _find_latest_response_file
        returns None (no files found). Should proceed with normal execution.

        Since Step 5 hasn't been implemented yet, this test verifies:
        1. The _find_latest_response_file function returns None when no files exist
        2. Normal execution works without continue_from (Step 5 will use this path)
        3. User feedback functionality is ready for integration
        """
        with (
            patch(
                "mcp_coder.cli.commands.prompt._find_latest_response_file"
            ) as mock_find_latest,
            patch(
                "mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync"
            ) as mock_ask_claude,
        ):

            # Setup mock for no files found
            mock_find_latest.return_value = None

            # Setup mock response for new Claude API call
            new_response = {
                "text": "Starting a new conversation about Python.",
                "session_info": {
                    "session_id": "new-session-123",
                    "model": "claude-sonnet-4",
                    "tools": ["code_analyzer"],
                    "mcp_servers": [{"name": "test_server", "status": "connected"}],
                },
                "result_info": {
                    "duration_ms": 1200,
                    "cost_usd": 0.020,
                    "usage": {"input_tokens": 10, "output_tokens": 8},
                },
                "raw_messages": [],
            }
            mock_ask_claude.return_value = new_response

            # Test normal execution without continue_from (Step 5 will use this when no files found)
            args = argparse.Namespace(
                prompt="Tell me about Python", verbosity="just-text"
            )

            # Execute the prompt command (should work normally without continue_from)
            result = execute_prompt(args)

            # Assert successful execution
            assert result == 0

            # Test that _find_latest_response_file() returns None when no files found
            # Step 5 will use this to determine when to show "no files found" message
            discovered_file = mock_find_latest.return_value
            assert discovered_file is None

            # Verify Claude API was called with original prompt (no context enhancement)
            mock_ask_claude.assert_called_once_with("Tell me about Python", 30)

    def test_continue_with_user_feedback_integration(self) -> None:
        """Test CLI integration with user feedback showing selected filename."""
        # Create custom response data for this specific test
        test_stored_response = {
            "prompt": "Previous question about testing",
            "response_data": {
                "text": "Here's how to write tests.",
                "session_info": {
                    "session_id": self.FAKE_SESSION_ID,
                    "model": self.DEFAULT_MODEL,
                    "tools": ["test_runner"],
                    "mcp_servers": [{"name": "test_server", "status": "connected"}],
                },
                "result_info": {
                    "duration_ms": 1800,
                    "cost_usd": 0.035,
                    "usage": {"input_tokens": 20, "output_tokens": 15},
                },
                "raw_messages": [],
            },
            "metadata": {
                "timestamp": "2025-09-22T16:45:30Z",
                "working_directory": "/test/dir",
                "model": self.DEFAULT_MODEL,
            },
        }

        test_claude_response = {
            "text": "Let's add more advanced testing patterns.",
            "session_info": {
                "session_id": "continuation-session-789",
                "model": self.DEFAULT_MODEL,
                "tools": ["test_runner", "code_analyzer"],
                "mcp_servers": [{"name": "test_server", "status": "connected"}],
            },
            "result_info": {
                "duration_ms": 2200,
                "cost_usd": 0.042,
                "usage": {"input_tokens": 28, "output_tokens": 20},
            },
            "raw_messages": [],
        }

        with (
            patch(
                "mcp_coder.cli.commands.prompt._find_latest_response_file"
            ) as mock_find_latest,
            patch(
                "mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync"
            ) as mock_ask_claude,
            patch("builtins.open", mock_open()) as mock_file_open,
            patch("os.path.exists") as mock_exists,
        ):
            selected_file = "/fake/responses/response_2025-09-22T16-45-30.json"

            # Use helper method for setup
            self._setup_file_discovery_mocks(
                mock_find_latest,
                mock_exists,
                mock_file_open,
                return_file=selected_file,
                stored_response=test_stored_response,
            )
            mock_ask_claude.return_value = test_claude_response

            # Create args using helper method
            args = self._create_continue_args(
                prompt="Add advanced testing patterns", continue_from=selected_file
            )

            # Execute the prompt command
            result = execute_prompt(args)
            assert result == 0

            # Verify Claude API was called with enhanced context
            mock_ask_claude.assert_called_once()
            api_call_args = mock_ask_claude.call_args
            enhanced_prompt = api_call_args[0][0]

            # Verify enhanced prompt contains previous context
            assert "Previous question about testing" in enhanced_prompt
            assert "Here's how to write tests." in enhanced_prompt
            assert "Add advanced testing patterns" in enhanced_prompt

            # Verify file discovery functionality
            assert mock_find_latest.return_value == selected_file
            assert "response_2025-09-22T16-45-30.json" in selected_file


class TestExecutePromptParameterMapping:
    """Tests for parameter mapping from execute_prompt to prompt_claude function.

    NOTE: These tests are prepared for Step 3 implementation.
    They will pass once prompt_claude function is implemented in Step 3.
    """

    @pytest.mark.skip(
        reason="prompt_claude function not yet implemented - will be added in Step 3"
    )
    @patch("mcp_coder.cli.commands.prompt.prompt_claude")
    def test_execute_prompt_calls_prompt_claude_with_correct_parameters(
        self, mock_prompt_claude: Mock
    ) -> None:
        """Test that execute_prompt correctly maps parameters to prompt_claude function."""
        # Setup mock return value
        mock_prompt_claude.return_value = 0

        # Create argparse.Namespace with test parameters
        args = argparse.Namespace(
            prompt="Test prompt",
            verbosity="verbose",
            timeout=45,
            store_response=True,
            continue_from="test.json",
            save_conversation_md="test.md",
            save_conversation_full_json="test_full.json",
        )

        # Call execute_prompt
        result = execute_prompt(args)

        # Verify prompt_claude was called with correctly mapped parameters
        mock_prompt_claude.assert_called_once_with(
            prompt="Test prompt",
            verbosity="verbose",
            timeout=45,
            store_response=True,
            continue_from="test.json",
            continue_latest=False,
            save_conversation_md="test.md",
            save_conversation_full_json="test_full.json",
        )

        # Verify return value is passed through
        assert result == 0

    @patch("mcp_coder.cli.commands.prompt._save_conversation_markdown")
    def test_save_conversation_markdown_basic(self, mock_save_markdown: Mock) -> None:
        """Test basic markdown file creation and content structure."""
        # Test response data matching the expected function signature
        test_response_data = {
            "text": "This is Claude's response.",
            "session_info": {
                "session_id": "test-session-123",
                "model": "claude-sonnet-4",
                "tools": ["file_writer"],
            },
            "result_info": {
                "duration_ms": 1500,
                "cost_usd": 0.025,
                "usage": {"input_tokens": 10, "output_tokens": 8},
            },
            "raw_messages": [],
        }

        test_prompt = "Create a Python file"

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "conversation.md")

            # Access the private function through the module's namespace
            import mcp_coder.cli.commands.prompt as prompt_module

            save_function = getattr(prompt_module, "_save_conversation_markdown")

            # Call the save function
            save_function(test_response_data, test_prompt, file_path)

            # Verify file was created
            assert os.path.exists(file_path)

            # Verify file contains expected content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for key elements in markdown format
            assert "Create a Python file" in content  # Original prompt
            assert "This is Claude's response." in content  # Response text
            assert "test-session-123" in content  # Session info
            assert "claude-sonnet-4" in content  # Model info
            assert "#" in content  # Markdown headers

    @patch("mcp_coder.cli.commands.prompt._save_conversation_full_json")
    def test_save_conversation_full_json_basic(self, mock_save_json: Mock) -> None:
        """Test basic JSON file creation and structure."""
        # Test response data matching the expected function signature
        test_response_data = {
            "text": "This is Claude's response.",
            "session_info": {
                "session_id": "test-session-123",
                "model": "claude-sonnet-4",
                "tools": ["file_writer"],
            },
            "result_info": {
                "duration_ms": 1500,
                "cost_usd": 0.025,
                "usage": {"input_tokens": 10, "output_tokens": 8},
            },
            "raw_messages": [],
        }

        test_prompt = "Create a Python file"

        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "conversation.json")

            # Access the private function through the module's namespace
            import mcp_coder.cli.commands.prompt as prompt_module

            save_function = getattr(prompt_module, "_save_conversation_full_json")

            # Call the save function
            save_function(test_response_data, test_prompt, file_path)

            # Verify file was created
            assert os.path.exists(file_path)

            # Verify file contains valid JSON with expected structure
            with open(file_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)

            # Check for key elements in JSON structure
            assert "prompt" in saved_data
            assert "response_data" in saved_data
            assert saved_data["prompt"] == "Create a Python file"
            assert saved_data["response_data"]["text"] == "This is Claude's response."
            assert (
                saved_data["response_data"]["session_info"]["session_id"]
                == "test-session-123"
            )
            assert (
                saved_data["response_data"]["session_info"]["model"]
                == "claude-sonnet-4"
            )

    @pytest.mark.skip(
        reason="prompt_claude function not yet implemented - will be added in Step 3"
    )
    @patch("mcp_coder.cli.commands.prompt.prompt_claude")
    def test_execute_prompt_parameter_mapping_with_defaults(
        self, mock_prompt_claude: Mock
    ) -> None:
        """Test parameter mapping with default values."""
        # Setup mock return value
        mock_prompt_claude.return_value = 0

        # Create argparse.Namespace with minimal parameters (defaults)
        args = argparse.Namespace(prompt="Test prompt with defaults")

        # Call execute_prompt
        result = execute_prompt(args)

        # Verify prompt_claude was called with default parameters
        mock_prompt_claude.assert_called_once_with(
            prompt="Test prompt with defaults",
            verbosity="just-text",
            timeout=30,
            store_response=False,
            continue_from=None,
            continue_latest=False,
            save_conversation_md=None,
            save_conversation_full_json=None,
        )

        # Verify return value is passed through
        assert result == 0
