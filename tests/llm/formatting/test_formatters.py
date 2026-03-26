"""Tests for response formatting functions."""

import argparse
import json
from typing import Any, Dict, Iterator, List
from unittest.mock import Mock, patch

import pytest

from mcp_coder.cli.commands.prompt import execute_prompt
from mcp_coder.llm.types import StreamEvent


def _make_stream_events(events: List[StreamEvent]) -> Iterator[StreamEvent]:
    """Return an iterator over the given stream events."""
    return iter(events)


class TestTextStreamFormat:
    """Tests for text output format via execute_prompt streaming."""

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_text_output_with_tool_calls(
        self,
        mock_stream: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test text format renders text deltas, tool calls, and results."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_stream.return_value = _make_stream_events(
            [
                {"type": "text_delta", "text": "Here's how to create a file."},
                {
                    "type": "tool_use_start",
                    "name": "file_writer",
                    "args": {"filename": "example.py"},
                },
                {
                    "type": "tool_result",
                    "name": "file_writer",
                    "output": "File created.",
                },
                {"type": "done", "usage": {"input_tokens": 25, "output_tokens": 18}},
            ]
        )

        args = argparse.Namespace(
            prompt="How do I create a file?",
            output_format="text",
            mcp_config=None,
            project_dir=None,
        )

        result = execute_prompt(args)
        assert result == 0

        captured = capsys.readouterr()
        out: str = captured.out or ""

        assert "Here's how to create a file." in out
        assert "file_writer" in out
        assert "example.py" in out
        assert "File created." in out
        assert "──" in out


class TestNdjsonStreamFormat:
    """Tests for ndjson output format via execute_prompt streaming."""

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_ndjson_output(
        self,
        mock_stream: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test ndjson format outputs JSON lines with Claude schema."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        mock_stream.return_value = _make_stream_events(
            [
                {"type": "text_delta", "text": "Hello world."},
                {
                    "type": "tool_use_start",
                    "name": "read_file",
                    "args": {"path": "x.py"},
                },
                {
                    "type": "tool_result",
                    "name": "read_file",
                    "output": "file content",
                },
                {
                    "type": "done",
                    "session_id": "ndjson-session-123",
                    "usage": {"input_tokens": 10, "output_tokens": 5},
                },
            ]
        )

        args = argparse.Namespace(
            prompt="Read file",
            output_format="ndjson",
            mcp_config=None,
            project_dir=None,
        )

        result = execute_prompt(args)
        assert result == 0

        captured = capsys.readouterr()
        lines = [ln for ln in (captured.out or "").strip().split("\n") if ln.strip()]
        assert len(lines) == 4

        text_msg = json.loads(lines[0])
        assert text_msg["type"] == "assistant"
        assert text_msg["message"]["content"][0]["text"] == "Hello world."

        tool_msg = json.loads(lines[1])
        assert tool_msg["message"]["content"][0]["type"] == "tool_use"
        assert tool_msg["message"]["content"][0]["name"] == "read_file"

        result_msg = json.loads(lines[3])
        assert result_msg["type"] == "result"
        assert result_msg["session_id"] == "ndjson-session-123"


