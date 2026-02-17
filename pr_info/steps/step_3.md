# Step 3 – Remove `pr_info/.conversations/` logging infrastructure

## Context
See `pr_info/steps/summary.md` for the full picture.

This step removes all the dead-end logging code from the implement workflow:
- `save_conversation()` and `save_conversation_comprehensive()` in `task_processing.py`
- `_call_llm_with_comprehensive_capture()` in `task_processing.py`
- `CONVERSATIONS_DIR` constant in `constants.py`
- The `.conversations/` directory creation in `create_plan.py`
- All call sites of the above in `task_processing.py` and `core.py`

After this step, the implement workflow makes LLM calls but does not yet log them to `.mcp-coder/implement_sessions/` — that is added in Steps 4 and 5. The workflow still functions correctly; it just no longer writes to `pr_info/.conversations/`.

This step deliberately makes no new LLM call changes — only deletes dead code and old logging paths.

---

## WHERE

- **Modify**: `src/mcp_coder/workflows/implement/constants.py` — remove `CONVERSATIONS_DIR`
- **Modify**: `src/mcp_coder/workflows/implement/task_processing.py` — delete functions and update call sites
- **Modify**: `src/mcp_coder/workflows/implement/core.py` — remove `save_conversation` import and call sites
- **Modify**: `src/mcp_coder/workflows/create_plan.py` — remove `.conversations/` directory creation
- **Modify**: `tests/workflows/implement/test_task_processing.py` — remove test classes for deleted functions
- **Modify**: `tests/workflows/create_plan/` — verify `.conversations/` creation is no longer tested

---

## WHAT

### Deletions in `task_processing.py`

Remove these entire functions:
- `save_conversation(project_dir, content, step_num, conversation_type)` → deleted
- `save_conversation_comprehensive(project_dir, content, step_num, conversation_type, comprehensive_data)` → deleted
- `_call_llm_with_comprehensive_capture(prompt, provider, method, timeout, env_vars, cwd, mcp_config)` → deleted

Remove these imports (no longer needed after deletions):
- `import json` (only used in `save_conversation_comprehensive`)
- `from datetime import datetime` (only used in deleted functions — double-check; keep if used elsewhere)
- `from mcp_coder.llm.providers.claude.claude_code_api import ask_claude_code_api_detailed_sync`
- `CONVERSATIONS_DIR` from constants import

Replace call sites in `task_processing.py`:

**In `check_and_fix_mypy()`** — replace:
```python
fix_response, mypy_comprehensive_data = _call_llm_with_comprehensive_capture(...)
...
save_conversation_comprehensive(project_dir, mypy_conversation, step_num, "mypy", comprehensive_data=mypy_comprehensive_data)
```
with a temporary placeholder call to `ask_llm()` (same as the CLI branch of `_call_llm_with_comprehensive_capture`):
```python
fix_response = ask_llm(mypy_prompt, provider=provider, method=method, timeout=..., ...)
```

**In `process_single_task()`** — replace:
```python
response, comprehensive_data = _call_llm_with_comprehensive_capture(full_prompt, ...)
...
save_conversation_comprehensive(project_dir, initial_conversation, step_num, comprehensive_data=comprehensive_data)
```
with:
```python
response = ask_llm(full_prompt, provider=provider, method=method, timeout=..., ...)
```

Note: `ask_llm` calls are temporary — they will be replaced by `prompt_llm` + `store_session` in Step 4.

### Deletions in `constants.py`

Remove:
```python
CONVERSATIONS_DIR = f"{PR_INFO_DIR}/.conversations"
```

### Changes in `core.py`

Remove from imports:
```python
from .task_processing import (
    ...
    save_conversation,   # ← remove this
)
```

In `_run_ci_analysis()` — remove the call:
```python
save_conversation(config.project_dir, f"# CI Failure Analysis\n\n{problem_description}", 0, f"ci_analysis_{fix_attempt + 1}")
```

In `_run_ci_fix()` — remove the call:
```python
save_conversation(config.project_dir, f"# CI Fix Attempt {fix_attempt + 1}\n\n{fix_response}", 0, f"ci_fix_{fix_attempt + 1}")
```

### Changes in `create_plan.py`

In `create_pr_info_structure()` — remove these three lines:
```python
# Create pr_info/.conversations/ directory
conversations_dir = pr_info_dir / ".conversations"
conversations_dir.mkdir()
```

---

## HOW

No new imports needed. This step only removes code.

Verify that `ask_llm` import remains in `task_processing.py` (it was already there; the `_call_llm_with_comprehensive_capture` CLI branch used it).

