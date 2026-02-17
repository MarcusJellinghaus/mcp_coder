# Step 6 – Update `create_plan.py` and `prompt.py` to pass `LLMResponseDict` directly to `store_session()`

## Context
See `pr_info/steps/summary.md` for the full picture.

After Steps 1–5, `store_session()` accepts `LLMResponseDict` directly and all implement workflow calls are migrated. This step migrates the remaining two callers:

1. **`create_plan.py`** — currently wraps `LLMResponseDict` into a manually-built dict before calling `store_session()`. Remove the wrapping; pass `LLMResponseDict` directly.

2. **`prompt.py`** — three cases:
   - **just-text** mode: currently calls `ask_llm()` then manually builds a dict for `store_session()`. Switch to `prompt_llm()` and pass `LLMResponseDict` directly.
   - **verbose/raw** mode: currently calls `ask_claude_code_api_detailed_sync()` then passes its return value to `store_session()`. Switch to `prompt_llm()`, pass `LLMResponseDict` directly to `store_session()`, and pass `llm_response["raw_response"]` to the formatters (which expect the same shape — `session_info`, `result_info`, `raw_messages` are inside `raw_response`).
   - **json / session-id** modes: already use `prompt_llm()` correctly; no `store_session()` calls here, no changes needed.

**Key simplification**: formatters are NOT changed. They receive `llm_response["raw_response"]` which has the same shape as before (`session_info`, `result_info`, `raw_messages`, `api_metadata` keys). This avoids touching `formatters.py` and `test_formatters.py`.

---

## WHERE

- **Modify**: `src/mcp_coder/workflows/create_plan.py`
- **Modify**: `src/mcp_coder/cli/commands/prompt.py`
- **Modify**: `tests/workflows/create_plan/test_prompt_execution.py`
- **Modify**: `tests/cli/commands/test_prompt.py`
- **NOT changed**: `src/mcp_coder/llm/formatting/formatters.py`
- **NOT changed**: `tests/llm/formatting/test_formatters.py`

---

## WHAT

### `create_plan.py` — simplify `store_session()` calls (×3)

**Before** (repeated 3 times for each prompt):
```python
response_data = {
    "text": response_1["text"],
    "session_info": {
        "session_id": session_id,
        "model": response_1.get("provider", "claude"),
    },
    "result_info": response_1.get("raw_response", {}),
}
stored_path = store_session(response_data, "Initial Analysis", store_path=session_storage_path)
```

**After**:
```python
stored_path = store_session(response_1, "Initial Analysis", store_path=session_storage_path)
```

Three call sites: `response_1` / `"Initial Analysis"`, `response_2` / `"Simplification Review"`, `response_3` / `"Implementation Plan Creation"`.

No other changes to `create_plan.py`.

### `prompt.py` — just-text mode with `--store-response`

**Before**:
```python
response = ask_llm(args.prompt, provider=provider, method=method, ...)
formatted_output = response.strip()
if getattr(args, "store_response", False):
    response_data = {
        "text": response,
        "session_info": {"model": "claude", "tools": []},
        "result_info": {"duration_ms": 0, "cost_usd": 0.0},
    }
    stored_path = store_session(response_data, args.prompt)
```

**After**:
```python
llm_response = prompt_llm(args.prompt, provider=provider, method=method, ...)
formatted_output = llm_response["text"].strip()
if getattr(args, "store_response", False):
    stored_path = store_session(llm_response, args.prompt)
```

Remove `ask_llm` import from `prompt.py` if no longer used (check the file — it may still be needed elsewhere, but looking at the code it is only used in just-text mode).

### `prompt.py` — verbose/raw mode

**Before**:
```python
response_data = ask_claude_code_api_detailed_sync(args.prompt, timeout, resume_session_id, env_vars, str(project_dir))
if getattr(args, "store_response", False):
    stored_path = store_session(response_data, args.prompt)
if verbosity == "raw":
    formatted_output = format_raw_response(response_data)
elif verbosity == "verbose":
    formatted_output = format_verbose_response(response_data)
else:
    formatted_output = format_text_response(response_data)
```

**After**:
```python
provider, method = parse_llm_method_from_args(llm_method)
llm_response = prompt_llm(args.prompt, provider=provider, method=method,
                           timeout=timeout, session_id=resume_session_id,
                           env_vars=env_vars, project_dir=str(project_dir),
                           execution_dir=str(execution_dir))
if getattr(args, "store_response", False):
    stored_path = store_session(llm_response, args.prompt)
# Pass raw_response sub-dict to formatters — same shape as before
raw_data = llm_response["raw_response"]
if verbosity == "raw":
    formatted_output = format_raw_response(raw_data)
elif verbosity == "verbose":
    formatted_output = format_verbose_response(raw_data)
else:
    formatted_output = format_text_response(raw_data)
```

Remove `ask_claude_code_api_detailed_sync` import from `prompt.py` (and the SDK message type imports) if no longer used. Verify they are not referenced elsewhere in the file before removing.

---

## HOW

**Imports to remove** from `prompt.py` (after verifying not used elsewhere):
```python
from ...llm.interface import ask_llm
from ...llm.providers.claude.claude_code_api import (
    AssistantMessage, ResultMessage, SystemMessage, TextBlock, UserMessage,
    ask_claude_code_api_detailed_sync,
)
```

**`prompt_llm` is already imported** in `prompt.py` (used in session-id and json modes).

**No formatter changes** — `format_verbose_response(raw_data)` where `raw_data = llm_response["raw_response"]` works because `raw_response` from both CLI and API contains `session_info`, `result_info`, `raw_messages`, `api_metadata` keys that the formatters already read.

---

## ALGORITHM

