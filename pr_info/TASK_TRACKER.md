# Task Status Tracker

## Instructions for LLM

This tracks **Feature Implementation** consisting of multiple **Tasks**.

**Summary:** See [summary.md](./steps/summary.md) for implementation overview.

**How to update tasks:**
1. Change [ ] to [x] when implementation step is fully complete (code + checks pass)
2. Change [x] to [ ] if task needs to be reopened
3. Add brief notes in the linked detail files if needed
4. Keep it simple - just GitHub-style checkboxes

**Task format:**
- [x] = Task complete (code + all checks pass)
- [ ] = Task not complete
- Each task links to a detail file in steps/ folder

---

## Tasks

### Step 1: Tool name formatting helper (`_format_tool_name`)
> [Detail](./steps/step_1.md) — `formatters.py`, `test_formatters.py`

- [x] Implementation: add `_format_tool_name()` + unit tests (TestFormatToolName)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

**Commit message:**
```
feat: add _format_tool_name() helper for rendered output format

Add private helper that strips mcp__ prefix and splits on first
remaining __ to produce human-readable server > tool display names.
Built-in tool names pass through unchanged. Includes unit tests.

Part of #642 (rendered output format) - Step 1/4.
```

### Step 2: Tool output rendering helper (`_render_tool_output`)
> [Detail](./steps/step_2.md) — `formatters.py`, `test_formatters.py`

- [x] Implementation: add `_render_tool_output()` + `_RENDERED_TRUNCATION_LIMIT` constant + unit tests (TestRenderToolOutput)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

**Commit message:**
```
feat: add _render_tool_output() helper with truncation support

Add _render_tool_output() and _RENDERED_TRUNCATION_LIMIT constant to
formatters.py. The helper renders tool output into display lines:
JSON dicts expand top-level keys as key: value with indented
multiline string values; non-dict JSON and plain text fall back to
splitlines(). Output is truncated to 5 lines. Includes 7 unit tests.

Part of #642 (rendered output format) - Step 2/4.
```

### Step 3: Rendered format branch in `print_stream_event`
> [Detail](./steps/step_3.md) — `formatters.py`, `test_formatters.py`

- [x] Implementation: add `rendered` branch in `print_stream_event()` + `_RENDERED_INLINE_ARG_LIMIT` constant + unit tests (TestRenderedStreamFormat)
- [x] Quality checks: pylint, pytest, mypy — fix all issues
- [x] Commit message prepared

**Commit message:**
```
feat: add rendered output format branch in print_stream_event()

Add _RENDERED_INLINE_ARG_LIMIT constant and "rendered" branch to
print_stream_event(). Tool calls with ≤2 args render inline as
┌ server > tool(args); 3+ args use block format with │ lines.
Tool results use _render_tool_output() with truncation and └ done
footer. Includes 10 unit tests in TestRenderedStreamFormat. Also
fixes pre-existing mypy type errors in the text format branch.

Part of #642 (rendered output format) - Step 3/4.
```

### Step 4: CLI wiring — parser + prompt command + test updates
> [Detail](./steps/step_4.md) — `parsers.py`, `prompt.py`, test files

- [ ] Implementation: add `rendered` to parser choices/default, add to streaming format tuple in `prompt.py`, update affected tests
- [ ] Quality checks: pylint, pytest, mypy — fix all issues
- [ ] Commit message prepared

## Pull Request

- [ ] PR review: verify all steps integrated correctly
- [ ] PR summary prepared
