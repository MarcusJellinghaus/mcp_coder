# Step 2: Return `"timeout"` from `process_single_task()` on `TimeoutExpired`

## Context
See [summary.md](./summary.md) for full implementation overview.

This step enables `core.py` to distinguish timeout failures from generic errors so it can apply the correct `FailureCategory`.

## WHERE
- `src/mcp_coder/workflows/implement/task_processing.py` — modify `process_single_task()`
- `tests/workflows/implement/test_task_processing.py` — add test

## WHAT

In `process_single_task()`, the LLM call is wrapped in a broad `except Exception`. We need to catch `TimeoutExpired` **before** the broad handler and return `(False, "timeout")` instead of `(False, "error")`.

### Function signature (unchanged)
```python
def process_single_task(...) -> tuple[bool, str]:
    # Returns: (False, "timeout") for TimeoutExpired
    # Returns: (False, "error") for other errors (unchanged)
    # Returns: (False, "no_tasks") when no tasks remain (unchanged)
    # Returns: (True, "completed") on success (unchanged)
```

## HOW

Import `TimeoutExpired` at the top of `task_processing.py`:
```python
from mcp_coder.utils.subprocess_runner import TimeoutExpired
```

In the LLM call try/except block (Step 5 in process_single_task), add a `TimeoutExpired` catch before the broad `Exception` catch:

## ALGORITHM (pseudocode)
```
try:
    llm_response = prompt_llm(...)
except TimeoutExpired:
    logger.error("LLM call timed out for task: %s", next_task)
    return False, "timeout"
except Exception as e:
    logger.error("Error calling LLM: %s", e)
    return False, "error"
```

## DATA
- Return value changes only for the timeout case: `(False, "timeout")` instead of `(False, "error")`
- All other return values remain unchanged

## TESTS (write first)

Add to `TestProcessSingleTask` in `tests/workflows/implement/test_task_processing.py`:

```python
@patch("mcp_coder.workflows.implement.task_processing.prompt_llm")
@patch("mcp_coder.workflows.implement.task_processing.get_prompt")
@patch("mcp_coder.workflows.implement.task_processing.get_next_task")
def test_process_single_task_llm_timeout(
    self, mock_get_next_task, mock_get_prompt, mock_prompt_llm
):
    """Test processing single task returns 'timeout' on TimeoutExpired."""
    from mcp_coder.utils.subprocess_runner import TimeoutExpired

    mock_get_next_task.return_value = "Step 1: Test task"
    mock_get_prompt.return_value = "Template"
    mock_prompt_llm.side_effect = TimeoutExpired(
        cmd="claude", timeout=3600, output="", stderr=""
    )

    success, reason = process_single_task(Path("/test/project"), "claude")

    assert success is False
    assert reason == "timeout"
```

Note: Check `TimeoutExpired` constructor signature — it may differ from `subprocess.TimeoutExpired`. Read `src/mcp_coder/utils/subprocess_runner.py` to confirm.

## LLM PROMPT
```
Implement Step 2 of issue #189 (see pr_info/steps/summary.md for context).

In `process_single_task()` in `task_processing.py`, catch `TimeoutExpired`
before the broad `except Exception` in the LLM call block, returning
`(False, "timeout")`.

Write the test first in `test_task_processing.py`, then implement.
See pr_info/steps/step_2.md for exact changes and test case.
Run all quality checks after changes.
```
