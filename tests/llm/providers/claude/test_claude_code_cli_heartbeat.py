#!/usr/bin/env python3
"""Unit tests for heartbeat and env_vars parameter support in claude_code_cli."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    LLM_HEARTBEAT_INTERVAL_SECONDS,
    ask_claude_code_cli,
)
from mcp_coder.utils.subprocess_runner import CommandResult

from .conftest import StreamJsonFactory


class TestAskClaudeCodeCliHeartbeat:
    """Tests for heartbeat parameter passing to execute_subprocess."""

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_passes_heartbeat_params_to_execute_subprocess(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Verify heartbeat parameters are passed to execute_subprocess."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=0,
                stdout=make_stream_json_output("Response", "sess-hb"),
                stderr="",
                timed_out=False,
            )
            mock_execute.return_value = mock_result

            ask_claude_code_cli("test question", timeout=30)

            assert (
                mock_execute.call_args.kwargs["heartbeat_interval_seconds"]
                == LLM_HEARTBEAT_INTERVAL_SECONDS
            )
            assert (
                "LLM call in progress"
                in mock_execute.call_args.kwargs["heartbeat_message"]
            )

    def test_llm_heartbeat_interval_constant_value(self) -> None:
        """Verify the heartbeat interval constant is 120 seconds (2 minutes)."""
        assert LLM_HEARTBEAT_INTERVAL_SECONDS == 120


class TestEnvVarsParameter:
    """Tests for env_vars parameter support."""

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_with_env_vars(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test that env_vars are passed to subprocess."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=0,
                stdout=make_stream_json_output("Test response", "test-123"),
                stderr="",
                timed_out=False,
            )
            mock_execute.return_value = mock_result

            env_vars = {"MCP_CODER_PROJECT_DIR": "/test/path"}
            result = ask_claude_code_cli("Test question", env_vars=env_vars)

            # Verify env_vars were passed to CommandOptions
            call_args = mock_execute.call_args
            options = call_args[0][1]
            assert options.env == env_vars
            assert result["text"] == "Test response"

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_without_env_vars(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test backward compatibility when env_vars is not provided."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=0,
                stdout=make_stream_json_output(),
                stderr="",
                timed_out=False,
            )
            mock_execute.return_value = mock_result

            result = ask_claude_code_cli("Test question")

            # Verify env is None when not provided
            call_args = mock_execute.call_args
            options = call_args[0][1]
            assert options.env is None
            assert result["text"] == "Test response"
