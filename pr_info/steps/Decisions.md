# Decisions — Issue #642

## D1: Nested dicts/lists in tool output rendering
Nested dicts/lists are serialized as a single-line JSON string via `json.dumps(value)` rather than recursively expanded.

## D2: Reuse `_format_tool_args()` for inline args
The `tool_use_start` inline format reuses the existing `_format_tool_args()` helper instead of duplicating the formatting logic inline.

## D3: Block format always uses `json.dumps` for values
In block format, all values (including strings) are rendered via `json.dumps(value)` for consistency and simplicity. The original issue examples show quoted strings in block format.

## D4: Named constant for inline arg limit
Replace magic number `2` with `_RENDERED_INLINE_ARG_LIMIT = 2` to clarify the threshold between inline and block arg display.

## D5: Use `@pytest.mark.parametrize` for related test groups
Group related test cases using parametrize:
- Tests 1/9/10 (non-tool events: text_delta, error, done)
- Tests 4/5/6/7 (result variations: short, long, JSON, empty)

## D6: Move test files from "Check" to "Modify" in Step 4
`test_prompt_streaming.py` and `test_prompt.py` are likely to need small updates (docstring/default references) when the default format changes, so they belong in the Modify list.
