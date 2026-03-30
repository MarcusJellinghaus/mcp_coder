# Step 2: Tool output rendering helper

> See `pr_info/steps/summary.md` for full context (Issue #642).

## Goal

Add `_render_tool_output()` to `formatters.py` with unit tests.

## WHERE

- **Implement**: `src/mcp_coder/llm/formatting/formatters.py`
- **Test**: `tests/llm/formatting/test_formatters.py`

## WHAT

```python
_RENDERED_TRUNCATION_LIMIT = 5

def _render_tool_output(output: str) -> tuple[list[str], int]:
    """Render tool output into display lines with truncation.

    1. If output is empty, return ([], 0)
    2. Try json.loads: if dict, expand top-level keys as "key: value" lines.
       For string values containing newlines, indent continuation lines.
    3. If json.loads fails, split output into plain text lines.
    4. Truncate to _RENDERED_TRUNCATION_LIMIT lines.

    Returns:
        (display_lines, total_line_count) — display_lines may be shorter
        than total_line_count if truncated.
    """
```

## ALGORITHM

```
if not output:
    return ([], 0)
try:
    parsed = json.loads(output)
    if isinstance(parsed, dict):
        lines = expand_dict_keys(parsed)   # "key: value", string values split on \n
    else:
        lines = str(parsed).splitlines()
except (json.JSONDecodeError, ValueError):
    lines = output.splitlines()
total = len(lines)
truncated = lines[:LIMIT]
return (truncated, total)
```

### Dict key expansion detail

For each `(key, value)` in the dict:
- If value is a string containing `\n`: first line is `key:`, subsequent lines indented by 2 extra spaces
- Otherwise: `key: <json-serialized value>` (use `json.dumps` for non-strings, `repr` not needed)

Example: `{"success": true, "diff": "@@ -1 @@\n-foo\n+bar"}` →
```
success: true
diff:
  @@ -1 @@
  -foo
  +bar
```

Nested dicts/lists are serialized as a single-line JSON string via `json.dumps(value)`.

## DATA

- **Input**: `output` string from `StreamEvent["output"]`
- **Output**: `(list[str], int)` — display lines and total line count

## Tests to write (new class `TestRenderToolOutput`)

1. Empty output → `([], 0)`
2. Short plain text (2 lines) → all lines returned, total=2
3. Long plain text (10 lines) → first 5 lines, total=10
4. JSON dict with simple values → expanded `key: value` lines
5. JSON dict with multiline string value → key on own line, value lines indented
6. Non-dict JSON (e.g., a JSON array) → falls back to `str().splitlines()`
7. Invalid JSON → plain text fallback

## LLM Prompt

```
Implement Step 2 of Issue #642 (see pr_info/steps/summary.md and pr_info/steps/step_2.md).

Add the _render_tool_output() helper function and _RENDERED_TRUNCATION_LIMIT constant to
src/mcp_coder/llm/formatting/formatters.py and its unit tests to
tests/llm/formatting/test_formatters.py. Follow TDD: write the tests first, then implement
the function. Run all three code quality checks after changes. Produce one commit.
```
