# Step 4 — `ask_claude_code_cli` raises `LLMAuthError`; clamp the return code

## LLM prompt

> Read `pr_info/steps/summary.md`, then implement `pr_info/steps/step_4.md` only. Steps 1–3
> are done. Write the tests first, then the code. Run pylint, pytest (`-n auto`, fast unit
> markers), mypy; run `run_format_code`; run `check_file_size`. Make one commit.

## WHERE

- `src/mcp_coder/llm/providers/claude/claude_code_cli.py`: `ask_claude_code_cli`.
- `src/mcp_coder/llm/interface.py`: the Raises section of the `prompt_llm` docstring only.
- Create `tests/llm/providers/claude/test_claude_cli_auth_errors.py`. Reuse
  `tests/llm/providers/claude/logged_out_capture.py`, and patch the same three
  `claude_code_cli_streaming` targets as step 3.

## WHAT

- Import `LLMAuthError` from `...types` (with `LLM_RESPONSE_VERSION`, etc.).
- In `ask_claude_code_cli`, after the inactivity-timeout branch and before the generic
  error branch:

## ALGORITHM

```
if last_error is not None and last_error.get("reason") == "auth":
    auth_error = LLMAuthError(str(last_error.get("message") or ""))
    log_llm_error(error=auth_error, duration_ms=duration_ms)
    logger.debug("Claude CLI authentication failed. Stream file: %s", stream_file)
    raise auth_error
# generic branch (unchanged except the clamp):
return_code = max(rc, 1) if isinstance(rc, int) else 1
```

- The `LLMAuthError` message is exactly the event message, with no `Stream file:` suffix.
- `log_llm_error`'s signature is unchanged.

## DATA

- Raises `LLMAuthError(str)` for `reason == "auth"`.
- Raises `CalledProcessError(returncode >= 1, ["claude", "-p"], stderr="<message> Stream file: <path>")`
  for `nonzero_exit` / `result_error`.
- Docstrings: the Raises section of `ask_claude_code_cli` adds `LLMAuthError`, and notes that
  `CalledProcessError` also covers exit 0 + `is_error` (returncode clamped to ≥ 1). The
  `prompt_llm` Raises section adds `LLMAuthError` (Claude login / langchain API-key failures).

## Tests (first)

- Fixture run (rc 1, trust-warning stderr) → `pytest.raises(LLMAuthError)`;
  `str(exc) == AUTH_MESSAGE`; `"Stream file" not in str(exc)`.
- The stream-file path appears in a DEBUG record (`caplog` at DEBUG for the
  `mcp_coder.llm.providers.claude.claude_code_cli` logger).
- Exit 0 + non-auth `is_error` result → `CalledProcessError` with `returncode == 1`, never 0;
  `.stderr` contains the result text.
- Non-zero exit with stderr `"auth failed"` → `CalledProcessError(1)`, not `LLMAuthError`.
- `isinstance(exc, LLMAuthError)` also holds via `mcp_coder.llm.interface.LLMAuthError`.
- Existing `test_claude_code_cli*.py` tests stay green.
