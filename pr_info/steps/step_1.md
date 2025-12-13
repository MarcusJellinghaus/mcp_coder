# Step 1: Add Regression Test for executor_os Passthrough

## LLM Prompt

```
Implement Step 1 of Issue #196 (see pr_info/steps/summary.md).

Add a regression test to verify that `execute_coordinator_run()` correctly passes 
`executor_os` to `dispatch_workflow()`. This test should fail before the fix and 
pass after.
```

## WHERE

- **File**: `tests/cli/commands/test_coordinator.py`
- **Class**: `TestExecuteCoordinatorRun`

## WHAT

Add new test method:

```python
def test_execute_coordinator_run_passes_executor_os_to_dispatch(
    self,
    # mocks...
) -> None:
    """Test that executor_os is passed to dispatch_workflow for Windows template selection."""
```

## HOW

- Add test to existing `TestExecuteCoordinatorRun` class
- Mock `dispatch_workflow` and verify it receives `executor_os` in `repo_config`
- Use `executor_os="windows"` in mock config to verify non-default value passes through

## ALGORITHM

```
1. Setup args with repo="test_repo"
2. Mock load_repo_config to return config with executor_os="windows"
3. Mock get_eligible_issues to return one issue
4. Mock dispatch_workflow
5. Call execute_coordinator_run(args)
6. Assert dispatch_workflow received repo_config with executor_os="windows"
```

## DATA

**Test Input:**
```python
mock_load_repo.return_value = {
    "repo_url": "https://github.com/user/repo.git",
    "executor_job_path": "Windows-Agents/Executor",
    "github_credentials_id": "github-pat",
    "executor_os": "windows",
}
```

**Expected Assertion:**
```python
call_kwargs = mock_dispatch_workflow.call_args[1]
assert call_kwargs["repo_config"]["executor_os"] == "windows"
```
