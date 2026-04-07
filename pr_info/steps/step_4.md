# Step 4: Wire failure handling into orchestration

> **Context**: See `pr_info/steps/summary.md` for full architecture overview.

## Goal
Modify `run_create_plan_workflow()` and `run_planning_prompts()` to detect failures, construct `WorkflowFailure` objects, and call `_handle_workflow_failure()`. Promote commit/push to hard errors.

## WHERE

### Modified files
- `src/mcp_coder/workflows/create_plan/core.py` — modify `run_create_plan_workflow()` and `run_planning_prompts()`

### Test files
- `tests/workflows/create_plan/test_main.py` — update 2 existing tests (commit/push now hard errors), add failure handling tests
- `tests/workflows/create_plan/test_prompt_execution.py` — update `run_planning_prompts` tests for new return type

## WHAT

### Changed function: `run_planning_prompts()`
**Old signature**: `(...) -> bool`
**New signature**: `(...) -> tuple[bool, WorkflowFailure | None]`

Returns `(True, None)` on success, `(False, WorkflowFailure(...))` on failure. Builds `WorkflowFailure` inline at each detection point to preserve prompt-stage info.

### Changed function: `run_create_plan_workflow()`
**Signature**: unchanged (returns `int`)
**Behavior changes**:
1. Add `import time` and `start_time = time.time()` at the top
2. At each failure point, construct `WorkflowFailure` and call `_handle_workflow_failure()`
3. Commit/push failures: change from `logger.warning` + continue to hard error (return 1)
4. Wire `post_issue_comments` parameter through to `_handle_workflow_failure()`

## HOW

### Failure point wiring in `run_create_plan_workflow()`

Each failure point follows this pattern:
```python
if not success:
    failure = WorkflowFailure(
        category=FailureCategory.PREREQ_FAILED,
        stage="Prerequisites (git working directory not clean)",
        message="...",
        elapsed_time=time.time() - start_time,
    )
    _handle_workflow_failure(failure, project_dir, issue_number, update_issue_labels, post_issue_comments)
    return 1
```

### Failure point → category mapping (from issue §4)

| Code location | Stage label | Category |
|---|---|---|
| `check_prerequisites` returns `(False, ...)` | `"Prerequisites"` | `PREREQ_FAILED` |
| `manage_branch` returns `None` | `"Branch management"` | `PREREQ_FAILED` |
| `check_pr_info_not_exists` returns `False` | `"Workspace setup (pr_info/ already exists)"` | `PREREQ_FAILED` |
| `create_pr_info_structure` returns `False` | `"Workspace setup (directory creation failed)"` | `PREREQ_FAILED` |
| `run_planning_prompts` returns `(False, failure)` | From `WorkflowFailure.stage` | From `WorkflowFailure.category` |
| `validate_output_files` returns `False` | `"Output validation"` | `GENERAL` |
| `commit_all_changes` returns `success=False` | `"Commit & push"` | `GENERAL` |
| `git_push` returns `success=False` | `"Commit & push"` | `GENERAL` |

### `run_planning_prompts()` failure detection

For each prompt (1, 2, 3):
```python
# Timeout detection
try:
    response = prompt_llm(...)
except LLMTimeoutError as e:
    return (False, WorkflowFailure(
        category=FailureCategory.LLM_TIMEOUT,
        stage=f"Prompt {n} (timeout)",
        message=str(e),
        prompt_stage=n,
        elapsed_time=None,  # elapsed computed by orchestrator
    ))
except Exception as e:
    return (False, WorkflowFailure(
        category=FailureCategory.GENERAL,
        stage=f"Prompt {n}",
        message=str(e),
        prompt_stage=n,
    ))

# Empty response detection
if not response or not response.get("text"):
    return (False, WorkflowFailure(
        category=FailureCategory.GENERAL,
        stage=f"Prompt {n} (empty response)",
        message="Prompt returned empty response",
        prompt_stage=n,
    ))

# Missing session_id (prompt 1 only)
if not session_id:
    return (False, WorkflowFailure(
        category=FailureCategory.GENERAL,
        stage="Prompt 1 (empty response)",
        message="Prompt 1 did not return session_id",
        prompt_stage=1,
    ))
```