class TestJsonRawStreamFormat:
    """Tests for json-raw output format via execute_prompt streaming."""

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_json_raw_output(
        self,
        mock_stream: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test json-raw format passes raw lines through and ignores other events."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        raw_json = '{"type":"assistant","message":{"role":"assistant"}}'
        mock_stream.return_value = _make_stream_events(
            [
                {"type": "text_delta", "text": "ignored"},
                {"type": "raw_line", "line": raw_json},
                {"type": "done", "usage": {}},
            ]
        )

        args = argparse.Namespace(
            prompt="Test",
            output_format="json-raw",
            mcp_config=None,
            project_dir=None,
        )

        result = execute_prompt(args)
        assert result == 0

        captured = capsys.readouterr()
        out: str = captured.out or ""

        assert raw_json in out
        assert "ignored" not in out


class TestStreamFormatComparison:
    """Tests comparing different streaming output formats via execute_prompt."""

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_text_vs_ndjson_difference(
        self,
        mock_stream: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that text and ndjson formats produce different output for same events."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        events: List[StreamEvent] = [
            {"type": "text_delta", "text": "Test response."},
            {
                "type": "tool_use_start",
                "name": "test_tool",
                "args": {"key": "val"},
            },
            {"type": "done", "usage": {"input_tokens": 5}},
        ]

        # text format
        mock_stream.return_value = _make_stream_events(events)
        args_text = argparse.Namespace(
            prompt="Test",
            output_format="text",
            mcp_config=None,
            project_dir=None,
        )
        execute_prompt(args_text)
        text_output = capsys.readouterr().out or ""

        # ndjson format
        mock_stream.return_value = _make_stream_events(events)
        args_ndjson = argparse.Namespace(
            prompt="Test",
            output_format="ndjson",
            mcp_config=None,
            project_dir=None,
        )
        execute_prompt(args_ndjson)
        ndjson_output = capsys.readouterr().out or ""

        # text output has human-readable formatting
        assert "Test response." in text_output
        assert "──" in text_output

        # ndjson output has JSON lines
        ndjson_lines = [ln for ln in ndjson_output.strip().split("\n") if ln.strip()]
        for line in ndjson_lines:
            parsed = json.loads(line)
            assert "type" in parsed

    @patch("mcp_coder.cli.commands.prompt.prepare_llm_environment")
    @patch("mcp_coder.cli.commands.prompt.prompt_llm_stream")
    def test_json_raw_vs_ndjson_difference(
        self,
        mock_stream: Mock,
        mock_prepare_env: Mock,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Test that json-raw only outputs raw_line events while ndjson normalizes."""
        mock_prepare_env.return_value = {"MCP_CODER_PROJECT_DIR": "/test"}
        raw_line = '{"type":"assistant","message":{}}'
        events: List[StreamEvent] = [
            {"type": "text_delta", "text": "Hello"},
            {"type": "raw_line", "line": raw_line},
            {"type": "done", "usage": {}},
        ]

        # ndjson format
        mock_stream.return_value = _make_stream_events(events)
        args_ndjson = argparse.Namespace(
            prompt="Test",
            output_format="ndjson",
            mcp_config=None,
            project_dir=None,
        )
        execute_prompt(args_ndjson)
        ndjson_output = capsys.readouterr().out or ""

        # json-raw format
        mock_stream.return_value = _make_stream_events(events)
        args_raw = argparse.Namespace(
            prompt="Test",
            output_format="json-raw",
            mcp_config=None,
            project_dir=None,
        )
        execute_prompt(args_raw)
        raw_output = capsys.readouterr().out or ""

        # ndjson normalizes text_delta and done events
        assert "Hello" in ndjson_output
        # json-raw only passes through raw_line events
        assert raw_line in raw_output
        assert "Hello" not in raw_output


class TestPrintStreamEvent:
    """Tests for print_stream_event() function."""

    def test_print_stream_event_text_delta(self) -> None:
        """text_delta prints text with no newline."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {"type": "text_delta", "text": "Hello"},
            output_format="text",
            file=buf,
        )
        assert buf.getvalue() == "Hello"

    def test_print_stream_event_tool_use_bordered(self) -> None:
        """tool_use_start prints bordered header."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {"type": "tool_use_start", "name": "read_file", "args": {"path": "x.py"}},
            output_format="text",
            file=buf,
        )
        output = buf.getvalue()
        assert "tool:" in output
        assert "read_file" in output
        assert "──" in output

    def test_print_stream_event_tool_result_bordered(self) -> None:
        """tool_result prints result + border close."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {"type": "tool_result", "name": "read_file", "output": "file content"},
            output_format="text",
            file=buf,
        )
        output = buf.getvalue()
        assert "file content" in output
        assert "─" in output

    def test_print_stream_event_error_to_stderr(self) -> None:
        """error event goes to stderr."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        out = io.StringIO()
        err = io.StringIO()
        print_stream_event(
            {"type": "error", "message": "Something failed"},
            output_format="text",
            file=out,
            err_file=err,
        )
        assert out.getvalue() == ""
        assert "Something failed" in err.getvalue()

    def test_print_stream_event_done_newline(self) -> None:
        """done event prints a final newline."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {"type": "done", "usage": {}},
            output_format="text",
            file=buf,
        )
        assert buf.getvalue() == "\n"

    def test_print_stream_event_ndjson_text(self) -> None:
        """ndjson format outputs JSON line with Claude schema."""
        import io
        import json

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {"type": "text_delta", "text": "Hello"},
            output_format="ndjson",
            file=buf,
        )
        line = buf.getvalue().strip()
        parsed = json.loads(line)
        assert parsed["type"] == "assistant"
        assert parsed["message"]["role"] == "assistant"
        content = parsed["message"]["content"]
        assert len(content) == 1
        assert content[0]["type"] == "text"
        assert content[0]["text"] == "Hello"

    def test_print_stream_event_ndjson_tool_use(self) -> None:
        """ndjson format maps tool_use_start to assistant message with tool_use."""
        import io
        import json

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {"type": "tool_use_start", "name": "sleep", "args": {"seconds": 2}},
            output_format="ndjson",
            file=buf,
        )
        parsed = json.loads(buf.getvalue().strip())
        assert parsed["type"] == "assistant"
        content = parsed["message"]["content"]
        assert content[0]["type"] == "tool_use"
        assert content[0]["name"] == "sleep"
        assert content[0]["input"] == {"seconds": 2}

    def test_print_stream_event_ndjson_done(self) -> None:
        """ndjson format maps done to result message."""
        import io
        import json

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {"type": "done", "session_id": "abc", "usage": {"input_tokens": 10}},
            output_format="ndjson",
            file=buf,
        )
        parsed = json.loads(buf.getvalue().strip())
        assert parsed["type"] == "result"
        assert parsed["session_id"] == "abc"
        assert parsed["usage"]["input_tokens"] == 10

    def test_print_stream_event_json_raw(self) -> None:
        """json-raw format prints raw_line content as-is."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {"type": "raw_line", "line": '{"type":"assistant","message":{}}'},
            output_format="json-raw",
            file=buf,
        )
        assert buf.getvalue().strip() == '{"type":"assistant","message":{}}'

    def test_print_stream_event_json_raw_ignores_non_raw_line(self) -> None:
        """json-raw format ignores events that are not raw_line."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {"type": "text_delta", "text": "Hello"},
            output_format="json-raw",
            file=buf,
        )
        assert buf.getvalue() == ""
