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


class TestFormatToolName:
    """Tests for _format_tool_name() helper."""

    def test_mcp_name_two_segments(self) -> None:
        """MCP name with two segments formats as 'server > tool'."""
        from mcp_coder.llm.formatting.formatters import _format_tool_name

        assert _format_tool_name("mcp__workspace__read_file") == "workspace > read_file"

    def test_mcp_name_hyphenated_server(self) -> None:
        """MCP name with hyphenated server preserves hyphen."""
        from mcp_coder.llm.formatting.formatters import _format_tool_name

        assert (
            _format_tool_name("mcp__tools-py__run_pytest_check")
            == "tools-py > run_pytest_check"
        )

    def test_builtin_tool_name(self) -> None:
        """Built-in tool name passes through unchanged."""
        from mcp_coder.llm.formatting.formatters import _format_tool_name

        assert _format_tool_name("Bash") == "Bash"

    def test_mcp_name_single_segment(self) -> None:
        """MCP name with only one segment returns just the server name."""
        from mcp_coder.llm.formatting.formatters import _format_tool_name

        assert _format_tool_name("mcp__something") == "something"


class TestRenderToolOutput:
    """Tests for _render_tool_output() helper."""

    def test_empty_output(self) -> None:
        """Empty output returns ([], 0)."""
        from mcp_coder.llm.formatting.formatters import _render_tool_output

        assert _render_tool_output("") == ([], 0)

    def test_short_plain_text(self) -> None:
        """Short plain text returns all lines."""
        from mcp_coder.llm.formatting.formatters import _render_tool_output

        lines, total = _render_tool_output("line one\nline two")
        assert lines == ["line one", "line two"]
        assert total == 2

    def test_long_plain_text_truncated(self) -> None:
        """Plain text longer than limit is truncated."""
        from mcp_coder.llm.formatting.formatters import _render_tool_output

        text = "\n".join(f"line {i}" for i in range(10))
        lines, total = _render_tool_output(text)
        assert len(lines) == 5
        assert total == 10
        assert lines[0] == "line 0"
        assert lines[4] == "line 4"

    def test_json_dict_simple_values(self) -> None:
        """JSON dict with simple values expands to key: value lines."""
        import json

        from mcp_coder.llm.formatting.formatters import _render_tool_output

        data = {"success": True, "count": 42}
        lines, total = _render_tool_output(json.dumps(data))
        assert lines == ["success: true", "count: 42"]
        assert total == 2

    def test_json_dict_multiline_string(self) -> None:
        """JSON dict with multiline string value indents continuation lines."""
        import json

        from mcp_coder.llm.formatting.formatters import _render_tool_output

        data = {"success": True, "diff": "@@ -1 @@\n-foo\n+bar"}
        lines, total = _render_tool_output(json.dumps(data))
        assert lines == [
            "success: true",
            "diff:",
            "  @@ -1 @@",
            "  -foo",
            "  +bar",
        ]
        assert total == 5

    def test_non_dict_json(self) -> None:
        """Non-dict JSON (array) falls back to str().splitlines()."""
        import json

        from mcp_coder.llm.formatting.formatters import _render_tool_output

        data = [1, 2, 3]
        lines, total = _render_tool_output(json.dumps(data))
        assert lines == ["[1, 2, 3]"]
        assert total == 1

    def test_invalid_json(self) -> None:
        """Invalid JSON falls back to plain text splitting."""
        from mcp_coder.llm.formatting.formatters import _render_tool_output

        lines, total = _render_tool_output("not json at all\nsecond line")
        assert lines == ["not json at all", "second line"]
        assert total == 2