## ALGORITHM (run_create_plan_workflow failure wiring)
```
1. Record start_time = time.time()
2. At each failure point:
   a. Compute elapsed = time.time() - start_time
   b. Construct WorkflowFailure with appropriate category + stage
   c. Call _handle_workflow_failure(failure, project_dir, issue_number, flags)
   d. Return 1
3. For run_planning_prompts failures: use the WorkflowFailure returned by the function
   (override elapsed_time with orchestrator's elapsed if None)
4. For commit/push: REMOVE the old logger.warning + continue pattern,
   REPLACE with hard error + failure handling
```

## DATA

### `run_planning_prompts` new return examples
```python
# Success
(True, None)

# Timeout on prompt 2
(False, WorkflowFailure(
    category=FailureCategory.LLM_TIMEOUT,
    stage="Prompt 2 (timeout)",
    message="LLM request timed out after 600s",
    prompt_stage=2,
))

# Empty response on prompt 3
(False, WorkflowFailure(
    category=FailureCategory.GENERAL,
    stage="Prompt 3 (empty response)",
    message="Prompt returned empty response",
    prompt_stage=3,
))
```

## Tests

### Updated existing tests in `test_main.py`

1. **`test_main_commit_fails_continues`** → rename to `test_main_commit_fails_returns_error`
   - Change assertion: `assert result == 1` (was `== 0`)
   - Push should NOT be called (workflow exits before push)

2. **`test_main_push_fails_continues`** → rename to `test_main_push_fails_returns_error`
   - Change assertion: `assert result == 1` (was `== 0`)

### Updated tests in `test_prompt_execution.py`

All `run_planning_prompts` tests need updating for new return type:
- Success: `assert result == (True, None)` (was `assert result is True`)
- Failure: `assert result[0] is False` and `assert result[1] is not None` (was `assert result is False`)
- Add assertions on `result[1].category`, `result[1].stage`, `result[1].prompt_stage` for specific failure cases

### New failure handling tests in `test_main.py`

```python
class TestFailureHandling:
    """Tests for failure handling in run_create_plan_workflow."""

    def test_prerequisites_failure_calls_handler(self):
        """Verify _handle_workflow_failure called with PREREQ_FAILED on prereq failure."""
        # Mock check_prerequisites to return (False, empty_issue_data)
        # Mock _handle_workflow_failure
        # Call run_create_plan_workflow with update_issue_labels=True, post_issue_comments=True
        # Assert _handle_workflow_failure called with WorkflowFailure(category=PREREQ_FAILED, stage="Prerequisites", ...)
        # Assert result == 1

    def test_branch_failure_calls_handler(self):
        """Verify handler called with PREREQ_FAILED on branch failure."""

    def test_pr_info_exists_calls_handler(self):
        """Verify handler called with PREREQ_FAILED when pr_info exists."""

    def test_planning_timeout_calls_handler(self):
        """Verify handler called with LLM_TIMEOUT when planning prompt times out."""
        # Mock run_planning_prompts to return (False, WorkflowFailure(LLM_TIMEOUT, ...))
        # Assert handler called with the timeout failure

    def test_commit_failure_calls_handler(self):
        """Verify handler called with GENERAL on commit failure."""

    def test_push_failure_calls_handler(self):
        """Verify handler called with GENERAL on push failure."""

    def test_no_handler_when_flags_false(self):
        """Verify handler called but with flags=False (handler respects internally)."""
        # Mock a failure, call with update_issue_labels=False, post_issue_comments=False
        # Assert handler still called (it gates internally)
```

## Commit message
```
feat(create_plan): wire failure handling into workflow orchestration

Modify run_create_plan_workflow() to call _handle_workflow_failure()
at every failure point with appropriate FailureCategory and stage.

Change run_planning_prompts() return type to tuple[bool, Optional[WorkflowFailure]]
to preserve prompt-stage information for LLM failures.

Promote commit/push failures from warnings to hard errors.
Wire post_issue_comments parameter to failure comment posting.
```

## LLM Prompt
```
Read pr_info/steps/summary.md for context, then implement pr_info/steps/step_4.md.

Key points:
- Modify run_create_plan_workflow() in src/mcp_coder/workflows/create_plan/core.py
- Add time tracking, construct WorkflowFailure at each failure point per the mapping table
- Import LLMTimeoutError from mcp_coder.llm.interface
- Change run_planning_prompts() return type to tuple[bool, Optional[WorkflowFailure]]
- Catch LLMTimeoutError separately from general Exception in prompt execution
- Promote commit/push from logger.warning to hard errors with failure handling
- Update existing tests (commit/push now return 1, run_planning_prompts returns tuple)
- Add new failure handling tests
- Run all quality checks (pylint, pytest, mypy) and fix any issues
```
