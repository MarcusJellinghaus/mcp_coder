# Step 2: Wire up new failure category in core.py

## LLM Prompt

> Read `pr_info/steps/summary.md` for context. Implement Step 2: In `src/mcp_coder/workflows/implement/core.py`, change the task tracker preparation failure from `FailureCategory.GENERAL` to `FailureCategory.TASK_TRACKER_PREP_FAILED`. Run all three code quality checks after changes. Commit as a single commit.

## WHERE

- `src/mcp_coder/workflows/implement/core.py` — one line change in `run_implement_workflow`

## WHAT

Change the `WorkflowFailure` construction at the task tracker prep failure site.

### Before

```python
if not prepare_task_tracker(project_dir, provider, mcp_config, execution_dir):
    _handle_workflow_failure(
        WorkflowFailure(
            category=FailureCategory.GENERAL,
            stage="Task tracker preparation",
            message="Failed to prepare task tracker",
            ...
        ),
        ...
    )
```

### After

```python
if not prepare_task_tracker(project_dir, provider, mcp_config, execution_dir):
    _handle_workflow_failure(
        WorkflowFailure(
            category=FailureCategory.TASK_TRACKER_PREP_FAILED,
            stage="Task tracker preparation",
            message="Failed to prepare task tracker",
            ...
        ),
        ...
    )
```

## HOW

- No new imports needed — `FailureCategory` is already imported from `.constants`.
- Only the `category=` argument changes. All other arguments stay the same.

## ALGORITHM

```
1. Find the WorkflowFailure with stage="Task tracker preparation"
2. Change category=FailureCategory.GENERAL → category=FailureCategory.TASK_TRACKER_PREP_FAILED
3. Done — no other changes needed
```

## DATA

- When task tracker prep fails, the issue now gets label `status-06f-prep:task-tracker-prep-failed` instead of `status-06f:implementing-failed`.

## Verification

Run all three checks:
- `mcp__tools-py__run_pylint_check`
- `mcp__tools-py__run_pytest_check` (with `-m "not git_integration and not claude_cli_integration and not claude_api_integration and not formatter_integration and not github_integration and not langchain_integration"`)
- `mcp__tools-py__run_mypy_check`
