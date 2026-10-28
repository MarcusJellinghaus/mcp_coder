# Step 1 — Exception summary helpers

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_1.md` only.
> TDD: write the tests first, then the code. Run pylint, mypy, pytest
> (`-n auto`, fast unit markers), lint-imports and tach; all must pass. Format, then
> make exactly one commit.

## WHERE

- Create `src/mcp_coder/llm/error_summary.py`
- Modify `src/mcp_coder/workflow_utils/failure_handling.py`
- Create `tests/llm/test_error_summary.py`
- Modify `tests/workflow_utils/test_failure_handling.py`

## WHAT

`llm/error_summary.py`:

```python
_STREAM_FILE_RE = re.compile(r"\s*Stream file: .*\Z")
_COMMENT_LIMIT = 300

def summarize_exception(exc: BaseException) -> str: ...
def comment_safe(text: str) -> str: ...
```

`workflow_utils/failure_handling.py` (next to `llm_failure_reason`):

```python
def exception_summary(exc: BaseException) -> str: ...
```

## HOW

- `error_summary.py` imports `CalledProcessError` from
  `mcp_coder.utils.subprocess_runner` (never `import subprocess` — the
  `subprocess_isolation` contract forbids it). No other project imports.
- `failure_handling.py` imports `summarize_exception` from
  `mcp_coder.llm.error_summary` (workflow_utils → llm is allowed).
- Do not change `llm_failure_reason` or `format_mcp_unavailable_message`.

## ALGORITHM

```
summarize_exception(exc):
    name = type(exc).__name__
    if isinstance(exc, CalledProcessError):
        stderr = exc.stderr decoded if bytes (errors="replace"), "" if None; .strip()
        if _STREAM_FILE_RE.sub("", stderr).strip():   # copilot-only suffix -> fallback
            return f"{name}: {stderr}"                 # full text, path kept (console)
    return f"{name}: {exc}"

comment_safe(text):
    text = _STREAM_FILE_RE.sub("", text.strip())
    return text if len(text) <= _COMMENT_LIMIT else text[: _COMMENT_LIMIT - 1].rstrip() + "…"

exception_summary(exc):
    if isinstance(exc, McpServersUnavailableError): return format_mcp_unavailable_message(exc)
    return summarize_exception(exc)
```

## DATA

All three return `str`. `comment_safe` output length is ≤ `_COMMENT_LIMIT`.

## Tests

`tests/llm/test_error_summary.py`:
- generic `RuntimeError("boom")` → `"RuntimeError: boom"`
- `CalledProcessError(1, "claude", stderr="529 Overloaded")` → `"CalledProcessError: 529 Overloaded"`
- bytes stderr is decoded
- `stderr=None` and `stderr="  "` → fallback `f"CalledProcessError: {exc}"`
- copilot-only `stderr="Stream file: /x/y.log"` → fallback
- `summarize_exception` keeps the stream-file suffix (console text is full)
- `comment_safe` strips each shape:
  `"CLI failed with code 1. Stream file: /p"` → `"CLI failed with code 1."`;
  `"msg Stream file: None"` → `"msg"`; `"err\nStream file: /p"` → `"err"`
- `comment_safe("x" * 1000)` → length 300, ends with `"…"`; short text unchanged

`tests/workflow_utils/test_failure_handling.py`:
- `exception_summary(McpServersUnavailableError("down", {"a": "failed"}))` equals
  `format_mcp_unavailable_message(...)` of the same error
- `exception_summary(RuntimeError("boom"))` → `"RuntimeError: boom"`
