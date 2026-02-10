# Step 9: Remove Redundant Status File Write

## Goal
Remove the redundant `create_status_file()` call in `restart_closed_sessions()` after `regenerate_session_files()` since the branch checkout happens before regeneration, making the second write unnecessary.

## Context
In `restart_closed_sessions()` (lines 781-795), after calling `regenerate_session_files()`, the code conditionally calls `create_status_file()` again if the branch changed. However:

1. `_prepare_restart_branch()` runs git checkout (line 619-620)
2. `regenerate_session_files()` is called (line 781)
3. Inside `regenerate_session_files()`, it reads the current branch using `git rev-parse --abbrev-ref HEAD` (lines 486-493)
4. Since checkout already happened, it gets the NEW branch
5. `regenerate_session_files()` calls `create_status_file()` with the correct branch (lines 526-535)
6. The conditional call at lines 784-795 is redundant

## Files to Modify

### `src/mcp_coder/workflows/vscodeclaude/orchestrator.py`

**Remove lines 784-795:**

```python
# DELETE THIS BLOCK:
# If branch was switched, update status file with new branch
if branch_result.branch_name:
    create_status_file(
        folder_path=folder_path,
        issue_number=issue_number,
        issue_title=issue["title"],
        status=current_status,
        repo_full_name=repo_full_name,
        branch_name=branch_result.branch_name,
        issue_url=issue.get("url", ""),
        is_intervention=session.get("is_intervention", False),
    )
```

**Result:** The code flow becomes:
```python
# Regenerate all session files with fresh data
regenerate_session_files(session, issue)

# (Status file already has correct branch - no additional write needed)
```

## Tests

### File: `tests/workflows/vscodeclaude/test_orchestrator_sessions.py`

**Update existing test:** `test_restart_handles_branch_switch_for_status_04`

Verify that `create_status_file` is called exactly ONCE (inside `regenerate_session_files`), not twice:

```python
def test_restart_handles_branch_switch_for_status_04(
    mock_subprocess, mock_sessions, mock_issue_manager, ...
):
    """Restart switches to linked branch for status-04."""
    
    # ... existing setup ...
    
    # Call restart
    result = restart_closed_sessions(cached_issues_by_repo=cached_issues)
    
    # Verify create_status_file called ONCE with correct branch
    mock_create_status_file.assert_called_once()
    call_kwargs = mock_create_status_file.call_args[1]
    assert call_kwargs["branch_name"] == "feature/issue-123"
```

**Add new test:** `test_regenerate_reads_branch_after_checkout`

Verify that `regenerate_session_files()` correctly reads the branch that was just checked out:

```python
def test_regenerate_reads_branch_after_checkout(
    mock_subprocess, tmp_path, ...
):
    """regenerate_session_files reads current branch from git."""
    
    # Setup: Mock git rev-parse to return specific branch
    mock_subprocess.return_value.stdout = "feature/test-branch"
    
    # Call regenerate
    regenerate_session_files(session, issue)
    
    # Verify git rev-parse was called
    assert any(
        "git" in str(call) and "rev-parse" in str(call)
        for call in mock_subprocess.call_args_list
    )
    
    # Verify create_status_file called with branch from git
    assert mock_create_status_file.call_args[1]["branch_name"] == "feature/test-branch"
```

## LLM Prompt

```
You are implementing Step 9 of issue #422 branch handling feature.

Reference: pr_info/steps/summary.md for full context
This step: pr_info/steps/step_9.md

Task: Remove redundant status file write in restart_closed_sessions().

Implementation order:
1. Read src/mcp_coder/workflows/vscodeclaude/orchestrator.py around line 784-795
2. Delete the conditional create_status_file() block (lines 784-795)
3. Update test in tests/workflows/vscodeclaude/test_orchestrator_sessions.py
4. Add test verifying regenerate_session_files reads correct branch
5. Run all quality checks (pylint, pytest, mypy)

The deletion is simple but verify tests still pass to confirm the redundancy.
Use MCP tools exclusively (no Read/Write/Edit tools).
Run code quality checks after implementation using MCP code-checker tools.
```

## Integration Points

No new imports needed. This is a pure deletion.

**Code flow after change:**
```
_prepare_restart_branch() 
  └─> git checkout <new_branch>
  
regenerate_session_files()
  ├─> git rev-parse --abbrev-ref HEAD  (gets new branch)
  ├─> create_startup_script()
  ├─> create_vscode_task()
  ├─> create_status_file()  <-- Writes status file with correct branch
  └─> create_workspace_file()

(No additional status file write needed)
```

## Acceptance Criteria

- [ ] Lines 784-795 removed from `restart_closed_sessions()`
- [ ] Existing test updated to verify single call to `create_status_file()`
- [ ] New test added to verify branch is read correctly after checkout
- [ ] All tests pass (no behavioral changes)
- [ ] Pylint, pytest, mypy all pass

## Commit Message

```
refactor(vscodeclaude): remove redundant status file write on restart

Remove duplicate create_status_file() call after regenerate_session_files()
since the branch checkout happens before regeneration and regenerate
already reads and writes the correct branch.

- Delete conditional create_status_file() block (lines 784-795)
- Update test to verify single status file write
- Add test for branch reading in regenerate_session_files()

Part of issue #422: Status-aware branch handling

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```
