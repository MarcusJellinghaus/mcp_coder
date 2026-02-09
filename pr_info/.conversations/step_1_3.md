# Implementation Task: Update `check_folder_dirty()` to use `get_folder_git_status()` internally

## Prompt Sent to LLM:
Implement ONE step from the task tracker.

**1. SELECT STEP**
- Read `pr_info/TASK_TRACKER.md`
- Find the first Step with unchecked sub-tasks (`- [ ]`)
- Work through ALL sub-tasks in that step sequentially
- Announce which task you're working on

**2. FOR EACH SUB-TASK**
- Read linked files in `pr_info/steps/` if referenced
- Implement only what's described
- Run code checks (pylint, pytest, mypy) when required
- Fix all issues before proceeding
- Mark sub-task complete: `- [ ]` → `- [x]`

**3. COMPLETE THE STEP**
- All sub-tasks must be `[x]` before finishing
- Write commit message to `pr_info/.commit_message.txt`
- Do NOT commit - just write the message to the file

**RULES:**
- ONE step per run (but complete all its sub-tasks)
- Mark each sub-task `[x]` immediately after completing it
- Use MCP tools for all operations

Current task from TASK_TRACKER.md: Update `check_folder_dirty()` to use `get_folder_git_status()` internally

Please implement this task step by step.

## LLM Response:
I'll start by reading the task tracker to understand the current state and find the task to implement.Now I can see I need to work on **Step 2**, and the first unchecked sub-task is:
- **Update `check_folder_dirty()` to use `get_folder_git_status()` internally**

Let me read the step 2 details and the current implementation files.Now I understand the task. I need to update `check_folder_dirty()` to use `get_folder_git_status()` internally. Let me create a todo list and implement the change.Now I'll update the `check_folder_dirty()` function to use `get_folder_git_status()` internally. According to the step_2.md instructions, the algorithm is simple:

```python
def check_folder_dirty(folder_path: Path) -> bool:
    status = get_folder_git_status(folder_path)
    # Only "Clean" means definitely not dirty
    # All other states (Dirty, Missing, No Git, Error) return True
    return status != "Clean"
```The edit was successful. Now let me mark this sub-task as complete in the task tracker and update the task status.I've completed the first sub-task of Step 2. Here's a summary of what was done:

## Task Completed: Update `check_folder_dirty()` to use `get_folder_git_status()` internally

### Changes Made
**File:** `src/mcp_coder/workflows/vscodeclaude/status.py:176-188`

**Before:** The function had its own try/except implementation that:
- Ran `git status --porcelain` directly
- Returned `True` on any error (conservative approach)

**After:** The function now delegates to `get_folder_git_status()`:
```python
def check_folder_dirty(folder_path: Path) -> bool:
    """Check if folder has uncommitted changes.

    Args:
        folder_path: Path to git repository

    Returns:
        True if there are uncommitted changes OR if status cannot be determined
        (conservative approach for backward compatibility)
    """
    status = get_folder_git_status(folder_path)
    # Only "Clean" means definitely not dirty
    # All other states (Dirty, Missing, No Git, Error) return True
    return status != "Clean"
```

### Key Points
- **Backward compatible:** Same return type (`bool`) and same conservative behavior (returns `True` for any non-clean state)
- **Code reuse:** Eliminates duplicate git status logic
- **Cleaner:** More maintainable single source of truth for git status checking

The task tracker has been updated to mark this sub-task as complete (`[x]`).

---
Generated on: 2026-02-09T22:50:40.257508