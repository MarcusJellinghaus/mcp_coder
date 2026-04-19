"""Shared fixtures for Copilot CLI tests."""

import json
from collections.abc import Callable
from typing import Any

import pytest


@pytest.fixture()
def make_copilot_jsonl_output() -> Callable[..., list[str]]:
    """Factory fixture that creates valid canned JSONL strings.

    Generates Copilot JSONL output with configurable text, session_id, and usage.
    """

    def _factory(
        text: str = "Hello from Copilot",
        session_id: str = "test-session-123",
        output_tokens: int = 42,
        include_tool_request: bool = False,
        extra_ephemeral_types: list[str] | None = None,
    ) -> list[str]:
        lines: list[str] = []

        # Ephemeral types (should be skipped by parser)
        if extra_ephemeral_types:
            for etype in extra_ephemeral_types:
                lines.append(json.dumps({"type": etype, "data": "ephemeral"}))

        # assistant.message with text content (real Copilot format: data.content is a string)
        assistant_msg: dict[str, Any] = {
            "type": "assistant.message",
            "data": {
                "content": text,
                "toolRequests": [],
            },
        }
        if include_tool_request:
            assistant_msg["data"]["toolRequests"] = [
                {"id": "tool-1", "name": "read_file", "args": {"path": "foo.py"}}
            ]
        lines.append(json.dumps(assistant_msg))

        if include_tool_request:
            lines.append(
                json.dumps(
                    {
                        "type": "tool.execution_complete",
                        "toolId": "tool-1",
                        "result": "file contents",
                    }
                )
            )

        # result message
        lines.append(
            json.dumps(
                {
                    "type": "result",
                    "sessionId": session_id,
                    "usage": {"outputTokens": output_tokens},
                    "exitCode": 0,
                }
            )
        )

        return lines

    return _factory
