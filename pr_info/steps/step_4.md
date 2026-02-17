# Step 4 – Switch `task_processing.py` to `prompt_llm()` + `store_session()`

## Context
See `pr_info/steps/summary.md` for the full picture.

After Step 3, `task_processing.py` calls `ask_llm()` for both main task implementation and mypy fix attempts. This step upgrades those calls to `prompt_llm()` and adds `store_session()` after each successful call, writing session JSON to `.mcp-coder/implement_sessions/`.

Two call sites:
1. **`process_single_task()`** — main task implementation (step_name: `step_N`)
2. **`check_and_fix_mypy()`** — each mypy fix attempt (step_name: `step_N_mypy_M`)

---

## WHERE

- **Modify**: `src/mcp_coder/workflows/implement/task_processing.py`
- **Modify**: `tests/workflows/implement/test_task_processing.py`

---

## WHAT

### `process_single_task()` — replace `ask_llm()` with `prompt_llm()` + `store_session()`

```python
from mcp_coder.llm.interface import prompt_llm          # replace ask_llm import
from mcp_coder.llm.storage.session_storage import store_session
from mcp_coder.utils.git_utils import get_branch_name_for_logging

# In process_single_task():
llm_response = prompt_llm(
    full_prompt,
    provider=provider,
    method=method,
    timeout=LLM_IMPLEMENTATION_TIMEOUT_SECONDS,
    env_vars=env_vars,
    execution_dir=cwd,
    mcp_config=mcp_config,
    branch_name=get_branch_name_for_logging(project_dir),
)
response = llm_response["text"]

# After validating response is non-empty:
store_session(
    response_data=llm_response,
    prompt=full_prompt,
    store_path=str(project_dir / ".mcp-coder" / "implement_sessions"),
    step_name=f"step_{step_num}",
    branch_name=get_branch_name_for_logging(project_dir),
)
```

Note: `step_num` is extracted later in the function (from the task string via regex). Reorder slightly so `step_num` is extracted before the LLM call, or call `store_session` after the step extraction block.

### `check_and_fix_mypy()` — replace `ask_llm()` with `prompt_llm()` + `store_session()`

```python
# In the retry loop:
llm_response = prompt_llm(
    mypy_prompt,
    provider=provider,
    method=method,
    timeout=LLM_IMPLEMENTATION_TIMEOUT_SECONDS,
    env_vars=env_vars,
    execution_dir=str(execution_dir) if execution_dir else str(project_dir),
    mcp_config=mcp_config,
    branch_name=get_branch_name_for_logging(project_dir),
)
fix_response = llm_response["text"]

store_session(
    response_data=llm_response,
    prompt=mypy_prompt,
    store_path=str(project_dir / ".mcp-coder" / "implement_sessions"),
    step_name=f"step_{step_num}_mypy_{mypy_attempt_counter}",
    branch_name=get_branch_name_for_logging(project_dir),
)
```

---

## HOW

**Imports to add** in `task_processing.py`:
```python
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.storage.session_storage import store_session
```

**Imports to remove** (if `ask_llm` is no longer called in this file):
```python
from mcp_coder.llm.interface import ask_llm   # remove if no longer used
```

Note: `get_branch_name_for_logging` is already imported.

**`store_session()` call** is wrapped in try/except to prevent storage failures from aborting the workflow:
```python
try:
    store_session(...)
except Exception as e:
    logger.warning("Failed to store implement session: %s", e)
```

---

## ALGORITHM

```
process_single_task():
    ...
    extract step_num from next_task string (regex)    # move this before LLM call
    llm_response = prompt_llm(full_prompt, ...)
    response = llm_response["text"]
    if not response: return False, "error"
    try: store_session(llm_response, full_prompt, implement_sessions_path, f"step_{step_num}", branch)
    except: log warning
    check file changes, run mypy, formatters, commit, push
    return True, "completed"

check_and_fix_mypy():
    ...
    while identical_count < max_identical_attempts:
        llm_response = prompt_llm(mypy_prompt, ...)
        fix_response = llm_response["text"]
        try: store_session(llm_response, mypy_prompt, implement_sessions_path, f"step_{step_num}_mypy_{attempt}", branch)
        except: log warning
        re-run mypy check
```

