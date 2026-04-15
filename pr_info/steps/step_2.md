# Step 2: Rewrite `_render_tool_output()` + Tests

> **Context:** Read `pr_info/steps/summary.md` first. This step replaces the field-filtering output renderer with generic rendering.

## Goal
Rewrite `_render_tool_output()` to use `_render_output_value()` from step 1. Remove field filtering (`_ENVELOPE_FIELDS`, `_MAIN_CONTENT_KEYS`). Add `full` parameter for truncation control. Only unwrap `{"result": ...}` envelope.

## WHERE

| File | Action |
|------|--------|
| `src/mcp_coder/llm/formatting/stream_renderer.py` | Rewrite `_render_tool_output()`, remove dead code |
| `tests/llm/formatting/test_stream_renderer.py` | Rewrite output-related test classes |

## WHAT — Changes in `stream_renderer.py`

### Remove
- `_ENVELOPE_FIELDS` frozenset
- `_MAIN_CONTENT_KEYS` tuple
- `_render_value()` function (replaced by `_render_output_value()` from step 1)

### Rewrite `_render_tool_output(output, *, format_tools=True, full=False) -> tuple[list[str], int]`

**New signature** adds `full: bool = False` parameter.

**Algorithm:**
```
if empty or not format_tools: return as before (unchanged)
try json.loads:
  if dict and "result" in parsed:
    render parsed["result"] via _render_output_value()
    render remaining keys via _render_output_value() with blank separator
  elif dict:
    render via _render_output_value(parsed)
  else:
    render via _render_output_value(parsed)
except json: split into plain lines
if not full: apply head/tail truncation (existing logic, unchanged)
return (lines, total)
```

**Key changes from current implementation:**
1. No `_MAIN_CONTENT_KEYS` priority — only `result` is unwrapped
2. No `_ENVELOPE_FIELDS` filtering — all non-`result` keys shown as extras
3. Uses `_render_output_value()` which splits multiline strings (fixes diff rendering)
4. `full=True` skips truncation

## DATA — Behavior changes

| Input | Before | After |
|-------|--------|-------|
| `{"result": "hello", "type": "text"}` | Shows "hello", hides "type" | Shows "hello", then "type: \"text\"" as extra |
| `{"text": "content"}` | Unwraps "text" as main | Renders as `text: "content"` (no unwrap) |
| `{"result": {"diff": "a\nb"}}` | `diff:` + indented but escaped | `diff:` + `  a` + `  b` (split) |
| `{"type": "x", "role": "y"}` | Empty output (all envelope) | `type: "x"` + `role: "y"` (no filtering) |
| any, `full=True` | N/A (param didn't exist) | No truncation applied |

## HOW — Test changes in `test_stream_renderer.py`

### Remove these test classes entirely
- `TestRenderToolOutputFieldFiltering` — field filtering no longer exists

### Rewrite `TestRenderToolOutputRenderer`
Keep existing tests that still apply, update expectations for changed behavior:
- `test_empty` — unchanged: `("", ...) → ([], 0)`
- `test_short_plain` — unchanged: plain text splits into lines
- `test_long_truncated` — unchanged: truncation still works
- `test_json_dict` — **update**: `{"success": True, "count": 42}` now renders via `_render_output_value()` → `["success: true", "count: 42"]` (same result, different code path)
- `test_json_dict_multiline_string` — **update**: multiline strings now split via `_render_output_value()`
- `test_non_dict_json` — unchanged
- `test_invalid_json` — unchanged

### Add new tests to `TestRenderToolOutputRenderer`
- `test_result_envelope_unwrap` — `{"result": "hello"}` → `["hello"]`
- `test_result_envelope_with_extras` — `{"result": "ok", "meta": "x"}` → `["ok", "", "meta: \"x\""]`
- `test_result_dict_with_multiline_diff` — `{"result": {"diff": "a\nb", "ok": true}}` → diff lines split
- `test_no_text_unwrap` — `{"text": "hello"}` renders as `text: "hello"`, NOT unwrapped
- `test_no_content_unwrap` — `{"content": "hello"}` renders as `content: "hello"`, NOT unwrapped
- `test_full_mode_no_truncation` — 30 lines with `full=True` → all 30 lines returned
- `test_compact_mode_truncates` — 30 lines with `full=False` → truncated (existing behavior)

### Rewrite `TestRenderToolOutputTruncation`
- Keep all existing truncation tests (they test `full=False` which is default)
- Add `test_full_mode_skips_truncation` — 30 lines, `full=True` → no truncation

### Rewrite `TestRenderToolOutputRawMode`
- Keep both existing tests unchanged (raw mode behavior is preserved)

### Keep `TestRendererFormatToolsParam` and `TestStreamEventRenderer` as-is
- `test_tool_result_short` and `test_tool_result_truncated` in `TestStreamEventRenderer` — behavior unchanged (they use format_tools=True default, full=False default)

## LLM Prompt

```
Read pr_info/steps/summary.md and pr_info/steps/step_2.md.

Implement Step 2: Rewrite _render_tool_output() to use generic rendering.
Remove _ENVELOPE_FIELDS, _MAIN_CONTENT_KEYS, and _render_value().
Add the full parameter. Rewrite the output-related tests.

Key: only unwrap {"result": ...} envelope. No text/content unwrap, no field filtering.
Use _render_output_value() from step 1 for all JSON rendering.

After implementation, run all three code quality checks.
```
