# Implementation Task: Implement `BranchPrepResult` NamedTuple in `orchestrator.py` (step_3.md)

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

Current task from TASK_TRACKER.md: Implement `BranchPrepResult` NamedTuple in `orchestrator.py` (step_3.md)

Please implement this task step by step.

## LLM Response:
I'll start by reading the task tracker to understand the current state and then implement the required step.Now I can see that Step 3 is the current step with unchecked sub-tasks. Let me read the step_3.md file to understand what needs to be implemented.Now let me read the current orchestrator.py file to understand its structure and where to add the new code.Now let me also check what imports are already available and look at the `status.py` for the `get_folder_git_status` function and `issues.py` for the `status_requires_linked_branch` function.I now have all the information I need. Let me also check the existing test file to understand its structure.Now I have a complete picture. Let me create the todo list for this step and start implementing.Now let me implement the `BranchPrepResult` NamedTuple in `orchestrator.py`. I need to add it after the imports and before any function definitions.Now I need to add the import for `status_requires_linked_branch` from `.issues` and add the import for `get_folder_git_status` from `.status`.Now let me add the `BranchPrepResult` NamedTuple class after the imports and before the `__all__` declaration. Let me read a small section to find the right location.Now I can add the `BranchPrepResult` NamedTuple after the logger definition and before `__all__`. Let me edit the file:The `BranchPrepResult` NamedTuple has been implemented. Let me update the task tracker and todo list, then move to the next sub-task.Now let me implement the `_prepare_restart_branch()` function. According to the step_3.md, it should be added before `restart_closed_sessions`. Let me read the current file to find the right location.Now I'll add the `_prepare_restart_branch()` function before `restart_closed_sessions()`:The `_prepare_restart_branch()` function has been implemented. Let me update the task tracker and todo list.Now let me add the tests for `_prepare_restart_branch()`. I need to add a new test class to `test_orchestrator_sessions.py`.Now I'll add the import for `_prepare_restart_branch` and `BranchPrepResult` and the new test class at the end of the file:Now I need to add the test class for `_prepare_restart_branch`. I'll add it at the end of the file:Now let me update the task tracker and run the code checks:Now let me run pylint to check for any issues:The pylint output shows warnings for unused arguments, but these are all in other test files not related to the current step. The key thing is there are no errors or fatal issues in the files I modified. Let me run pylint more specifically on the files I changed:There's a pre-existing deprecation warning not related to my changes. Let me run pytest to verify all tests pass:Let me check if there's an issue with the test file by validating the syntax:Let me run all checks to see if there are any issues:The mypy issues are just about unused type: ignore comments in my tests. Let me remove those unnecessary comments to fix the mypy warnings:The mypy errors are about unused `# type: ignore` comments in my tests. Let me fix those by removing the unnecessary comments:It seems the edit resulted in some duplication. Let me read the file again and fix it properly:The file looks good, but there are still some `# type: ignore` comments that mypy is flagging as unnecessary. Let me run mypy again to verify:Let me remove all the remaining `# type: ignore` comments from the new test class:Only one instance was replaced. Let me search for all remaining instances:I can see there are still several `# type: ignore` comments. Let me remove them all:Now let me run mypy to verify all issues are fixed:All mypy issues are fixed. Let me update the task tracker and write the commit message:Now let me write the commit message to the file:I have completed Step 3 of the task tracker. Here's a summary of what was implemented:

## Step 3 Completed: Add `_prepare_restart_branch()` Helper

### Files Modified:
1. **`src/mcp_coder/workflows/vscodeclaude/orchestrator.py`**
   - Added `NamedTuple` import from `typing`
   - Added imports for `status_requires_linked_branch` from `.issues` and `get_folder_git_status` from `.status`
   - Added `BranchPrepResult` NamedTuple with fields:
     - `should_proceed: bool` - Whether restart can continue
     - `skip_reason: str | None` - Reason if cannot proceed ("No branch", "Dirty", "Git error", "Multi-branch")
     - `branch_name: str | None` - Branch name if switched, None if staying on current
   - Added `_prepare_restart_branch()` function that handles:
     - Running `git fetch origin` (always)
     - Checking if status requires linked branch (status-04/07 do, status-01 doesn't)
     - Getting linked branch from GitHub API
     - Handling multi-branch error cases
     - Checking for dirty repo
     - Performing git checkout and pull

2. **`tests/workflows/vscodeclaude/test_orchestrator_sessions.py`**
   - Added imports for `BranchPrepResult` and `_prepare_restart_branch`
   - Added `TestPrepareRestartBranch` class with 8 tests:
     - `test_status_01_skips_branch_check` - status-01 returns success without branch check
     - `test_status_04_no_branch_returns_skip` - status-04 without branch returns "No branch"
     - `test_status_07_dirty_returns_skip` - dirty repo returns "Dirty"
     - `test_status_04_clean_switches_branch` - successful branch switch
     - `test_git_checkout_failure_returns_error` - checkout failure returns "Git error"
     - `test_git_fetch_always_runs` - git fetch runs for all statuses
     - `test_git_fetch_failure_returns_error` - fetch failure returns "Git error"
     - `test_multi_branch_returns_skip` - multiple branches returns "Multi-branch"

### Verification:
- ✅ Pylint: No errors (only pre-existing warnings in other files)
- ✅ Mypy: No type errors
- ✅ Commit message written to `pr_info/.commit_message.txt`

---
Generated on: 2026-02-10T19:47:38.252387