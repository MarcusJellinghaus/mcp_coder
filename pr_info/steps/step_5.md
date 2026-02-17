# Step 5 – Switch `core.py` to `prompt_llm()` + `store_session()`

## Context
See `pr_info/steps/summary.md` for the full picture.

After Step 4, `task_processing.py` is fully migrated. This step migrates the four `ask_llm()` call sites in `core.py`:

| Function | Current call | `step_name` |
|---|---|---|
| `_run_ci_analysis()` | `ask_llm()` | `ci_analysis_{fix_attempt+1}` |
| `_run_ci_fix()` | `ask_llm()` | `ci_fix_{fix_attempt+1}` |
| `prepare_task_tracker()` | `ask_llm()` | `task_tracker` |
| `run_finalisation()` | `ask_llm()` | `finalisation` |

All sessions go to the same `.mcp-coder/implement_sessions/` directory.

---

## WHERE

- **Modify**: `src/mcp_coder/workflows/implement/core.py`
- **Modify**: `tests/workflows/implement/test_core.py`

---

## WHAT

### `_run_ci_analysis()` pattern

```python
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.storage.session_storage import store_session

# Replace:
analysis_response = ask_llm(analysis_prompt, provider=..., method=..., ...)

# With:
llm_response = prompt_llm(analysis_prompt, provider=config.provider, method=config.method,
                           timeout=LLM_CI_ANALYSIS_TIMEOUT_SECONDS,
                           env_vars=config.env_vars, execution_dir=config.cwd,
                           mcp_config=config.mcp_config,
                           branch_name=get_branch_name_for_logging(config.project_dir))
analysis_response = llm_response["text"]
try:
    store_session(llm_response, analysis_prompt,
                  store_path=str(config.project_dir / ".mcp-coder" / "implement_sessions"),
                  step_name=f"ci_analysis_{fix_attempt + 1}",
                  branch_name=get_branch_name_for_logging(config.project_dir))
except Exception as e:
    logger.warning("Failed to store CI analysis session: %s", e)
```

### `_run_ci_fix()` pattern

Same pattern, `step_name=f"ci_fix_{fix_attempt + 1}"`.

### `prepare_task_tracker()` pattern

```python
llm_response = prompt_llm(prompt_template, provider=provider, method=method,
                           timeout=LLM_TASK_TRACKER_PREPARATION_TIMEOUT_SECONDS,
                           env_vars=env_vars,
                           execution_dir=str(execution_dir) if execution_dir else None,
                           mcp_config=mcp_config,
                           branch_name=get_branch_name_for_logging(project_dir))
response = llm_response["text"]
try:
    store_session(llm_response, prompt_template,
                  store_path=str(project_dir / ".mcp-coder" / "implement_sessions"),
                  step_name="task_tracker",
                  branch_name=get_branch_name_for_logging(project_dir))
except Exception as e:
    logger.warning("Failed to store task tracker session: %s", e)
```

### `run_finalisation()` pattern

```python
llm_response = prompt_llm(FINALISATION_PROMPT, provider=provider, method=method,
                           timeout=LLM_FINALISATION_TIMEOUT_SECONDS,
                           env_vars=env_vars,
                           execution_dir=str(execution_dir) if execution_dir else None,
                           mcp_config=mcp_config,
                           branch_name=branch_name)
response = llm_response["text"]
try:
    store_session(llm_response, FINALISATION_PROMPT,
                  store_path=str(project_dir / ".mcp-coder" / "implement_sessions"),
                  step_name="finalisation",
                  branch_name=branch_name)
except Exception as e:
    logger.warning("Failed to store finalisation session: %s", e)
```

Note: `branch_name = get_branch_name_for_logging(project_dir)` is already computed earlier in `run_finalisation()`.

---

## HOW

**Imports to add** in `core.py`:
```python
from mcp_coder.llm.interface import prompt_llm
from mcp_coder.llm.storage.session_storage import store_session
```

