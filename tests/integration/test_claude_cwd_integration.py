#!/usr/bin/env python3
"""Integration tests for Claude's working directory.

Tests the complete flow from CLI to subprocess execution, verifying that the
project directory is what anchors the Claude subprocess.

This module validates that:
1. project_dir controls where the Claude subprocess runs (working directory)
2. project_dir also controls where files are modified and git operations occur
"""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.utils.subprocess_runner import CommandResult


class _StreamMock:
    """Mimics stream_subprocess output: iterable NDJSON lines + a .result."""

    def __init__(
        self, stdout: str, return_code: int = 0, timed_out: bool = False
    ) -> None:
        self._lines = stdout.split("\n") if stdout else []
        self._result = CommandResult(
            return_code=return_code,
            stdout="",
            stderr="",
            timed_out=timed_out,
        )

    def __iter__(self) -> Iterator[str]:
        return iter(self._lines)

    @property
    def result(self) -> CommandResult:
        return self._result


@pytest.mark.integration
@pytest.mark.claude_cli_integration
class TestSubprocessCwdParameter:
    """Test that subprocess actually receives correct cwd parameter.

    These tests verify the complete flow from command handler through to the
    actual subprocess execution, ensuring project_dir is used as cwd.
    """

    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    def test_prompt_command_no_project_dir_falls_back_to_cwd(
        self,
        mock_prepare_env: MagicMock,
        mock_execute_subprocess: MagicMock,
        require_claude_cli: None,
    ) -> None:
        """No --project-dir: the subprocess cwd is the shell's CWD.

        This documents the no-``project_dir`` fallback, not the default. The
        default is ``project_dir`` (see
        ``test_prompt_command_defaults_cwd_to_project_dir`` below); this test
        only reaches the CWD because ``project_dir`` is None.
        """
        from mcp_coder.cli.commands.prompt import execute_prompt

        # Setup
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}

        # Create proper subprocess result mock with all required attributes
        # The CLI uses stream-json format (NDJSON) by default
        mock_execute_subprocess.return_value = _StreamMock(
            '{"type": "assistant", "message": {"content": [{"type": "text", "text": "Claude response"}]}}\n'
            '{"type": "result", "session_id": "test-session-456", "result": "Claude response"}'
        )

        # Execute with project_dir=None (default)
        import argparse

        args = argparse.Namespace(
            prompt="Test prompt",
            project_dir=None,
            timeout=30,
            llm_method="claude",
            verbosity="just-text",
            session_id=None,
            mcp_config=None,
        )

        result = execute_prompt(args)

        # Verify
        assert result == 0
        # Check that execute_subprocess was called with the process CWD
        assert mock_execute_subprocess.called
        # execute_subprocess is called with (command, options) as positional args
        call_args = mock_execute_subprocess.call_args[0]
        assert len(call_args) == 2  # command, options
        options = call_args[1]
        # With project_dir=None the command falls back to Path.cwd(), which is
        # then converted to string and passed as cwd.
        assert options.cwd == str(Path.cwd())

    @patch("mcp_coder.llm.providers.claude.claude_code_cli_streaming.stream_subprocess")
    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    def test_prompt_command_defaults_cwd_to_project_dir(
        self,
        mock_prepare_env: MagicMock,
        mock_execute_subprocess: MagicMock,
        require_claude_cli: None,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        """The subprocess cwd is --project-dir, not the shell's cwd."""
        from mcp_coder.cli.commands.prompt import execute_prompt

        # Setup
        project_dir = tmp_path / "repo"
        project_dir.mkdir()
        elsewhere = tmp_path / "elsewhere"
        elsewhere.mkdir()

        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": str(project_dir)}

        # Create proper subprocess result mock with all required attributes
        # The CLI uses stream-json format (NDJSON) by default
        mock_execute_subprocess.return_value = _StreamMock(
            '{"type": "assistant", "message": {"content": [{"type": "text", "text": "Claude response"}]}}\n'
            '{"type": "result", "session_id": "test-session-789", "result": "Claude response"}'
        )

        # Execute with an explicit project_dir
        import argparse

        args = argparse.Namespace(
            prompt="Test prompt",
            project_dir=str(project_dir),
            timeout=30,
            llm_method="claude",
            verbosity="just-text",
            session_id=None,
            mcp_config=None,
        )

        # Stand outside the project directory: "from any shell working directory"
        # is half the acceptance criterion.
        monkeypatch.chdir(elsewhere)

        result = execute_prompt(args)

        # Verify
        assert result == 0
        assert mock_execute_subprocess.called
        # execute_subprocess is called with (command, options) as positional args
        call_args = mock_execute_subprocess.call_args[0]
        assert len(call_args) == 2  # command, options
        options = call_args[1]
        assert options.cwd == str(project_dir)
        assert options.cwd != str(Path.cwd())
