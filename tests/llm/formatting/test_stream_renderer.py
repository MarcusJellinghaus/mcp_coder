"""Tests for StreamEventRenderer and private helpers."""

import json

from mcp_coder.llm.formatting.render_actions import (
    ErrorMessage,
    StreamDone,
    TextChunk,
    ToolResult,
    ToolStart,
)
from mcp_coder.llm.formatting.stream_renderer import (
    StreamEventRenderer,
    _format_tool_name,
    _render_tool_output,
)

_RENDERER = StreamEventRenderer()


class TestStreamEventRenderer:
    """Tests for StreamEventRenderer.render()."""

    def test_text_delta(self) -> None:
        action = _RENDERER.render({"type": "text_delta", "text": "Hello"})
        assert action == TextChunk(text="Hello")

    def test_tool_use_start_inline(self) -> None:
        action = _RENDERER.render(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__read_file",
                "args": {"file_path": "x.py"},
            }
        )
        assert isinstance(action, ToolStart)
        assert action.display_name == "workspace > read_file"
        assert action.raw_name == "mcp__workspace__read_file"
        assert action.inline_args == "file_path='x.py'"
        assert action.block_args == []

    def test_tool_use_start_block(self) -> None:
        action = _RENDERER.render(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__edit_file",
                "args": {"file_path": "a.py", "old_text": "foo", "new_text": "bar"},
            }
        )
        assert isinstance(action, ToolStart)
        assert action.display_name == "workspace > edit_file"
        assert action.inline_args is None
        assert action.block_args == [
            ("file_path", '"a.py"'),
            ("old_text", '"foo"'),
            ("new_text", '"bar"'),
        ]

    def test_tool_result_short(self) -> None:
        action = _RENDERER.render(
            {
                "type": "tool_result",
                "name": "mcp__workspace__read_file",
                "output": "line1\nline2",
            }
        )
        assert isinstance(action, ToolResult)
        assert action.name == "workspace > read_file"
        assert action.output_lines == ["line1", "line2"]
        assert action.total_lines == 2
        assert action.truncated is False

    def test_tool_result_truncated(self) -> None:
        output = "\n".join(f"line {i}" for i in range(10))
        action = _RENDERER.render(
            {
                "type": "tool_result",
                "name": "mcp__workspace__read_file",
                "output": output,
            }
        )
        assert isinstance(action, ToolResult)
        assert action.name == "workspace > read_file"
        assert len(action.output_lines) == 5
        assert action.total_lines == 10
        assert action.truncated is True

    def test_error(self) -> None:
        action = _RENDERER.render({"type": "error", "message": "fail"})
        assert action == ErrorMessage(message="fail")

    def test_done(self) -> None:
        action = _RENDERER.render({"type": "done"})
        assert action == StreamDone()

    def test_unknown_returns_none(self) -> None:
        action = _RENDERER.render({"type": "raw_line", "line": "..."})
        assert action is None


class TestFormatToolNameRenderer:
    """Tests for _format_tool_name() in stream_renderer."""

    def test_mcp_two_segments(self) -> None:
        assert _format_tool_name("mcp__workspace__read_file") == "workspace > read_file"

    def test_mcp_hyphenated_server(self) -> None:
        assert (
            _format_tool_name("mcp__tools-py__run_pytest_check")
            == "tools-py > run_pytest_check"
        )

    def test_builtin(self) -> None:
        assert _format_tool_name("Bash") == "Bash"

    def test_single_segment(self) -> None:
        assert _format_tool_name("mcp__something") == "something"


class TestRenderToolOutputRenderer:
    """Tests for _render_tool_output() in stream_renderer."""

    def test_empty(self) -> None:
        assert _render_tool_output("") == ([], 0)

    def test_short_plain(self) -> None:
        lines, total = _render_tool_output("line one\nline two")
        assert lines == ["line one", "line two"]
        assert total == 2

    def test_long_truncated(self) -> None:
        text = "\n".join(f"line {i}" for i in range(10))
        lines, total = _render_tool_output(text)
        assert len(lines) == 5
        assert total == 10

    def test_json_dict(self) -> None:
        data = {"success": True, "count": 42}
        lines, total = _render_tool_output(json.dumps(data))
        assert lines == ["success: true", "count: 42"]
        assert total == 2

    def test_json_dict_multiline_string(self) -> None:
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
        lines, total = _render_tool_output(json.dumps([1, 2, 3]))
        assert lines == ["[1, 2, 3]"]
        assert total == 1

    def test_invalid_json(self) -> None:
        lines, total = _render_tool_output("not json\nsecond line")
        assert lines == ["not json", "second line"]
        assert total == 2
