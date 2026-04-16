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
    _render_output_value,
    _render_tool_output,
    _render_value_compact,
    _render_value_full,
)

_RENDERER = StreamEventRenderer()


class TestRendererFormatToolsParam:
    """Tests for format_tools constructor parameter."""

    def test_renderer_format_tools_default_true(self) -> None:
        """StreamEventRenderer defaults to format_tools=True."""
        renderer = StreamEventRenderer()
        assert renderer._format_tools is True

    def test_renderer_format_tools_false(self) -> None:
        """StreamEventRenderer accepts format_tools=False."""
        renderer = StreamEventRenderer(format_tools=False)
        assert renderer._format_tools is False


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
        output = "\n".join(f"line {i}" for i in range(20))
        action = _RENDERER.render(
            {
                "type": "tool_result",
                "name": "mcp__workspace__read_file",
                "output": output,
            }
        )
        assert isinstance(action, ToolResult)
        assert action.name == "workspace > read_file"
        # head 10 + separator + tail 5 = 16
        assert len(action.output_lines) == 16
        assert action.output_lines[10] == "... (5 lines skipped)"
        assert action.total_lines == 20
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
        text = "\n".join(f"line {i}" for i in range(20))
        lines, total = _render_tool_output(text)
        # head 10 + separator + tail 5 = 16
        assert len(lines) == 16
        assert lines[:10] == [f"line {i}" for i in range(10)]
        assert lines[10] == "... (5 lines skipped)"
        assert lines[11:] == [f"line {i}" for i in range(15, 20)]
        assert total == 20

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


class TestRenderToolOutputFieldFiltering:
    """Tests for field filtering in _render_tool_output()."""

    def test_render_tool_output_extracts_result_field(self) -> None:
        """Main content: 'result' field shown prominently."""
        data = {"result": "hello\nworld"}
        lines, total = _render_tool_output(json.dumps(data))
        assert lines[:2] == ["hello", "world"]
        assert total == 2

    def test_render_tool_output_extracts_text_field(self) -> None:
        """Main content: 'text' field when 'result' absent."""
        data = {"text": "some text"}
        lines, total = _render_tool_output(json.dumps(data))
        assert lines == ["some text"]
        assert total == 1

    def test_render_tool_output_extracts_content_field(self) -> None:
        """Main content: 'content' field when 'result' and 'text' absent."""
        data = {"content": "body content"}
        lines, total = _render_tool_output(json.dumps(data))
        assert lines == ["body content"]
        assert total == 1

    def test_render_tool_output_priority_result_over_text(self) -> None:
        """'result' wins over 'text' when both present."""
        data = {"result": "winner", "text": "loser"}
        lines, _total = _render_tool_output(json.dumps(data))
        assert lines[0] == "winner"
        # 'text' should appear as extra
        assert "" in lines  # blank separator
        assert "text: loser" in lines

    def test_render_tool_output_skips_envelope_fields(self) -> None:
        """Envelope fields (type, role, model, etc.) not shown."""
        data = {
            "result": "hello",
            "type": "text",
            "role": "assistant",
            "model": "gpt-4",
            "stop_reason": "end",
            "session_id": "abc",
            "usage": {"tokens": 10},
        }
        lines, _total = _render_tool_output(json.dumps(data))
        full_text = "\n".join(lines)
        assert "hello" in full_text
        assert "type:" not in full_text
        assert "role:" not in full_text
        assert "model:" not in full_text
        assert "stop_reason:" not in full_text
        assert "session_id:" not in full_text
        assert "usage:" not in full_text

    def test_render_tool_output_shows_extra_fields(self) -> None:
        """Non-envelope, non-main fields shown below main content."""
        data = {"result": "hello", "extra_field": "val"}
        lines, total = _render_tool_output(json.dumps(data))
        assert lines == ["hello", "", "extra_field: val"]
        assert total == 3

    def test_render_tool_output_no_duplicate_main_in_extras(self) -> None:
        """Winning main content field not duplicated in extras."""
        data = {"result": "hello", "extra": "other"}
        lines, _total = _render_tool_output(json.dumps(data))
        # 'result' should not appear in extras section
        result_count = sum(1 for line in lines if line.startswith("result:"))
        assert result_count == 0  # main content shown directly, not as "result: ..."

    def test_render_tool_output_single_level_unwrap(self) -> None:
        """Nested dicts shown as structured key-value, not recursed."""
        data = {"result": "ok", "metadata": {"key": "value"}}
        lines, _total = _render_tool_output(json.dumps(data))
        full_text = "\n".join(lines)
        assert "ok" in full_text
        assert "metadata:" in full_text

    def test_render_tool_output_only_envelope_fields(self) -> None:
        """Dict with only envelope fields returns empty output."""
        data = {"type": "text", "role": "assistant"}
        lines, total = _render_tool_output(json.dumps(data))
        assert lines == []
        assert total == 0


