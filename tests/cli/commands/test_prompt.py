"""Tests for prompt command functionality."""

import argparse
import json
from unittest.mock import Mock, mock_open, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt


class TestExecutePrompt:
    """Tests for execute_prompt function."""

    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_basic_prompt_success(
        self,
        mock_ask_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful prompt execution with mocked ask_llm function."""
        mock_ask_llm.return_value = "The capital of France is Paris."
        args = argparse.Namespace(prompt="What is the capital of France?")

        result = execute_prompt(args)

        assert result == 0
        mock_ask_llm.assert_called_once_with(
            "What is the capital of France?",
            provider="claude",
            method="api",
            timeout=30,
            session_id=None,
        )
        captured = capsys.readouterr()
        assert "The capital of France is Paris." in captured.out

    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    def test_prompt_api_error(
        self,
        mock_ask_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test API error handling when Claude API fails."""
        mock_ask_llm.side_effect = Exception("Claude API connection failed")
        args = argparse.Namespace(prompt="Test question")

        result = execute_prompt(args)

        assert result == 1
        captured = capsys.readouterr()
        assert "Error" in captured.err
        assert "Claude API connection failed" in captured.err

    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_success(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test successful continuation from stored response file using session_id."""
        stored_response = {
            "response_data": {"session_info": {"session_id": "previous-session-456"}}
        }

        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(stored_response)
        mock_ask_llm.return_value = "Adding error handling."

        args = argparse.Namespace(
            prompt="Add error handling",
            continue_session_from="path/to/previous_response.json",
        )

        result = execute_prompt(args)

        assert result == 0
        mock_ask_llm.assert_called_once_with(
            "Add error handling",
            provider="claude",
            method="api",
            timeout=30,
            session_id="previous-session-456",
        )
        captured = capsys.readouterr()
        assert "Adding error handling." in captured.out
        assert "Resuming session: previous-session" in captured.out

    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch("os.path.exists")
    def test_continue_from_file_not_found(
        self,
        mock_exists: Mock,
        mock_ask_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling when continue_from file doesn't exist."""
        mock_exists.return_value = False
        mock_ask_llm.return_value = "Starting new conversation."

        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_session_from="path/to/nonexistent_file.json",
        )

        result = execute_prompt(args)

        assert result == 0
        mock_ask_llm.assert_called_once_with(
            "Continue conversation",
            provider="claude",
            method="api",
            timeout=30,
            session_id=None,
        )
        captured = capsys.readouterr()
        assert (
            "Warning: No session_id found" in captured.out
            or "starting new conversation" in captured.out.lower()
        )

    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_invalid_json(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling when continue_from file contains invalid JSON."""
        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = "{ invalid json content }"
        mock_ask_llm.return_value = "Starting new conversation."

        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_session_from="path/to/invalid.json",
        )

        result = execute_prompt(args)

        assert result == 0
        mock_ask_llm.assert_called_once_with(
            "Continue conversation",
            provider="claude",
            method="api",
            timeout=30,
            session_id=None,
        )
        captured = capsys.readouterr()
        assert (
            "Warning: No session_id found" in captured.out
            or "starting new conversation" in captured.out.lower()
        )

    @patch("mcp_coder.cli.commands.prompt.ask_llm")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_missing_session_id(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_llm: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test graceful handling when continue_from file has missing session_id."""
        incomplete_response = {"metadata": {"timestamp": "2025-09-19T10:30:00Z"}}

        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(incomplete_response)
        mock_ask_llm.return_value = "Starting new conversation."

        args = argparse.Namespace(
            prompt="Continue conversation",
            continue_session_from="path/to/incomplete.json",
        )

        result = execute_prompt(args)

        assert result == 0
        mock_ask_llm.assert_called_once_with(
            "Continue conversation",
            provider="claude",
            method="api",
            timeout=30,
            session_id=None,
        )
        captured = capsys.readouterr()
        assert "Warning: No session_id found" in captured.out

    @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
    @patch("builtins.open", new_callable=mock_open)
    @patch("os.path.exists")
    def test_continue_from_with_verbose_output(
        self,
        mock_exists: Mock,
        mock_file_open: Mock,
        mock_ask_claude: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test continuation functionality works with verbose verbosity."""
        stored_response = {
            "response_data": {
                "session_info": {"session_id": "verbose-continuation-123"}
            }
        }

        mock_exists.return_value = True
        mock_file_open.return_value.read.return_value = json.dumps(stored_response)

        new_response = {
            "text": "Here are some advanced Python features.",
            "session_info": {"session_id": "verbose-continuation-new-456"},
            "result_info": {"duration_ms": 2500, "cost_usd": 0.040},
        }
        mock_ask_claude.return_value = new_response

        args = argparse.Namespace(
            prompt="Tell me about advanced features",
            continue_session_from="path/to/previous.json",
            verbosity="verbose",
        )

        result = execute_prompt(args)

        assert result == 0
        mock_ask_claude.assert_called_once_with(
            "Tell me about advanced features",
            30,
            "verbose-continuation-123",
        )
        captured = capsys.readouterr()
        assert "Here are some advanced Python features." in captured.out
        assert "verbose-continuation-new-456" in captured.out
