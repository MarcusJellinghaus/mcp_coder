# Step 2: Workflow Integration and Tests

## Overview

Integrate the finalisation step into the implement workflow and add tests.

## WHERE

**Files to modify**:
- `src/mcp_coder/workflows/implement/core.py`
- `tests/workflows/implement/test_core.py`

## WHAT

### 2.1 Add Finalisation to Workflow

Add a new function and integrate it into `run_implement_workflow()`.

#### New Constant

```python
LLM_FINALISATION_TIMEOUT_SECONDS = 600  # 10 minutes
COMMIT_MESSAGE_FILE = ".commit_message.txt"
```

#### New Function Signature

```python
def run_finalisation(
    project_dir: Path,
    provider: str,
    method: str,
    mcp_config: Optional[str] = None,
    execution_dir: Optional[Path] = None,
    auto_push: bool = False,
) -> bool:
    """Run implementation finalisation to verify and complete remaining tasks.
    
    Args:
        project_dir: Path to the project directory
        provider: LLM provider (e.g., 'claude')
        method: LLM method (e.g., 'cli' or 'api')
        mcp_config: Optional path to MCP configuration file
        execution_dir: Optional working directory for Claude subprocess
        auto_push: If True, push changes after commit (workflow mode)
    
    Returns:
        bool: True if finalisation succeeded or was skipped (no tasks), False on error
    """
```

### 2.2 Integration Point in run_implement_workflow()

Insert between Step 5 (final mypy check) and Step 6 (progress summary):

```python
# Step 5.5: Run finalisation to complete any remaining tasks
if not error_occurred:
    finalisation_success = run_finalisation(
        project_dir,
        provider,
        method,
        mcp_config,
        execution_dir,
        auto_push=update_labels,  # Auto-push only in workflow mode
    )
    if not finalisation_success:
        logger.warning("Finalisation encountered issues - continuing anyway")
```

## HOW

### Finalisation Prompt (embedded in function)

```python
FINALISATION_PROMPT = """
Please check pr_info/TASK_TRACKER.md for unchecked tasks (- [ ]).

For each unchecked task:
1. If it's a "commit message" task and changes are already committed → mark [x] and skip
2. Otherwise: verify if done, complete it if not, then mark [x]

If step files exist in pr_info/steps/, use them for context.
If not, analyse based on task names and codebase.

If you cannot complete a task, DO NOT mark the box as done. 
Instead, briefly explain the issue.

Run quality checks (pylint, pytest, mypy) if any code changes were made.
Write commit message to pr_info/.commit_message.txt.
"""
```

### Import Changes

Add to existing imports in core.py:
```python
from mcp_coder.workflow_utils.task_tracker import has_incomplete_work
```

Note: `has_incomplete_work` may already be available via `get_step_progress` import chain, but explicit import is clearer.

## ALGORITHM

```python
def run_finalisation(...) -> bool:
    # 1. Check if there are incomplete tasks
    if not has_incomplete_work(str(project_dir / PR_INFO_DIR)):
        logger.info("No incomplete tasks - skipping finalisation")
        return True
    
    # 2. Call LLM with finalisation prompt
    response = ask_llm(FINALISATION_PROMPT, ...)
    
    # 3. If auto_push and changes were made, push
    if auto_push:
        status = get_full_status(project_dir)
        if status["staged"] or status["modified"]:
            push_changes(project_dir)
    
    return True
```

## DATA

- **Input**: Task tracker state, project directory
- **Output**: Updated task tracker, commit message file, optional git push
- **Returns**: `bool` indicating success

## TEST APPROACH

Add tests to `tests/workflows/implement/test_core.py`:

### Test Cases

1. **test_run_finalisation_skips_when_no_incomplete_tasks**
   - Mock `has_incomplete_work` to return `False`
   - Verify `ask_llm` is NOT called
   - Verify returns `True`

2. **test_run_finalisation_calls_llm_when_incomplete_tasks**
   - Mock `has_incomplete_work` to return `True`
   - Mock `ask_llm` to return success
   - Verify `ask_llm` is called with finalisation prompt
   - Verify returns `True`

3. **test_run_finalisation_pushes_in_workflow_mode**
   - Mock `has_incomplete_work` to return `True`
   - Mock `ask_llm`, `get_full_status` (with changes), `push_changes`
   - Call with `auto_push=True`
   - Verify `push_changes` is called

4. **test_run_finalisation_no_push_in_slash_command_mode**
   - Same as above but `auto_push=False`
   - Verify `push_changes` is NOT called

## LLM PROMPT FOR THIS STEP

```
Implement Step 2 from pr_info/steps/step_2.md.

Read the summary at pr_info/steps/summary.md for context.

Tasks:
1. Add the `run_finalisation()` function to `src/mcp_coder/workflows/implement/core.py`
2. Integrate finalisation call into `run_implement_workflow()` after the final mypy check
3. Add unit tests to `tests/workflows/implement/test_core.py`

Follow the specifications in step_2.md for:
- Function signature
- Integration point in workflow
- Test cases

Run quality checks (pylint, pytest, mypy) after implementation.
Prepare git commit message.
```
