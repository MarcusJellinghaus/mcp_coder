# Implementation Task: Implement `update_workflow_label()` method in IssueManager class

## Prompt Sent to LLM:
You are implementing tasks from a task tracker. Follow these steps in order:

**STEP 1: SELECT TASK**
- Read `pr_info/TASK_TRACKER.md`
- Find the FIRST unchecked task (format: `- [ ] Task description`)
- Announce which task you're working on

**STEP 2: IMPLEMENT**
- Read the linked step file in `pr_info/steps/` for detailed requirements
- Implement ONLY what's described - no extra complexity
- If you encounter issues or need decisions, ask immediately

**STEP 3: VERIFY WITH CODE QUALITY CHECKS**
- Run MCP code checker tools (pylint, pytest, mypy)
- See `tests/readme.md` for test execution guidelines (avoid slow integration tests when possible)
- Fix ALL issues found by the checkers
- Repeat checks until everything passes

**STEP 4: VERIFY TASK COMPLETION**
- Re-read the task requirements in `pr_info/TASK_TRACKER.md`
- Confirm ALL requirements are met
- Verify all code quality checks pass

**STEP 5: PREPARE COMMIT MESSAGE** ⚠️ REQUIRED
- Generate a short, concise commit message with step name in the title
- DO NOT actually perform the commit - only prepare the message
- Edit `pr_info/TASK_TRACKER.md` and mark the commit message preparation task as complete
- Change its checkbox from `- [ ] Prepare git commit message` to `- [x] Prepare git commit message`

**STEP 6: MARK MAIN TASK COMPLETE** ⚠️ CRITICAL - DO NOT SKIP THIS STEP
- Edit `pr_info/TASK_TRACKER.md` using the appropriate file editing tool
- Change the main implementation task checkbox from `- [ ]` to `- [x]`
- Example: `- [ ] Implement core.py` becomes `- [x] Implement core.py`
- Verify the file was actually updated
- ⚠️ WARNING: If you skip this step, the workflow will loop infinitely on the same task

**CRITICAL RULES:**
- Work on EXACTLY ONE task per run - do not pick additional tasks
- You MUST complete Step 5 (mark task as `[x]`) before finishing
- The checkbox update is non-negotiable and required for workflow progression

Current task from TASK_TRACKER.md: Implement `update_workflow_label()` method in IssueManager class

Please implement this task step by step.

## LLM Response:
I can see the pytest configuration includes addopts with "-n", "auto" which requires pytest-xdist. The issue might be that the MCP pytest server has a problem with the current setup. Since I've verified that:

1. ✅ Mypy passes (only unrelated clipboard.py issues)
2. ✅ Pylint passes  
3. ❌ Pytest MCP tool has an error

Let me inform the user about this issue and ask for their help to run the tests manually. But first, let me make sure my implementation is complete according to the specification. Let me review the checklist from step_2.md:

Looking at the requirements:
- ✅ Method signature matches specification exactly
- ✅ All imports added to top of file
- ✅ `@log_function_call` decorator applied
- ✅ Complete docstring with Args, Returns, Example
- ✅ Branch name regex extracts issue number correctly
- ✅ Branch-issue verification via `get_linked_branches()`
- ✅ Label config loading with proper error handling
- ✅ Idempotent behavior (checks current state)
- ✅ All error cases return False (never raise)
- ✅ Appropriate logging at all levels (INFO/DEBUG/WARNING/ERROR)
- ✅ Uses existing `self.get_issue()` and `self.set_labels()`
- ✅ No GitHub API calls outside existing methods

The implementation is complete according to the specification. The only issue is that I cannot run pytest to verify the tests pass due to the MCP tool error. Let me inform the user and ask them to run the tests manually.

I have successfully implemented the `update_workflow_label()` method in the IssueManager class. The implementation:

## Summary of Implementation

**What was done:**
1. ✅ Added the `update_workflow_label()` method to `IssueManager` class in `src/mcp_coder/utils/github_operations/issue_manager.py`
2. ✅ Implemented all required features:
   - Branch name auto-detection or manual specification
   - Issue number extraction via regex `^(\d+)-`
   - Branch-issue verification via `get_linked_branches()`
   - Label config loading and ID-to-name lookups
   - Idempotent behavior (checks current state)
   - Label transition using existing `set_labels()` method
   - Comprehensive error handling (non-blocking, always returns bool)
   - Proper logging (INFO/DEBUG/WARNING/ERROR levels)

**Code Quality Checks:**
- ✅ **Mypy**: PASSED (only unrelated clipboard.py issues remain)
- ✅ **Pylint**: PASSED (no issues)  
- ❌ **Pytest**: MCP tool error - "Usage Error: pytest command line usage error"

## Issue with Pytest MCP Tool

I encountered a persistent error with the `mcp__code-checker__run_pytest_check` tool. Every invocation returns:
```
Error running pytest: Usage Error: pytest command line usage error
```

This occurs regardless of parameters used (empty, with markers, with extra_args, etc.). The `run_all_checks` tool has the same pytest error.

**Could you please run the tests manually to verify the implementation?**

```bash
# Run the label update tests specifically
python -m pytest tests/utils/github_operations/test_issue_manager_label_update.py -v

# Or run all IssueManager tests  
python -m pytest tests/utils/github_operations/test_issue_manager*.py -v
```

The implementation follows the specification exactly and should pass all 8 test cases from Step 1.

---
Generated on: 2025-11-14T08:21:38.633185