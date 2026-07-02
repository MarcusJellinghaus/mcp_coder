#!/usr/bin/env python3
"""Unit tests for env_vars parameter support in claude_code_cli."""

import tempfile
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.llm.providers.claude.claude_code_cli import ask_claude_code_cli
from mcp_coder.utils.subprocess_runner import CommandResult

from .conftest import StreamJsonFactory


class _MockStreamResult:
    """Mimics StreamResult for testing: iterable with a .result property."""

    def __init__(self, lines: list[str]) -> None:
        self._lines = lines
        self._result = CommandResult(
            return_code=0,
            stdout="",
            stderr="",
            timed_out=False,
        )

    def __iter__(self) -> Iterator[str]:
        return iter(self._lines)

    @property
    def result(self) -> CommandResult:
        return self._result


class TestEnvVarsParameter:
    """Tests for env_vars parameter support (forwarded via the streaming core)."""

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_code_cli_with_env_vars(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test that env_vars are passed to the subprocess options."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _MockStreamResult(
                make_stream_json_output("Test response", "test-123").split("\n")
            )

            env_vars = {"MCP_CODER_PROJECT_DIR": "/test/path"}
            result = ask_claude_code_cli("Test question", env_vars=env_vars)

            # Verify env_vars were passed to CommandOptions
            call_args = mock_stream.call_args
            options = call_args[0][1]
            assert options.env == env_vars
            assert result["text"] == "Test response"

    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming._find_claude_executable"
    )
    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch(
        "mcp_coder.llm.providers.claude.claude_code_cli_streaming.get_stream_log_path"
    )
    def test_ask_claude_code_cli_without_env_vars(
        self,
        mock_get_path: MagicMock,
        mock_stream: MagicMock,
        mock_find: MagicMock,
        make_stream_json_output: StreamJsonFactory,
    ) -> None:
        """Test backward compatibility when env_vars is not provided."""
        mock_find.return_value = "claude"
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_get_path.return_value = Path(tmpdir) / "test.ndjson"
            mock_stream.return_value = _MockStreamResult(
                make_stream_json_output().split("\n")
            )

            result = ask_claude_code_cli("Test question")

            # Verify env is None when not provided
            call_args = mock_stream.call_args
            options = call_args[0][1]
            assert options.env is None
            assert result["text"] == "Test response"