---

## DATA

**`prompt_llm()` returns**: `LLMResponseDict`
```python
{
    "version": "1.0",
    "timestamp": "...",
    "text": "...",
    "session_id": "...",
    "method": "cli" | "api",
    "provider": "claude",
    "raw_response": { ... }  # contains stream_file for CLI, session_info/cost for API
}
```

**`store_session()` writes** to `.mcp-coder/implement_sessions/`:
- CLI: `2025-10-02T14-30-00_step_1.json`
- API: `2025-10-02T14-30-00_step_1.json` (same format)

---

## TESTS

**File**: `tests/workflows/implement/test_task_processing.py`

### Update `TestCheckAndFixMypy`

`test_check_and_fix_mypy_fixes_errors`:
- Replace `@patch("...ask_llm")` with `@patch("...prompt_llm")`
- Mock `prompt_llm` to return `LLMResponseDict` dict (with `"text": "Fixed the errors"`)
- Add `@patch("...store_session")` mock — verify it is called with correct `step_name` pattern `"step_1_mypy_1"`

`test_check_and_fix_mypy_max_attempts`:
- Same mock updates
- Verify `store_session` called 3 times (max_identical_attempts)

### Update `TestProcessSingleTask`

`test_process_single_task_success`:
- Replace `@patch("...ask_llm")` with `@patch("...prompt_llm")`
- Mock returns `LLMResponseDict`
- Add `@patch("...store_session")` — verify called once with `step_name="step_1"` (extracted from "Step 1: Create test file")

`test_process_single_task_llm_error`:
- Mock `prompt_llm` to raise exception

`test_process_single_task_no_changes`:
- Mock `prompt_llm` returns `LLMResponseDict`; `store_session` still called

### Update `TestIntegration.test_full_task_processing_workflow`

- Replace `_call_llm_with_comprehensive_capture` with `prompt_llm`
- Replace `save_conversation_comprehensive` with `store_session`
- Verify `store_session` called with `step_name="step_2"` (task: "Step 2: Implement feature X")
- Verify `store_path` contains "implement_sessions"

---

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_4.md for full context.

Your task is to implement Step 4: switch task_processing.py LLM calls to prompt_llm() + store_session().

Follow TDD — update tests FIRST, then implement:

1. In `tests/workflows/implement/test_task_processing.py`:
   - Replace all mocks of ask_llm with prompt_llm in TestCheckAndFixMypy and TestProcessSingleTask
   - prompt_llm mocks must return LLMResponseDict dicts (with "text", "session_id", etc.)
   - Add mock of store_session and verify it is called with:
     * store_path containing "implement_sessions"
     * step_name matching "step_N" for process_single_task
     * step_name matching "step_N_mypy_M" for check_and_fix_mypy
   - Run tests — they will fail until implementation

2. In `src/mcp_coder/workflows/implement/task_processing.py`:
   - Add imports: from mcp_coder.llm.interface import prompt_llm
                  from mcp_coder.llm.storage.session_storage import store_session
   - In process_single_task():
     * Move step_num extraction (regex) BEFORE the LLM call
     * Replace ask_llm() with prompt_llm(); extract text via ["text"]
     * After response validation, call store_session() with step_name=f"step_{step_num}"
       wrapped in try/except that logs a warning on failure
   - In check_and_fix_mypy():
     * Replace ask_llm() with prompt_llm(); extract text via ["text"]
     * After response validation, call store_session() with step_name=f"step_{step_num}_mypy_{mypy_attempt_counter}"
       wrapped in try/except
   - store_path = str(project_dir / ".mcp-coder" / "implement_sessions")
   - Remove ask_llm import if no longer used in this file

3. Run all tests to confirm they pass.
```
