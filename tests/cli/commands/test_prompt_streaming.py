"""Integration tests for streaming output in the prompt command.

Tests the streaming paths (text, ndjson, json-raw) in execute_prompt(),
verifying events flow through ResponseAssembler and print_stream_event.
"""

import argparse
import json
from typing import Any
from unittest import mock
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt


def _stream_events(
    text: str = "Hello world",
    session_id: str | None = "test-session-abc",
    include_tool: bool = False,
) -> list[dict[str, object]]:
    """Build a sequence of stream events for testing."""
    events: list[dict[str, object]] = []
    if include_tool:
        events.append(
            {"type": "tool_use_start", "name": "read_file", "args": {"path": "x.py"}}
        )
        events.append({"type": "tool_result", "name": "read_file", "output": "content"})
    events.append({"type": "text_delta", "text": text})
    done: dict[str, object] = {"type": "done", "usage": {"input_tokens": 10}}
    if session_id is not None:
        done["session_id"] = session_id
    events.append(done)
    return events


def _make_args(**overrides: Any) -> argparse.Namespace:
    """Create a prompt args Namespace with sensible defaults."""
    defaults: dict[str, Any] = {
        "prompt": "test prompt",
        "output_format": "text",
        "timeout": 30,
        "llm_method": "claude",
        "session_id": None,
        "continue_session_from": None,
        "continue_session": False,
        "project_dir": None,
        "execution_dir": None,
        "mcp_config": None,
        "store_response": False,
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Helpers shared across patch stacks
# ---------------------------------------------------------------------------
_RESOLVE_LLM = "mcp_coder.cli.commands.prompt.resolve_llm_method"
_PREPARE_ENV = "mcp_coder.cli.commands.prompt.prepare_llm_environment"
_STREAM = "mcp_coder.cli.commands.prompt.prompt_llm_stream"
_RESOLVE_MCP = "mcp_coder.cli.commands.prompt.resolve_mcp_config_path"


class TestStreamingTextFormat:
    """Tests for --output-format text (default) streaming path."""

    @patch(_RESOLVE_MCP)
    @patch(_RESOLVE_LLM)
    @patch(_PREPARE_ENV)
    @patch(_STREAM)
    def test_text_format_prints_streamed_text(
        self,
        mock_stream: Mock,
        mock_env: Mock,
        mock_llm: Mock,
        mock_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Text format streams text_delta content to stdout."""
        mock_llm.return_value = ("claude", "cli")
        mock_mcp.return_value = None
        mock_env.return_value = {"MCP_CODER_PROJECT_DIR": "/t"}
        mock_stream.return_value = iter(
            _stream_events(text="Streamed answer", session_id="s1")
        )

        result = execute_prompt(_make_args(output_format="text"))

        assert result == 0
        captured = capsys.readouterr()
        assert "Streamed answer" in captured.out

    @patch(_RESOLVE_MCP)
    @patch(_RESOLVE_LLM)
    @patch(_PREPARE_ENV)
    @patch(_STREAM)
    def test_text_format_shows_tool_calls(
        self,
        mock_stream: Mock,
        mock_env: Mock,
        mock_llm: Mock,
        mock_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Text format renders tool use start and result."""
        mock_llm.return_value = ("claude", "cli")
        mock_mcp.return_value = None
        mock_env.return_value = {"MCP_CODER_PROJECT_DIR": "/t"}
        mock_stream.return_value = iter(_stream_events(text="Done", include_tool=True))

        result = execute_prompt(_make_args(output_format="text"))

        assert result == 0
        captured = capsys.readouterr()
        assert "read_file" in captured.out
        assert "Done" in captured.out


class TestStreamingNdjsonFormat:
    """Tests for --output-format ndjson streaming path."""

    @patch(_RESOLVE_MCP)
    @patch(_RESOLVE_LLM)
    @patch(_PREPARE_ENV)
    @patch(_STREAM)
    def test_ndjson_emits_json_lines(
        self,
        mock_stream: Mock,
        mock_env: Mock,
        mock_llm: Mock,
        mock_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """NDJSON format emits one JSON object per line."""
        mock_llm.return_value = ("claude", "cli")
        mock_mcp.return_value = None
        mock_env.return_value = {"MCP_CODER_PROJECT_DIR": "/t"}
        mock_stream.return_value = iter(
            _stream_events(text="token", session_id="sess-1")
        )

        result = execute_prompt(_make_args(output_format="ndjson"))

        assert result == 0
        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().split("\n") if l.strip()]
        assert len(lines) >= 2  # at least text_delta + done/result
        # Each line should be valid JSON
        for line in lines:
            parsed = json.loads(line)
            assert "type" in parsed

    @patch(_RESOLVE_MCP)
    @patch(_RESOLVE_LLM)
    @patch(_PREPARE_ENV)
    @patch(_STREAM)
    def test_ndjson_includes_session_id_in_result(
        self,
        mock_stream: Mock,
        mock_env: Mock,
        mock_llm: Mock,
        mock_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """NDJSON result line includes session_id."""
        mock_llm.return_value = ("claude", "cli")
        mock_mcp.return_value = None
        mock_env.return_value = {"MCP_CODER_PROJECT_DIR": "/t"}
        mock_stream.return_value = iter(
            _stream_events(text="hi", session_id="my-session-id")
        )

        result = execute_prompt(_make_args(output_format="ndjson"))

        assert result == 0
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        result_lines = [json.loads(l) for l in lines if l.strip() and '"result"' in l]
        assert len(result_lines) == 1
        assert result_lines[0].get("session_id") == "my-session-id"

    @patch(_RESOLVE_MCP)
    @patch(_RESOLVE_LLM)
    @patch(_PREPARE_ENV)
    @patch(_STREAM)
    def test_ndjson_includes_tool_events(
        self,
        mock_stream: Mock,
        mock_env: Mock,
        mock_llm: Mock,
        mock_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """NDJSON format includes tool_use and tool_result events."""
        mock_llm.return_value = ("claude", "cli")
        mock_mcp.return_value = None
        mock_env.return_value = {"MCP_CODER_PROJECT_DIR": "/t"}
        mock_stream.return_value = iter(
            _stream_events(text="answer", include_tool=True)
        )

        result = execute_prompt(_make_args(output_format="ndjson"))

        assert result == 0
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        all_parsed = [json.loads(l) for l in lines if l.strip()]
        types = [p["type"] for p in all_parsed]
        assert "assistant" in types  # tool_use_start maps to assistant
        assert "user" in types  # tool_result maps to user


class TestStreamingJsonRawFormat:
    """Tests for --output-format json-raw streaming path."""

    @patch(_RESOLVE_MCP)
    @patch(_RESOLVE_LLM)
    @patch(_PREPARE_ENV)
    @patch(_STREAM)
    def test_json_raw_passes_through_raw_lines(
        self,
        mock_stream: Mock,
        mock_env: Mock,
        mock_llm: Mock,
        mock_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """json-raw format passes through raw_line events as-is."""
        mock_llm.return_value = ("claude", "cli")
        mock_mcp.return_value = None
        mock_env.return_value = {"MCP_CODER_PROJECT_DIR": "/t"}
        raw_json = '{"type":"assistant","message":{"role":"assistant"}}'
        events: list[dict[str, object]] = [
            {"type": "raw_line", "line": raw_json},
            {"type": "text_delta", "text": "ignored in json-raw"},
            {"type": "done"},
        ]
        mock_stream.return_value = iter(events)

        result = execute_prompt(_make_args(output_format="json-raw"))

        assert result == 0
        captured = capsys.readouterr()
        # Only raw_line content should appear
        assert raw_json in captured.out
        # text_delta should NOT appear (json-raw only shows raw_line)
        assert "ignored in json-raw" not in captured.out

    @patch(_RESOLVE_MCP)
    @patch(_RESOLVE_LLM)
    @patch(_PREPARE_ENV)
    @patch(_STREAM)
    def test_json_raw_multiple_lines(
        self,
        mock_stream: Mock,
        mock_env: Mock,
        mock_llm: Mock,
        mock_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """json-raw outputs multiple raw lines."""
        mock_llm.return_value = ("claude", "cli")
        mock_mcp.return_value = None
        mock_env.return_value = {"MCP_CODER_PROJECT_DIR": "/t"}
        events: list[dict[str, object]] = [
            {"type": "raw_line", "line": '{"type":"assistant","seq":1}'},
            {"type": "raw_line", "line": '{"type":"assistant","seq":2}'},
            {"type": "done"},
        ]
        mock_stream.return_value = iter(events)

        result = execute_prompt(_make_args(output_format="json-raw"))

        assert result == 0
        captured = capsys.readouterr()
        lines = [l for l in captured.out.strip().split("\n") if l.strip()]
        assert len(lines) == 2
        assert json.loads(lines[0])["seq"] == 1
        assert json.loads(lines[1])["seq"] == 2


class TestStreamingStoreResponse:
    """Tests for --store-response with streaming formats."""

    @patch("mcp_coder.cli.commands.prompt.store_session")
    @patch(_RESOLVE_MCP)
    @patch(_RESOLVE_LLM)
    @patch(_PREPARE_ENV)
    @patch(_STREAM)
    def test_store_response_saves_assembled_result(
        self,
        mock_stream: Mock,
        mock_env: Mock,
        mock_llm: Mock,
        mock_mcp: Mock,
        mock_store: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """With --store-response, the assembled response is stored."""
        mock_llm.return_value = ("claude", "cli")
        mock_mcp.return_value = None
        mock_env.return_value = {"MCP_CODER_PROJECT_DIR": "/t"}
        mock_stream.return_value = iter(
            _stream_events(text="stored text", session_id="store-sess")
        )
        mock_store.return_value = "/tmp/stored.json"

        result = execute_prompt(_make_args(output_format="text", store_response=True))

        assert result == 0
        mock_store.assert_called_once()
        stored_response = mock_store.call_args[0][0]
        assert stored_response["text"] == "stored text"
        assert stored_response["session_id"] == "store-sess"


class TestStreamingErrorHandling:
    """Tests for error handling in streaming paths."""

    @patch(_RESOLVE_MCP)
    @patch(_RESOLVE_LLM)
    @patch(_PREPARE_ENV)
    @patch(_STREAM)
    def test_stream_exception_returns_error(
        self,
        mock_stream: Mock,
        mock_env: Mock,
        mock_llm: Mock,
        mock_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Exception during streaming returns exit code 1."""
        mock_llm.return_value = ("claude", "cli")
        mock_mcp.return_value = None
        mock_env.return_value = {"MCP_CODER_PROJECT_DIR": "/t"}
        mock_stream.side_effect = Exception("stream failed")

        result = execute_prompt(_make_args(output_format="ndjson"))

        assert result == 1
        captured = capsys.readouterr()
        assert "stream failed" in captured.err

    @patch(_RESOLVE_MCP)
    @patch(_RESOLVE_LLM)
    @patch(_PREPARE_ENV)
    @patch(_STREAM)
    def test_error_event_printed_to_stderr_in_text_format(
        self,
        mock_stream: Mock,
        mock_env: Mock,
        mock_llm: Mock,
        mock_mcp: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Error events are printed to stderr in text format."""
        mock_llm.return_value = ("claude", "cli")
        mock_mcp.return_value = None
        mock_env.return_value = {"MCP_CODER_PROJECT_DIR": "/t"}
        events: list[dict[str, object]] = [
            {"type": "error", "message": "something went wrong"},
            {"type": "done"},
        ]
        mock_stream.return_value = iter(events)

        result = execute_prompt(_make_args(output_format="text"))

        assert result == 0
        captured = capsys.readouterr()
        assert "something went wrong" in captured.err