**Import to remove** (if `ask_llm` is no longer used in `core.py`):
```python
from mcp_coder.llm.interface import ask_llm   # remove
```

`get_branch_name_for_logging` is already imported in `core.py`.

---

## ALGORITHM

```
for each ask_llm() call site in core.py:
    replace with prompt_llm() → get LLMResponseDict
    extract ["text"] for the response variable
    wrap store_session() in try/except (non-critical — never abort workflow on storage failure)
    step_name follows convention: ci_analysis_N, ci_fix_N, task_tracker, finalisation
remove ask_llm import from core.py
```

---

## DATA

Same pattern as Step 4. `store_session()` writes to `.mcp-coder/implement_sessions/`.

For `_run_ci_analysis()` and `_run_ci_fix()`, `config.project_dir` is a `Path`, so:
```python
store_path=str(config.project_dir / ".mcp-coder" / "implement_sessions")
```

For `prepare_task_tracker()` and `run_finalisation()`, `project_dir` is a `Path`:
```python
store_path=str(project_dir / ".mcp-coder" / "implement_sessions")
```

---

## TESTS

**File**: `tests/workflows/implement/test_core.py`

Read the existing test file to understand what is already mocked. The pattern to apply:

### For each test that mocks `ask_llm` in core.py:

Replace:
```python
@patch("mcp_coder.workflows.implement.core.ask_llm")
```
with:
```python
@patch("mcp_coder.workflows.implement.core.prompt_llm")
@patch("mcp_coder.workflows.implement.core.store_session")
```

The `prompt_llm` mock must return a `LLMResponseDict` dict (not a plain string):
```python
mock_prompt_llm.return_value = {
    "text": "LLM response text",
    "session_id": "test-session",
    "version": "1.0",
    "timestamp": "2025-01-01T00:00:00",
    "method": "cli",
    "provider": "claude",
    "raw_response": {},
}
```

### New assertions to add:

For `prepare_task_tracker` tests:
- Verify `store_session` called with `step_name="task_tracker"`
- Verify `store_path` ends with `"implement_sessions"`

For `run_finalisation` tests:
- Verify `store_session` called with `step_name="finalisation"`

For `_run_ci_analysis` / `_run_ci_fix` tests (if they exist):
- Verify `store_session` called with `step_name="ci_analysis_1"` / `"ci_fix_1"`

### Store_session failure is non-critical:
- Add a test: if `store_session` raises an exception, the function still succeeds (warning logged, not propagated)

---

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_5.md for full context.

Your task is to implement Step 5: switch core.py LLM calls to prompt_llm() + store_session().

Follow TDD — update tests FIRST, then implement:

1. Read `tests/workflows/implement/test_core.py` to understand existing test structure.

2. For each test that mocks ask_llm in core.py:
   - Replace @patch of ask_llm with @patch of prompt_llm AND @patch of store_session
   - prompt_llm mock must return a LLMResponseDict dict (with "text", "session_id", etc.)
   - Add assertion that store_session is called with the correct step_name and store_path

3. Add a test verifying that if store_session raises an exception, the workflow function
   still returns successfully (storage failure is non-critical).

4. Run tests — they will fail until implementation.

5. In `src/mcp_coder/workflows/implement/core.py`:
   - Add imports: from mcp_coder.llm.interface import prompt_llm
                  from mcp_coder.llm.storage.session_storage import store_session
   - Replace ask_llm() with prompt_llm() at all 4 call sites:
     * _run_ci_analysis(): step_name=f"ci_analysis_{fix_attempt + 1}"
     * _run_ci_fix(): step_name=f"ci_fix_{fix_attempt + 1}"
     * prepare_task_tracker(): step_name="task_tracker"
     * run_finalisation(): step_name="finalisation"
   - Each store_session() call is wrapped in try/except that logs a warning on failure
   - store_path = str(project_dir / ".mcp-coder" / "implement_sessions")
     (use config.project_dir for _run_ci_analysis and _run_ci_fix)
   - Remove ask_llm import from core.py

6. Run all tests to confirm they pass.
```