```
create_plan.py store_session calls:
    remove manual dict construction (3 lines per call site × 3 call sites)
    pass response_N directly as first argument to store_session()

prompt.py just-text mode:
    replace ask_llm() with prompt_llm()
    extract text via ["text"]
    pass LLMResponseDict to store_session() directly

prompt.py verbose/raw mode:
    replace ask_claude_code_api_detailed_sync() with prompt_llm()
    pass LLMResponseDict to store_session() directly
    pass llm_response["raw_response"] to formatters (unchanged interface)
    remove now-unused imports
```

---

## DATA

**`create_plan.py`**: `store_session()` receives `LLMResponseDict` with `session_id` at top level; `extract_session_id()` now finds it via the new lookup path added in Step 1.

**`prompt.py` verbose/raw**: `raw_response` shape (from `ask_claude_code_api_detailed_sync` previously):
```python
{
  "session_info": { "session_id": "...", "model": "...", "tools": [...] },
  "result_info": { "duration_ms": ..., "cost_usd": ..., "usage": {...} },
  "raw_messages": [...],
  "api_metadata": {...}
}
```

After change, `llm_response["raw_response"]` for API calls contains the same structure (set in `create_api_response_dict()` in `claude_code_api.py`). Formatters receive the same dict — no change needed.

---

## TESTS

### `tests/workflows/create_plan/test_prompt_execution.py`

In `TestRunPlanningPrompts`:
- The existing tests mock `prompt_llm` and `store_session` and assert store is called. Those mocks need updating because the `store_session` call signature changes (no more manual wrapping).
- Verify that `store_session` is called with `response_1` directly (not a manually-built dict).
- The existing test `test_run_planning_prompts_success` does NOT patch `store_session` — it just checks `prompt_llm` was called 3 times. Confirm the test still passes (store_session is called but not asserted on).
- If `store_session` calls fail silently in tests (no mock), add `@patch("mcp_coder.workflows.create_plan.store_session")` to prevent file system side effects.

### `tests/cli/commands/test_prompt.py`

**just-text mode tests** (`test_basic_prompt_success`, etc.):
- These currently mock `ask_llm`. After the change, they should mock `prompt_llm` instead.
- `prompt_llm` mock returns `LLMResponseDict` dict; the test verifies `["text"]` is printed.
- All existing test assertions about call args need updating (mock target changes).

**verbose/raw mode tests** (`TestFormatVerboseResponse`, `TestFormatRawResponse`):
- Currently mock `ask_claude_code_api_detailed_sync`. After the change, mock `prompt_llm` instead.
- `prompt_llm` mock returns `LLMResponseDict` where `raw_response` contains the same rich data that the tests currently set up in the `mock_response` dict.
- The formatters receive `raw_response`, so test assertions about output content remain valid.
- The call signature assertion changes: instead of `mock_ask_claude.call_args[0][0] == "prompt"`, check `mock_prompt_llm.call_args[0][0] == "prompt"` etc.

**`test_continue_from_with_verbose_output`**:
- Currently calls `ask_claude_code_api_detailed_sync` and asserts on its call args.
- Update to mock `prompt_llm` and assert on its call args instead.

---

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_6.md for full context.

Your task is to implement Step 6: update create_plan.py and prompt.py to pass LLMResponseDict
directly to store_session().

Follow TDD — update tests FIRST, then implement:

PART A — create_plan.py:
1. In `tests/workflows/create_plan/test_prompt_execution.py`:
   - Add @patch("mcp_coder.workflows.create_plan.store_session") to tests that call prompt_llm
   - Verify store_session is called with the LLMResponseDict directly (not a manually-wrapped dict)
   - Run tests — they will fail until implementation
2. In `src/mcp_coder/workflows/create_plan.py`, in run_planning_prompts():
   - Remove the manual response_data dict construction at each store_session call site (×3)
   - Pass response_1, response_2, response_3 directly as first arg to store_session()
3. Run tests to confirm they pass.

PART B — prompt.py just-text mode:
1. In `tests/cli/commands/test_prompt.py`:
   - Replace @patch("mcp_coder.cli.commands.prompt.ask_llm") with @patch("mcp_coder.cli.commands.prompt.prompt_llm")
   - prompt_llm mock must return LLMResponseDict with "text" key
   - Update call_args assertions accordingly
   - Run tests — they will fail until implementation
2. In `src/mcp_coder/cli/commands/prompt.py` just-text branch:
   - Replace ask_llm() with prompt_llm(); extract text via ["text"]
   - Pass llm_response directly to store_session() instead of manually-built dict
3. Run tests.

PART C — prompt.py verbose/raw mode:
1. In `tests/cli/commands/test_prompt.py`:
   - Replace @patch("mcp_coder.cli.commands.prompt.ask_claude_code_api_detailed_sync")
     with @patch("mcp_coder.cli.commands.prompt.prompt_llm")
   - prompt_llm mock returns LLMResponseDict where raw_response contains session_info, result_info,
     raw_messages, api_metadata (same data the tests currently set up)
   - Update call_args assertions (e.g. call_args[0][0] → check prompt was first arg)
   - Run tests — they will fail until implementation
2. In `src/mcp_coder/cli/commands/prompt.py` verbose/raw branch:
   - Replace ask_claude_code_api_detailed_sync() with prompt_llm()
   - Pass llm_response directly to store_session()
   - Pass llm_response["raw_response"] to format_verbose_response() / format_raw_response()
     (formatters are NOT changed — they receive the same dict shape via raw_response)
3. Remove now-unused imports from prompt.py:
   - ask_llm (if no longer used)
   - ask_claude_code_api_detailed_sync, AssistantMessage, ResultMessage, SystemMessage,
     TextBlock, UserMessage (if no longer used — verify before removing)
4. Run all tests to confirm they pass.

DO NOT modify formatters.py or test_formatters.py.
```
