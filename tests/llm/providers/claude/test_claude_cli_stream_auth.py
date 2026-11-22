"""Tests for the streaming error event built from the ``result`` message.

Covers the logged-out capture (issue #33): one ``auth`` error event, no
double-printed CLI text, and the non-auth ``is_error`` variants.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from mcp_coder.llm.providers.claude.claude_code_cli_streaming import (
    ask_claude_code_cli_stream,
)
from mcp_coder.llm.types import StreamEvent
from mcp_coder.utils.subprocess_runner import CommandResult
from tests.logged_out_capture import (
    AUTH_HINT,
    AUTH_MESSAGE,
    CLI_TEXT,
    LOGGED_OUT_RC,
    LOGGED_OUT_STDERR,
    load_logged_out_lines,
)

_MODULE = "mcp_coder.llm.providers.claude.claude_code_cli_streaming"


def _make_mock_stream(
    lines: list[str],
    *,
    timed_out: bool = False,
    return_code: int = 0,
    stderr: str = "",
) -> MagicMock:
    """Create a mock stream_subprocess return value."""
    mock_stream = MagicMock()
    mock_stream.__iter__ = lambda self: iter(lines)
    mock_stream.result = CommandResult(
        return_code=return_code,
        stdout="",
        stderr=stderr,
        timed_out=timed_out,
    )
    return mock_stream


def _lines_with_result_text(text: str) -> list[str]:
    """Return the fixture lines with the result message's text replaced."""
    lines = load_logged_out_lines()
    result = json.loads(lines[-1])
    result["result"] = text
    return lines[:-1] + [json.dumps(result)]


def _result_line(**fields: object) -> str:
    """Build a minimal ``result`` NDJSON line."""
    return json.dumps({"type": "result", "session_id": "sess-1", **fields})


def _errors(events: list[StreamEvent]) -> list[StreamEvent]:
    return [e for e in events if e.get("type") == "error"]


@patch(f"{_MODULE}.stream_subprocess")
@patch(f"{_MODULE}.get_stream_log_path")
@patch(f"{_MODULE}._find_claude_executable", return_value="claude")
class TestStreamAuthError:
    """Error event emitted after the loop from the final ``result`` message."""

    @staticmethod
    def _run(
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
        lines: list[str],
        **stream_kwargs: object,
    ) -> list[StreamEvent]:
        mock_log_path.return_value = tmp_path / "stream.ndjson"
        mock_stream_sub.return_value = _make_mock_stream(
            lines,
            **stream_kwargs,  # type: ignore[arg-type]
        )
        return list(ask_claude_code_cli_stream("Reply with OK"))

    def test_logged_out_capture_yields_one_auth_error(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """The capture yields exactly one auth error with the hinted CLI text."""
        events = self._run(
            mock_log_path,
            mock_stream_sub,
            tmp_path,
            load_logged_out_lines(),
            return_code=LOGGED_OUT_RC,
            stderr=LOGGED_OUT_STDERR,
        )
        errors = _errors(events)
        assert len(errors) == 1
        assert errors[0]["reason"] == "auth"
        assert errors[0]["return_code"] == LOGGED_OUT_RC
        message = str(errors[0]["message"])
        assert message == AUTH_MESSAGE
        assert message.startswith(AUTH_HINT)
        assert message.count(AUTH_HINT) == 1
        assert "trust" not in message
        assert "\n" not in message

    def test_logged_out_capture_does_not_print_cli_text(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """The flagged assistant block yields no text_delta; done is still emitted."""
        events = self._run(
            mock_log_path,
            mock_stream_sub,
            tmp_path,
            load_logged_out_lines(),
            return_code=LOGGED_OUT_RC,
            stderr=LOGGED_OUT_STDERR,
        )
        deltas = [e for e in events if e.get("type") == "text_delta"]
        assert all(CLI_TEXT not in str(e.get("text")) for e in deltas)
        assert len([e for e in events if e.get("type") == "done"]) == 1

    def test_unflagged_assistant_text_still_yields_text_delta(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """An assistant text block without the flag is still streamed."""
        assistant = json.dumps(
            {
                "type": "assistant",
                "message": {"content": [{"type": "text", "text": "OK"}]},
            }
        )
        lines = [assistant, _result_line(is_error=False, result="OK")]
        events = self._run(mock_log_path, mock_stream_sub, tmp_path, lines)
        deltas = [e for e in events if e.get("type") == "text_delta"]
        assert [e["text"] for e in deltas] == ["OK"]
        assert not _errors(events)

    def test_non_auth_is_error_with_nonzero_exit(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A non-auth is_error result reports its text plus stderr."""
        lines = [
            _result_line(is_error=True, subtype="success", result="Something broke")
        ]
        events = self._run(
            mock_log_path,
            mock_stream_sub,
            tmp_path,
            lines,
            return_code=1,
            stderr="boom",
        )
        errors = _errors(events)
        assert len(errors) == 1
        assert errors[0]["reason"] == "nonzero_exit"
        assert errors[0]["message"] == "Something broke; stderr: boom"

    def test_is_error_with_exit_zero_is_result_error(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Exit 0 with is_error is now a failure (reason result_error)."""
        events = self._run(
            mock_log_path,
            mock_stream_sub,
            tmp_path,
            _lines_with_result_text("Something broke"),
            return_code=0,
        )
        errors = _errors(events)
        assert len(errors) == 1
        assert errors[0]["reason"] == "result_error"
        assert errors[0]["return_code"] == 0
        assert errors[0]["message"] == "Something broke"

    def test_is_error_with_empty_result_text(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Empty result text with subtype success gives the generic message."""
        lines = [_result_line(is_error=True, subtype="success", result="")]
        events = self._run(
            mock_log_path, mock_stream_sub, tmp_path, lines, return_code=0
        )
        errors = _errors(events)
        assert len(errors) == 1
        message = str(errors[0]["message"])
        assert message == "CLI reported an error"
        assert "code 0" not in message

    def test_timeout_takes_precedence_over_is_error(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A timed-out run yields only the inactivity_timeout event."""
        events = self._run(
            mock_log_path,
            mock_stream_sub,
            tmp_path,
            load_logged_out_lines(),
            timed_out=True,
            return_code=LOGGED_OUT_RC,
        )
        errors = _errors(events)
        assert len(errors) == 1
        assert errors[0]["reason"] == "inactivity_timeout"

    def test_exit_zero_without_is_error_yields_no_error(
        self,
        _mock_find: MagicMock,
        mock_log_path: MagicMock,
        mock_stream_sub: MagicMock,
        tmp_path: Path,
    ) -> None:
        """A clean run yields no error event."""
        lines = [_result_line(is_error=False, subtype="success", result="OK")]
        events = self._run(mock_log_path, mock_stream_sub, tmp_path, lines)
        assert not _errors(events)
