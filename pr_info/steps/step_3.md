# Step 3: Rendered format branch in print_stream_event

> See `pr_info/steps/summary.md` for full context (Issue #642).

## Goal

Add the `rendered` output format handling to `print_stream_event()` using the helpers
from Steps 1-2. This is the core rendering logic.

## WHERE

- **Implement**: `src/mcp_coder/llm/formatting/formatters.py`
- **Test**: `tests/llm/formatting/test_formatters.py`

## WHAT

New `elif output_format == "rendered":` branch inside `print_stream_event()`.

## HOW

Uses `_format_tool_name()` (Step 1) and `_render_tool_output()` (Step 2).
No new imports needed — just `json` (already imported).

## ALGORITHM — tool_use_start

```
display_name = _format_tool_name(name)
if len(args) <= _RENDERED_INLINE_ARG_LIMIT:
    args_str = _format_tool_args(args)  # existing helper from formatters.py
    print(f"┌ {display_name}({args_str})")
else:  # block format
    print(f"┌ {display_name}")
    for key, value in args.items():
        print(f"│  {key}: {json.dumps(value)}")
```

## ALGORITHM — tool_result

```
lines, total = _render_tool_output(str(output))
for line in lines:
    print(f"│  {line}")
if total > LIMIT:
    print(f"└ done ({total} lines, truncated to {LIMIT})")
else:
    print(f"└ done")
print()  # blank line after └
```

## ALGORITHM — other events

```
text_delta:  print(text, end="")           # same as text format
error:       print(message, file=stderr)   # same as text format
done:        print()                       # final newline
```

## CONSTANTS

```python
_RENDERED_INLINE_ARG_LIMIT = 2  # max args for inline format; more switches to block format
```

## DATA

- **Input**: `StreamEvent` dict + `output_format="rendered"`
- **Output**: printed to `file` (stdout by default)

## Tests to write (new class `TestRenderedStreamFormat`)

All tests use `io.StringIO` buffer passed as `file` to `print_stream_event()`.

1. **text_delta** — prints text inline (no newline between deltas)
2. **Inline params (1-2 args)** — `┌ workspace > read_file(file_path="x.py")`
3. **Block params (3+ args)** — `┌ name` then `│  key: value` lines
4. **Short result** — `│  line` + `└ done`
5. **Long result (>5 lines)** — truncated lines + `└ done (N lines, truncated to 5)`
6. **JSON result** — expanded keys with indented multiline strings
7. **Empty result** — `└ done` only (no `│` lines)
8. **Blank line after `└`** — output ends with `\n` after `└ done`
9. **Error to stderr** — same behavior as text format
10. **Done event** — prints newline

**Note:** Use `@pytest.mark.parametrize` to group related cases:
- Tests 1/9/10 (non-tool events: text_delta, error, done) as parametrized
- Tests 4/5/6/7 (result variations: short, long, JSON, empty) as parametrized

## LLM Prompt

```
Implement Step 3 of Issue #642 (see pr_info/steps/summary.md and pr_info/steps/step_3.md).

Add the "rendered" output format branch to print_stream_event() in
src/mcp_coder/llm/formatting/formatters.py, using _format_tool_name() and
_render_tool_output() from previous steps. Add unit tests to
tests/llm/formatting/test_formatters.py using io.StringIO. Follow TDD: write
the tests first, then implement. Run all three code quality checks after changes.
Produce one commit.
```
