# Step 4: Merge utility functions from p_tools reference

> **Context**: See `pr_info/steps/summary.md` for full issue context (Issue #618).
> This step ports missing utilities from the p_tools reference repo into this leading repo.

## LLM Prompt

```
Implement Step 4 of Issue #618 (see pr_info/steps/summary.md and pr_info/steps/step_4.md).

Copy check_tool_missing_error, truncate_stderr, and MAX_STDERR_IN_ERROR from the p_tools
reference project into subprocess_runner.py. Write tests first (TDD). Run all three code quality checks.
```

## WHERE

- `tests/utils/test_subprocess_runner.py` — add tests
- `src/mcp_coder/utils/subprocess_runner.py` — add functions + constant + update `__all__`

## WHAT

### 1. Add constant

```python
MAX_STDERR_IN_ERROR: int = 500
```

### 2. Add `check_tool_missing_error`

```python
def check_tool_missing_error(
    stderr: str, tool_name: str, python_path: str
) -> str | None:
    """Check if stderr indicates the tool is not installed."""
    if f"No module named {tool_name}" in stderr:
        return (
            f"{tool_name} is not installed in the configured Python environment "
            f"({python_path}). Ensure --python-executable and --venv-path point "
            f"to the environment where {tool_name} is installed."
        )
    return None
```

### 3. Add `truncate_stderr`

```python
def truncate_stderr(stderr: str, max_len: int = MAX_STDERR_IN_ERROR) -> str:
    """Truncate stderr to a maximum length."""
    if len(stderr) > max_len:
        return stderr[:max_len] + "..."
    return stderr
```

### 4. Update `__all__`

Add to the existing `__all__` list:
- `"MAX_STDERR_IN_ERROR"`
- `"check_tool_missing_error"`
- `"truncate_stderr"`

## SOURCE

These are copied from `p_tools/src/mcp_tools_py/utils/subprocess_runner.py` (reference project).
The implementations are identical — no adaptation needed.

## TESTS

Add a new `TestMergedUtilities` class:

1. **`test_check_tool_missing_error_detects_missing_module`** — stderr containing "No module named pytest" → returns actionable message
2. **`test_check_tool_missing_error_returns_none_for_other_errors`** — stderr with unrelated error → returns None
3. **`test_truncate_stderr_short_string_unchanged`** — string shorter than max_len → returned as-is
4. **`test_truncate_stderr_long_string_truncated`** — string longer than max_len → truncated with "..."
5. **`test_truncate_stderr_custom_max_len`** — verify custom max_len parameter works
6. **`test_max_stderr_in_error_constant`** — verify `MAX_STDERR_IN_ERROR == 500`

## COMMIT MESSAGE

```
feat: merge check_tool_missing_error and truncate_stderr from p_tools (#618)
```
