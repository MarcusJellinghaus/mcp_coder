#!/usr/bin/env python3
"""Shared pytest fixtures for Claude provider unit tests."""

import json

import pytest


@pytest.fixture
def make_stream_json_output():
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
