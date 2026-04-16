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
    format_tool_start,
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

    def test_tool_use_start_short_args(self) -> None:
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
        assert action.args == {"file_path": "x.py"}

    def test_tool_use_start_many_args(self) -> None:
        action = _RENDERER.render(
            {
                "type": "tool_use_start",
                "name": "mcp__workspace__edit_file",
                "args": {"file_path": "a.py", "old_text": "foo", "new_text": "bar"},
            }
        )
        assert isinstance(action, ToolStart)
        assert action.args == {
            "file_path": "a.py",
            "old_text": "foo",
            "new_text": "bar",
        }

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

    def test_result_envelope_unwrap(self) -> None:
        """`{"result": "hello"}` unwraps to just the value."""
        lines, total = _render_tool_output(json.dumps({"result": "hello"}))
        assert lines == ["hello"]
        assert total == 1

    def test_result_envelope_with_extras(self) -> None:
        """Non-`result` keys render as extras below a blank separator."""
        data = {"result": "ok", "meta": "x"}
        lines, total = _render_tool_output(json.dumps(data))
        assert lines == ["ok", "", 'meta: "x"']
        assert total == 3

    def test_result_dict_with_multiline_diff(self) -> None:
        """Multiline string inside a `result` dict is split into lines."""
        data = {"result": {"diff": "a\nb", "ok": True}}
        lines, total = _render_tool_output(json.dumps(data))
        assert lines == ["diff:", "  a", "  b", "ok: true"]
        assert total == 4

    def test_no_text_unwrap(self) -> None:
        """`{"text": ...}` is not treated as an envelope — shown as key/value."""
        lines, total = _render_tool_output(json.dumps({"text": "hello"}))
        assert lines == ['text: "hello"']
        assert total == 1

    def test_no_content_unwrap(self) -> None:
        """`{"content": ...}` is not treated as an envelope — shown as key/value."""
        lines, total = _render_tool_output(json.dumps({"content": "hello"}))
        assert lines == ['content: "hello"']
        assert total == 1

    def test_full_mode_no_truncation(self) -> None:
        """30-line input with ``full=True`` returns all 30 lines."""
        text = "\n".join(f"line {i}" for i in range(30))
        lines, total = _render_tool_output(text, full=True)
        assert len(lines) == 30
        assert total == 30
        assert lines == [f"line {i}" for i in range(30)]

    def test_compact_mode_truncates(self) -> None:
        """30-line input with default ``full=False`` is truncated."""
        text = "\n".join(f"line {i}" for i in range(30))
        lines, total = _render_tool_output(text)
        assert total == 30
        assert len(lines) == 16  # 10 head + 1 separator + 5 tail


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

    def test_full_mode_skips_truncation(self) -> None:
        """``full=True`` disables truncation regardless of line count."""
        text = "\n".join(f"line {i}" for i in range(30))
        lines, total = _render_tool_output(text, full=True)
        assert total == 30
        assert len(lines) == 30
        assert "skipped" not in "\n".join(lines)


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