class TestRenderedStreamFormat:
    """Tests for rendered output format in print_stream_event()."""

    @pytest.mark.parametrize(
        "event,expected_output,use_stderr",
        [
            pytest.param(
                {"type": "text_delta", "text": "Hello world"},
                "Hello world",
                False,
                id="text_delta",
            ),
            pytest.param(
                {"type": "error", "message": "Something failed"},
                "Something failed",
                True,
                id="error_to_stderr",
            ),
            pytest.param(
                {"type": "done", "usage": {}},
                "\n",
                False,
                id="done_newline",
            ),
        ],
    )
    def test_non_tool_events(
        self, event: StreamEvent, expected_output: str, use_stderr: bool
    ) -> None:
        """Non-tool events: text_delta, error, done."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        out = io.StringIO()
        err = io.StringIO()
        print_stream_event(event, output_format="rendered", file=out, err_file=err)
        if use_stderr:
            assert expected_output in err.getvalue()
            assert out.getvalue() == ""
        else:
            assert out.getvalue() == expected_output

    def test_inline_params(self) -> None:
        """Tool with 1-2 args renders inline: ┌ server > tool(args)."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__read_file",
                "args": {"file_path": "x.py"},
            },
            output_format="rendered",
            file=buf,
        )
        output = buf.getvalue()
        assert output.startswith("\u250c")
        assert "workspace > read_file" in output
        assert "file_path='x.py'" in output
        # Should be single line (inline)
        assert output.strip().count("\n") == 0

    def test_block_params(self) -> None:
        """Tool with 3+ args renders block format with │ lines."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__edit_file",
                "args": {"file_path": "a.py", "old_text": "foo", "new_text": "bar"},
            },
            output_format="rendered",
            file=buf,
        )
        output = buf.getvalue()
        lines = output.strip().split("\n")
        assert lines[0].startswith("\u250c")
        assert "workspace > edit_file" in lines[0]
        # Block lines with │
        assert any("\u2502" in line for line in lines[1:])
        assert any("file_path" in line for line in lines[1:])
        assert any("old_text" in line for line in lines[1:])
        assert any("new_text" in line for line in lines[1:])

    @pytest.mark.parametrize(
        "output_str,expected_lines,expected_footer",
        [
            pytest.param(
                "line one\nline two",
                ["\u2502  line one", "\u2502  line two"],
                "\u2514 done",
                id="short_result",
            ),
            pytest.param(
                "\n".join(f"line {i}" for i in range(10)),
                [f"\u2502  line {i}" for i in range(5)],
                "\u2514 done (10 lines, truncated to 5)",
                id="long_result_truncated",
            ),
            pytest.param(
                "",
                [],
                "\u2514 done",
                id="empty_result",
            ),
        ],
    )
    def test_result_variations(
        self,
        output_str: str,
        expected_lines: list[str],
        expected_footer: str,
    ) -> None:
        """Result rendering: short, long (truncated), empty."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {"type": "tool_result", "output": output_str},
            output_format="rendered",
            file=buf,
        )
        output = buf.getvalue()
        all_lines = output.split("\n")
        # Check expected │ lines
        for exp in expected_lines:
            assert exp in all_lines
        # Check footer
        assert expected_footer in output

    def test_json_result_expanded(self) -> None:
        """JSON dict result expands keys with indented multiline strings."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        data = json.dumps({"success": True, "diff": "@@ -1 @@\n-foo\n+bar"})
        buf = io.StringIO()
        print_stream_event(
            {"type": "tool_result", "output": data},
            output_format="rendered",
            file=buf,
        )
        output = buf.getvalue()
        assert "\u2502  success: true" in output
        assert "\u2502  diff:" in output
        assert "\u2502    @@ -1 @@" in output
        assert "\u2514 done" in output

    def test_blank_line_after_footer(self) -> None:
        """Output ends with blank line after └ done."""
        import io

        from mcp_coder.llm.formatting.formatters import print_stream_event

        buf = io.StringIO()
        print_stream_event(
            {"type": "tool_result", "output": "ok"},
            output_format="rendered",
            file=buf,
        )
        output = buf.getvalue()
        # Should end with └ done\n\n (footer + blank line)
        assert output.endswith("\n\n")


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
