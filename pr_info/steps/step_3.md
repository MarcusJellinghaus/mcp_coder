# Step 3: Thread `session_id` Through CLI and API Callers

## Context
See [summary.md](summary.md) for the full design.
Steps 1 and 2 must be complete before this step.

This step makes the two LLM callers pass the Claude-returned `session_id` into
`log_llm_response()`. With this in place, every successful LLM call:
1. Ends its MLflow run (from Step 2)
2. Stores the `session_id → run_id` mapping (from Step 1) so that `_log_to_mlflow()`
   in `prompt.py` can later resume that exact run

Both files are one-liner changes.

---

## WHERE

| Role | Path |
|------|------|
| Tests | `tests/llm/providers/claude/test_claude_code_cli.py` — add one test |
| Tests | `tests/llm/providers/claude/test_claude_code_api.py` — add one test |
| Implementation | `src/mcp_coder/llm/providers/claude/claude_code_cli.py` |
| Implementation | `src/mcp_coder/llm/providers/claude/claude_code_api.py` |

---

## WHAT

### `claude_code_cli.py` — change in `ask_claude_code_cli()`

**Before:**
```python
log_llm_response(
    method="cli", duration_ms=duration_ms, cost_usd=cost_usd, usage=usage
)
```

**After:**
```python
log_llm_response(
    method="cli",
    duration_ms=duration_ms,
    session_id=parsed["session_id"],   # NEW
    cost_usd=cost_usd,
    usage=usage,
)
```

`parsed["session_id"]` is already available at this point — it was extracted by
`parse_stream_json_string()` earlier in the same function.

### `claude_code_api.py` — change in `ask_claude_code_api()`

**Before:**
```python
log_llm_response(
    method="api",
    duration_ms=duration_ms,
    cost_usd=detailed["result_info"].get("cost_usd"),
    usage=detailed["result_info"].get("usage"),
    num_turns=detailed["result_info"].get("num_turns"),
)
```

**After:**
```python
log_llm_response(
    method="api",
    duration_ms=duration_ms,
    session_id=actual_session_id,      # NEW
    cost_usd=detailed["result_info"].get("cost_usd"),
    usage=detailed["result_info"].get("usage"),
    num_turns=detailed["result_info"].get("num_turns"),
)
```

`actual_session_id` is already assigned a few lines above (`actual_session_id =
detailed["session_info"].get("session_id")`), so no new variable is needed.

---

## HOW

### Integration points
- `session_id` may be `None` in both cases (Claude occasionally omits it); this is
  safe — `end_run(session_id=None)` simply skips the mapping (Step 1 behaviour)
- No imports change
- Error paths (`log_llm_error()`) are already handled separately and unaffected

---

## ALGORITHM

No algorithmic logic in this step — purely threading an existing variable into an
existing function call. The logic is all in Steps 1 and 2.

---

## DATA

| Source | Variable | Passed to |
|--------|----------|-----------|
| `parsed["session_id"]` from `parse_stream_json_string()` | `str \| None` | `log_llm_response(session_id=...)` |
| `actual_session_id` from `detailed["session_info"].get("session_id")` | `str \| None` | `log_llm_response(session_id=...)` |

---

## TESTS

Write these tests **first**, then implement.

### `test_claude_code_cli.py` — Test 1: session_id from parsed response passed to log_llm_response

```
Patch: log_llm_response, _find_claude_executable, execute_subprocess,
       get_stream_log_path

Set up execute_subprocess to return a stream-json payload where
session_id = "cli-session-abc"

Call ask_claude_code_cli("test question")

Capture the call to log_llm_response.
Assert: log_llm_response was called with session_id="cli-session-abc"
```

### `test_claude_code_api.py` — Test 1: actual_session_id passed to log_llm_response

```
Patch: log_llm_response, ask_claude_code_api_detailed_sync

Set up ask_claude_code_api_detailed_sync to return:
    {
        "text": "answer",
        "session_info": {"session_id": "api-session-xyz"},
        "result_info": {"cost_usd": 0.01, "usage": {}, "num_turns": 1},
    }

Call ask_claude_code_api("test question")

Assert: log_llm_response was called with session_id="api-session-xyz"
```

### Regression: all existing tests in both test files still pass

No existing tests assert that `session_id` was absent from the `log_llm_response`
call, so no existing tests break.

---

## LLM Prompt

```
You are implementing Step 3 of GitHub issue #491 "Fix MLflow 'already active run' warning".

Read pr_info/steps/summary.md for full context and design.
Steps 1 and 2 must already be complete.

Your task: add one test to each of the two test files, then make one-line changes
to each of the two implementation files.

Follow TDD: write the tests FIRST, then implement.

--- claude_code_cli.py ---
In ask_claude_code_cli(), find the call to log_llm_response().
Add `session_id=parsed["session_id"]` as a keyword argument.
`parsed` is the ParsedStreamResponse already in scope at that point.

--- claude_code_api.py ---
In ask_claude_code_api(), find the call to log_llm_response().
Add `session_id=actual_session_id` as a keyword argument.
`actual_session_id` is already assigned a few lines above this call.

--- Tests ---
In test_claude_code_cli.py: add a test that patches `log_llm_response` and asserts
it is called with `session_id="cli-session-abc"` when the stream-json output
contains that session_id.

In test_claude_code_api.py: add a test that patches `log_llm_response` and asserts
it is called with `session_id="api-session-xyz"` when
ask_claude_code_api_detailed_sync returns session_info={"session_id": "api-session-xyz"}.

Do not change any other logic in either file.

Run the tests after implementation:
    pytest tests/llm/providers/claude/test_claude_code_cli.py -v
    pytest tests/llm/providers/claude/test_claude_code_api.py -v
```
