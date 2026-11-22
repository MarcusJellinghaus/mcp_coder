"""Tests for the exception mapping in ``ask_claude_code_cli`` (issue #33).

``reason == "auth"`` raises ``LLMAuthError``; other failures stay
``CalledProcessError`` with the return code clamped to at least 1.
"""

import json
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mcp_coder.llm import interface
from mcp_coder.llm.providers.claude.claude_code_cli import ask_claude_code_cli
from mcp_coder.llm.types import LLMAuthError
from mcp_coder.utils.subprocess_runner import CalledProcessError, CommandResult

from .logged_out_capture import (
    AUTH_MESSAGE,
    LOGGED_OUT_RC,
    LOGGED_OUT_STDERR,
    load_logged_out_lines,
)

_MODULE = "mcp_coder.llm.providers.claude.claude_code_cli_streaming"
_CLI_LOGGER = "mcp_coder.llm.providers.claude.claude_code_cli"


def _make_mock_stream(
    lines: list[str], *, return_code: int = 0, stderr: str = ""
) -> MagicMock:
    """Create a mock stream_subprocess return value."""
    mock_stream = MagicMock()
    mock_stream.__iter__ = lambda self: iter(lines)
    mock_stream.result = CommandResult(
        return_code=return_code,
        stdout="",
        stderr=stderr,
        timed_out=False,
    )
    return mock_stream


def _result_line(**fields: object) -> str:
    """Build a minimal ``result`` NDJSON line."""
    return json.dumps({"type": "result", "session_id": "sess-1", **fields})


@patch(f"{_MODULE}.stream_subprocess")
@patch(f"{_MODULE}.get_stream_log_path")
@patch(f"{_MODULE}._find_claude_executable", return_value="claude")
class TestAskClaudeCodeCliAuthErrors:
    """Error events from the streaming core map to typed exceptions."""

    @staticmethod
    def _run(
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
        lines: list[str],
        *,
        return_code: int = 0,
        stderr: str = "",
    ) -> None:
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        mock_stream_sub.return_value = _make_mock_stream(
            lines, return_code=return_code, stderr=stderr
        )
        ask_claude_code_cli("Reply with OK")

    def test_logged_out_capture_raises_llm_auth_error(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """The capture raises LLMAuthError carrying exactly the event message."""
        with pytest.raises(LLMAuthError) as exc_info:
            self._run(
                mock_log_path,
                mock_stream_sub,
                tmp_path,
                load_logged_out_lines(),
                return_code=LOGGED_OUT_RC,
                stderr=LOGGED_OUT_STDERR,
            )
        assert str(exc_info.value) == AUTH_MESSAGE
        assert "Stream file" not in str(exc_info.value)

    def test_stream_file_path_logged_at_debug(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The stream-file path goes to a DEBUG record instead of the message."""
        caplog.set_level(logging.DEBUG, logger=_CLI_LOGGER)
        with pytest.raises(LLMAuthError):
            self._run(
                mock_log_path,
                mock_stream_sub,
                tmp_path,
                load_logged_out_lines(),
                return_code=LOGGED_OUT_RC,
                stderr=LOGGED_OUT_STDERR,
            )
        stream_path = str(tmp_path / "stream.ndjson")
        assert any(
            record.name == _CLI_LOGGER
            and record.levelno == logging.DEBUG
            and stream_path in record.getMessage()
            for record in caplog.records
        )

    def test_exit_zero_with_is_error_raises_called_process_error_rc_1(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Exit 0 with a non-auth is_error result is clamped to returncode 1."""
        lines = [
            _result_line(is_error=True, subtype="success", result="Something broke")
        ]
        with pytest.raises(CalledProcessError) as exc_info:
            self._run(mock_log_path, mock_stream_sub, tmp_path, lines, return_code=0)
        assert exc_info.value.returncode == 1
        assert "Something broke" in str(exc_info.value.stderr)

    def test_nonzero_exit_with_non_auth_stderr_is_called_process_error(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Stderr "auth failed" is not an auth pattern: CalledProcessError(1)."""
        lines = [_result_line(is_error=False, subtype="success", result="")]
        with pytest.raises(CalledProcessError) as exc_info:
            self._run(
                mock_log_path,
                mock_stream_sub,
                tmp_path,
                lines,
                return_code=1,
                stderr="auth failed",
            )
        assert not isinstance(exc_info.value, LLMAuthError)
        assert exc_info.value.returncode == 1

    def test_auth_error_is_interface_llm_auth_error(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """The raised error is the same class re-exported by llm.interface."""
        with pytest.raises(LLMAuthError) as exc_info:
            self._run(
                mock_log_path,
                mock_stream_sub,
                tmp_path,
                load_logged_out_lines(),
                return_code=LOGGED_OUT_RC,
                stderr=LOGGED_OUT_STDERR,
            )
        assert isinstance(exc_info.value, interface.LLMAuthError)
