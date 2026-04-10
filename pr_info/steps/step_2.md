# Step 2: Field Filtering and Head/Tail Truncation

## Context
See [summary.md](summary.md) for overall design. This step rewrites `_render_tool_output()` in `stream_renderer.py` to add:
- Field filtering (main content extraction, envelope skipping, extras below)
- Head/tail truncation (10 first + 5 last lines with skip separator)
- `format_tools=False` bypass (return raw output identical to today)

## LLM Prompt
> Implement Step 2 of issue #763 (see `pr_info/steps/summary.md` and `pr_info/steps/step_2.md`).
> Rewrite `_render_tool_output()` with field filtering and head/tail truncation.
> When `format_tools=False`, return raw output split into lines (no filtering, no truncation).
> Write tests first (TDD), then implement. Run all three quality checks after changes.

## Part A: Tests

### WHERE
- `tests/llm/formatting/test_stream_renderer.py`

### WHAT — New/updated test functions

```python
# --- Field filtering tests ---

def test_render_tool_output_extracts_result_field() -> None:
    """Main content: 'result' field shown prominently."""

def test_render_tool_output_extracts_text_field() -> None:
    """Main content: 'text' field when 'result' absent."""

def test_render_tool_output_extracts_content_field() -> None:
    """Main content: 'content' field when 'result' and 'text' absent."""

def test_render_tool_output_priority_result_over_text() -> None:
    """'result' wins over 'text' when both present."""

def test_render_tool_output_skips_envelope_fields() -> None:
    """Envelope fields (type, role, model, etc.) not shown."""

def test_render_tool_output_shows_extra_fields() -> None:
    """Non-envelope, non-main fields shown below main content."""

def test_render_tool_output_no_duplicate_main_in_extras() -> None:
    """Winning main content field not duplicated in extras."""

def test_render_tool_output_single_level_unwrap() -> None:
    """Nested dicts shown as structured key-value, not recursed."""

# --- Truncation tests (update existing) ---

def test_render_tool_output_head_tail_truncation() -> None:
    """Long output: first 10 + separator + last 5 lines."""

def test_render_tool_output_exactly_at_threshold() -> None:
    """15 lines = no truncation (threshold is >15)."""

def test_render_tool_output_just_over_threshold() -> None:
    """16 lines = truncated with separator."""

# --- format_tools=False bypass ---

def test_render_tool_output_raw_mode_no_filtering() -> None:
    """format_tools=False: raw output, no field filtering."""

def test_render_tool_output_raw_mode_no_truncation() -> None:
    """format_tools=False: no truncation even for long output."""
```

### DATA — Expected return values

Field filtering example:
```python
# Input: {"result": "hello\nworld", "type": "text", "extra_field": "val"}
# Output lines: ["hello", "world", "", "extra_field: val"]
# (result shown as main content, type skipped as envelope, extra_field shown below)
```

Truncation example:
```python
# Input: 20 lines "line 0" .. "line 19"
# Output: ["line 0".."line 9", "... (5 lines skipped)", "line 15".."line 19"]
# total_lines = 20
```

## Part B: Implementation

### WHERE
- `src/mcp_coder/llm/formatting/stream_renderer.py`

### WHAT — Updated constants and function signature

```python
_HEAD_LINES = 10
_TAIL_LINES = 5

_ENVELOPE_FIELDS: frozenset[str] = frozenset({
    "type", "role", "model", "stop_reason", "session_id", "usage",
})

_MAIN_CONTENT_KEYS: tuple[str, ...] = ("result", "text", "content")

def _render_tool_output(output: str, *, format_tools: bool = True) -> tuple[list[str], int]:
```

### HOW — Integration
- `StreamEventRenderer.render()` passes `self._format_tools` to `_render_tool_output()`
- Existing callers in `render()` method updated to pass the flag

### ALGORITHM
```
1. If not format_tools: return (output.splitlines(), len(output.splitlines()))  # raw, no truncation
2. Try json.loads(output) — if dict, apply field filtering:
   a. Find main content: first key in ("result", "text", "content") that exists
   b. Render main content value (multiline strings split + indented, others as-is)
   c. Collect extras: keys not in envelope set and not the main content key
   d. Render extras below with blank separator line
3. If not dict or json fails: split into plain text lines
4. Apply head/tail truncation if total > HEAD + TAIL:
   lines = head[:10] + ["... (N lines skipped)"] + tail[-5:]
5. Return (display_lines, total_line_count)
```

### DATA — Return structure
Same as today: `tuple[list[str], int]` — no dataclass changes needed.

## Commit Message
```
feat(icoder): field filtering and head/tail truncation in tool output (#763)

Rewrite _render_tool_output() to:
- Extract main content (result > text > content priority)
- Skip envelope fields (type, role, model, stop_reason, etc.)
- Show extra fields below main content
- Truncate to first 10 + last 5 lines with skip separator
- Bypass all formatting when format_tools=False
```