class TestRenderToolOutputTruncation:
    """Tests for head/tail truncation in _render_tool_output()."""

    def test_render_tool_output_head_tail_truncation(self) -> None:
        """Long output: first 10 + separator + last 5 lines."""
        text = "\n".join(f"line {i}" for i in range(30))
        lines, total = _render_tool_output(text)
        assert total == 30
        assert lines[:10] == [f"line {i}" for i in range(10)]
        assert lines[10] == "... (15 lines skipped)"
        assert lines[11:] == [f"line {i}" for i in range(25, 30)]

    def test_render_tool_output_exactly_at_threshold(self) -> None:
        """15 lines = no truncation (threshold is >15)."""
        text = "\n".join(f"line {i}" for i in range(15))
        lines, total = _render_tool_output(text)
        assert total == 15
        assert len(lines) == 15
        assert "skipped" not in "\n".join(lines)

    def test_render_tool_output_just_over_threshold(self) -> None:
        """16 lines = truncated with separator."""
        text = "\n".join(f"line {i}" for i in range(16))
        lines, total = _render_tool_output(text)
        assert total == 16
        # head 10 + separator + tail 5 = 16, but 1 line skipped
        assert lines[10] == "... (1 line skipped)"
        assert len(lines) == 16  # 10 + 1 separator + 5


class TestRenderToolOutputRawMode:
    """Tests for format_tools=False bypass in _render_tool_output()."""

    def test_render_tool_output_raw_mode_no_filtering(self) -> None:
        """format_tools=False: raw output, no field filtering."""
        data = {"result": "hello", "type": "text", "extra": "val"}
        output = json.dumps(data)
        lines, total = _render_tool_output(output, format_tools=False)
        # Raw mode returns output.splitlines() — the JSON string as-is
        assert lines == [output]
        assert total == 1

    def test_render_tool_output_raw_mode_no_truncation(self) -> None:
        """format_tools=False: no truncation even for long output."""
        text = "\n".join(f"line {i}" for i in range(50))
        lines, total = _render_tool_output(text, format_tools=False)
        assert len(lines) == 50
        assert total == 50
        assert "skipped" not in "\n".join(lines)


class TestRenderValueCompact:
    """Tests for _render_value_compact()."""

    def test_short_string(self) -> None:
        assert _render_value_compact("hello") == "'hello'"

    def test_long_string(self) -> None:
        assert _render_value_compact("x" * 100) == "(100 chars)"

    def test_string_exactly_80_chars(self) -> None:
        value = "x" * 80
        assert _render_value_compact(value) == repr(value)

    def test_string_81_chars(self) -> None:
        assert _render_value_compact("x" * 81) == "(81 chars)"

    def test_simple_list(self) -> None:
        assert _render_value_compact([1, 2]) == "[1, 2]"

    def test_list_with_dicts(self) -> None:
        assert _render_value_compact([{"a": 1}]) == "(1 items)"

    def test_long_list(self) -> None:
        value = list(range(100))
        assert _render_value_compact(value) == f"({len(value)} items)"

    def test_small_dict(self) -> None:
        assert _render_value_compact({"a": 1}) == '{"a": 1}'

    def test_large_dict(self) -> None:
        value = {f"key_{i}": i for i in range(20)}
        assert _render_value_compact(value) == f"({len(value)} keys)"

    def test_bool_value(self) -> None:
        assert _render_value_compact(True) == "True"

    def test_int_value(self) -> None:
        assert _render_value_compact(42) == "42"