class TestFormatToolStart:
    """Tests for format_tool_start()."""

    def test_no_args(self) -> None:
        """Empty args → single header line, no separator."""
        action = ToolStart(
            display_name="workspace > read_file",
            raw_name="mcp__workspace__read_file",
            args={},
        )
        assert format_tool_start(action) == ["\u250c workspace > read_file"]

    def test_inline_short_args(self) -> None:
        """Short args fit inline → header line + separator."""
        action = ToolStart(
            display_name="workspace > read_file",
            raw_name="mcp__workspace__read_file",
            args={"file_path": "x.py"},
        )
        result = format_tool_start(action)
        assert result == [
            "\u250c workspace > read_file(file_path='x.py')",
            "\u251c\u2500\u2500",
        ]

    def test_block_long_args(self) -> None:
        """Args exceeding 100 chars → block header, per-arg lines, separator."""
        # Use values of 50 chars each (below 80-char compact threshold,
        # so they keep their repr form). Three args with repr'd 50-char
        # values easily exceed the 100-char inline threshold.
        val = "x" * 50
        action = ToolStart(
            display_name="workspace > edit_file",
            raw_name="mcp__workspace__edit_file",
            args={"file_path": "a.py", "old_text": val, "new_text": val},
        )
        result = format_tool_start(action)
        assert result[0] == "\u250c workspace > edit_file"
        assert result[-1] == "\u251c\u2500\u2500"
        # Block lines for each arg with │
        assert any("file_path" in line and line.startswith("\u2502") for line in result)
        assert any("old_text" in line and line.startswith("\u2502") for line in result)
        assert any("new_text" in line and line.startswith("\u2502") for line in result)

    def test_inline_threshold_boundary(self) -> None:
        """Exactly 100 chars → inline; 101 chars → block."""
        # Line format: "┌ NAME(KEY='<80 x's>')"
        # Length = 7 + len(NAME) + len(KEY) + 80 (since repr adds 2 quotes)
        # = 7 + 4 + 9 + 80 = 100
        value = "x" * 80  # repr is 82 chars
        action_100 = ToolStart(
            display_name="tool",
            raw_name="tool",
            args={"keystr_xx": value},
        )
        result_100 = format_tool_start(action_100)
        assert result_100[0].startswith("\u250c tool(keystr_xx=")
        assert len(result_100[0]) == 100
        # Inline form: header + separator only (2 lines)
        assert len(result_100) == 2
        assert result_100[-1] == "\u251c\u2500\u2500"

        # Now 101-char variant: add one more char to NAME
        action_101 = ToolStart(
            display_name="toolx",
            raw_name="toolx",
            args={"keystr_xx": value},
        )
        result_101 = format_tool_start(action_101)
        # Block form: header + arg line + separator (3 lines)
        assert result_101[0] == "\u250c toolx"
        assert len(result_101) == 3
        assert result_101[-1] == "\u251c\u2500\u2500"

    def test_compact_value_summaries(self) -> None:
        """Large list arg → compact mode shows '(N items)'."""
        action = ToolStart(
            display_name="workspace > edit_file",
            raw_name="mcp__workspace__edit_file",
            args={"edits": [{"a": 1}] * 5, "file_path": "a.py", "other": "x" * 150},
        )
        result = format_tool_start(action, full=False)
        # Block format: must contain '(5 items)' for edits and '(150 chars)' for other
        joined = "\n".join(result)
        assert "(5 items)" in joined
        assert "(150 chars)" in joined

    def test_full_mode_expands_values(self) -> None:
        """Full mode expands multiline string values as indented blocks."""
        # Use enough args to force block format in compact inline attempt.
        action = ToolStart(
            display_name="workspace > edit_file",
            raw_name="mcp__workspace__edit_file",
            args={
                "file_path": "some/path/to/file.py",
                "old_text": "line1\nline2\nline3",
                "new_text": "y" * 50,
                "extra": "z" * 50,
            },
        )
        result = format_tool_start(action, full=True)
        # Should be block mode (exceeds 100 chars inline)
        assert result[0] == "\u250c workspace > edit_file"
        # Multi-line string expanded
        assert "\u2502  old_text:" in result
        assert "\u2502    line1" in result
        assert "\u2502    line2" in result
        assert "\u2502    line3" in result
        assert result[-1] == "\u251c\u2500\u2500"

    def test_full_mode_still_inlines_short(self) -> None:
        """Short args + full=True → still inline (full doesn't force block)."""
        action = ToolStart(
            display_name="workspace > read_file",
            raw_name="mcp__workspace__read_file",
            args={"file_path": "x.py"},
        )
        result = format_tool_start(action, full=True)
        assert result == [
            "\u250c workspace > read_file(file_path='x.py')",
            "\u251c\u2500\u2500",
        ]

    def test_separator_present_with_args(self) -> None:
        """Last line is always '├──' when args are present."""
        action = ToolStart(
            display_name="tool",
            raw_name="tool",
            args={"k": "v"},
        )
        result = format_tool_start(action)
        assert result[-1] == "\u251c\u2500\u2500"

    def test_separator_absent_without_args(self) -> None:
        """No '├──' in output when no args."""
        action = ToolStart(display_name="tool", raw_name="tool", args={})
        result = format_tool_start(action)
        assert "\u251c\u2500\u2500" not in result

    def test_block_preserves_arg_order(self) -> None:
        """Block format preserves insertion order, not alphabetical."""
        # Use 50-char string values (repr form, not summarized) to ensure
        # the inline form exceeds 100 chars and block mode is used.
        val = "x" * 50
        action = ToolStart(
            display_name="tool",
            raw_name="tool",
            args={
                "zebra": val,
                "apple": val,
                "middle": val,
            },
        )
        result = format_tool_start(action)
        # Strip to find arg lines (those starting with │)
        arg_lines = [line for line in result if line.startswith("\u2502")]
        assert len(arg_lines) == 3
        assert "zebra" in arg_lines[0]
        assert "apple" in arg_lines[1]
        assert "middle" in arg_lines[2]
