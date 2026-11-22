# Step 2 — Pure failure-message builder

## LLM prompt

> Read `pr_info/steps/summary.md` (section "Message formats"), then implement
> `pr_info/steps/step_2.md` only. Write the tests first, then the code. Run pylint, pytest
> (`-n auto`, fast unit markers), mypy; run `run_format_code`; run `check_file_size`. Make one commit.

## WHERE

- Create `src/mcp_coder/llm/providers/claude/claude_cli_failure.py`. It is pure: no I/O, no
  logging, and it imports nothing from `mcp_coder`.
- Create `tests/llm/providers/claude/test_claude_cli_failure.py`.

## WHAT

```python
__all__ = ["build_cli_failure"]

_AUTH_HINT = "Run `claude`, then `/login`."
_AUTH_PATTERNS = (
    "not logged in",           # confirmed by the capture
    "please run /login",       # confirmed by the capture
    "authentication_error",    # #148 repro
    "oauth token has expired", # #148 repro
    "invalid api key",
)
_STDERR_LIMIT = 500

def build_cli_failure(
    result_text: str | None,
    is_error: bool,
    subtype: str | None,
    stderr: str,
    return_code: int,
) -> tuple[str, str]:
    """Build the error-event (message, reason) for a failed Claude CLI run.

    Call only on failure (non-zero exit or is_error). reason is
    "auth" | "nonzero_exit" | "result_error".
    """
```

## ALGORITHM

```
result = (result_text or "").strip() if is_error else ""
failure_text = result or stderr                     # full stderr for matching
if any(p in failure_text.lower() for p in _AUTH_PATTERNS):
    text = result or stderr[:_STDERR_LIMIT]
    return f"{_AUTH_HINT} {' '.join(text.split())}", "auth"   # one line, no stderr suffix
reason = "nonzero_exit" if return_code != 0 else "result_error"
if result:     msg = result + (f"; stderr: {stderr[:500]}" if stderr else "")
elif is_error: msg = "CLI reported an error" + (f" (subtype: {subtype})" if subtype and subtype != "success" else "") + (f": {stderr[:500]}" if stderr else "")
else:          msg = f"CLI failed with code {return_code}" + (f": {stderr[:500]}" if stderr else "")
return msg, reason
```

- The non-auth branches keep `stderr[:500]` exactly as today, without stripping, so the
  existing `CLI failed with code 1: <stderr>` tests stay green.

## DATA

- Returns `tuple[str, str]` = `(message, reason)`.

## Tests (first) — one parametrized table plus a few named cases

- Auth from the result text: `("Not logged in · Please run /login", is_error=True, subtype="success", stderr=<trust warning>, rc=1)`
  → ``("Run `claude`, then `/login`. Not logged in · Please run /login", "auth")``. The
  stderr is not appended.
- #148 text (`API Error: 401 {..."authentication_error"..."OAuth token has expired..."} · Please run /login`)
  → `auth`, and the message starts with the hint.
- Auth from stderr, with `is_error=False` and with `is_error=True` + empty result → `auth`;
  the failure text is the stderr.
- Case-insensitive: `"NOT LOGGED IN"` and `"invalid API KEY"` → `auth`.
- `stderr="auth failed"`, rc=1 → `("CLI failed with code 1: auth failed", "nonzero_exit")`. This
  must stay non-auth.
- Patterns are not matched against assistant text: the function never receives it (document
  this in the docstring); `is_error=False` ignores `result_text` containing "Please run /login".
- Non-auth `is_error` with result text and stderr → `"<text>; stderr: <stderr>"`; rc=0 →
  `result_error`, rc=2 → `nonzero_exit`.
- `is_error`, empty result, `subtype="error_during_execution"` →
  `"CLI reported an error (subtype: error_during_execution)"`.
- `is_error`, empty result, `subtype="success"` or `None` → `"CLI reported an error"`, with
  no parenthetical.
- No message ever contains `"code 0"` (rc=0 cases).
- stderr of 600 characters is truncated to 500 in the message; an auth pattern at position
  550 of stderr is still detected.
- An auth message from multi-line stderr has no `\n`.
