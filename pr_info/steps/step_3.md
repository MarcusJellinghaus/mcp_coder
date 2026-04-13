# Step 3: stream_subprocess API update in claude_code_cli_streaming.py

**Commit message:** `adopt mcp-coder-utils: adapt claude_code_cli_streaming to new stream_subprocess API`

> **Context:** See `pr_info/steps/summary.md` for the full plan (issue #744).
> This step updates the only caller of `stream_subprocess` to use the new API from mcp-coder-utils.

## WHERE

- `src/mcp_coder/llm/providers/claude/claude_code_cli_streaming.py`

## WHAT

The shared `stream_subprocess()` now:
1. Returns `StreamResult` directly (no manual wrapping needed)
2. Takes `inactivity_timeout_seconds` as a separate kwarg instead of using `options.timeout_seconds`

### Changes

**Remove:** `stream = StreamResult(stream_subprocess(command, options))`

**Replace with:** `stream = stream_subprocess(command, options, inactivity_timeout_seconds=timeout)`

**Also:** The `CommandOptions.timeout_seconds` should no longer be set to the inactivity timeout value. Either remove it from options or set it to a large value (process-level timeout vs inactivity timeout are now separate concerns). Check the current code — `timeout_seconds=timeout` in CommandOptions means the same value is used for both. With the new API, `inactivity_timeout_seconds` is passed separately, so `timeout_seconds` in options can be omitted (it defaults to 120s in CommandOptions).

**Remove import:** `StreamResult` is no longer needed in the import from `subprocess_streaming` (it's used internally by the returned object, but the caller doesn't construct it). Keep it if the type annotation `stream.result` still needs it for type checking.

## HOW

```python
# Before:
from ....utils.subprocess_streaming import StreamResult, stream_subprocess

options = CommandOptions(
    timeout_seconds=timeout,
    input_data=input_data,
    ...
)
stream = StreamResult(stream_subprocess(command, options))

# After:
from ....utils.subprocess_streaming import stream_subprocess

options = CommandOptions(
    input_data=input_data,
    ...
)
stream = stream_subprocess(command, options, inactivity_timeout_seconds=timeout)
```

## ALGORITHM

```python
# 1. Build command and options (no timeout_seconds in options)
options = CommandOptions(input_data=input_data, env=env_vars, cwd=cwd, env_remove=["CLAUDECODE"])
# 2. Call stream_subprocess with inactivity_timeout_seconds kwarg
stream = stream_subprocess(command, options, inactivity_timeout_seconds=timeout)
# 3. Iterate stream lines (unchanged)
for line in stream: ...
# 4. Access stream.result after iteration (unchanged)
cmd_result = stream.result
```

## DATA

No data structure changes. `StreamResult` is returned by `stream_subprocess()` directly now.

## VERIFICATION

- Existing streaming tests pass
- The function signature matches: `stream_subprocess(command, options, inactivity_timeout_seconds=None) -> StreamResult`
- Run pylint, mypy, pytest

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md.

Implement step 3: Update claude_code_cli_streaming.py to use the new
stream_subprocess API. Remove the manual StreamResult() wrapper, pass
inactivity_timeout_seconds as a kwarg, and remove timeout_seconds from
CommandOptions. Do NOT modify any other files. Run all checks after.
```