class TestRenderValueFull:
    """Tests for _render_value_full()."""

    def test_short_string(self) -> None:
        assert _render_value_full("hello") == ["hello"]

    def test_multiline_string(self) -> None:
        assert _render_value_full("a\nb") == ["a", "b"]

    def test_long_string_truncated(self) -> None:
        value = "x" * 200
        result = _render_value_full(value)
        assert len(result) == 1
        assert result[0] == "x" * 117 + "..."
        assert len(result[0]) == 120

    def test_short_list(self) -> None:
        assert _render_value_full([1, 2]) == ["[1, 2]"]

    def test_long_list_expanded(self) -> None:
        value = list(range(50))
        result = _render_value_full(value)
        assert result == json.dumps(value, indent=2).splitlines()
        assert len(result) > 1

    def test_short_dict(self) -> None:
        assert _render_value_full({"k": "v"}) == ['{"k": "v"}']

    def test_large_dict_expanded(self) -> None:
        value = {f"key_{i}": i for i in range(20)}
        result = _render_value_full(value)
        assert result == json.dumps(value, indent=2).splitlines()
        assert len(result) > 1


class TestRenderOutputValue:
    """Tests for _render_output_value()."""

    def test_plain_string(self) -> None:
        assert _render_output_value("hello") == ["hello"]

    def test_multiline_string_split(self) -> None:
        assert _render_output_value("a\nb\nc") == ["a", "b", "c"]

    def test_bool(self) -> None:
        assert _render_output_value(True) == ["true"]

    def test_int(self) -> None:
        assert _render_output_value(42) == ["42"]

    def test_simple_dict(self) -> None:
        assert _render_output_value({"a": True, "b": 42}) == ["a: true", "b: 42"]

    def test_dict_multiline_string_expanded(self) -> None:
        result = _render_output_value({"diff": "line1\nline2"})
        assert result == ["diff:", "  line1", "  line2"]

    def test_dict_nested_dict(self) -> None:
        # Nested dicts always render as an indented block (recursion
        # produces key: value lines, which is multi-line when >1 key).
        value = {"meta": {"a": 1, "b": 2}}
        result = _render_output_value(value)
        assert result == ["meta:", "  a: 1", "  b: 2"]

    def test_dict_nested_dict_multiline(self) -> None:
        # Nested dict whose inner value contains newlines expands as a block
        value = {"meta": {"note": "line1\nline2"}}
        result = _render_output_value(value)
        assert result == ["meta:", "  note:", "    line1", "    line2"]

    def test_short_list_inline(self) -> None:
        assert _render_output_value([1, 2, 3]) == ["[1, 2, 3]"]

    def test_long_list_expanded(self) -> None:
        value = list(range(50))
        result = _render_output_value(value)
        assert result == json.dumps(value, indent=2).splitlines()
        assert len(result) > 1

    def test_dict_with_list_value_inline(self) -> None:
        result = _render_output_value({"items": [1, 2, 3]})
        assert result == ["items: [1, 2, 3]"]

    def test_dict_with_list_value_expanded(self) -> None:
        value = {"items": list(range(50))}
        result = _render_output_value(value)
        assert result[0] == "items:"
        # Remaining lines are the indented json.dumps output
        expected_inner = json.dumps(list(range(50)), indent=2).splitlines()
        assert result[1:] == [f"  {line}" for line in expected_inner]

    def test_string_value_in_dict(self) -> None:
        assert _render_output_value({"key": "simple"}) == ['key: "simple"']
