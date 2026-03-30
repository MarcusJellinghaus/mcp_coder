# Issue #642: Add 'rendered' output format for prompt command

## Goal

Add a new `--output-format rendered` option to the `prompt` command that provides
structured, human-readable terminal output using box-drawing characters for tool calls
and results. Make it the default output format.

## Architectural / Design Changes

### Rendering pipeline (unchanged)

```
Provider → StreamEvent → print_stream_event() → terminal
```

The `rendered` format is a new branch inside the existing `print_stream_event()` function,
following the same stateless pattern as `text`, `ndjson`, and `json-raw`. No new classes,
modules, or state machines are introduced.

### New helpers in `formatters.py`

Two small private functions added to `src/mcp_coder/llm/formatting/formatters.py`:

1. **`_format_tool_name(name: str) -> str`** — Strips `mcp__` prefix and splits on first
   remaining `__` to produce `server > tool_name`. Built-in tool names pass through unchanged.

2. **`_render_tool_output(output: str) -> tuple[list[str], int]`** — Converts tool output
   into display lines. Tries `json.loads` for structured expansion of top-level keys
   (with nested newline handling for string values), falls back to plain text split.
   Truncates to 5 lines (hardcoded). Returns `(display_lines, total_line_count)`.

### Default format change

The default `--output-format` changes from `text` to `rendered`. Existing scripts should
use `--output-format text` explicitly for backward compatibility.

### Output format lineup (after change)

| Format       | Streaming | Default  | Use case                      |
|------------- |-----------|----------|-------------------------------|
| `rendered`   | yes       | **yes**  | Human watching the terminal   |
| `text`       | yes       | no       | Plain text, pipeable          |
| `ndjson`     | yes       | no       | Programmatic consumption      |
| `json-raw`   | yes       | no       | Provider-native debug events  |
| `json`       | no        | no       | Complete response as one blob |
| `session-id` | no        | no       | Just the session UUID         |

## Files Modified

| File | Change |
|------|--------|
| `src/mcp_coder/llm/formatting/formatters.py` | Add `_format_tool_name()`, `_render_tool_output()`, and `rendered` branch in `print_stream_event()` |
| `src/mcp_coder/cli/parsers.py` | Add `"rendered"` to `--output-format` choices, change default to `"rendered"` |
| `src/mcp_coder/cli/commands/prompt.py` | Add `"rendered"` to the streaming format tuple |
| `tests/llm/formatting/test_formatters.py` | Unit tests for all rendered format behaviors |

## Implementation Steps

| Step | Description | Commit scope |
|------|-------------|--------------|
| 1 | `_format_tool_name()` helper + unit tests | `formatters.py`, `test_formatters.py` |
| 2 | `_render_tool_output()` helper + unit tests | `formatters.py`, `test_formatters.py` |
| 3 | `rendered` branch in `print_stream_event()` + unit tests | `formatters.py`, `test_formatters.py` |
| 4 | CLI wiring: parser choices/default + prompt streaming tuple + test updates | `parsers.py`, `prompt.py`, `test_formatters.py` |
