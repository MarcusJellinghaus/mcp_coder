#!/usr/bin/env python3
"""Shared pytest fixtures for Claude provider tests."""

import json
from collections.abc import Callable, Iterator

import pytest

from mcp_coder.utils.subprocess_runner import CommandResult

# Type alias for the stream output factory function
# Uses Callable[..., str] to allow optional/default arguments
StreamJsonFactory = Callable[..., str]


class _MockStreamResult:
    """Mimics StreamResult for testing: iterable with a .result property."""

    def __init__(
        self,
        lines: list[str],
        return_code: int = 0,
        timed_out: bool = False,
    ) -> None:
        self._lines = lines
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


def _make_stream_gen(
    lines: list[str],
    return_code: int = 0,
    timed_out: bool = False,
) -> _MockStreamResult:
    """Create a mock StreamResult mimicking stream_subprocess output."""
    return _MockStreamResult(lines, return_code=return_code, timed_out=timed_out)


@pytest.fixture
def make_stream_json_output() -> StreamJsonFactory:
    """Factory fixture to create valid stream-json output for testing.

    Usage:
        def test_something(make_stream_json_output):
            output = make_stream_json_output("Response text", "session-123")
            # ... use output in test
    """

    def _make_stream_json_output(
        result_text: str = "Test response",
        session_id: str = "test-session-123",
        is_error: bool = False,
    ) -> str:
        """Create valid stream-json output for testing."""
        system_msg = json.dumps(
            {
                "type": "system",
                "subtype": "init",
                "session_id": session_id,
                "model": "claude-opus-4-5-20251101",
                "tools": ["Task", "Bash"],
            }
        )
        assistant_msg = json.dumps(
            {
                "type": "assistant",
                "message": {
                    "content": [{"type": "text", "text": result_text}],
                },
                "session_id": session_id,
            }
        )
        result_msg = json.dumps(
            {
                "type": "result",
                "subtype": "success" if not is_error else "error",
                "is_error": is_error,
                "result": result_text,
                "session_id": session_id,
                "duration_ms": 1500,
                "total_cost_usd": 0.05,
                "usage": {"input_tokens": 100, "output_tokens": 50},
            }
        )
        return f"{system_msg}\n{assistant_msg}\n{result_msg}"

    return _make_stream_json_output
