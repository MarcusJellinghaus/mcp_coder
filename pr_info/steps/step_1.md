# Step 1: Add Rendering Helper Functions + Tests

> **Context:** Read `pr_info/steps/summary.md` first. This step adds pure helper functions with no changes to existing behavior.

## Goal
Add the three new rendering helpers that steps 2 and 3 will use. Pure additions — nothing removed, nothing broken.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/formatting/stream_renderer.py` | Add constant + 3 functions |
| `tests/llm/formatting/test_stream_renderer.py` | Add 3 test classes |

## WHAT — New constant and functions in `stream_renderer.py`

### Constant
```python
_MAX_INLINE_LEN = 100
```

### Function 1: `_render_value_compact(value: object) -> str`
Single-line summary of a value for compact-mode arg display.

**Algorithm:**
```
if str and len > 80: return "(N chars)"
if str: return repr(value)
if list with any dicts, or list json > 120 chars: return "(N items)"
if list: return json.dumps(value)
if dict and json > 120 chars: return "(N keys)"
if dict: return json.dumps(value)
else: return repr(value)
```

**Examples:**
- `"short"` → `"'short'"`
- `"x" * 100` → `"(100 chars)"`
- `[1, 2, 3]` → `"[1, 2, 3]"`
- `[{"a": 1}]` → `"(1 items)"`
- `{"key": "val"}` → `'{"key": "val"}'`

### Function 2: `_render_value_full(value: object) -> list[str]`
Multi-line expansion of a value for full-mode arg display.

**Algorithm:**
```
if str with newlines: return value.splitlines()
if str and len > 120: return [truncated to 117 chars + "..."]
if str: return [value]
if list/dict and json.dumps <= 120: return [compact json]
if list/dict: return json.dumps(indent=2).splitlines()
else: return [repr(value)]
```

### Function 3: `_render_output_value(value: object) -> list[str]`
Recursive rendering of any JSON value for tool output display. Splits multiline strings, expands dict values recursively.

**Algorithm:**
```
if str with newlines: return value.splitlines()
if str: return [value]
if dict: for each key, render value recursively;
         if rendered is multi-line, put key: on its own line + indent children
         if single-line, put key: value on one line
if list and json.dumps <= _MAX_INLINE_LEN: return [compact]
if list: return json.dumps(indent=2).splitlines()
else: return [json.dumps(value)]
```

**Key behavior — this single function replaces both `_render_dict` and `_render_json_value` from the reference implementation.**

## DATA — Return values

| Function | Returns | Purpose |
|----------|---------|---------|
| `_render_value_compact` | `str` | Single-line summary for compact headers |
| `_render_value_full` | `list[str]` | Multi-line expansion for full-mode block args |
| `_render_output_value` | `list[str]` | Recursive JSON rendering for tool output body |

## HOW — Tests in `test_stream_renderer.py`

Add three new test classes **below** existing tests (no existing tests modified in this step):

### `TestRenderValueCompact`
- `test_short_string` — `"hello"` → `"'hello'"`
- `test_long_string` — 100-char string → `"(100 chars)"`
- `test_string_exactly_80_chars` — boundary: still returns repr
- `test_string_81_chars` — boundary: returns `"(81 chars)"`
- `test_simple_list` — `[1, 2]` → `"[1, 2]"`
- `test_list_with_dicts` — `[{"a": 1}]` → `"(1 items)"`
- `test_long_list` — list with json > 120 chars → `"(N items)"`
- `test_small_dict` — `{"a": 1}` → `'{"a": 1}'`
- `test_large_dict` — dict with json > 120 chars → `"(N keys)"`
- `test_bool_value` — `True` → `"True"`
- `test_int_value` — `42` → `"42"`

### `TestRenderValueFull`
- `test_short_string` — `"hello"` → `["hello"]`
- `test_multiline_string` — `"a\nb"` → `["a", "b"]`
- `test_long_string_truncated` — 200-char string → single item truncated at 120
- `test_short_list` — `[1, 2]` → `["[1, 2]"]`
- `test_long_list_expanded` — long list → `json.dumps(indent=2).splitlines()`
- `test_short_dict` — small dict → `['{"k": "v"}']`
- `test_large_dict_expanded` — large dict → json.dumps(indent=2) lines

### `TestRenderOutputValue`
- `test_plain_string` — `"hello"` → `["hello"]`
- `test_multiline_string_split` — `"a\nb\nc"` → `["a", "b", "c"]`
- `test_bool` — `True` → `["true"]`
- `test_int` — `42` → `["42"]`
- `test_simple_dict` — `{"a": True, "b": 42}` → `["a: true", "b: 42"]`
- `test_dict_multiline_string_expanded` — `{"diff": "line1\nline2"}` → `["diff:", "  line1", "  line2"]`
- `test_dict_nested_dict` — nested dict renders as indented block
- `test_short_list_inline` — `[1, 2, 3]` → `["[1, 2, 3]"]`
- `test_long_list_expanded` — long list → json.dumps(indent=2) lines
- `test_dict_with_list_value` — list value in dict rendered inline or expanded based on length
- `test_string_value_in_dict` — `{"key": "simple"}` → `["key: \"simple\""]` (json.dumps for non-multiline non-dict/list)

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_1.md.

Implement Step 1: Add the three rendering helper functions to stream_renderer.py
and their tests to test_stream_renderer.py. This is pure additions — do not modify
or remove any existing code. Add the new functions after the existing helpers.
Add test classes at the bottom of the test file.

After implementation, run all three code quality checks.
```