---

## ALGORITHM

No new algorithm. This is a pure deletion step.

Checklist:
```
1. Remove CONVERSATIONS_DIR from constants.py
2. Delete save_conversation() from task_processing.py
3. Delete save_conversation_comprehensive() from task_processing.py
4. Delete _call_llm_with_comprehensive_capture() from task_processing.py
5. Replace call sites in check_and_fix_mypy() and process_single_task() with ask_llm()
6. Remove save_conversation import and call sites from core.py
7. Remove .conversations/ mkdir from create_plan.py
8. Remove related imports no longer needed
```

---

## DATA

No new data structures. The implement workflow LLM calls now return `str` via `ask_llm()`. Session logging will be added in Steps 4 and 5.

---

## TESTS

**File**: `tests/workflows/implement/test_task_processing.py`

### Remove entire test classes:
- `TestSaveConversation` — tests the deleted `save_conversation()` function
- `TestSaveConversationComprehensive` — tests the deleted `save_conversation_comprehensive()` function

### Update existing test classes:

**`TestCheckAndFixMypy`**:
- Replace mocks of `_call_llm_with_comprehensive_capture` with `ask_llm`
- Replace mocks of `save_conversation_comprehensive` with nothing (no longer called)
- `test_check_and_fix_mypy_fixes_errors` — mock `ask_llm` to return `"Fixed the errors"` (plain string)
- `test_check_and_fix_mypy_max_attempts` — mock `ask_llm` similarly

**`TestProcessSingleTask`**:
- Replace mocks of `_call_llm_with_comprehensive_capture` with `ask_llm`
- Replace mocks of `save_conversation_comprehensive` with nothing
- Adjust return value: `ask_llm` returns `str`, not `(str, dict)`
- `test_process_single_task_success` — simplify: no `save_conversation` assertion
- `test_process_single_task_llm_error` — mock `ask_llm` raising exception

**`TestIntegration`**:
- Update `test_full_task_processing_workflow` — replace `_call_llm_with_comprehensive_capture` mock with `ask_llm`, remove `save_conversation_comprehensive` assertion

### Remove the import of deleted functions from the test file:
```python
# Remove these from the import:
save_conversation,
save_conversation_comprehensive,
```

**File**: `tests/workflows/create_plan/test_prompt_execution.py` or `test_main.py`
- If any test asserts that `.conversations/` directory is created, remove/update that assertion

---

## LLM PROMPT

```
Read pr_info/steps/summary.md and pr_info/steps/step_3.md for full context.

Your task is to implement Step 3: remove the pr_info/.conversations/ logging infrastructure.

Follow TDD — update tests FIRST, then implement:

1. In `tests/workflows/implement/test_task_processing.py`:
   - Remove TestSaveConversation and TestSaveConversationComprehensive classes entirely
   - Remove save_conversation and save_conversation_comprehensive from the import list
   - In TestCheckAndFixMypy: replace mock of _call_llm_with_comprehensive_capture with mock of ask_llm
     (ask_llm returns str, not tuple); remove save_conversation_comprehensive mock
   - In TestProcessSingleTask and TestIntegration: same replacements
   - Run tests — they will fail until implementation

2. In `src/mcp_coder/workflows/implement/constants.py`:
   - Remove CONVERSATIONS_DIR constant

3. In `src/mcp_coder/workflows/implement/task_processing.py`:
   - Delete save_conversation(), save_conversation_comprehensive(), _call_llm_with_comprehensive_capture()
   - In check_and_fix_mypy(): replace _call_llm_with_comprehensive_capture() call with ask_llm()
   - In process_single_task(): replace _call_llm_with_comprehensive_capture() call with ask_llm()
   - Remove save_conversation_comprehensive() call sites
   - Remove unused imports: ask_claude_code_api_detailed_sync, CONVERSATIONS_DIR, json
     (keep datetime only if still used elsewhere in the file — check carefully)

4. In `src/mcp_coder/workflows/implement/core.py`:
   - Remove save_conversation from the import from .task_processing
   - Remove save_conversation() call in _run_ci_analysis()
   - Remove save_conversation() call in _run_ci_fix()

5. In `src/mcp_coder/workflows/create_plan.py`:
   - In create_pr_info_structure(): remove the 3 lines that create pr_info/.conversations/

6. Run all tests. Check for any remaining references to CONVERSATIONS_DIR, save_conversation,
   save_conversation_comprehensive, or _call_llm_with_comprehensive_capture and remove them.
```
