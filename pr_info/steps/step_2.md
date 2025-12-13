# Step 2: Fix executor_os Passthrough in execute_coordinator_run

## LLM Prompt

```
Implement Step 2 of Issue #196 (see pr_info/steps/summary.md).

Fix the bug by adding `executor_os` to the `validated_config` dictionary in 
`execute_coordinator_run()`. The test from Step 1 should now pass.
```

## WHERE

- **File**: `src/mcp_coder/cli/commands/coordinator.py`
- **Function**: `execute_coordinator_run()`
- **Line**: ~440 (the `validated_config` dictionary definition)

## WHAT

Modify the `validated_config` dictionary to include `executor_os`:

```python
validated_config: dict[str, str] = {
    "repo_url": repo_config["repo_url"],
    "executor_job_path": repo_config["executor_job_path"],
    "github_credentials_id": repo_config["github_credentials_id"],
    "executor_os": repo_config["executor_os"],  # ADD THIS LINE
}
```

## HOW

- Locate the `validated_config` dictionary in `execute_coordinator_run()` (around line 440)
- Add the `executor_os` key with value from `repo_config["executor_os"]`
- No type ignore comment needed since `executor_os` always has a value (defaults to "linux" in `load_repo_config()`)

## ALGORITHM

```
1. Find validated_config dict in execute_coordinator_run()
2. Add "executor_os": repo_config["executor_os"] to the dict
3. Run tests to verify fix works
```

## DATA

**Before:**
```python
validated_config: dict[str, str] = {
    "repo_url": repo_config["repo_url"],
    "executor_job_path": repo_config["executor_job_path"],
    "github_credentials_id": repo_config["github_credentials_id"],
}
```

**After:**
```python
validated_config: dict[str, str] = {
    "repo_url": repo_config["repo_url"],
    "executor_job_path": repo_config["executor_job_path"],
    "github_credentials_id": repo_config["github_credentials_id"],
    "executor_os": repo_config["executor_os"],
}
```

## Verification

Run tests to confirm:
```bash
mcp__code-checker__run_pytest_check(extra_args=["-n", "auto", "-k", "test_coordinator"])
```
