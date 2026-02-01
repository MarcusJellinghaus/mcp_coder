#!/usr/bin/env python3
"""Unit tests for MCP config parameter handling in claude_code_cli module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm.providers.claude.claude_code_cli import (
    ask_claude_code_cli,
    build_cli_command,
)
from mcp_coder.utils.subprocess_runner import CommandResult

from .conftest import StreamJsonFactory


class TestClaudeMcpConfig:
    """Test suite for MCP config parameter handling."""

    def test_build_cli_command_without_mcp_config(self) -> None:
        """Verify command built correctly without mcp_config parameter."""
        cmd = build_cli_command(session_id=None, claude_cmd="claude")

        # Expected command structure without mcp_config (uses stream-json with full logging)
        assert cmd == [
            "claude",
            "-p",
            "",
            "--output-format",
            "stream-json",
            "--verbose",
            "--input-format",
            "stream-json",
            "--replay-user-messages",
        ]
        assert "--mcp-config" not in cmd
        assert "--strict-mcp-config" not in cmd

    def test_build_cli_command_with_mcp_config(self) -> None:
        """Verify command includes --mcp-config and --strict-mcp-config when specified."""
        cmd = build_cli_command(
            session_id=None, claude_cmd="claude", mcp_config=".mcp.linux.json"
        )

        # Verify basic command structure is preserved
        assert "claude" in cmd
        assert "-p" in cmd
        assert "" in cmd
        assert "--output-format" in cmd
        assert "stream-json" in cmd  # Now uses stream-json

        # Verify mcp_config flags are added
        assert "--mcp-config" in cmd
        assert ".mcp.linux.json" in cmd
        assert "--strict-mcp-config" in cmd

        # Verify --mcp-config flag is followed by the config path
        mcp_config_index = cmd.index("--mcp-config")
        assert cmd[mcp_config_index + 1] == ".mcp.linux.json"

    def test_build_cli_command_with_session_and_mcp_config(self) -> None:
        """Verify both --resume and --mcp-config work together."""
        cmd = build_cli_command(
            session_id="abc123", claude_cmd="claude", mcp_config=".mcp.linux.json"
        )

        # Verify session flags
        assert "--resume" in cmd
        assert "abc123" in cmd

        # Verify mcp_config flags
        assert "--mcp-config" in cmd
        assert ".mcp.linux.json" in cmd
        assert "--strict-mcp-config" in cmd

        # Verify basic command structure
        assert "claude" in cmd
        assert "-p" in cmd
        assert "--output-format" in cmd

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_passes_mcp_config(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Verify ask_claude_code_cli() accepts and passes mcp_config to build_cli_command()."""
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

            # Call ask_claude_code_cli with mcp_config parameter
            result = ask_claude_code_cli("Test question", mcp_config=".mcp.linux.json")

            # Verify the command passed to execute_subprocess contains mcp_config flags
            call_args = mock_execute.call_args
            command = call_args[0][0]

            assert "--mcp-config" in command
            assert ".mcp.linux.json" in command
            assert "--strict-mcp-config" in command

            # Verify response is valid
            assert result["text"] == "Test response"
            assert result["session_id"] == "test-123"

    @patch("mcp_coder.llm.providers.claude.claude_code_cli._find_claude_executable")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.execute_subprocess")
    @patch("mcp_coder.llm.providers.claude.claude_code_cli.get_stream_log_path")
    def test_ask_claude_code_cli_with_session_and_mcp_config(
        self,
        mock_get_path: MagicMock,
        mock_execute: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Verify ask_claude_code_cli() passes both session_id and mcp_config correctly."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_result = CommandResult(
                return_code=0,
                stdout=make_stream_json_output("Continued", "existing"),
                stderr="",
                timed_out=False,
            )
            mock_execute.return_value = mock_result

            # Call with both session_id and mcp_config
            result = ask_claude_code_cli(
                "Follow up", session_id="existing", mcp_config=".mcp.linux.json"
            )

            # Verify command contains both session and mcp_config flags
            call_args = mock_execute.call_args
            command = call_args[0][0]

            assert "--resume" in command
            assert "existing" in command
            assert "--mcp-config" in command
            assert ".mcp.linux.json" in command
            assert "--strict-mcp-config" in command

            # Verify response is valid
            assert result["session_id"] == "existing"
